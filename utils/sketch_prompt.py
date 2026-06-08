"""
LLM prompt builder for annotated Arduino sketch generation.

Analogous to circuit_prompt.py — the LLM receives the project concept and
circuit pin assignments, and outputs a FULLY ANNOTATED sketch with //>>
//## and //?? directives already applied.

The prompt is built from block_vocabulary.py so it automatically stays in
sync with the parser as new block types are added.
"""

from utils.block_vocabulary import BLOCKS, COMPONENT_BLOCKS, VARIABLE_TYPES

SYSTEM_PROMPT = "Output only the annotated Arduino sketch. No markdown fences. No explanation. No preamble. Start directly with the first //>> line."


def _build_vocabulary_section():
    teachable_stmts = []
    locked_stmts = []
    teachable_exprs = []
    locked_exprs = []

    for name, b in BLOCKS.items():
        if b.get("ui_only"):
            continue
        syntax = b["syntax"]
        if b.get("as_expr"):
            if b.get("teachable"):
                teachable_exprs.append(syntax)
            else:
                locked_exprs.append(syntax)
        else:
            if b.get("teachable"):
                teachable_stmts.append(syntax)
            else:
                locked_stmts.append(syntax)

    lines = ["══ BLOCK VOCABULARY ══",
             "",
             "PHANTOM-eligible statements (use //?? hint then the line):"]
    for s in teachable_stmts:
        lines.append(f"  {s}")

    lines += ["",
              "PHANTOM-eligible expressions (appear as RHS of assignments or in conditions):"]
    for s in teachable_exprs:
        lines.append(f"  {s}")

    lines += ["",
              "ALWAYS LOCK these as //## (never phantom):"]
    for s in locked_stmts + locked_exprs:
        lines.append(f"  {s}")

    lines += ["",
              "Variable types:"]
    for vtype, info in VARIABLE_TYPES.items():
        flag = "phantom OK" if info["teachable"] else "always lock"
        lines.append(f"  {vtype:<16} — {flag}  ({info['note']})")

    return "\n".join(lines)


USER_PROMPT_TEMPLATE = """\
You are an Arduino curriculum author for a kids coding platform (ages 8–14).

Given a project concept and the circuit pin assignments, write a FULLY ANNOTATED
Arduino sketch using the directive system below.

══ DIRECTIVE SYNTAX ══
//>> Step Label | guidance | view
  Marks the START of a new step. guidance: guided/free/open. view: blocks/editor.
  The FINAL step is always:  //>> Mission Complete | open | blocks  (no code after it)

//?? hint text
actual code line;
  Phantom slot — student must place this block. hint is shown inside the block.
  ONE //?? per code line. Hints: 5-10 words, plain English, purpose not syntax.
  ONLY use //?? for lines whose function call is listed under PHANTOM-eligible.

//## actual code line;
  Locked block — pre-placed, read-only. Use for: complex math, boilerplate,
  timing constants, locked calls listed above, and ALL servo lines.

══ GUIDANCE MODES ══
guided — at least one //?? phantom exists in this step
free   — zero phantoms, all lines are //## (student watches step appear)
open   — no validation (Mission Complete step only)

══ STRUCTURAL RULES ══
1. Globals ARE cumulative — declared once, carry forward automatically.
   Do NOT repeat global declarations in later steps.

2. Setup and loop are NOT cumulative — every step chunk that contains
   setup or loop code MUST re-list ALL previous steps' code as //## lines
   before adding new code for this step.

3. Chunks that only declare globals omit void setup() / void loop() wrappers.

4. All other chunks MUST include both void setup() {{}} and void loop() {{}}
   even if one section is empty for that step.

5. if/else-if/else chains MUST be split into separate steps — one per branch:
   - Step for if branch: full if (...) {{}} block, phantom on the if line
   - Step for else if branch: chunk contains ONLY the else if clause
   - Step for else branch: chunk contains ONLY the else clause

6. The //?? directive goes on the line IMMEDIATELY before the code line.
   For else-if and else: //?? goes immediately before the else if / else keyword.

══ if/else SPLIT EXAMPLE ══
//>> Safe Zone | guided | blocks

void setup() {{}}

void loop() {{
  //?? Check if object is in the safe zone
  if (distance > 30) {{
    //?? Turn on the green LED
    digitalWrite(greenLED, HIGH);
    //## noTone(buzzerPin);
  }}
}}

//>> Warning Zone | guided | blocks

void setup() {{}}

void loop() {{
  //?? Add the warning zone check
  else if (distance > 15) {{
    //?? Turn on the yellow LED
    digitalWrite(yellowLED, HIGH);
    //## tone(buzzerPin, 500);
  }}
}}

//>> Danger Zone | guided | blocks

void setup() {{}}

void loop() {{
  //?? Add the danger zone
  else {{
    //?? Turn on the red LED
    digitalWrite(redLED, HIGH);
    //## tone(buzzerPin, 1000);
  }}
}}

{vocabulary}

══ PHANTOM HINT RULES ══
- 5–10 words maximum
- Plain English — describe purpose, not syntax
- Use the project theme where natural
Good:  "Turn on the green safety LED"
Bad:   "digitalWrite(greenLED, HIGH)"
Bad:   "Use a digital write block"

For variable declarations:
Good:  "Declare the trigger pin variable"
Bad:   "Create an int called trigPin"

For control flow:
Good:  "Check if the sensor sees something close"
Bad:   "Write an if statement"

══ STEP COUNT RULE ══
Target approximately {step_count} coding steps PLUS the final Mission Complete step.
if/else-if/else chains count as multiple steps (one per branch).
A global-only step (variable declarations) counts as one step.

══ NOW GENERATE ══
Project:    {topic}
Theme:      {theme}
Age group:  {age_group}
Difficulty: {difficulty}
Components: {components}

Circuit pin assignments (from the circuit designer):
{pin_assignments}

Write the fully annotated sketch now.
Start with the first //>> step. End with //>> Mission Complete | open | blocks
"""


def _format_pin_assignments(circuit_json):
    """
    Extract pin assignments from circuit engine output for the LLM.
    Returns a human-readable string like:
      LED1 anode → Arduino D4 (via signal wire)
      BUZZER BUZ1 positive → Arduino D8
      BUTTON BTN1 TL → Arduino D5
    """
    lines = []
    placed = {c["id"]: c for c in circuit_json.get("components", [])}

    for wire in circuit_json.get("connections", []):
        frm = wire.get("from", "")
        to  = wire.get("to", "")

        # Only report arduino ↔ component signal wires (not power/gnd rail wires)
        if "arduino." in frm and "breadboard." not in to and "-1." not in to and "+1." not in to:
            arduino_pin = frm.replace("arduino.", "")
            comp_ref    = to
            lines.append(f"  {comp_ref} → Arduino {arduino_pin}")
        elif "arduino." in to and "breadboard." not in frm and "-1." not in frm and "+1." not in frm:
            arduino_pin = to.replace("arduino.", "")
            comp_ref    = frm
            lines.append(f"  {comp_ref} → Arduino {arduino_pin}")

    if not lines:
        # Fall back to listing component pin rows
        for cid, info in placed.items():
            ctype = info.get("type", "")
            for pin_name, pin in info.get("pins", {}).items():
                lines.append(f"  {cid}.{pin_name} at breadboard {pin['col']}{pin['row']}")

    return "\n".join(lines) if lines else "  (see circuit JSON for pin details)"


def build_prompt(topic, theme, age_group, difficulty, components, circuit_json,
                 step_count=8):
    """
    Return (system_prompt, user_message) ready for run_local_task.

    Args:
        topic         — project description, e.g. "parking distance alarm"
        theme         — narrative, e.g. "spy gadget that detects intruders"
        age_group     — "8-10", "11-12", or "13-14"
        difficulty    — "easy", "medium", or "hard"
        components    — list of component types, e.g. ["LED", "BUTTON", "BUZZER"]
        circuit_json  — output from circuit_engine.generate_circuit()
        step_count    — target number of coding steps (excluding Mission Complete)
    """
    vocab = _build_vocabulary_section()
    pin_assignments = _format_pin_assignments(circuit_json)
    component_str = ", ".join(components)

    user_message = USER_PROMPT_TEMPLATE.format(
        vocabulary=vocab,
        topic=topic,
        theme=theme,
        age_group=age_group,
        difficulty=difficulty,
        components=component_str,
        pin_assignments=pin_assignments,
        step_count=step_count,
    )
    return SYSTEM_PROMPT, user_message


def count_steps(annotated_sketch):
    """Count the number of //>> steps in an annotated sketch."""
    return sum(1 for line in annotated_sketch.splitlines() if line.startswith("//>>" ))


def validate_sketch(annotated_sketch):
    """
    Basic validation of an annotated sketch.
    Returns (ok: bool, errors: list[str]).
    """
    lines = annotated_sketch.splitlines()
    errors = []

    step_lines = [l for l in lines if l.startswith("//>>")]
    if not step_lines:
        errors.append("No //>> step markers found")
        return False, errors

    if not step_lines[-1].strip().startswith("//>> Mission Complete"):
        errors.append("Last step must be '//>> Mission Complete | open | blocks'")

    # Check phantom directives are immediately followed by a code line
    for i, line in enumerate(lines):
        if line.startswith("//?? "):
            if i + 1 >= len(lines):
                errors.append(f"Phantom directive at line {i+1} has no following code line")
            elif lines[i + 1].startswith("//"):
                errors.append(f"Phantom at line {i+1} is followed by another directive, not code")

    return len(errors) == 0, errors


if __name__ == "__main__":
    import json, sys

    topic      = sys.argv[1] if len(sys.argv) > 1 else "a simple LED blink"
    theme      = sys.argv[2] if len(sys.argv) > 2 else "space mission"
    age_group  = sys.argv[3] if len(sys.argv) > 3 else "11-12"
    difficulty = sys.argv[4] if len(sys.argv) > 4 else "easy"
    components = sys.argv[5].split(",") if len(sys.argv) > 5 else ["LED"]

    # Minimal fake circuit_json for CLI testing
    fake_circuit = {"components": [{"id": "LED1", "type": "LED", "pins": {}}], "connections": [
        {"from": "arduino.D4", "to": "LED1.anode", "color": "#00AA00"}
    ]}

    system, user = build_prompt(topic, theme, age_group, difficulty, components, fake_circuit)
    print("=" * 60)
    print("SYSTEM PROMPT")
    print("=" * 60)
    print(system)
    print()
    print("=" * 60)
    print("USER MESSAGE")
    print("=" * 60)
    print(user)
