# /lesson-drawer — Generate Drawer Content from Sketch Steps

This skill reads the annotated sketch and the landing page, then generates
rich, theme-consistent drawer content for every step. One drawer step per
sketch step, including the final Mission Complete step.

Read CLAUDE.md before doing anything else.

---

## What this skill produces

For each sketch step: a drawer entry with three tabs.
For the final Mission Complete step: four tabs.
For troubleshooting lessons: a different tab structure on step 1.

The output goes into `DRAWER_CONTENT` in `utils/{project_key}.py`.

---

## Step 1 — Gather inputs

Ask for all missing items in ONE message.

**`project_key`**
Which project to generate drawer content for.
The skill reads `utils/{project_key}.py` for the sketch steps and
`templates/lessons/{project_key}*.html` for the theme and narrative.

**`age_group`**
`8-10` / `11-12` / `13-14`. Determines language depth and analogy style.

**`lesson_type` — do NOT ask the user for this.**
Read it directly from `META['lesson_type']` in `utils/{project_key}.py`.
It was set by `/lesson-landing` and persists in the file.
Default to `'progression'` if the key is missing.

---

## Step 2 — Read the project silently

Before showing the user anything:

1. **Read `utils/{project_key}.py`**
   - Extract the `SKETCH_PRESET['sketch']` string
   - Parse every `//>>` step boundary — get the label, guidance mode, and view
   - For each step, list every line and its type:
     - `//?? hint` lines → phantom (note the hint text)
     - `//##` lines → locked (note the code)
     - plain lines → unlocked guided
   - Count total steps including the final `Mission Complete | open` step

2. **Read the landing page template(s)**
   - Find `templates/lessons/{project_key}*.html` files
   - Extract: theme, narrative framing, student's role (engineer, spy, agent, etc.),
     project name, component names as used in the story
   - Note any specific analogies or metaphors already established

3. **Build an internal step map:**
   ```
   Step 1  │ Variables          │ guided  │ phantoms: [trigPin, echoPin] │ locked: [buzzerPin, duration, distance]
   Step 2  │ Setup              │ guided  │ phantoms: [pinMode OUTPUT x2] │ locked: [Serial.begin]
   ...
   Step N  │ Mission Complete   │ open    │ no code
   ```

---

## Step 3 — Show the plan and get approval

Display the step map to the user. For each step, show:
- Step number, label, guidance mode
- What the "explain" tab will cover (one sentence)
- What the "how-to" tab will focus on (one sentence)
- What the "logic" analogy theme will be (one sentence)

Example:
```
Drawer plan: project_sixteen (Dragon Fire Alarm, age 11-12)
─────────────────────────────────────────────────────────────
Step 1  │ Variables    │ guided  │ explain: why variables store the system's memory
                                │ how-to:  declaring pin numbers for each dragon sensor
                                │ logic:   labelling wires in a control panel

Step 2  │ Setup        │ guided  │ explain: configuring each pin's role before the loop
                                │ how-to:  pinMode for each output and input
                                │ logic:   plugging devices in before turning them on

Step 6  │ Calc Dist    │ free    │ explain: why the formula converts time to distance
                                │ how-to:  DEEP EXPLAIN — the maths behind sound speed
                                │ logic:   timing a ball throw to calculate distance

Step N  │ Mission Comp │ open    │ celebrate / challenges / what you learned / sim
─────────────────────────────────────────────────────────────
```

Ask: "Does this plan look right? Any tab content you want handled differently?"

Wait for approval before generating any content.

---

## Step 4 — Generate content step by step

Generate all steps in sequence. Show all content to the user as a formatted
preview, then ask for approval before writing to the file.

### Age calibration — apply to ALL tab content

**Ages 8–10:**
- Maximum 2 sentences per paragraph.
- Emoji on every concept. Short words only.
- Analogies: toys, games, food, animals, everyday home objects.
- Never use the word "variable" — use "label" or "memory box."
- Never use "function" — use "instruction" or "rule."

**Ages 11–12:**
- Up to 4 sentences per paragraph.
- Introduce technical terms with plain-English inline definitions.
- Analogies can involve machines, vehicles, gadgets, sports.
- Light emoji for emphasis.

**Ages 13–14:**
- Full paragraph explanations acceptable.
- Use correct technical vocabulary, defined on first use.
- Analogies can reference engineering, science, real systems.
- Minimal emoji — substance over decoration.

---

### Tab 1: "📖 What & Why" — explain

Purpose: Tell the student what this step accomplishes in the context of the
full project, and why it matters. This is the "big picture" before the
student touches any blocks.

Structure:
1. Open with the project narrative — what is happening in the story right now?
2. State what this step adds to the system (one concrete sentence).
3. Explain WHY it is needed — what breaks or doesn't work without it.
4. Optional: preview how this step connects to the next one.

**Theme rule:** Every explain tab should reference the narrative established
on the landing page. If the theme is "dragon fire alarm," the sensor isn't
"detecting proximity" — it's "sensing when the dragon is getting close."
The student's role (engineer, spy, etc.) should be addressed directly.

**Do NOT mention code, block names, or values in this tab.**
The explain tab is concept-only.

Example (age 11-12, backup alarm theme):
> Your backup alarm system now knows the distance — but knowing a number
> isn't enough. The system needs to *decide* what that number means.
>
> This step adds the first decision: checking whether the object is far
> enough away to be safe. We use an if statement to ask a yes/no question
> about the distance.
>
> Without this step, your system would measure distance but never react
> to it — like a speedometer that shows speed but can't slow the car down.

---

### Tab 2: "🔧 How To" — howto

This tab varies significantly by step guidance mode.

---

#### Guided steps — the 4-beat framework

For every phantom block in the step, apply these four beats in order.
Never give raw code syntax before completing all four beats.

**Beat 1 — Intent**
Plain English statement of what needs to happen. No code. No block names.
> "Your buzzer needs to turn ON."
> "The system needs to know which pin connects to the trigger wire."

**Beat 2 — Block**
Name the block type and describe what it does generally.
> "Use a `digitalWrite` block — it switches a pin between ON (HIGH) and OFF (LOW)."
> "Use a `pinMode` block — it tells the Arduino whether a pin sends or receives signals."

**Beat 3 — Values**
Walk through every slot/argument the block requires. For each one:
- State what it expects (pin name, direction, value)
- Give the specific value to use
- Explain WHY that specific value is correct for this project

> "The first slot needs the pin. Use `greenLED` — that's the variable that
> stores pin 4, where your green LED is wired."
> "The second slot needs HIGH or LOW. Use `HIGH` — this sends electricity
> to the LED and lights it up."

> "We chose `50` as the safe distance because it gives the driver enough
> time to react — not too sensitive, not too slow."

**Beat 4 — Result**
One sentence: what the student will see or observe when this block is placed
and the step is complete.
> "When this step is complete, the green LED turns on whenever the sensor
> reads a safe distance."

**Multiple phantoms in one step:**
Apply all four beats to each phantom in sequence, numbered:
`1. [four beats for first phantom]`
`2. [four beats for second phantom]`

**Locked lines in a guided step:**
After covering all phantoms, add a brief note for any locked lines:
> "The `noTone` line is pre-set for you — turning the buzzer off is handled
> automatically so you can focus on the LED logic."

---

#### Free steps (guidance mode = `free`) — deep explanation

Free steps have all locked code. The student watches the step appear without
placing anything. The how-to tab becomes an educational deep-dive instead of
a placement guide.

Structure:
1. Acknowledge that this step is handled automatically and explain why
   (complexity, precision required, abstract concept).
2. Break down the locked code in plain English — every component, every value.
3. If there is a formula, explain where each number comes from and what it
   represents in the real world.
4. End with what the student now has available to use in future steps.

Example (Calculate Distance, age 11-12):
> This step is handled for you because the formula involves precise maths
> that would be easy to get wrong.
>
> Here is what the line does:
> `distance = duration * 0.034 / 2`
>
> **`duration`** — this is the time (in microseconds) the sound took to
> travel to the object and back. You captured it in the last step.
>
> **`× 0.034`** — sound travels at 34,000 cm per second through air.
> Dividing by 1,000,000 to convert to microseconds gives us 0.034 cm per
> microsecond. Multiplying duration by 0.034 gives the total distance
> travelled.
>
> **`÷ 2`** — the sound travelled TO the object AND back. We only want
> the one-way distance, so we halve the result.
>
> After this step, the `distance` variable holds the real centimetre
> distance to the nearest object. Every decision your system makes from
> here is based on this number.

---

### Tab 3: "🧠 Logic" — logic

Purpose: A real-world analogy that connects the code concept to something
the student already understands physically. One concise paragraph.

Rules:
- The analogy must match the age group (see calibration above).
- It should illuminate the WHY, not restate the HOW.
- It should NOT be a direct retelling of the code — it should make the
  underlying concept click from a completely different angle.
- Keep it to 2–4 sentences max. Brevity is power here.
- Tie it to the lesson theme where it fits naturally.

Good (age 11-12, if statement, backup alarm):
> "This is like a driver checking their mirrors before reversing. They
> ask one question: 'Is it clear?' If yes, they move. If no, they stop.
> Your if statement is doing exactly that — one question, one decision."

Bad (too literal):
> "An if statement checks a condition. If the condition is true, it runs
> the code inside. Otherwise it skips it."

Bad (too abstract for age):
> "Boolean logic gates form the basis of all computational decision-making."

---

### The final Mission Complete step — 4 tabs

This step has no code. The block builder is open (students can experiment
freely). Generate four tabs:

**Tab 1: "📖 What You Built"**
- Open with a celebratory line addressed to the student in their narrative
  role (e.g. "Outstanding work, Engineer!" / "Mission accomplished, Agent!")
- 1–2 sentences describing the complete system
- A `<ul>` list of 4–6 bullet points: what the system can NOW do
  - Each starts with an emoji, uses an action verb, themed language
  - Example: `"📡 Detect objects approaching using an ultrasonic sensor"`
- Close with one sentence about what they have proven they can do

**Tab 2: "🔧 Try This Next"**
- Opening: "Now that your system works, here are some ideas to make it
  even better."
- A `<ul>` list of 4–6 challenge ideas, each:
  - Emoji + bold title + one sentence description
  - Graded: first 2 are easy tweaks (change a value, add a delay)
  - Next 2 are medium (add a new component, new zone)
  - Last 1–2 are hard/open-ended (combine with another project, build a game)
- These are NOT curated — students figure them out independently
- Close: "Experimenting is how real [engineers/spies/etc.] improve their designs."

**Tab 3: "🧠 What You Learned"**
- Opening line: "This project brought together everything you have been building."
- A `<ul>` list of 5–7 concepts mastered, each:
  - Emoji + bold concept name + one-sentence plain-English description
  - Example: `"🧠 Conditional logic — making decisions using if / else if / else"`
- Close with the "you are now thinking like a [role]" line, themed.

**Tab 4: "🎮 Try It" (sim placeholder)**
- Label: `"🎮 Try It"`
- Type: `"sim"`
- Leave `sim_config` as an empty dict `{}` with a comment:
  `# TODO: add sim_config once sim engine supports this lesson's components`

---

### Troubleshooting lessons — different structure

For `lesson_type = "troubleshoot"`, the drawer has exactly 2 steps matching
the 2 sketch steps (`Find the Bug` + `Mission Complete`).

**Step 1 — Find the Bug**
Three tabs in this exact order:

- **Tab 1: "🎯 The Challenge"**
  Set the scene in the lesson's narrative voice.
  Describe what the system *should* do when it's working correctly.
  Describe what it is currently doing wrong (the symptom — not the cause).
  End with a direct challenge: "Your mission: find what's wrong and fix it."
  Never name the bug. Never hint at the fix here.

- **Tab 2: "🎮 Try It" (sim)**
  Type: `"sim"`, `sim_config: {}` placeholder.
  This is where the broken simulation will live — the student interacts with
  the sim to observe the broken behaviour before editing the code.

- **Tab 3: "💡 Hints"**
  **Exactly 3 hints, graduated in specificity. Each one is a separate
  numbered item. The student reads them in order when stuck.**

  - **Hint 1 — Area:** Points to the broad section of the sketch.
    Example: "The problem is somewhere in how the system is set up, not in
    the loop." Or: "Look at how the pins are configured."
    No line numbers. No variable names.

  - **Hint 2 — Section:** Narrows to a specific block or function.
    Example: "Take a close look at the pinMode settings — is each pin
    configured to do what the system needs it to do?"
    Can name a function or variable but not the wrong value.

  - **Hint 3 — Near-answer:** Describes the symptom in precise technical
    terms. The student should be able to fix it after reading this.
    Example: "The echo pin is set to OUTPUT, but it needs to receive signals
    — it should be set to INPUT."
    This hint effectively gives away the fix. That is intentional.
    A student who reaches hint 3 has genuinely tried.

  Format all three hints clearly in the HTML:
  ```html
  <p><strong>Hint 1:</strong> ...</p>
  <p><strong>Hint 2:</strong> ...</p>
  <p><strong>Hint 3:</strong> ...</p>
  ```

**Step 2 — Mission Complete**
Same four-tab format as the standard final step above.

---

## Step 5 — Show all generated content

Present every drawer step's content to the user as a readable preview.
Format it clearly so the user can review each tab.

Ask: "Does this look right? Any tabs to adjust before I write the file?"

---

## Step 6 — Write to the project module

Once approved, open `utils/{project_key}.py` and write or replace the
`DRAWER_CONTENT` dict:

```python
DRAWER_CONTENT = {
    "{project_key}": {
        "steps": [
            {
                "title": "Step 1 — Variables 📦",
                "tip": "One-line tip shown below the drawer title.",
                "tabs": {
                    "explain": {
                        "label": "📖 What & Why",
                        "content": "<p>...</p>"
                    },
                    "howto": {
                        "label": "🔧 How To",
                        "content": "<p>...</p>"
                    },
                    "logic": {
                        "label": "🧠 Logic",
                        "content": "<p>...</p>"
                    }
                }
            },
            # ... one entry per sketch step ...
            {
                "title": "Mission Complete 🎉",
                "tip": "Your system is fully operational!",
                "tabs": {
                    "explain": {
                        "label": "📖 What You Built",
                        "content": "<p>...</p>"
                    },
                    "howto": {
                        "label": "🔧 Try This Next",
                        "content": "<p>...</p>"
                    },
                    "logic": {
                        "label": "🧠 What You Learned",
                        "content": "<p>...</p>"
                    },
                    "sim": {
                        "label": "🎮 Try It",
                        "type": "sim",
                        "sim_config": {}
                    }
                }
            }
        ]
    }
}
```

Also update the `PROJECT` dict to reference the updated `DRAWER_CONTENT`:
```python
PROJECT = {
    "meta": META,
    "steps": STEPS,
    "drawer": DRAWER_CONTENT,   # ← confirm this line exists
    "presets": { ... }
}
```

**Step count check:** Before writing, verify that the number of entries in
`DRAWER_CONTENT[key]["steps"]` exactly matches the number of `//>>` markers
in `SKETCH_PRESET['sketch']` (including the Mission Complete step).
If they do not match, report the mismatch and do not write.

---

## Step 7 — Post-write summary

```
✅ utils/{project_key}.py updated — DRAWER_CONTENT written.

Drawer steps: N  (matches sketch steps: ✅)

  Step 1  │ Variables       │ 3 tabs
  Step 2  │ Setup           │ 3 tabs
  ...
  Step N  │ Mission Complete│ 4 tabs (sim placeholder)

📋 Next:
  [ ] Add circuit image    → static/graphics/{project_key}_circuit.png
  [ ] Update STEPS with real rect()/line() coordinates
  [ ] Add wiring build_step entries
  [ ] Test full lesson at /lessons/{lesson_key}
  [ ] Replace sim_config {} placeholder on Mission Complete step when sim engine is ready
```
