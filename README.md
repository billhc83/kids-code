# KidsCode — Arduino Learning Platform for Kids

A story-driven, web-based platform that teaches kids (ages 8–14) Arduino programming through themed missions, hands-on circuit building, and a visual block-based coding environment — all in the browser.

---

## What It Does

KidsCode guides students through a progressive curriculum of 17 projects, from blinking an LED to building alarm systems and reaction timers. Every lesson combines:

- **A themed story mission** — spy vaults, dragon alarms, space stations, deep sea exploration
- **A step-by-step circuit assembly guide** with annotated diagrams
- **An in-browser block builder IDE** — no installation required
- **A guided coding drawer** with explanations, how-to steps, and real-world analogies for every coding concept

---

## Features

### Visual Block Builder IDE
- Drag-and-drop block interface for writing Arduino code without typing
- Real-time code generation — blocks produce valid Arduino C++ as you build
- Dual view: switch between **blocks mode** and a **Monaco text editor** at any time
- Round-trip parsing: code typed in the editor syncs back into blocks
- Guided progression mode — lessons unlock one step at a time with phantom slots the student must fill in
- Locked blocks for code the student isn't expected to write yet
- Free and open modes for sandbox exploration

### Lesson System
- **17 story-themed projects** covering core Arduino concepts:
  | # | Project | Concept |
  |---|---------|---------|
  | 1 | Lights ON!! | Digital output, pinMode |
  | 2 | Blinking Beacon | delay(), loops |
  | 3 | Mad Scientist Button Machine | Digital input, conditionals |
  | 4 | Space Station Launch Button | Push buttons, if/else |
  | 5 | *(continuing curriculum)* | Variables |
  | 6 | Deep Sea Explorer | Analog input |
  | 7 | The Automagic Night Light | LDR sensors, thresholds |
  | 8 | The Dragon's Crystal Alarm | Buzzer, tone() |
  | 9 | The Universal Power Slot | Modular functions |
  | 10 | The Spy Vault Security Console | Multi-sensor logic |
  | 11 | Engine System Start | State machines |
  | 12 | Night Patrol Alarm | PIR sensors |
  | 13 | The Reaction Timer | millis(), timing |
  | 14 | Codebreaker | Serial monitor |
  | 15 | Backup Alarm | Nested conditions |
  | 16 | Broken Blinker | Debugging / troubleshoot mode |
  | 17 | Magical Harp | Tone arrays, music |

- **Single-page and multi-part lesson formats** — complex projects split across intro, build, and completion screens
- **Lesson unlocking and progression** — completing a lesson unlocks the next; progress saved to the database

### Circuit Assembly Guide
- Annotated circuit diagrams with step-by-step highlighting
- Zoom-in overlays on circuit regions as the student follows along
- Greyout mode dims everything except the current component being placed
- Separate wiring and component steps

### In-Lesson Coding Drawer
Each coding step has a three-tab knowledge drawer:
- **What & Why** — explains the concept being introduced
- **How To** — numbered instructions for placing blocks
- **Logic** — a real-world analogy or mental model (e.g., "a variable is like a labeled box")

### Accounts & Roles
- **Student accounts** — email verification, session persistence (30 days), per-lesson progress
- **Parent accounts** — dashboard to monitor linked students, create child accounts, reset passwords
- **Admin accounts** — feedback moderation, challenge review, user management, lesson-building tools

### Progression & Badges
- Lesson completion unlocks the next lesson in sequence
- Badge system awards achievements as students progress
- Dashboard shows current lesson, completed lessons, and earned badges

### Challenge System
- Optional challenge submissions per lesson
- Admin review queue for submitted challenges

### Feedback System
- Students can submit in-app feedback
- Threaded admin moderation interface

### Physical Arduino Upload (via Local Agent)
- Optional local Arduino agent runs alongside the app
- When connected, the IDE exposes:
  - Available serial ports
  - Compile and upload to board
  - Live serial monitor output via WebSocket
- Flask and the local agent are cleanly separated — the browser calls the agent directly on `localhost:3210`/`3211`

### Browser Simulator
- A built-in simulation engine (`sim-engine.js`) lets students run basic sketches without physical hardware

### Rate Limiting
- Flask-Limiter applied globally to prevent abuse on auth and submission endpoints

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python, Flask |
| Database / Auth | Supabase (Postgres + REST) |
| Frontend IDE | Custom block builder (vanilla JS) |
| Code Editor | Monaco Editor |
| Deployment | Gunicorn / Heroku (Procfile included) |
| Password hashing | bcrypt |
| Image processing | Pillow |
| Sketch parsing | Custom parser + Lark grammar |
| Tests | pytest, pytest-flask |

---

## Project Structure

```
app.py                      # Flask app entry point
config.py                   # Env var loading
extensions.py               # Flask-Limiter setup

routes/
  auth.py                   # Login, register, verify, reset
  main.py                   # Dashboard, root, feedback, activity
  lessons.py                # Lesson pages and completion
  builder.py                # IDE, sketch parsing, preset loading, sim
  parent.py                 # Parent dashboard
  admin.py                  # Admin tools

utils/
  lessons.py                # Lesson order and sidebar groups
  project_registry.py       # Auto-discovers project_*.py modules
  project_one.py            # Lesson content: meta, steps, drawer, sketch
  project_two.py            # ... (17 project modules total)
  block_parser.py           # Parses Arduino sketches into block trees
  block_builder_config.py   # Builds frontend BB_CONFIG from presets
  block_builder.py          # Generates builder HTML fragments
  assembly_guide_flask.py   # Circuit step guide renderer
  progression.py            # Unlock/completion state
  auth.py                   # User creation, hashing, email flows
  db_client.py              # Supabase client
  badges.py                 # Badge award logic
  challenges.py             # Challenge helpers
  feedback.py               # Feedback helpers
  activity.py               # Activity logging

templates/
  base.html                 # Shared shell
  lessons/                  # One template per lesson
  components/
    arduino_interface.html  # IDE shell (Monaco + block builder + drawer)

static/
  js/
    block_builder.js        # Block builder runtime entry point
    bb-blocks.js            # Block type definitions
    bb-render.js            # Block rendering
    bb-validation.js        # Guided step validation
    sim-engine.js           # Browser simulator
  css/                      # Global and builder styles
  graphics/                 # Circuit diagrams, banners, UI assets

tests/
  test_auth.py
  test_admin.py
  conftest.py
```

---

## Getting Started

### Prerequisites
- Python 3.10+
- A [Supabase](https://supabase.com) project with the required tables

### Install

```bash
git clone https://github.com/billhc83/kids-code.git
cd kids-code
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Configure

Create a `.env` file in the project root:

```env
SECRET_KEY=your-flask-secret-key
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-role-key
SUPABASE_ANON_KEY=your-anon-key
```

### Run

```bash
python app.py
```

The app starts on `http://localhost:5001`.

### Run Tests

```bash
pytest
```

---

## Lesson Content Architecture

Each lesson is self-contained in a `utils/project_*.py` module:

- **META** — title, circuit image path, lesson type
- **STEPS** — assembly guide steps with circuit highlights
- **DRAWER_CONTENT** — per-step three-tab knowledge content
- **SKETCH_PRESET** — annotated Arduino sketch with `//>>` step markers, `//?? ` phantom slots, and `//##` locked lines

The project registry auto-discovers any `utils/project_*.py` that defines a `PROJECT` dict — no imports or registration needed.

---

## Adding a New Lesson

1. Create `utils/project_name.py` with `META`, `STEPS`, `DRAWER_CONTENT`, `SKETCH_PRESET`, and a `PROJECT` dict
2. Add a template to `templates/lessons/project_name.html`
3. Add an entry to `utils/lessons.py`
4. Add circuit and banner images to `static/graphics/`

The project registry picks it up automatically on next server start.

---

## License

MIT
