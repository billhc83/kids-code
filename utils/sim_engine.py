"""
sim_engine.py — Server-side Arduino sketch parser and timeline builder.

Extracts digitalWrite / delay calls from a student's sketch and returns a
timeline that the frontend SimEngine can animate without understanding any
Arduino code itself.

Public API
----------
run(sketch: str, sim_config: dict) -> dict
    Returns:
        {
            "duration": <total_ms: int>,
            "components": [
                {
                    "id":       "led_13",
                    "type":     "led",
                    "color":    "red",
                    "pin":      13,
                    "label":    "Drone Light",
                    "timeline": [{"t": 0, "state": "off"}, ...]
                },
                ...
            ]
        }

sim_config keys
---------------
  pins            : {str(pin): {"type": "led", "color"?: ..., "label"?: ...}}
  loop_iterations : int  — how many loop() cycles to expand  (default 4)
  max_ms          : int  — hard cap on total timeline duration (default 12000)

interpret(sketch: str, input_state: dict) -> dict
    Phase 0 real interpreter (see SIM_ENGINE_ROLLOUT_SPEC.md). Unlike run()
    above, this actually evaluates if/else against live input state instead
    of blindly replaying every digitalWrite call in source order. It runs
    setup() once then loop() once against a fixed input_state snapshot and
    returns the resulting pin states — there is no timeline, because the
    target UX is discrete request/response per interaction (see spec's
    "Target architecture" section), not animation replay.

    input_state: {pin: value} — value is 0/1 for digitalRead, an int for
    analogRead. Pins absent from input_state default per pin_mode: HIGH (1)
    for INPUT_PULLUP (idle/not-pressed), LOW (0) otherwise.

    Returns:
        {
            "pin_states": {13: "HIGH", 8: "LOW", ...},   # OUTPUT pins only
            "pin_modes":  {13: "OUTPUT", 2: "INPUT_PULLUP", ...},

            # Present only if a pin was written more than once at distinct
            # simulated timestamps within this single loop() pass — i.e. a
            # branch has its own delay()-paced blink/chase, not just a
            # steady on/off. `t` is milliseconds since the pass started,
            # accumulated from that branch's own delay() calls (a per-call
            # clock, reset every interpret() call — not the persistent
            # virtual clock described as Phase 1 in the rollout spec).
            # Frontend consumers should loop this timeline every
            # sequence_duration ms until the next real input event, rather
            # than treating pin_states as the pin's steady value.
            "pin_sequences":     {8: [{"t": 0, "state": "HIGH"}, {"t": 150, "state": "LOW"}]},
            "sequence_duration": 300,   # ms; only present if pin_sequences is non-empty
        }

    Only setup()/loop() are read — //>>, //??, //## block-builder directives
    and anything outside those two functions is ignored. Callers must pass
    the fully-resolved sketch text (what the student's editor/blocks
    currently generate), not a raw multi-step //>>-annotated preset — see
    BLOCK_BUILDER_SYNC.md.

    Phase 1 — persistent state & virtual clock (SIM_ENGINE_ROLLOUT_SPEC.md
    step 4). Real Arduino sketches only run global-var-init + setup() once,
    then loop() forever — but every interpret() call so far re-ran all three
    every time, which is fine when nothing needs to remember anything between
    interactions. Sketches with persistent state (a `running` flag, a
    `startTime` captured from millis()) need setup() to run exactly once and
    globals to survive across calls, so a later loop() sees what an earlier
    one wrote.

    interpret(sketch, input_state, state=None, now_ms=None):
      state:  the `_state` dict returned by a *previous* interpret() call for
              this same sketch/session, or None/{} for a fresh run (power-on:
              globals + setup() execute, a new clock epoch starts). When
              state is provided, globals/setup() are skipped entirely and
              vars/pin_modes/epoch are restored from it before loop() runs —
              callers (the /sim/run route, then the browser) are responsible
              for round-tripping this opaquely between requests.
      now_ms: wall-clock milliseconds to use for this call's millis()/micros()
              — defaults to real time.time()*1000 when omitted. Exposed for
              deterministic tests; callers in production never need to pass
              this.

    Returns the same dict as before, plus:
        "console_lines": ["312"],   # Serial.print/println args, str()'d, in
                                    # call order — only present if the sketch
                                    # printed anything this pass. Serial.begin
                                    # is accepted as an inert no-op. This is
                                    # not the dedicated scrolling Serial
                                    # console component described for `five`/
                                    # `six` in the rollout spec — just enough
                                    # to surface a printed value (e.g.
                                    # `thirteen`'s reaction time) in the
                                    # existing status bar.
        "_state": {"vars": {...}, "pin_modes": {...}, "epoch_ms": 1234.5},
                                    # opaque — pass back verbatim as `state`
                                    # on the next call for this sketch.

    Phase 2 — continuous value mapping (SIM_ENGINE_ROLLOUT_SPEC.md step 5).
    `map()` is now a supported builtin (Arduino's `long`-based five-argument
    range remap — arguments are truncated toward zero the same way a float
    narrows to `long` in real Arduino code, matching e.g. `map(distance, 5,
    50, 200, 1000)` where `distance` is a `float`). This unblocks any sketch
    that turns a continuously-varying sensor reading into a continuously-
    varying output instead of a fixed small set of hand-picked zones —
    `project_seventeen`'s sonar-distance-to-buzzer-pitch harp is the first
    project that needs it.

    Relatedly, `tone(pin, frequency)` no longer collapses to a bare on/off
    write: the frequency argument is captured too. `pin_states`/
    `pin_sequences` are unchanged (a toning pin is still reported "HIGH" for
    on/off-driven UI like an LED), but the result gains:
        "pin_frequencies": {3: 620},   # Hz, only pins currently toning HIGH
    present only when at least one OUTPUT pin ended the pass with an active
    (non-noTone'd) `tone()` call carrying an explicit frequency argument.
    This is what lets a frontend show/play the actual continuous pitch
    rather than just "buzzer is on".

    Phase 3 — Servo actuator (SIM_ENGINE_ROLLOUT_SPEC.md step 6). A global
    `Servo <name>;` declaration (alongside the `#include <Servo.h>` line,
    which is stripped as a preprocessor directive — see _strip_comments)
    registers a servo object with no pin yet. `<name>.attach(pin)` binds it
    to a pin; `<name>.write(angle)` moves it — tracked the same way
    `_record_write` tracks digitalWrite, but on a separate angle-valued
    channel rather than the binary HIGH/LOW one, since a servo's state isn't
    on/off. There's no pinMode()/OUTPUT gate here: a servo pin is designated
    by its own `.attach()` call. The servo/pin binding persists across
    interpret() calls via `state` exactly like pin_modes does, since
    `.attach()` normally only runs once in setup(). `project_nineteen`'s
    gate — sweep to 90°, hold via delay(), sweep back to 0° — is the first
    and, so far, only project that needs this.

    Returns, in addition to everything above:
        "servo_angles": {9: 0},   # last .write() angle per servo pin this
                                   # pass, only present if at least one
                                   # .write() call happened
        "servo_sequences": {9: [{"t": 0, "angle": 90}, {"t": 2000, "angle": 0}]},
                                   # present only if a pin was .write()'n more
                                   # than once at distinct simulated
                                   # timestamps this pass (same collapsing
                                   # rule as pin_sequences) — frontends should
                                   # loop this every sequence_duration ms
                                   # until the next real input event, exactly
                                   # like pin_sequences.
"""

import re
import time


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _strip_comments(text):
    """Remove // line comments (including //>> directives) and preprocessor
    directives (`#include <Servo.h>`, etc.) — the interpreter has no
    preprocessor model, and Servo support (Phase 3) only needs the `Servo`
    type/object the sketch declares, not the header path itself."""
    text = re.sub(r'^\s*#.*$', '', text, flags=re.MULTILINE)
    return re.sub(r'//[^\n]*', '', text)


def _extract_globals(sketch):
    """Return {var_name: int_value} for simple `int x = N;` declarations."""
    result = {}
    for m in re.finditer(r'\bint\s+(\w+)\s*=\s*(\d+)\s*;', sketch):
        result[m.group(1)] = int(m.group(2))
    return result


def _resolve(val, globals_):
    """Resolve a token that may be a variable name or an integer literal."""
    val = val.strip()
    if val in globals_:
        return globals_[val]
    try:
        return int(val)
    except ValueError:
        return None


def _extract_body(sketch, func_name):
    """Return the body of `void func_name()` using brace counting."""
    pattern = re.compile(r'void\s+' + re.escape(func_name) + r'\s*\(\s*\)\s*\{')
    m = pattern.search(sketch)
    if not m:
        return ''
    start = m.end()
    depth = 1
    i = start
    while i < len(sketch) and depth:
        if sketch[i] == '{':
            depth += 1
        elif sketch[i] == '}':
            depth -= 1
        i += 1
    return sketch[start:i - 1]


def _extract_pin_modes(body, globals_):
    """Return {pin: 'INPUT'|'OUTPUT'} for all pinMode() calls found in *body*."""
    modes = {}
    for m in re.finditer(r'pinMode\s*\(\s*(\w+)\s*,\s*(INPUT|OUTPUT)\s*\)', body):
        pin = _resolve(m.group(1), globals_)
        if pin is not None:
            modes[pin] = m.group(2)
    return modes


def _extract_ops(body, globals_):
    """
    Return a list of operations found in *body*, in source order.

    Each op is a tuple:
        ('write', pin: int, signal: str)   — signal is 'HIGH' or 'LOW'
        ('delay', ms: int)
    """
    events = []

    for m in re.finditer(r'digitalWrite\s*\(\s*(\w+)\s*,\s*(HIGH|LOW)\s*\)', body):
        pin = _resolve(m.group(1), globals_)
        if pin is not None:
            events.append((m.start(), 'write', pin, m.group(2)))

    for m in re.finditer(r'\bdelay\s*\(\s*(\w+|\d+)\s*\)', body):
        ms = _resolve(m.group(1), globals_)
        if ms is not None:
            events.append((m.start(), 'delay', ms))

    events.sort(key=lambda x: x[0])
    return [e[1:] for e in events]          # strip position prefix


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def run(sketch, sim_config):
    """
    Parse *sketch* and return a timeline dict ready to JSON-serialise.

    Guards applied:
    - Variables in digitalWrite / delay are resolved to int values.
    - loop() with no delay gets a 1 ms minimum tick so it doesn't spin.
    - Total timeline is capped at sim_config['max_ms'] milliseconds.
    - If a pin emits no events, its timeline still starts with an 'off' state.
    """
    clean    = _strip_comments(sketch)
    globals_ = _extract_globals(clean)

    setup_body = _extract_body(clean, 'setup')
    pin_modes  = _extract_pin_modes(setup_body, globals_)

    setup_ops = _extract_ops(setup_body, globals_)
    loop_ops  = _extract_ops(_extract_body(clean, 'loop'), globals_)

    loop_iterations = int(sim_config.get('loop_iterations', 4))
    max_ms          = int(sim_config.get('max_ms', 12000))
    pins_cfg        = sim_config.get('pins', {})
    tracked         = {int(k): v for k, v in pins_cfg.items()}

    # Initialise per-pin timeline with a t=0 off state
    pin_tl = {pin: [{'t': 0, 'state': 'off'}] for pin in tracked}
    t = 0

    def process(ops):
        nonlocal t
        for op in ops:
            if t >= max_ms:
                return
            if op[0] == 'write':
                _, pin, signal = op
                # Respect pinMode: INPUT pins cannot be driven HIGH/LOW
                if pin in tracked and pin_modes.get(pin, 'OUTPUT') == 'OUTPUT':
                    pin_tl[pin].append({
                        't': t,
                        'state': 'on' if signal == 'HIGH' else 'off',
                    })
            elif op[0] == 'delay':
                _, ms = op
                t = min(t + ms, max_ms)

    process(setup_ops)

    # Guard: loop with no delay would produce a zero-duration cycle
    has_delay = any(op[0] == 'delay' for op in loop_ops)
    if loop_ops and not has_delay:
        loop_ops = list(loop_ops) + [('delay', 1)]

    for _ in range(loop_iterations):
        if t >= max_ms:
            break
        process(loop_ops)

    # Build component descriptors
    components = []
    for pin, cfg in tracked.items():
        comp_id = '{type}_{pin}'.format(type=cfg.get('type', 'led'), pin=pin)
        components.append({
            'id':       comp_id,
            'type':     cfg.get('type', 'led'),
            'color':    cfg.get('color', 'red'),
            'pin':      pin,
            'label':    cfg.get('label', 'Pin {}'.format(pin)),
            'pin_mode': pin_modes.get(pin, 'OUTPUT'),
            'timeline': pin_tl[pin],
        })

    return {
        'duration':   t,
        'components': components,
    }


# ---------------------------------------------------------------------------
# Phase 0 interpreter — tokenizer
# ---------------------------------------------------------------------------

_TOKEN_REGEX = re.compile(r'''
      (?P<NUMBER>\d+\.\d+|\d+)
    | (?P<STRING>"[^"]*")
    | (?P<IDENT>[A-Za-z_]\w*)
    | (?P<OP>==|!=|<=|>=|&&|\|\||[<>=!(){};,.+\-*/%])
    | (?P<SKIP>[ \t\r\n]+)
    | (?P<MISMATCH>.)
''', re.VERBOSE)


def _tokenize(text):
    """Return a list of (kind, value) tokens. kind in NUMBER/STRING/IDENT/OP."""
    tokens = []
    for m in _TOKEN_REGEX.finditer(text):
        kind = m.lastgroup
        value = m.group()
        if kind == 'SKIP':
            continue
        if kind == 'MISMATCH':
            raise ValueError(f"Unexpected character {value!r} in sketch")
        tokens.append((kind, value))
    return tokens


# ---------------------------------------------------------------------------
# Phase 0 interpreter — parser
#
# AST nodes are tagged tuples (same style as circuit_engine.py's resolved-ref
# tuples), not a class hierarchy:
#   statements:  ('vardecl', type, name, expr_or_None)
#                ('exprstmt', expr)
#                ('block', [stmt, ...])
#                ('if', [(cond_expr, [stmt, ...]), ...], else_stmts_or_None)
#   expressions: ('num', int) | ('str', str) | ('ident', name)
#                ('unary', '!', expr)
#                ('binop', op, left, right)
#                ('assign', name, expr)
#                ('call', name, [arg_expr, ...])
# ---------------------------------------------------------------------------

_TYPE_KEYWORDS = ('int', 'bool', 'String', 'long', 'float', 'Servo')


class _Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def peek(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def peek_next(self):
        return self.tokens[self.pos + 1] if self.pos + 1 < len(self.tokens) else None

    def advance(self):
        tok = self.tokens[self.pos]
        self.pos += 1
        return tok

    def check(self, value):
        tok = self.peek()
        return tok is not None and tok[1] == value

    def starts_vardecl(self):
        """True if the token at `pos` begins a variable declaration —
        either a single-word type keyword or the two-word `unsigned long`."""
        tok = self.peek()
        if tok is None:
            return False
        if tok[1] in _TYPE_KEYWORDS:
            return True
        nxt = self.peek_next()
        return tok[1] == 'unsigned' and nxt is not None and nxt[1] == 'long'

    def expect(self, value):
        tok = self.peek()
        if tok is None or tok[1] != value:
            got = tok[1] if tok else 'end of sketch'
            raise ValueError(f"Expected '{value}' but found '{got}'")
        return self.advance()

    # -- top level --------------------------------------------------------

    def parse_program(self):
        """Return (global_stmts, {func_name: [stmt, ...]})."""
        global_stmts = []
        functions = {}
        while self.peek() is not None:
            tok = self.peek()
            if tok[1] == 'void':
                self.advance()
                name_tok = self.advance()
                self.expect('(')
                self.expect(')')
                functions[name_tok[1]] = self.parse_block()
            elif self.starts_vardecl():
                global_stmts.append(self.parse_vardecl())
            else:
                raise ValueError(
                    f"Unexpected top-level token '{tok[1]}' — sim interpreter only "
                    "understands global variable declarations and void setup()/loop()"
                )
        return global_stmts, functions

    # -- statements ---------------------------------------------------------

    def parse_block(self):
        self.expect('{')
        stmts = []
        while not self.check('}'):
            if self.peek() is None:
                raise ValueError("Unexpected end of sketch — missing '}'")
            stmts.append(self.parse_statement())
        self.expect('}')
        return stmts

    def parse_block_or_single(self):
        if self.check('{'):
            return self.parse_block()
        return [self.parse_statement()]

    def parse_statement(self):
        tok = self.peek()
        if tok is None:
            raise ValueError("Unexpected end of sketch")
        if self.starts_vardecl():
            return self.parse_vardecl()
        if tok[1] == 'if':
            return self.parse_if()
        if tok[1] == '{':
            return ('block', self.parse_block())
        return self.parse_expr_statement()

    def parse_vardecl(self):
        vtype = self.advance()[1]
        if vtype == 'unsigned':
            self.expect('long')
            vtype = 'unsigned long'
        name_tok = self.advance()
        if name_tok[0] != 'IDENT':
            raise ValueError(f"Expected a variable name after '{vtype}', found '{name_tok[1]}'")
        expr = None
        if self.check('='):
            self.advance()
            expr = self.parse_expr()
        self.expect(';')
        return ('vardecl', vtype, name_tok[1], expr)

    def parse_expr_statement(self):
        expr = self.parse_expr()
        self.expect(';')
        return ('exprstmt', expr)

    def parse_if(self):
        self.expect('if')
        self.expect('(')
        cond = self.parse_expr()
        self.expect(')')
        branches = [(cond, self.parse_block_or_single())]
        else_block = None
        while self.check('else'):
            self.advance()
            if self.check('if'):
                self.advance()
                self.expect('(')
                cond2 = self.parse_expr()
                self.expect(')')
                branches.append((cond2, self.parse_block_or_single()))
            else:
                else_block = self.parse_block_or_single()
                break
        return ('if', branches, else_block)

    # -- expressions (precedence, low → high) --------------------------------

    def parse_expr(self):
        return self.parse_assignment()

    def parse_assignment(self):
        tok, nxt = self.peek(), self.peek_next()
        if tok is not None and tok[0] == 'IDENT' and nxt is not None and nxt[1] == '=':
            name = self.advance()[1]
            self.advance()  # '='
            return ('assign', name, self.parse_assignment())
        return self.parse_or()

    def parse_or(self):
        left = self.parse_and()
        while self.check('||'):
            self.advance()
            left = ('binop', '||', left, self.parse_and())
        return left

    def parse_and(self):
        left = self.parse_equality()
        while self.check('&&'):
            self.advance()
            left = ('binop', '&&', left, self.parse_equality())
        return left

    def parse_equality(self):
        left = self.parse_relational()
        while self.peek() is not None and self.peek()[1] in ('==', '!='):
            op = self.advance()[1]
            left = ('binop', op, left, self.parse_relational())
        return left

    def parse_relational(self):
        left = self.parse_additive()
        while self.peek() is not None and self.peek()[1] in ('<', '>', '<=', '>='):
            op = self.advance()[1]
            left = ('binop', op, left, self.parse_additive())
        return left

    def parse_additive(self):
        left = self.parse_multiplicative()
        while self.peek() is not None and self.peek()[1] in ('+', '-'):
            op = self.advance()[1]
            left = ('binop', op, left, self.parse_multiplicative())
        return left

    def parse_multiplicative(self):
        left = self.parse_unary()
        while self.peek() is not None and self.peek()[1] in ('*', '/', '%'):
            op = self.advance()[1]
            left = ('binop', op, left, self.parse_unary())
        return left

    def parse_unary(self):
        if self.check('!'):
            self.advance()
            return ('unary', '!', self.parse_unary())
        if self.check('-'):
            self.advance()
            return ('unary', '-', self.parse_unary())
        return self.parse_primary()

    def parse_primary(self):
        tok = self.peek()
        if tok is None:
            raise ValueError("Unexpected end of sketch inside an expression")
        if tok[0] == 'NUMBER':
            self.advance()
            return ('num', float(tok[1]) if '.' in tok[1] else int(tok[1]))
        if tok[0] == 'STRING':
            self.advance()
            return ('str', tok[1][1:-1])
        if tok[1] == '(':
            self.advance()
            expr = self.parse_expr()
            self.expect(')')
            return expr
        if tok[0] == 'IDENT':
            self.advance()
            name = tok[1]
            while self.check('.'):          # e.g. Serial.println
                self.advance()
                name += '.' + self.advance()[1]
            if self.check('('):
                self.advance()
                args = []
                if not self.check(')'):
                    args.append(self.parse_expr())
                    while self.check(','):
                        self.advance()
                        args.append(self.parse_expr())
                self.expect(')')
                return ('call', name, args)
            return ('ident', name)
        raise ValueError(f"Unexpected token '{tok[1]}' in expression")


# ---------------------------------------------------------------------------
# Phase 0 interpreter — evaluator
# ---------------------------------------------------------------------------

_CONSTANTS = {
    'HIGH': 1, 'LOW': 0,
    'INPUT': 'INPUT', 'OUTPUT': 'OUTPUT', 'INPUT_PULLUP': 'INPUT_PULLUP',
    'true': True, 'false': False,
    # Uno's analog pins are physically pins 14-19 on the chip — analogRead(A0)
    # compiles to analogRead(14) on real hardware, so these resolve the same
    # way rather than occupying a separate namespace from digital pins 0-13.
    'A0': 14, 'A1': 15, 'A2': 16, 'A3': 17, 'A4': 18, 'A5': 19,
}

_DEFAULTS_BY_TYPE = {
    'int': 0, 'bool': False, 'String': '',
    'long': 0, 'unsigned long': 0, 'float': 0.0,
}

# Soft cap on a single loop() pass's accumulated delay() time, so a
# pathological sketch (many/huge delay() calls) can't produce an unbounded
# pin_sequences timeline. Raised from 4000 to fit project_twelve's redesigned
# counter chase (three sequential 1500ms delays = 4500ms in the pass where
# the red light fires) — 4000 was silently truncating that pass's last
# delay by 500ms, cutting the final light's on-phase short with no error.
_MAX_LOOP_MS = 6000


class _Env:
    def __init__(self, input_state, vars_=None, pin_modes=None, epoch_ms=None, now_ms=None,
                 servo_pins=None):
        self.vars = dict(vars_) if vars_ else {}
        self.pin_modes = dict(pin_modes) if pin_modes else {}
        self.outputs = {}
        self.t = 0                # per-pass virtual clock, advanced by delay()
        self.sequence = {}        # {pin: [(t, state), ...]} — write history for this pass
        self.frequencies = {}     # {pin: hz} — last tone() frequency argument per pin
        self.console = []         # completed Serial lines, str()'d, in call order
        self.console_buf = ''     # in-progress line — Serial.print() args accumulate
                                   # here without a newline, same as real hardware,
                                   # until a Serial.println() (or end of pass) flushes it
        # {servo_var_name: pin_or_None} — registered by a `Servo x;` global
        # declaration, bound to a pin by that variable's own .attach() call.
        # Restored from Phase 1 `state` like pin_modes/vars, since a Servo
        # object (like a pin's mode) is set up once and must survive across
        # discrete interpret() calls, not just within one pass.
        self.servo_pins = dict(servo_pins) if servo_pins else {}
        self.servo_angles = {}    # {pin: angle} — last .write() angle per pin, this pass
        self.servo_sequence = {}  # {pin: [(t, angle), ...]} — write history for this pass
        self.input_state = {int(k): v for k, v in (input_state or {}).items()}
        # Persistent (Phase 1) wall-clock backing for millis()/micros(): `now_ms`
        # is when *this* call happens, `epoch_ms` is when setup() first ran —
        # both real time.time()*1000 unless a test overrides `now_ms`.
        self.now_ms = now_ms if now_ms is not None else time.time() * 1000.0
        self.epoch_ms = epoch_ms if epoch_ms is not None else self.now_ms


def _truthy(value):
    if isinstance(value, str):
        return value != ''
    return bool(value)


def _eval_expr(node, env):
    kind = node[0]
    if kind == 'num' or kind == 'str':
        return node[1]
    if kind == 'ident':
        name = node[1]
        if name in env.vars:
            return env.vars[name]
        if name in _CONSTANTS:
            return _CONSTANTS[name]
        raise ValueError(f"Unknown identifier '{name}'")
    if kind == 'unary':
        operand = _eval_expr(node[2], env)
        if node[1] == '-':
            return -operand
        return not _truthy(operand)
    if kind == 'binop':
        op = node[1]
        if op == '&&':
            return _truthy(_eval_expr(node[2], env)) and _truthy(_eval_expr(node[3], env))
        if op == '||':
            return _truthy(_eval_expr(node[2], env)) or _truthy(_eval_expr(node[3], env))
        left, right = _eval_expr(node[2], env), _eval_expr(node[3], env)
        if op == '==':
            return left == right
        if op == '!=':
            return left != right
        if op == '<':
            return left < right
        if op == '>':
            return left > right
        if op == '<=':
            return left <= right
        if op == '>=':
            return left >= right
        if op == '+':
            return left + right
        if op == '-':
            return left - right
        if op == '*':
            return left * right
        if op in ('/', '%'):
            if right == 0:
                raise ValueError("Division by zero in sim sketch")
            if op == '%':
                return left % right
            # C truncates int/int division toward zero; Python's int() on a
            # float already does exactly that (unlike floor-dividing '//').
            is_int_division = (
                isinstance(left, int) and isinstance(right, int)
                and not isinstance(left, bool) and not isinstance(right, bool)
            )
            return int(left / right) if is_int_division else left / right
        raise ValueError(f"Unsupported operator '{op}'")
    if kind == 'assign':
        value = _eval_expr(node[2], env)
        env.vars[node[1]] = value
        return value
    if kind == 'call':
        return _eval_call(node[1], node[2], env)
    raise ValueError(f"Unsupported expression node {node!r}")


def _record_write(env, pin, state, frequency=None):
    """Set *pin*'s output state (OUTPUT pins only) and log it at the current
    virtual-clock time, so a repeated write after a delay() shows up as a
    timed sequence rather than just overwriting the final value.

    *frequency*, when given, is a tone() call's Hz argument — recorded
    separately from `state` so a continuous pitch isn't lost to the binary
    on/off `state` value (see Phase 2, module docstring)."""
    if env.pin_modes.get(pin, 'OUTPUT') == 'OUTPUT':
        env.outputs[pin] = state
        env.sequence.setdefault(pin, []).append((env.t, state))
        if frequency is not None:
            env.frequencies[pin] = frequency


def _record_servo_write(env, pin, angle):
    """Set *pin*'s servo angle and log it at the current virtual-clock time —
    same shape as _record_write's digitalWrite history, so a servo that
    moves, holds via delay(), then moves again (e.g. project_nineteen's
    open-wait-close gate) produces a timed sequence instead of only ever
    reporting the final angle. Unlike digitalWrite, there's no pinMode/
    OUTPUT gate here — a servo pin is designated by its own .attach() call,
    not pinMode()."""
    env.servo_angles[pin] = angle
    env.servo_sequence.setdefault(pin, []).append((env.t, angle))


def _eval_call(name, arg_nodes, env):
    args = [_eval_expr(a, env) for a in arg_nodes]

    if '.' in name:
        base, method = name.split('.', 1)
        if base in env.servo_pins:
            if method == 'attach':
                env.servo_pins[base] = int(args[0])
                return None
            if method == 'write':
                pin = env.servo_pins.get(base)
                if pin is None:
                    raise ValueError(f"Servo '{base}'.write() called before .attach()")
                _record_servo_write(env, pin, int(args[0]))
                return None

    if name == 'pinMode':
        pin, mode = int(args[0]), args[1]
        env.pin_modes[pin] = mode
        return None
    if name == 'digitalRead':
        pin = int(args[0])
        default = 1 if env.pin_modes.get(pin) == 'INPUT_PULLUP' else 0
        return env.input_state.get(pin, default)
    if name == 'analogRead':
        pin = int(args[0])
        return env.input_state.get(pin, 0)
    if name == 'digitalWrite':
        pin, value = int(args[0]), args[1]
        _record_write(env, pin, 'HIGH' if _truthy(value) else 'LOW')
        return None
    if name in ('tone', 'noTone'):
        pin = int(args[0])
        freq = args[1] if name == 'tone' and len(args) >= 2 else None
        _record_write(env, pin, 'HIGH' if name == 'tone' else 'LOW', frequency=freq)
        return None
    if name == 'map':
        if len(args) != 5:
            raise ValueError("map() expects exactly 5 arguments")
        x, in_min, in_max, out_min, out_max = (int(a) for a in args)
        denom = in_max - in_min
        if denom == 0:
            raise ValueError("map() called with in_min == in_max (division by zero)")
        # Arduino's map() is `long`-typed throughout — args narrow from float
        # the same way a C++ implicit cast would (Python's int() on a float
        # already truncates toward zero, matching that narrowing), and the
        # final division truncates toward zero too (same convention as the
        # '/' operator above, not Python's floor-dividing '//').
        return int((x - in_min) * (out_max - out_min) / denom) + out_min
    if name == 'delay':
        env.t = min(env.t + int(args[0]), _MAX_LOOP_MS)
        return None
    if name == 'delayMicroseconds':
        # Real trigger pulses are 2-10us — negligible next to the ms-scale
        # per-pass clock that drives pin_sequences, so treated as inert
        # (same as delay() was before Phase 0's timed-sequence work).
        return None
    if name == 'millis':
        return int(env.now_ms - env.epoch_ms)
    if name == 'micros':
        return int((env.now_ms - env.epoch_ms) * 1000)
    if name == 'pulseIn':
        # No real electrical pulse exists in this simulation — the sonar
        # input component supplies the pulse duration (microseconds)
        # directly via input_state, keyed by the echo pin, same as
        # digitalRead/analogRead read live component state for their pins.
        pin = int(args[0])
        return env.input_state.get(pin, 0)
    if name in ('Serial.begin',):
        return None
    if name in ('Serial.print', 'Serial.println'):
        if args:
            env.console_buf += str(args[0])
        if name == 'Serial.println':
            env.console.append(env.console_buf)
            env.console_buf = ''
        return None
    raise ValueError(f"'{name}()' is not supported by the sim interpreter yet")


def _exec_block(stmts, env):
    for stmt in stmts:
        _exec_stmt(stmt, env)


def _exec_stmt(stmt, env):
    kind = stmt[0]
    if kind == 'vardecl':
        _, vtype, name, expr = stmt
        if vtype == 'Servo':
            # A `Servo gateServo;` declaration registers the object with no
            # pin yet — env.vars is for plain values, not the servo/pin
            # binding, which lives in env.servo_pins (see _Env docstring).
            env.servo_pins.setdefault(name, None)
        else:
            env.vars[name] = _eval_expr(expr, env) if expr is not None else _DEFAULTS_BY_TYPE.get(vtype, 0)
    elif kind == 'exprstmt':
        _eval_expr(stmt[1], env)
    elif kind == 'block':
        _exec_block(stmt[1], env)
    elif kind == 'if':
        _, branches, else_block = stmt
        for cond, block in branches:
            if _truthy(_eval_expr(cond, env)):
                _exec_block(block, env)
                return
        if else_block is not None:
            _exec_block(else_block, env)
    else:
        raise ValueError(f"Unsupported statement {stmt!r}")


# ---------------------------------------------------------------------------
# Phase 0 interpreter — public entry point
# ---------------------------------------------------------------------------

def interpret(sketch, input_state=None, state=None, now_ms=None):
    """
    Evaluate *sketch* once against a fixed *input_state* snapshot and return
    the resulting output pin states. See module docstring for the full
    contract (including the Phase 1 `state`/`now_ms` params and the returned
    `_state` key); see SIM_ENGINE_ROLLOUT_SPEC.md for what this covers vs.
    defers.
    """
    clean = _strip_comments(sketch)
    tokens = _tokenize(clean)
    global_stmts, functions = _Parser(tokens).parse_program()

    if state:
        # Not the first call for this sketch/session — globals + setup()
        # already ran once; restore what they produced instead of re-running
        # them (re-running would reset e.g. a `running` flag or `startTime`
        # back to its initial value every single call).
        env = _Env(
            input_state,
            vars_=state.get('vars'),
            pin_modes=state.get('pin_modes'),
            epoch_ms=state.get('epoch_ms'),
            now_ms=now_ms,
            servo_pins=state.get('servo_pins'),
        )
    else:
        env = _Env(input_state, now_ms=now_ms)
        _exec_block(global_stmts, env)
        if 'setup' in functions:
            _exec_block(functions['setup'], env)
    if 'loop' in functions:
        _exec_block(functions['loop'], env)

    pin_sequences = {}
    for pin, events in env.sequence.items():
        collapsed = []
        for t, state in events:
            if collapsed and collapsed[-1][0] == t:
                collapsed[-1] = (t, state)
            else:
                collapsed.append((t, state))
        if len(collapsed) > 1:
            pin_sequences[pin] = [{'t': t, 'state': state} for t, state in collapsed]

    servo_sequences = {}
    for pin, events in env.servo_sequence.items():
        collapsed = []
        for t, angle in events:
            if collapsed and collapsed[-1][0] == t:
                collapsed[-1] = (t, angle)
            else:
                collapsed.append((t, angle))
        if len(collapsed) > 1:
            servo_sequences[pin] = [{'t': t, 'angle': angle} for t, angle in collapsed]

    result = {
        'pin_states': env.outputs,
        'pin_modes': env.pin_modes,
    }
    if pin_sequences or servo_sequences:
        result['sequence_duration'] = env.t
    if pin_sequences:
        result['pin_sequences'] = pin_sequences
    if servo_sequences:
        result['servo_sequences'] = servo_sequences
    if env.servo_angles:
        result['servo_angles'] = env.servo_angles
    pin_frequencies = {
        pin: freq for pin, freq in env.frequencies.items()
        if env.outputs.get(pin) == 'HIGH'
    }
    if pin_frequencies:
        result['pin_frequencies'] = pin_frequencies
    if env.console_buf:
        # A trailing Serial.print() with no matching println() before the pass
        # ended still needs to reach the console — this pass's interpret() call
        # won't run again to flush it later (each call gets a fresh buffer).
        env.console.append(env.console_buf)
        env.console_buf = ''
    if env.console:
        result['console_lines'] = env.console
    result['_state'] = {
        'vars': env.vars,
        'pin_modes': env.pin_modes,
        'epoch_ms': env.epoch_ms,
        'servo_pins': env.servo_pins,
    }
    return result
