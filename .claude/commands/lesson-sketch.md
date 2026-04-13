# /lesson-sketch — Annotate a Sketch with Progression Directives

The user provides a complete Arduino sketch. This skill segments it into guided
progression steps and annotates every line with the correct directive flags.

Read CLAUDE.md before doing anything else — particularly the directive syntax
reference and the step chunk structure rules.

---

## What this skill does NOT do

It does not write, modify, or improve the Arduino code. The user's sketch is
the source of truth. The skill only decides WHERE step boundaries go and WHICH
directive each line gets.

---

## Step 1 — Read the project type first

Before asking the user for anything, read `utils/{project_key}.py` if a
`project_key` was supplied. Check `META['lesson_type']`.

- If `lesson_type` is `'troubleshoot'` → jump directly to **Troubleshoot Mode** below.
- If `lesson_type` is `'progression'` or missing → continue with the standard flow.

If no `project_key` was supplied yet, ask for it first, then read the file.

---

## Troubleshoot mode

When `META['lesson_type'] == 'troubleshoot'` the annotation process is
fundamentally different. Do not apply the standard step analysis.

**Ask for ONE thing:**

**`broken_sketch`**
The complete broken Arduino sketch as it should appear to the student —
already containing the intentional bug(s). The student will see this code
in the block builder and must diagnose and fix it.

The skill does NOT analyse, annotate, lock, or add phantom directives.
The broken sketch is loaded as-is into an `open` step so the student can
freely edit every block.

**Generate this annotated sketch:**

```cpp
//>> Find the Bug | open | blocks

{broken_sketch_pasted_verbatim_here}

//>> Mission Complete | open | blocks
```

That is the entire sketch. Two steps, no directives, no `//##`, no `//?? `.

Show the wrapped sketch to the user and ask:
"Does this look right? Ready to write to the file?"

On approval, write it to `SKETCH_PRESET['sketch']` in `utils/{project_key}.py`
and report:

```
✅ utils/{project_key}.py updated — troubleshoot sketch written.

Steps: 2
  Step 1  │ Find the Bug    │ open
  Step 2  │ Mission Complete│ open

📋 Next:
  [ ] Run /lesson-drawer to generate drawer content
      (drawer will generate: Challenge → Sim → Hints for step 1,
       Mission Complete for step 2)
```

---

## Standard progression mode

## Step 1 — Gather inputs

Ask for all missing items in ONE message.

**Required:**

**`sketch`**
The complete Arduino sketch. User pastes the full code.

**`project_key`**
Which project to update. E.g. `project_sixteen`. The skill will write the
result into `utils/{project_key}.py`.

**`step_count`**
Approximate number of steps the user wants. The skill will adjust upward if
an if/else chain must be split (one step per zone), but will not go below
the requested count.

**Optional:**

**`placements`**
Any specific instructions about where certain things should land. Examples:
- "Lock the distance calculation entirely"
- "Put all three LED zones as separate steps"
- "Combine the sensor prep and signal send into one step"
- "Keep setup as a single free step"

If not provided, the skill uses its default rules.

**`default_view`**
`blocks` or `editor`. Default: `blocks`.

---

## Step 2 — Analyse the sketch silently

Before showing the user anything, mentally parse the sketch:

1. Split into three sections: **globals**, **setup()**, **loop()**
2. Within each section, identify every statement
3. Identify all if/else/else-if chains in the loop — each zone will become
   its own step
4. Count the natural logical groups in the loop
5. Reconcile with the user's requested step count

Apply placement overrides from `placements` if provided.

---

## Step 3 — Show the plan and get approval

Present a step breakdown table. Do not generate any annotated code yet.

```
Sketch analysis: {project_key}
──────────────────────────────────────────────
Step 1  │ Variables          │ guided  │ 3 phantom, 2 locked
Step 2  │ Setup              │ guided  │ 2 phantom, 2 locked
Step 3  │ Prepare Sensor     │ guided  │ 1 phantom, 1 locked
Step 4  │ Send Signal        │ guided  │ 1 phantom, 2 locked
Step 5  │ Listen for Echo    │ guided  │ 1 phantom
Step 6  │ Calculate Distance │ free    │ 1 locked (complex math)
Step 7  │ Safe Zone          │ guided  │ 1 phantom (if), 1 phantom, 1 locked
Step 8  │ Warning Zone       │ guided  │ 1 phantom (else if), 1 phantom, 1 locked
Step 9  │ Danger Zone        │ guided  │ 1 phantom (else), 1 phantom, 1 locked
──────────────────────────────────────────────
Total: 9 steps  (requested: ~9)
```

For each step, also list:
- Which lines will be phantom (with their hint text)
- Which lines will be locked

Example:
```
Step 1 — Variables │ guided
  phantom:  int trigPin = 9;       → "Declare the trigger pin variable"
  phantom:  int echoPin = 10;      → "Declare the echo pin variable"
  locked:   int buzzerPin = 3;
  locked:   int greenLED = 4;
  locked:   long duration = 0;
  locked:   float distance = 0;
```

Ask: "Does this plan look right? Any changes before I generate the sketch?"

Wait for explicit approval before proceeding.

---

## Step 4 — Generate the annotated sketch

Once the plan is approved, generate the full annotated sketch.

### Directive syntax — memorise these exactly

```
//>> Step Label | guidance | view
```
Step boundary. Pipe-separated. `guidance` and `view` are optional (default:
`guided`, `blocks`). This line marks the START of a new step.

```
//?? hint text
actual code line;
```
Phantom slot. The hint line immediately precedes the code line the student
must place. ONE `//?? ` per code line. The hint is the instruction shown in
the block.

```
//## actual code line;
```
Locked block. The code after `//##` is shown pre-placed and read-only.
One statement per `//##` line. For multi-line constructs that need locking,
lock each line individually.

**Guidance modes:**
- `guided` — student places phantom blocks, validation checks completion
- `free`   — all blocks pre-filled/locked, student just watches the step appear
- `full`   — blocks pre-filled, student confirms each one
- `open`   — no structure, no validation, free build

---

### Structural rules for step chunks

Each step chunk is the text between two `//>>` markers (or between the last
marker and end of file). The parser reads each chunk as a mini-sketch.

**Every chunk that contains setup or loop code MUST include the appropriate
wrapper**, even if the other section is empty:

```cpp
//>> Step Label | guided | blocks

void setup() {}

void loop() {
  // new code here
}
```

If a step only affects globals (variable declarations), omit the wrappers:
```cpp
//>> Variables | guided | blocks

//?? Declare trigger pin
int trigPin = 9;
//## int buzzerPin = 3;
```

**Global declarations are cumulative.** Variables declared in earlier steps
carry forward automatically — do not repeat them in later step chunks.

**Setup and loop sections are NOT cumulative.** Every step chunk that contains
loop or setup code must explicitly re-list all previous steps' code as `//##`
locked lines, followed by the new code for this step.

This is how the workspace shows the full program at each step. Without the
`//##` re-listing, the student only sees the new lines, not the complete
picture of what has been built so far.

```cpp
//>> Step 5 — Listen for Echo | guided | blocks

void setup() {}

void loop() {
  //## digitalWrite(trigPin, LOW);      ← carried from step 3
  //## delayMicroseconds(2);            ← carried from step 3
  //## digitalWrite(trigPin, HIGH);     ← carried from step 4
  //## delayMicroseconds(10);           ← carried from step 4
  //## digitalWrite(trigPin, LOW);      ← carried from step 4

  //?? Measure the echo duration        ← NEW this step
  duration = pulseIn(echoPin, HIGH);
}
```

When building the annotated sketch, maintain a running list of all loop lines
added in previous steps. Each new loop step prepends that full list as `//##`
lines before the new content.

---

### Decision rules — apply these in order

#### Globals section

| Line | Rule |
|------|------|
| `int name = N;` — simple, well-named pin variable | phantom, up to 2 per step. Hint: "Declare the [name] variable" |
| `int name = N;` — 3rd+ variable in same step | locked |
| `long duration = 0;` | locked — `long` type is abstract |
| `float distance = 0;` | locked — `float` type is abstract |
| `bool name = false;` | locked unless it is the educational focus |
| `String name = "";` | locked |

**If the user has many variables (5+), always lock all but the first 2.**
The skill may propose splitting globals into two steps if there are 6+ lines.

#### Setup section

| Line | Rule |
|------|------|
| First `pinMode(x, OUTPUT)` | phantom. Hint: "Set [name] as an output" |
| Second `pinMode(x, OUTPUT)` | phantom if OUTPUT was not in a prior step, otherwise lock |
| `pinMode(x, INPUT)` — first INPUT pin | phantom if INPUT is a new concept in this lesson. Hint: "Set [name] as an input" |
| Additional `pinMode()` calls | locked |
| `Serial.begin(9600)` | always locked — boilerplate |
| `lcd.begin()`, `servo.attach()` | locked unless it is the focus of the lesson |

If the setup has only locked lines → use `free` guidance.

#### Loop section — general

| Line | Rule |
|------|------|
| `digitalWrite(pin, HIGH/LOW)` | phantom. Hint describes the purpose, not the syntax |
| `delay(N)` where N is a round number | phantom if it is educationally meaningful; lock if it is a tiny timing constant (< 20ms) |
| `delayMicroseconds(N)` | always locked — microsecond timing is invisible |
| `analogRead(pin)` | phantom. Hint: "Read the [sensor name]" |
| `digitalRead(pin)` | phantom |
| `pulseIn(pin, HIGH)` | phantom. Hint: "Measure the echo duration" |
| Simple assignment `x = y;` | phantom if the variable is one the student declared |
| Math with constants `x = y * 0.034 / 2;` | locked — complex math, wrap with `//##` |
| `map(...)` with 5 args | locked |
| `constrain(...)` | locked unless it is the focus |
| `Serial.print(...)` / `Serial.println(...)` | phantom if it is the new concept; lock if it is diagnostic boilerplate |
| `tone(pin, freq)` | phantom. Hint: "Sound the [name] alarm" |
| `noTone(pin)` | phantom. Hint: "Turn off the [name]" |

#### if / else-if / else chains — ALWAYS split into separate steps

Each branch of a chain is its own step. The rule:

**Step for the `if` branch:**
The chunk contains the full `if (...) { ... }` block. The `if` statement
itself gets a `//?? ` phantom. Lines inside the if body follow the general
loop rules (phantom or locked per line type).

```cpp
//>> Safe Zone | guided | blocks

void setup() {}

void loop() {
  //?? Check if object is in the safe zone
  if (distance > 30) {
    //?? Turn on the green LED
    digitalWrite(greenLED, HIGH);
    //## noTone(buzzerPin);
  }
}
```

**Step for each `else if` branch:**
The chunk contains ONLY the `else if` clause. The `//?? ` directive goes on
the line immediately before `else if (...)`. The grammar treats `//??` +
`else if (...) { }` as a phantom else-if clause that attaches to the
preceding if block in the workspace.

```cpp
//>> Warning Zone | guided | blocks

void setup() {}

void loop() {
  //?? Add the warning zone check
  else if (distance > 15) {
    //?? Turn on the yellow LED
    digitalWrite(yellowLED, HIGH);
    //## tone(buzzerPin, 500);
  }
}
```

**Step for the `else` branch:**
Same pattern — `//?? ` immediately before `else { }`.

```cpp
//>> Danger Zone | guided | blocks

void setup() {}

void loop() {
  //?? Add the danger zone
  else {
    //?? Turn on the red LED
    digitalWrite(redLED, HIGH);
    //## tone(buzzerPin, 1000);
  }
}
```

---

### The final "Mission Complete" step — ALWAYS add this last

After all coding steps, append one final step with NO code at all:

```cpp
//>> Mission Complete | open | blocks
```

Nothing follows the marker. No `void setup()`. No `void loop()`. No code.

This step is handled entirely by the drawer — it shows a celebration tab,
a challenges tab, and a simulation tab. The `open` flag means the block
builder accepts any input freely with no validation. This is the independent
exploration zone.

The drawer skill must receive the same number of steps INCLUDING this final
one. Always count it when reporting step totals.

---

### Step guidance mode summary

Determine the guidance mode for each step after deciding which lines are
phantom and which are locked:

| Condition | Mode |
|-----------|------|
| At least one `//?? ` phantom in the step | `guided` |
| Zero phantoms, all lines are `//##` | `free` |
| Final Mission Complete step | `open` |
| Step is intentionally open-ended (challenge) | `open` |
| All lines pre-filled but student confirms each one | `full` |

---

### Phantom hint writing rules

Hints tell the student WHAT to place, not HOW. They appear inside the
phantom block in the block builder UI.

- **5–10 words max**
- **Plain English, no code syntax**
- **Describe the purpose, not the block name**
- Use the lesson theme where natural

Good:   `"Turn on the green safety LED"`
Bad:    `"digitalWrite(greenLED, HIGH)"`
Bad:    `"Use a digital write block"`

For variable declarations:
Good:   `"Declare the trigger pin variable"`
Bad:    `"Create an int called trigPin"`

For control flow:
Good:   `"Check if the object is in the safe zone"`
Bad:    `"Write an if statement"`

---

## Step 5 — Show the annotated sketch

Present the full annotated sketch to the user. Also show a summary table:

```
Final step map:
Step 1  │ Variables          │ guided  │ 2 phantom  │ 4 locked
Step 2  │ Setup              │ guided  │ 2 phantom  │ 2 locked
...
```

Ask: "Does this look correct? Any adjustments before I write the file?"

---

## Step 6 — Write to the project module

Once approved, open `utils/{project_key}.py` and update the `SKETCH_PRESET`
dict:

```python
SKETCH_PRESET = {
    'sketch': """[annotated sketch here]""",
    'default_view': 'blocks',
    'read_only': False,
    'lock_view': False,
    'fill_values': True,
    'fill_conditions': True,
}
```

Update the `'sketch'` value with the full annotated sketch. Leave all other
fields at their current values unless the user requested a change.

Also update the `PROJECT` dict's `presets` key to reference the updated
`SKETCH_PRESET`. It should already reference it by name — just confirm it does:

```python
PROJECT = {
    ...
    "presets": {
        "default": SKETCH_PRESET,
    }
}
```

---

## Step 7 — Post-write summary

After writing the file, tell the user:

```
✅ utils/{project_key}.py updated — SKETCH_PRESET written.

Steps created: N
  Step 1  │ Variables       │ guided
  Step 2  │ Setup           │ guided
  ...

📋 Next:
  [ ] Run /lesson-drawer to generate drawer content for these N steps
  [ ] Verify the step count matches the drawer steps in DRAWER_CONTENT
  [ ] Test in the block builder at /lessons/{lesson_key}
```
