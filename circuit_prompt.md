# Circuit Generation Prompt — circuit_renderer.js

## How to call

- Put the **System Prompt** section below into the LLM system message (or `system_prompt_override`)
- Put the **User Input** section (filled with your circuit spec) as the user message
- Requires **min 2048 tokens** output budget (4096 recommended for circuits with 3+ components)

---

## System Prompt

```
Output only raw JSON. No markdown. No explanation.
```

---

## User Input Template

Replace the `NOW GENERATE` section at the bottom with your specific circuit. Everything above it is fixed.

```
You generate Arduino circuit definitions for a kids learning app.
Output ONLY valid JSON. No markdown fences. No explanation. No preamble. The JSON must exactly match the format and pin names shown below.

════ BREADBOARD LAYOUT ════
Columns (left to right): +1 -1 A B C D E [gap] F G H I J +2 -2
+1/+2 = positive rails, -1/-2 = ground rails.
A–E = left bus (connected within row). F–J = right bus (connected within row).
A–E and F–J in the SAME row are NOT connected (DIP gap between them).
Rows: 1–30 (top to bottom).
CRITICAL: A wire at breadboard.E10 ONLY reaches A–E bus at row 10. It does NOT reach F10–J10.

════ ARDUINO UNO PINS ════
Digital: arduino.D2 through arduino.D13 (avoid D0, D1 — USB reserved)
PWM (analogWrite/servo/tone): arduino.D3 D5 D6 D9 D10 D11
Power: arduino.GND arduino.5V arduino.3V3 arduino.VIN
GND NOTE: Multiple wires may connect to arduino.GND. The "one wire per pin" rule applies to digital/analog pins only.

════ COMPONENT PIN NAMES — use EXACTLY these ════
LED:      anode (long leg +, higher row), cathode (short leg −, anode row − 1)
RESISTOR: pin1, pin2
BUTTON:   TL (top-left), TR (top-right), BL (bottom-left), BR (bottom-right)
          TL/BL on col E, TR/BR on col F — button straddles the DIP gap
          TL/TR same row, BL/BR same row, 1 row apart
BUZZER:   positive (+, marked with dot), negative (−), legs 1 row apart
SERVO:    body (visual anchor only — any convenient col/row near placement area)

════ CIRCUIT RULES ════
1. Every LED needs a 220Ω resistor in series.
   A–E side (left bus):
   LED anode:     col E, row N
   LED cathode:   col E, row N−1   ← anode row minus 1
   Resistor pin1: col D, row N−1   ← same row as cathode
   Resistor pin2: col D, row N−5   ← 4 rows below pin1
   Signal wire: arduino.D{X} → breadboard.A{N}   color "#00AA00"
   Ground wire: breadboard.D{N−5} → arduino.GND  color "#111111"

   F–J side (right bus):
   LED anode:     col F, row N
   LED cathode:   col F, row N−1   ← anode row minus 1
   Resistor pin1: col G, row N−1   ← same row as cathode
   Resistor pin2: col G, row N−5   ← 4 rows below pin1
   Signal wire: arduino.D{X} → breadboard.J{N}   color "#00AA00"
   Ground wire: breadboard.G{N−5} → arduino.GND  color "#111111"

2. Every BUTTON needs a 10kΩ pulldown resistor to GND.

3. BUZZER: positive pin → arduino digital pin (no resistor needed), negative → arduino.GND.

4. SERVO signal MUST use a PWM pin (D3/D5/D6/D9/D10/D11).
   Three connections required: signal (PWM pin), 5V, GND.

5. One wire per digital/analog Arduino pin. GND and 5V accept multiple wires.

6. Wire colours: signal="#00AA00", ground="#111111", power 5V="#CC2222"

════ LED SPACING — USE THESE EXACT ROWS, DO NOT CHANGE THEM ════
Each pair has a PROTECTED ZONE. No pin from any component may share a row with another pair's zone.

Pair 1  PROTECTED ZONE rows 7–12:
  LED anode: E12, cathode: E11, Resistor pin1: D11, pin2: D7
  Signal: arduino.D{X} → breadboard.A12
  Ground: breadboard.D7 → arduino.GND

Pair 2  PROTECTED ZONE rows 17–22:
  LED anode: E22, cathode: E21, Resistor pin1: D21, pin2: D17
  Signal: arduino.D{X} → breadboard.A22
  Ground: breadboard.D17 → arduino.GND

Pair 3  PROTECTED ZONE rows 23–28:
  LED anode: E28, cathode: E27, Resistor pin1: D27, pin2: D23
  Signal: arduino.D{X} → breadboard.A28
  Ground: breadboard.D23 → arduino.GND

CRITICAL: Pair 1 rows {7,11,12}. Pair 2 rows {17,21,22}. Pair 3 rows {23,27,28}. These sets never overlap.

════ F–J SIDE LED ZONES ════
A–E and F–J buses are isolated by the DIP gap — the same row numbers may be used on both sides simultaneously without conflict.

Pair 4  PROTECTED ZONE rows 7–12 (F–J side):
  LED anode: F12, cathode: F11, Resistor pin1: G11, pin2: G7
  Signal: arduino.D{X} → breadboard.J12
  Ground: breadboard.G7 → arduino.GND

Pair 5  PROTECTED ZONE rows 17–22 (F–J side):
  LED anode: F22, cathode: F21, Resistor pin1: G21, pin2: G17
  Signal: arduino.D{X} → breadboard.J22
  Ground: breadboard.G17 → arduino.GND

Pair 6  PROTECTED ZONE rows 23–28 (F–J side):
  LED anode: F28, cathode: F27, Resistor pin1: G27, pin2: G23
  Signal: arduino.D{X} → breadboard.J28
  Ground: breadboard.G23 → arduino.GND

CRITICAL (F–J): Pair 4 rows {7,11,12}. Pair 5 rows {17,21,22}. Pair 6 rows {23,27,28}. These sets never overlap within the F–J bus.

════ WALKTHROUGH RULES ════
List all components first, then all wires. Each step has:
  component: { "type":"component", "id":"...", "instruction":"exact col+row for each leg", "tip":"one kid-friendly sentence" }
  wire:       { "type":"wire", "from":"...", "to":"...", "instruction":"colour + start + end", "tip":"one kid-friendly sentence" }
Use "long leg" for anode, "short leg" for cathode in instructions.

════ BUTTON EXAMPLE (for reference) ════
{ "id": "BTN1", "type": "BUTTON", "pins": { "TL": {"col":"E","row":8}, "TR": {"col":"F","row":8}, "BL": {"col":"E","row":9}, "BR": {"col":"F","row":9} }, "properties": { "color": "#2266CC" } }

════ BUZZER EXAMPLE (for reference) ════
{ "id": "BUZ1", "type": "BUZZER", "pins": { "positive": {"col":"E","row":20}, "negative": {"col":"E","row":21} }, "properties": { "type": "passive" } }

════ SERVO EXAMPLE (for reference) ════
{ "id": "SRV1", "type": "SERVO", "pins": { "body": {"col":"H","row":10} }, "properties": {} }
Servo connections (signal MUST be a PWM pin):
{ "from": "arduino.D9",  "to": "breadboard.H10", "color": "#FF8800", "label": "PWM signal" }
{ "from": "arduino.5V",  "to": "breadboard.I10", "color": "#CC2222", "label": "Power" }
{ "from": "arduino.GND", "to": "breadboard.J10", "color": "#111111", "label": "Ground" }

════ COMPLETE 1-LED EXAMPLE — match this format exactly ════
{
  "meta": { "title": "LED Blink", "difficulty": "beginner" },
  "components": [
    { "id": "LED1", "type": "LED", "pins": { "anode": {"col":"E","row":12}, "cathode": {"col":"E","row":11} }, "properties": { "color": "red" } },
    { "id": "R1",   "type": "RESISTOR", "pins": { "pin1": {"col":"D","row":11}, "pin2": {"col":"D","row":7} }, "properties": { "ohms": 220 } }
  ],
  "connections": [
    { "from": "arduino.D8",    "to": "breadboard.A12", "color": "#00AA00", "label": "Signal to LED anode" },
    { "from": "breadboard.D7", "to": "arduino.GND",    "color": "#111111", "label": "Resistor to GND" }
  ],
  "walkthrough": [
    { "type": "component", "id": "LED1", "instruction": "Place the LED with its long leg (anode) in row 12 column E, and its short leg (cathode) in row 11 column E.", "tip": "The long leg is positive — it's called the anode!" },
    { "type": "component", "id": "R1",   "instruction": "Place the resistor with one leg in row 11 column D and the other leg in row 7 column D.", "tip": "The resistor protects the LED by limiting the current." },
    { "type": "wire", "from": "arduino.D8",    "to": "breadboard.A12", "instruction": "Connect a green wire from Arduino pin D8 to row 12 column A on the breadboard.", "tip": "This wire carries the signal that turns the LED on and off." },
    { "type": "wire", "from": "breadboard.D7", "to": "arduino.GND",    "instruction": "Connect a black wire from row 7 column D on the breadboard to the Arduino GND pin.", "tip": "Black wires always carry ground — the return path for electricity." }
  ]
}

════ NOW GENERATE ════
Generate a circuit for: {TITLE}
Components available: {COMPONENT LIST}
Difficulty: {easy | medium | hard}
Arduino pins to use: {PIN LIST} (optional — omit if not specified)
```

---

## What changed from the original prompt

| Issue | Original | Fixed |
|-------|----------|-------|
| Spacing rule too vague | "Second pair starts 10 rows lower" | Explicit PROTECTED ZONE rows per pair — model must not deviate |
| GND multi-wire ambiguous | "One wire per Arduino pin" | Clarified: rule applies to digital/analog only; GND accepts multiple |
| System prompt too long | Full rules in system_prompt_override | Minimal system prompt; all rules in user_input |
| Output token budget | 1024 (truncates 3-LED circuit) | Requires 2048+; recommend 4096 |

## Key finding from LLM testing

The original prompt caused the model to space LED pairs only 5 rows apart (anodes at rows 12, 17, 22),
which put each resistor's pin2 on the same breadboard row as the previous LED's anode — a short circuit.

The fixed prompt with explicit protected zones produced correct placements (anodes at rows 12, 22, 28)
on the first generative attempt.
