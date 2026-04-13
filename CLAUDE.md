# KidsCode — Project Context for Claude

## What This Is
A Flask-based platform that teaches kids (ages 8–14) Arduino programming through themed, story-driven lessons. Each lesson has a physical circuit-building guide, an in-browser block builder IDE, and rich educational drawer content.

## Lesson Architecture

A lesson is made of these files:

| File | Purpose |
|------|---------|
| `utils/project_{key}.py` | All data: meta, assembly steps, drawer content, sketch presets |
| `templates/lessons/{page_key}.html` | One template per page (single or multi-part) |
| `utils/lessons.py` | Registry — one entry per page |
| `static/graphics/project_{key}_circuit.png` | Circuit diagram image (provided manually) |
| `static/graphics/project_{key}_banner.png` | Banner image (provided manually, optional) |

The project registry (`utils/project_registry.py`) auto-discovers any `utils/project_*.py` that defines a `PROJECT` dict — **no imports needed**, just drop the file in.

### Single-page lessons
Templates extend `lessons/project_base.html`. Use `{% block intro %}`, `{% block parts %}`, `{% block tips %}`.
Banner and circuit tabs are handled automatically by the base template.

### Multi-part lessons
Each part gets its own template extending `lesson_base.html` directly.
All parts share one `utils/project_{key}.py` module and one circuit image.
Each part has its own `lessons.py` entry sharing the same `"part"` group name.

**Page types:**
- `intro` — story/mission setup, no circuit, no block builder
- `build` — circuit tabs + block builder + mission checklist
- `completion` — celebration + what you built + what's next ideas

---

## Project Module Structure (`utils/project_{name}.py`)

```python
from utils.step_builder import build_step, intro_step, rect, circle, line, lbl

META = {
    'title': 'Project N: Title Here',
    'circuit_image': 'static/graphics/project_{name}_circuit.png',
    'banner_image': 'project_{name}_banner.png',  # or None
    'lesson_type': 'progression',                  # or 'troubleshoot'
}

STEPS = [
    intro_step("Intro headline", "Subtext shown before step 1"),
    build_step(
        "Instruction text shown to student.<br>Can use HTML.",
        "Tip text shown in green box.",
        rect(x1, y1, x2, y2),       # highlight area on circuit image
        greyout=True,                # dims everything outside highlight
    ),
    # Wiring steps also use build_step with line() highlights — excluded from generation
]

DRAWER_CONTENT = {
    "project_{name}": {
        "steps": [
            {
                "title": "Step N — Title 🔧",
                "tip": "One-line guidance for this step.",
                "tabs": {
                    "explain": {
                        "label": "📖 What & Why",
                        "content": "<p>HTML content...</p>"
                    },
                    "howto": {
                        "label": "🔧 How To",
                        "content": "<p>HTML content...</p>"
                    },
                    "logic": {
                        "label": "🧠 Logic",
                        "content": "<p>Analogy or metaphor explaining the concept...</p>"
                    }
                }
            },
            # One entry per coding step
        ]
    }
}

SKETCH_PRESET = {
    'sketch': """void setup() {
  // setup code
}

void loop() {
  //>> Step 1 label
  // code for step 1
  //>> Step 2 label
  // code for step 2
}""",
    'default_view': 'blocks',   # 'blocks' or 'editor'
    'read_only': False,
    'lock_view': False,
    'fill_values': True,
    'fill_conditions': True,
}

PROJECT = {
    "meta": META,
    "steps": STEPS,
    "drawer": DRAWER_CONTENT,
    "presets": {
        "default": SKETCH_PRESET,
    }
}
```

### Sketch Directives — exact syntax

```
//>> Step Label | guidance | view
```
Step boundary. Placed at the START of a step chunk. Pipe-separated options.
`guidance`: `guided` (default) / `free` / `full` / `open`
`view`: `blocks` (default) / `editor`

```
//?? hint text
actual code line;
```
Phantom slot. The `//?? ` line immediately precedes the code line the student places.
One phantom directive per statement. Hint is shown inside the block in the UI.

```
//## actual code line;
```
Locked block. The code after `//##` is pre-placed and read-only. One statement per line.

**Guidance mode rules:**
- `guided` — at least one `//?? ` phantom exists in the step
- `free`   — zero phantoms, all lines are `//##` (step auto-completes, student watches)
- `full`   — all blocks pre-filled but student must confirm/place each
- `open`   — no structure, no validation

**Accumulation rules — critical:**
- **Globals ARE cumulative** — declared once, carry forward automatically into all later steps
- **Setup and loop are NOT cumulative** — every step chunk must re-list all previous loop/setup code as `//##` locked lines before adding new code
- Global-only chunks (variable declarations only) omit `void setup()` / `void loop()` wrappers
- All other chunks must include both wrappers even if one section is empty
- if/else/else-if chains are ALWAYS split — one step per branch
- The final step is always `//>> Mission Complete | open | blocks` with no code — handled entirely by the drawer

---

## Template Structure (`templates/lessons/project_{name}.html`)

```html
{% extends "lessons/project_base.html" %}
{% set banner_image = "project_{name}_banner.png" %}
{% block title %}Project N: Title — KidsCode{% endblock %}

{% set project_title = "Project N — Title 🎯" %}
{% set circuit_image = "project_{name}_circuit.png" %}

{% block intro %}
<h2>Goal</h2>
<p>One sentence mission statement with emoji.</p>

<h3>New ideas 💭</h3>
<hr>
<!-- Concept explanations, age-appropriate, themed to the lesson -->
{% endblock %}

{% block parts %}
<h2>🔌 Build the circuit</h2>
<h4>What parts do I need?</h4>
<ul class="parts-list">
    <li>🟦 Arduino UNO</li>
    <!-- list components with fun descriptions -->
</ul>
{% endblock %}

{% block tips %}
<div class="tips-box">
    <p>💡 <strong>Tip title:</strong> Tip content...</p>
</div>
{% endblock %}
```

---

## Lessons Registry (`utils/lessons.py`)

Add one entry to the `LESSONS` list:

```python
{
    "key": "project_{name}",
    "title": "🎯 Lesson Title",
    "template": "lessons/project_{name}.html",
    "part": None,           # or "Part Group Name" for multi-part lessons
    "block_builder": "project_{name}"
},
```

---

## Content Conventions

- **Age target**: Write for the stated age group. Younger (8–10): short sentences, lots of emoji, physical analogies. Older (11–14): can handle more technical language but still story-driven.
- **Tone**: Encouraging, adventurous. Themes like spy gadgets, space missions, dragons, science labs work well.
- **Drawer tabs**: Always include `explain` (what & why), `howto` (numbered steps), `logic` (real-world analogy). One drawer step per coding step.
- **Sketch**: Steps should build progressively. Each `//>>` step should be achievable in 2–5 blocks.
- **No wiring steps in STEPS**: Wiring build_steps use `line()` highlights tied to circuit image pixel coordinates — these are always provided manually after circuit image is created.

---

## Skills — Lesson Generation Pipeline

Lessons are built in stages using modular skills. Run them in order:

| Skill | What it does |
|-------|-------------|
| `/lesson-landing` | Creates landing page templates, project module stub, lessons.py entries |
| `/lesson-sketch` | Annotates a user-provided sketch with `//>>`, `//?? `, and `//##` directives |
| `/lesson-drawer` | Generates themed drawer tab content from sketch steps |

Skills are markdown files in `.claude/commands/`. Type `/skill-name` in any
Claude Code chat opened in this project to invoke one.

### `utils/lesson_scaffold.py`
All skills write a `lesson_spec.json` to the project root then call:
```bash
python utils/lesson_scaffold.py lesson_spec.json
```
The script handles both single-page and multi-part lessons from the same unified spec format.
Delete `lesson_spec.json` after generation — it is gitignored.
