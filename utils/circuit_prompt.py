"""
LLM prompt builder for the circuit generation pipeline.

The LLM outputs meta + component list + logical connections only.
No coordinates. No resistors. No breadboard awareness.
The engine (circuit_engine.py) handles all physical placement.
"""

SYSTEM_PROMPT = "Output only raw JSON. No markdown fences. No explanation. No preamble."

USER_PROMPT_TEMPLATE = """\
You are a creative director for an Arduino kids learning app (ages 8–14).

Given a project idea, output a single JSON object describing the circuit logically.
The placement engine handles all physical breadboard layout automatically.
Do NOT include coordinates, row numbers, or column letters anywhere in your output.

══ COMPONENT TYPES ══
LED          — props: {{"color": "red" | "green" | "yellow" | "blue" | "white"}}
BUTTON       — props: {{}}   (momentary push button — pressed momentarily)
SLIDE_SWITCH — props: {{}}   (SPDT slide switch — toggled on/off; read via digitalRead + INPUT_PULLUP)
BUZZER       — props: {{}}
SERVO        — props: {{}}
LDR          — props: {{}}   (light-dependent resistor / photoresistor — reads light via analog pin)
HC_SR04      — props: {{}}   (ultrasonic distance sensor)

Resistors are injected automatically for LEDs and LDRs only. Do not include RESISTOR in your component list.
The engine creates them as R_{{component_id}}. Reference them in connections as R_{{id}}.pin1 / R_{{id}}.pin2.
BUTTON, SLIDE_SWITCH, BUZZER, HC_SR04, and SERVO do NOT get a resistor — never use R_{{id}} for them.

══ PIN NAMES (use exactly) ══
LED:          anode (long leg +),  cathode (short leg −)
BUTTON:       TL (top-left E col), TR (top-right F col), BL (bottom-left E col), BR (bottom-right F col)
              Diagonal activation: TL↔BR are one switch pair, BL↔TR are the other pair.
SLIDE_SWITCH: com (common/wiper → Arduino signal), pin2 (active throw → GND)  [pin1 unused]
BUZZER:       positive (+), negative (−)
SERVO:  signal, power, ground
LDR:    pin1 (5V end),  pin2 (analog read / pull-down junction)
HC_SR04: vcc, trig (trigger OUT), echo (echo IN), gnd

Arduino endpoints:
  Digital:  arduino.D2  … arduino.D13   (do not use D0 or D1 — USB reserved)
  Analog:   arduino.A0  … arduino.A5
  Power:    arduino.GND  arduino.5V
  PWM pins (required for servo signal / tone() / analogWrite()): D3 D5 D6 D9 D10 D11
  GND and 5V may appear in multiple connections. Digital/analog pins: one connection each.

══ CONNECTION FORMAT ══
Each connection is {{"from": "X", "to": "Y"}} where X and Y are one of:
  "arduino.D4"          Arduino pin
  "LED1.anode"          component pin  (component_id.pin_name)
  "R_LED1.pin2"         injected resistor pin  (R_{{component_id}}.pin1 or .pin2)

══ OUTPUT FORMAT ══
{{
  "meta": {{
    "title":         "short project title",
    "difficulty":    "easy" | "medium" | "hard",
    "description":   "one sentence — what the student builds",
    "learning_goal": "one sentence — what concept this teaches",
    "code_hint":     "one sentence — what the Arduino sketch does"
  }},
  "components": [
    {{"id": "LED1",  "type": "LED",    "properties": {{"color": "red"}}}},
    {{"id": "BTN1",  "type": "BUTTON", "properties": {{}}}},
    {{"id": "BUZ1",  "type": "BUZZER", "properties": {{}}}},
    {{"id": "SRV1",  "type": "SERVO",  "properties": {{}}}}
  ],
  "connections": [
    {{"from": "...", "to": "..."}}
  ]
}}

══ WIRING RULES ══
LED:    arduino.D{{pin}} → LED1.anode
        LED1.cathode → R_LED1.pin1   (resistor auto-injected)
        R_LED1.pin2  → arduino.GND

BUTTON:       arduino.D{{pin}} → BTN1.TL          (signal — TL-BR diagonal, use INPUT_PULLUP)
              BTN1.BR → arduino.GND               (same diagonal as TL — closes circuit when pressed)

SLIDE_SWITCH: arduino.D{{pin}} → SW1.com           (signal — INPUT_PULLUP reads toggle position)
              SW1.pin2 → arduino.GND               (active throw — completes circuit when slid on)

BUZZER: arduino.D{{pin}} → BUZ1.positive
        BUZ1.negative → arduino.GND

SERVO:  arduino.D{{pwm}} → SRV1.signal      (must be a PWM pin)
        arduino.5V       → SRV1.power
        arduino.GND      → SRV1.ground

LDR:    arduino.5V   → LDR1.pin1            (power top of voltage divider)
        LDR1.pin2    → R_LDR1.pin1          (pull-down auto-injected — 10kΩ)
        R_LDR1.pin2  → arduino.GND
        LDR1.pin2    → arduino.A{{n}}       (read analog voltage at junction)

HC_SR04: arduino.5V       → SR1.vcc
         arduino.GND      → SR1.gnd
         arduino.D{{n}}   → SR1.trig        (trigger — digital OUTPUT)
         SR1.echo         → arduino.D{{m}}  (echo — digital INPUT, different pin from trig)

══ EXAMPLE OUTPUT — 2 LEDs ══
{{
  "meta": {{
    "title":         "Traffic Light",
    "difficulty":    "easy",
    "description":   "Build a two-LED traffic light that blinks red then green.",
    "learning_goal": "Controlling multiple outputs with digital pins",
    "code_hint":     "Turn each LED on and off in sequence with delay() between each"
  }},
  "components": [
    {{"id": "LEDR", "type": "LED", "properties": {{"color": "red"}}}},
    {{"id": "LEDG", "type": "LED", "properties": {{"color": "green"}}}}
  ],
  "connections": [
    {{"from": "arduino.D4",   "to": "LEDR.anode"}},
    {{"from": "LEDR.cathode", "to": "R_LEDR.pin1"}},
    {{"from": "R_LEDR.pin2",  "to": "arduino.GND"}},
    {{"from": "arduino.D5",   "to": "LEDG.anode"}},
    {{"from": "LEDG.cathode", "to": "R_LEDG.pin1"}},
    {{"from": "R_LEDG.pin2",  "to": "arduino.GND"}}
  ]
}}

══ NOW GENERATE ══
Project idea:   {topic}
Components:     {components}
Difficulty:     {difficulty}{pin_hint_line}
"""


def build_prompt(topic, components, difficulty="easy", pin_hint=None):
    """
    Return (system_prompt, user_message) ready to send to the LLM.

    Args:
        topic       — free-text project idea, e.g. "a doorbell that plays a tune"
        components  — list of component types to use, e.g. ["LED", "BUTTON", "BUZZER"]
        difficulty  — "easy", "medium", or "hard"
        pin_hint    — optional list of arduino pin names to constrain, e.g. ["D8", "D9"]
    """
    component_str = ", ".join(components) if isinstance(components, list) else components
    pin_hint_line = (
        f"\nSignal pin assignments — use these digital/analog pins for component connections: {', '.join(pin_hint)}"
        f"\n(arduino.GND and arduino.5V are always required for power/return paths — do not replace them with signal pins)"
        if pin_hint else ""
    )
    user_message = USER_PROMPT_TEMPLATE.format(
        topic=topic,
        components=component_str,
        difficulty=difficulty,
        pin_hint_line=pin_hint_line,
    )
    return SYSTEM_PROMPT, user_message


def print_prompt(topic, components, difficulty="easy"):
    """Print the prompt to stdout for manual copy-paste into an LLM."""
    system, user = build_prompt(topic, components, difficulty)
    print("=" * 60)
    print("SYSTEM PROMPT")
    print("=" * 60)
    print(system)
    print()
    print("=" * 60)
    print("USER MESSAGE")
    print("=" * 60)
    print(user)


if __name__ == "__main__":
    import sys
    topic      = sys.argv[1] if len(sys.argv) > 1 else "a simple LED blink"
    components = sys.argv[2].split(",") if len(sys.argv) > 2 else ["LED"]
    difficulty = sys.argv[3] if len(sys.argv) > 3 else "easy"
    print_prompt(topic, components, difficulty)
