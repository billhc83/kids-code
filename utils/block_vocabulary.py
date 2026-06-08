"""
Block Vocabulary — single source of truth for sketch generation constraints.

Derived from utils/block_parser.py (what the Lark grammar and BlockTransformer produce)
and utils/bb-blocks.js (what the block builder UI renders).

Rules for sketch generators:
  teachable=True  → safe to use as a //?? phantom step (student places the block)
  teachable=False → use //## (pre-placed locked line) instead
  ui_only=True    → block exists in UI palette but parser CANNOT produce it from
                    sketch annotation; phantom steps are not possible
"""

# ── Parser-supported blocks ────────────────────────────────────────────────────
# These are recognized by block_parser.py and produce typed block dicts.

BLOCKS = {

    # ── Variable declarations (global zone only) ────────────────────────────

    "intvar": {
        "syntax":    "int {name} = {value};",
        "zones":     ["global"],
        "teachable": True,
        "note":      "Simple pin/value variables — up to 2 phantoms per step. "
                     "3rd+ variable in same step → lock.",
    },
    "longvar": {
        "syntax":    "long {name} = {value}; | unsigned long {name} = {value};",
        "zones":     ["global"],
        "teachable": False,
        "note":      "Abstract type — always lock.",
    },
    "boolvar": {
        "syntax":    "bool {name} = {value};",
        "zones":     ["global"],
        "teachable": False,
        "note":      "Lock unless bool IS the sole educational focus of the step.",
    },
    "stringvar": {
        "syntax":    'String {name} = "{value}";',
        "zones":     ["global"],
        "teachable": False,
        "note":      "Always lock.",
    },

    # ── Setup blocks ────────────────────────────────────────────────────────

    "pinmode": {
        "syntax":    "pinMode({pin}, {mode});",
        "zones":     ["setup"],
        "teachable": True,
        "note":      "First OUTPUT pin → phantom. First INPUT pin → phantom if INPUT is new concept. "
                     "Additional same-mode pins → lock. Serial.begin always follows as //##.",
    },
    "serialbegin": {
        "syntax":    "Serial.begin(9600);",
        "zones":     ["setup"],
        "teachable": False,
        "note":      "Boilerplate — always lock.",
    },

    # ── Loop / conditional statement blocks ────────────────────────────────

    "digitalwrite": {
        "syntax":    "digitalWrite({pin}, HIGH|LOW);",
        "zones":     ["loop", "if", "for", "while"],
        "teachable": True,
    },
    "analogwrite": {
        "syntax":    "analogWrite({pin}, {0-255});",
        "zones":     ["loop", "if", "for", "while"],
        "teachable": True,
    },
    "tone": {
        "syntax":    "tone({pin}, {freq});",
        "zones":     ["loop", "if", "for", "while"],
        "teachable": True,
    },
    "notone": {
        "syntax":    "noTone({pin});",
        "zones":     ["loop", "if", "for", "while"],
        "teachable": True,
    },
    "delay": {
        "syntax":    "delay({ms});",
        "zones":     ["loop", "if", "for", "while"],
        "teachable": True,
        "note":      "Phantom if educationally meaningful. Lock if < 20ms timing constant.",
    },
    "delaymicroseconds": {
        "syntax":    "delayMicroseconds({us});",
        "zones":     ["loop", "if", "for", "while"],
        "teachable": False,
        "note":      "Microsecond timing is invisible to kids — always lock.",
    },
    "serialprint": {
        "syntax":    "Serial.println({value}); | Serial.print({value});",
        "zones":     ["loop", "if", "for", "while"],
        "teachable": True,
        "note":      "Phantom if Serial IS the new concept. Lock if diagnostic boilerplate.",
    },

    # ── Assignment ──────────────────────────────────────────────────────────

    "setvar": {
        "syntax":    "{name} = {expr};",
        "zones":     ["loop", "if", "for", "while"],
        "teachable": True,
        "note":      "Phantom when variable is one the student declared. "
                     "Lock when RHS contains map()/constrain()/complex math.",
    },
    "increment": {
        "syntax":    "{name}++; | {name}--; | {name} += {val}; | {name} -= {val};",
        "zones":     ["loop", "if", "for", "while"],
        "teachable": True,
    },

    # ── Expression blocks (used as RHS of setvar, in conditions, etc.) ─────

    "digitalread": {
        "syntax":    "digitalRead({pin})",
        "zones":     ["loop", "if", "for", "while"],
        "teachable": True,
        "as_expr":   True,
        "note":      "Used as: sensorVal = digitalRead(pin);",
    },
    "analogread": {
        "syntax":    "analogRead({pin})",
        "zones":     ["loop", "if", "for", "while"],
        "teachable": True,
        "as_expr":   True,
        "note":      "Used as: sensorVal = analogRead(pin);",
    },
    "pulsein": {
        "syntax":    "pulseIn({pin}, HIGH)",
        "zones":     ["loop", "if", "for", "while"],
        "teachable": True,
        "as_expr":   True,
        "note":      "Used as: duration = pulseIn(echoPin, HIGH);",
    },
    "random": {
        "syntax":    "random({lo}, {hi})",
        "zones":     ["loop", "if", "for", "while"],
        "teachable": True,
        "as_expr":   True,
    },
    "millis": {
        "syntax":    "millis()",
        "zones":     ["loop", "if", "for", "while"],
        "teachable": True,
        "as_expr":   True,
        "note":      "Used as: currentTime = millis();",
    },
    "map": {
        "syntax":    "map({val}, {fromLow}, {fromHigh}, {toLow}, {toHigh})",
        "zones":     ["loop", "if", "for", "while"],
        "teachable": False,
        "as_expr":   True,
        "note":      "Too complex for phantom — always lock the entire line.",
    },
    "constrain": {
        "syntax":    "constrain({val}, {lo}, {hi})",
        "zones":     ["loop", "if", "for", "while"],
        "teachable": False,
        "as_expr":   True,
        "note":      "Always lock.",
    },
    "math": {
        "syntax":    "{a} + {b} | {a} - {b} | {a} * {b} | {a} / {b} | {a} % {b}",
        "zones":     ["loop", "if", "for", "while"],
        "teachable": False,
        "as_expr":   True,
        "note":      "Lock lines containing complex math formulas (e.g. distance calculations).",
    },

    # ── Control flow ────────────────────────────────────────────────────────

    "ifblock": {
        "syntax":    "if ({condition}) { ... } [else if (...) { ... }] [else { ... }]",
        "zones":     ["loop", "if", "for", "while"],
        "teachable": True,
        "note":      "ALWAYS split if/else-if/else into separate //>> steps — one per branch.",
    },
    "whileloop": {
        "syntax":    "while ({condition}) { ... }",
        "zones":     ["loop"],
        "teachable": True,
    },
    "forloop": {
        "syntax":    "for ({init}; {cond}; {incr}) { ... }",
        "zones":     ["loop"],
        "teachable": True,
    },

    # ── Servo blocks ────────────────────────────────────────────────────────
    # Parser fully recognises all four servo constructs (added to block_parser.py).
    # Phantom steps are now possible for all of them.

    "servodeclare": {
        "syntax":    "Servo {name};",
        "zones":     ["global"],
        "teachable": True,
        "note":      "Global declaration — phantom when introducing servo for the first time.",
    },
    "servoattach": {
        "syntax":    "{name}.attach({pin});",
        "zones":     ["setup"],
        "teachable": True,
        "note":      "Analogous to pinMode — phantom when attaching the servo in setup.",
    },
    "servowrite": {
        "syntax":    "{name}.write({angle});",
        "zones":     ["loop", "if", "for", "while"],
        "teachable": True,
        "note":      "Main servo action block — phantom whenever the student moves the servo.",
    },
    "servoread": {
        "syntax":    "{name}.read()",
        "zones":     ["loop", "if", "for", "while"],
        "teachable": True,
        "as_expr":   True,
        "note":      "Expression — used as RHS: angle = myServo.read();",
    },
}


# ── Component → block mapping ──────────────────────────────────────────────────
# teachable: blocks that CAN appear as phantom (//??) steps for this component.
# locked:    blocks that must be //## (auto-placed, read-only) for this component.

COMPONENT_BLOCKS = {
    "LED": {
        "teachable": ["pinmode", "digitalwrite"],
        "locked":    [],
    },
    "BUTTON": {
        "teachable": ["pinmode", "digitalread", "ifblock"],
        "locked":    [],
        "note":      "pinMode uses INPUT_PULLUP. Pressed = LOW.",
    },
    "BUZZER": {
        "teachable": ["pinmode", "tone", "notone"],
        "locked":    [],
    },
    "LDR": {
        "teachable": ["analogread", "setvar", "ifblock"],
        "locked":    ["map", "constrain"],
        "note":      "10kΩ pull-down auto-injected. Reads 0–1023.",
    },
    "HC_SR04": {
        "teachable": ["pinmode", "digitalwrite", "pulsein", "setvar"],
        "locked":    ["delaymicroseconds", "math"],
        "note":      "Distance formula (duration * 0.034 / 2) always locked. "
                     "delayMicroseconds always locked.",
    },
    "SLIDE_SWITCH": {
        "teachable": ["pinmode", "digitalread", "ifblock"],
        "locked":    [],
        "note":      "Uses INPUT_PULLUP. Slid ON = LOW.",
    },
    "SERVO": {
        "teachable": ["servodeclare", "servoattach", "servowrite"],
        "locked":    [],
        "note":      "Parser fully supports servo blocks. servodeclare → phantom on first use. "
                     "servoattach → phantom in setup step. servowrite → phantom whenever angle changes.",
    },
}


# ── Variable types the grammar recognises ──────────────────────────────────────

VARIABLE_TYPES = {
    "int":           {"teachable": True,  "note": "Pin numbers and simple integer values"},
    "long":          {"teachable": False, "note": "Timing variables — always lock"},
    "unsigned long": {"teachable": False, "note": "millis() timing — always lock"},
    "bool":          {"teachable": False, "note": "Lock unless bool IS the focus"},
    "String":        {"teachable": False, "note": "Always lock"},
    "float":         {"teachable": False, "note": "Parser produces codeblock — always lock"},
    "byte":          {"teachable": False, "note": "Parser produces codeblock — always lock"},
}


# ── Helpers ────────────────────────────────────────────────────────────────────

def teachable_calls():
    """Return the list of function call syntaxes that can be phantom steps."""
    return [
        b["syntax"] for b in BLOCKS.values()
        if b.get("teachable") and not b.get("as_expr") and not b.get("ui_only")
    ]


def locked_calls():
    """Return the list of function call syntaxes that must be //## locked."""
    return [
        b["syntax"] for b in BLOCKS.values()
        if not b.get("teachable") and not b.get("as_expr")
    ]


def teachable_exprs():
    """Return the list of expression syntaxes that can be phantom steps."""
    return [
        b["syntax"] for b in BLOCKS.values()
        if b.get("teachable") and b.get("as_expr")
    ]


def component_teachable(component_type):
    """Return teachable block names for a given circuit component type."""
    return COMPONENT_BLOCKS.get(component_type, {}).get("teachable", [])


def component_locked(component_type):
    """Return locked block names for a given circuit component type."""
    return COMPONENT_BLOCKS.get(component_type, {}).get("locked", [])
