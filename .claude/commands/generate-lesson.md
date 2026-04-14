# Generate Lesson Skill

You are generating a new themed lesson for the KidsCode Arduino platform. Read CLAUDE.md first for the full architecture reference before doing anything else.

## Step 1 — Gather Inputs

Ask the user for the following if not already provided in their message. Ask for all missing items in a single message, not one at a time:

- **Theme / narrative**: What is the story? (e.g. "spy gadget that detects intruders", "dragon fire alarm", "space station power system")
- **Lesson key**: Short snake_case name used in filenames and URLs (e.g. `project_sixteen`, `project_dragon`)
- **Lesson title**: Display title with emoji (e.g. `🐉 Dragon Fire Alarm`)
- **Target age group**: 8–10 (younger), 11–12 (middle), 13–14 (older)
- **Arduino sketch**: The full sketch or at minimum the key functions, pins, and variables used
- **Component list**: What physical parts are used (LED, buzzer, ultrasonic sensor, button, etc.)
- **Number of coding steps**: How many `//>>` progression steps the sketch has (or should have)
- **Multi-part lesson?**: Yes/No. If yes, how many parts?

## Step 2 — Plan the Content

Before writing anything, lay out a brief plan:

1. List the coding steps with one-line descriptions
2. Identify which concepts each step introduces
3. Confirm the theme can carry through all steps naturally

Show this plan to the user and ask for confirmation or changes before proceeding to Step 3.

## Step 3 — Generate All Content

Generate the following in order. Show each section to the user before moving on to the next. Wait for approval or corrections.

### 3a. Drawer Content (`DRAWER_CONTENT`)

For each coding step, write a drawer entry with three tabs:
- `📖 What & Why` — Explains what this step does and why it matters. Use the theme/narrative. Keep it concrete. Avoid abstract jargon.
- `🔧 How To` — Numbered steps the student follows. Short, direct sentences.
- `🧠 Logic` — A real-world analogy or metaphor. Connect the code concept to something physical the student knows.

Age calibration:
- Ages 8–10: Very short sentences. Max 2–3 sentences per paragraph. Heavy emoji. Physical toy analogies.
- Ages 11–12: Can handle slightly longer explanations. Analogies can be slightly more technical (machines, vehicles, gadgets).
- Ages 13–14: Full sentences, technical vocabulary introduced carefully with plain-English definitions inline.

### 3b. Sketch Preset (`SKETCH_PRESET`)

Write the Arduino sketch with `//>>` step markers matching the drawer steps. Each step should:
- Be achievable in 2–5 blocks in the block builder
- Build on the previous step
- Have a clear, descriptive step label after `//>>` 

Include phantom placeholders `//??` for lines the student fills in themselves.

### 3c. Main Page Template (HTML)

Write the `{% block intro %}` section with:
- A one-sentence goal with emoji
- "New ideas" section introducing the 2–3 key concepts for this lesson (themed to the narrative)
- Age-appropriate language throughout

Write the `{% block parts %}` section with the component list, each with a fun description matching the theme.

Write the `{% block tips %}` section with 2–3 practical tips specific to this lesson's common pitfalls.

### 3d. Assembly Steps (`STEPS`)

Write only the **non-wiring** build steps (component placement only, not wire routing). Use this format:

```python
build_step(
    "Place the [component] in row [N], column [X].<br>Place the [other end] in row [N], column [X].",
    "Interesting fact or tip about this component.",
    rect(0, 0, 100, 100),  # PLACEHOLDER — real coordinates added after circuit image is created
    greyout=True,
),
```

Use `rect(0, 0, 100, 100)` as a placeholder for all highlight coordinates. Note clearly in comments that coordinates must be updated once the circuit image is available.

### 3e. Lessons Registry Entry

Write the dict entry to be added to `utils/lessons.py`.

## Step 4 — Write the Files

Once the user has approved all content, call `utils/lesson_scaffold.py` using:

```bash
python utils/lesson_scaffold.py lesson_spec.json
```

Before calling the script, write the full lesson spec to `lesson_spec.json` in the project root using this structure:

```json
{
  "key": "project_{name}",
  "title": "🎯 Lesson Title",
  "age_group": "11-12",
  "part": null,
  "banner_image": "project_{name}_banner.png",
  "circuit_image": "project_{name}_circuit.png",
  "meta_title": "Project N: Title",
  "intro_html": "...",
  "parts_html": "...",
  "tips_html": "...",
  "sketch": "void setup() {...}",
  "default_view": "blocks",
  "read_only": false,
  "lock_view": false,
  "fill_values": true,
  "fill_conditions": true,
  "steps": [
    {
      "instruction": "Place the LED...",
      "tip": "Fun fact about LEDs",
      "highlight": "rect",
      "coords": [0, 0, 100, 100],
      "greyout": true
    }
  ],
  "drawer_steps": [
    {
      "title": "Step 1 — Title 🔧",
      "tip": "One-line tip",
      "tabs": {
        "explain": {"label": "📖 What & Why", "content": "<p>...</p>"},
        "howto": {"label": "🔧 How To", "content": "<p>...</p>"},
        "logic": {"label": "🧠 Logic", "content": "<p>...</p>"}
      }
    }
  ],
  "lessons_registry_position": "end"
}
```

The scaffold script will:
1. Create `utils/project_{key}.py`
2. Create `templates/lessons/project_{key}.html`
3. Insert the registry entry into `utils/lessons.py`

## Step 5 — Post-Generation Checklist

After the files are written, remind the user of what still needs to be done manually:

- [ ] Add circuit diagram PNG → `static/graphics/project_{name}_circuit.png`
- [ ] Add banner image PNG → `static/graphics/project_{name}_banner.png`
- [ ] Update `rect()` / `circle()` / `line()` coordinates in `STEPS` once circuit image is available
- [ ] Add wiring `build_step` entries for each wire connection (uses `line()` with pixel coordinates)
- [ ] Test the lesson by starting the Flask app and navigating to `/lessons/project_{name}`
- [ ] Delete `lesson_spec.json` from the project root
