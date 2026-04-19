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

**`project_key`** — which project to generate drawer content for.

**`age_group`** — `8-10` / `11-12` / `13-14`. Determines language depth and analogy style.

**`lesson_type` — do NOT ask the user.**
Read it from `META['lesson_type']` in `utils/{project_key}.py`. Default to `'progression'`.

---

## Step 2 — Read the project silently

Before showing the user anything:

1. **Read `utils/{project_key}.py`**
   - Extract `SKETCH_PRESET['sketch']`
   - Parse every `//>>` step: label, guidance mode, view
   - For each step, note phantom (`//?? `) hints and locked (`//##`) lines

2. **Read `templates/lessons/{project_key}*.html`**
   - Extract: theme, narrative framing, student role, component names, established analogies

---

## Step 3 — Generate all content and show for approval

Generate every drawer step in sequence, then show the full preview to the user.
**Do not write the file yet** — wait for approval first.

Format the preview clearly so each step and tab is readable.

Ask: "Does this look right? Any tabs to adjust before I write the file?"

---

## Age calibration — apply to ALL tab content

**Ages 8–10:** Max 2 sentences per paragraph. Emoji on every concept. Short words. Analogies: toys, games, food, animals. Never use "variable" (use "label"/"memory box") or "function" (use "instruction"/"rule").

**Ages 11–12:** Up to 4 sentences per paragraph. Technical terms with inline plain-English definitions. Analogies: machines, vehicles, gadgets, sports. Light emoji.

**Ages 13–14:** Full paragraphs. Correct technical vocabulary defined on first use. Analogies: engineering, science, real systems. Minimal emoji.

---

### Tab 1: "📖 What & Why" — explain

Tell the student what this step accomplishes in the project context and why it matters.
This is concept-only — **do not mention code, block names, or values.**

Structure:
1. Open with the project narrative — what is happening in the story right now?
2. State what this step adds to the system (one concrete sentence).
3. Explain WHY it is needed — what breaks without it.
4. Optional: preview how it connects to the next step.

**Theme rule:** Reference the landing page narrative throughout. The student's role should be addressed directly.

---

### Tab 2: "🔧 How To" — howto

#### Guided steps — 4-beat framework

For every phantom block (`//?? `) in the step, apply these four beats in order.
Never give raw code syntax before completing all four beats.

**Beat 1 — Intent:** Plain English — what needs to happen. No code, no block names.
**Beat 2 — Block:** Name the block type and what it does generally.
**Beat 3 — Values:** Walk through every slot/argument: what it expects, the specific value, and WHY that value is correct for this project.
**Beat 4 — Result:** One sentence — what the student will see when the block is placed.

Multiple phantoms: apply all four beats to each in sequence, numbered.

Locked lines in a guided step: after covering phantoms, add a brief note for any locked lines explaining why they are pre-set.

#### Free steps (guidance mode = `free`) — deep explanation

All code is locked; the student watches. The how-to tab becomes an educational deep-dive:
1. Acknowledge the step is handled automatically and why (complexity, precision).
2. Break down every locked line in plain English — every component and value.
3. For formulas, explain where each number comes from and what it represents.
4. End with what the student now has available to use in future steps.

---

### Tab 3: "🧠 Logic" — logic

A real-world analogy connecting the code concept to something the student already
understands physically. 2–4 sentences max. Illuminates the WHY, not the HOW.
Must match the age group. Tie to the lesson theme where natural.

---

### The final Mission Complete step — 4 tabs

**Tab 1: "📖 What You Built"**
- Celebratory opening addressed to the student in their narrative role
- 1–2 sentences describing the complete system
- `<ul>` of 4–6 bullets: what the system can NOW do (emoji + action verb + themed language)
- Close: one sentence on what they have proven they can do

**Tab 2: "🔧 Try This Next"**
- Opening: "Now that your system works, here are some ideas to make it even better."
- `<ul>` of 4–6 challenges: emoji + bold title + one sentence, graded easy → hard
  - Easy (2): change a value, add a delay
  - Medium (2): add a component, new zone
  - Hard (1–2): combine with another project, build a game
- Close: "Experimenting is how real [role]s improve their designs."

**Tab 3: "🧠 What You Learned"**
- Opening: "This project brought together everything you have been building."
- `<ul>` of 5–7 mastered concepts: emoji + bold name + one-sentence plain-English description
- Close: "you are now thinking like a [role]" line, themed

**Tab 4: "🎮 Try It" (sim placeholder)**
- Label: `"🎮 Try It"`, type: `"sim"`, `sim_config: {}`
- Add comment: `# TODO: add sim_config once sim engine supports this lesson's components`

---

### Troubleshooting lessons (`lesson_type = "troubleshoot"`)

Exactly 2 drawer steps matching the 2 sketch steps.

**Step 1 — Find the Bug — three tabs:**

- **"🎯 The Challenge":** Set the scene. Describe what the system *should* do. Describe the symptom (not the cause). End with "Your mission: find what's wrong and fix it." Never name the bug or hint at the fix.

- **"🎮 Try It":** `type: "sim"`, `sim_config: {}` placeholder.

- **"💡 Hints":** Exactly 3 graduated hints:
  - **Hint 1 — Area:** Broad section only. No line numbers or variable names.
  - **Hint 2 — Section:** Narrows to a specific block or function. Can name a function/variable but not the wrong value.
  - **Hint 3 — Near-answer:** Precise technical description of the symptom — student should be able to fix it after reading this.

  ```html
  <p><strong>Hint 1:</strong> ...</p>
  <p><strong>Hint 2:</strong> ...</p>
  <p><strong>Hint 3:</strong> ...</p>
  ```

**Step 2 — Mission Complete:** Same four-tab format as the standard final step.

---

## Step 4 — Write to the project module

Once approved, write or replace `DRAWER_CONTENT` in `utils/{project_key}.py`:

```python
DRAWER_CONTENT = {
    "{project_key}": {
        "steps": [
            {
                "title": "Step 1 — Variables 📦",
                "tip": "One-line tip shown below the drawer title.",
                "tabs": {
                    "explain": {"label": "📖 What & Why", "content": "<p>...</p>"},
                    "howto":   {"label": "🔧 How To",    "content": "<p>...</p>"},
                    "logic":   {"label": "🧠 Logic",     "content": "<p>...</p>"}
                }
            },
            # ... one entry per sketch step ...
            {
                "title": "Mission Complete 🎉",
                "tip": "Your system is fully operational!",
                "tabs": {
                    "explain": {"label": "📖 What You Built",  "content": "<p>...</p>"},
                    "howto":   {"label": "🔧 Try This Next",   "content": "<p>...</p>"},
                    "logic":   {"label": "🧠 What You Learned","content": "<p>...</p>"},
                    "sim":     {"label": "🎮 Try It", "type": "sim", "sim_config": {}}
                }
            }
        ]
    }
}
```

Confirm `PROJECT["drawer"]` references `DRAWER_CONTENT`.

**Step count check:** Verify `DRAWER_CONTENT[key]["steps"]` count exactly matches
the number of `//>>` markers in `SKETCH_PRESET['sketch']`. If mismatch, report and do not write.

---

## Step 5 — Post-write summary

```
✅ utils/{project_key}.py updated — DRAWER_CONTENT written.
Drawer steps: N  (matches sketch steps ✅)

  Step 1  │ Variables       │ 3 tabs
  ...
  Step N  │ Mission Complete│ 4 tabs (sim placeholder)

Next: add circuit image, update STEPS coordinates, test at /lessons/{lesson_key}
```
