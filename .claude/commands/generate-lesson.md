# Generate Lesson Skill

You are generating a new themed lesson for the KidsCode Arduino platform. Read CLAUDE.md first for the full architecture reference before doing anything else.

## Step 1 — Gather Inputs

Ask for all missing items in a single message:

- **Theme / narrative**: The story (e.g. "spy gadget that detects intruders", "dragon fire alarm")
- **Lesson key**: Short snake_case name (e.g. `project_sixteen`)
- **Lesson title**: Display title with emoji (e.g. `🐉 Dragon Fire Alarm`)
- **Target age group**: 8–10, 11–12, or 13–14
- **Arduino sketch**: Full sketch or key functions, pins, and variables
- **Component list**: Physical parts used
- **Number of coding steps**: How many `//>>` steps
- **Multi-part lesson?**: Yes/No. If yes, how many parts?

## Step 2 — Generate Sketch + Drawer Content

Generate both together and show them side-by-side for a single approval. These must match 1:1 — reviewing together catches mismatches before proceeding.

**Sketch** (`SKETCH_PRESET`): Annotate with `//>>`, `//?? `, and `//##` directives per CLAUDE.md Sketch Directives rules. Each step should be achievable in 2–5 blocks. The final step is always `//>> Mission Complete | open | blocks` with no code.

**Drawer** (`DRAWER_CONTENT`): One entry per `//>>` step, three tabs each — `📖 What & Why`, `🔧 How To`, `🧠 Logic`. Follow age calibration and tab structure from CLAUDE.md Content Conventions.

Wait for user approval or corrections before Step 3.

## Step 3 — Generate Page Content

Generate all three together and show as a single block for approval:

**3a. Main Page Template** (`{% block intro %}`, `{% block parts %}`, `{% block tips %}`): Follow template structure from CLAUDE.md. Age-appropriate language, themed to the narrative.

**3b. Assembly Steps** (`STEPS`): Non-wiring placement steps only. Use `rect(0, 0, 100, 100)` as placeholder coords for all highlights — real coordinates are added after the circuit image is created. Format per CLAUDE.md module structure.

**3c. Lessons Registry Entry**: Dict entry for `utils/lessons.py` per CLAUDE.md registry format.

Wait for user approval or corrections before Step 4.

## Step 4 — Write the Files

Write `lesson_spec.json` to the project root, then run:

```bash
python utils/lesson_scaffold.py lesson_spec.json
```

Spec format:

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
    { "instruction": "...", "tip": "...", "highlight": "rect", "coords": [0,0,100,100], "greyout": true }
  ],
  "drawer_steps": [
    {
      "title": "Step 1 — Title 🔧",
      "tip": "One-line tip",
      "tabs": {
        "explain": {"label": "📖 What & Why", "content": "<p>...</p>"},
        "howto":   {"label": "🔧 How To",     "content": "<p>...</p>"},
        "logic":   {"label": "🧠 Logic",      "content": "<p>...</p>"}
      }
    }
  ],
  "lessons_registry_position": "end"
}
```

## Step 5 — Post-Generation Checklist

- [ ] Add circuit diagram PNG → `static/graphics/project_{name}_circuit.png`
- [ ] Add banner image PNG → `static/graphics/project_{name}_banner.png`
- [ ] Update `rect()` / `circle()` / `line()` coordinates in `STEPS` once circuit image is available
- [ ] Add wiring `build_step` entries for each wire connection (uses `line()` with pixel coordinates)
- [ ] Test the lesson at `/lessons/project_{name}`
- [ ] Delete `lesson_spec.json` from the project root
