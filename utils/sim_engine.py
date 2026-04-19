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
"""

import re


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _strip_comments(text):
    """Remove // line comments (including //>> directives)."""
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
