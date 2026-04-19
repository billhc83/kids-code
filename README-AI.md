# README-AI

## Purpose
KidsCode is a Flask app for teaching Arduino programming to kids through guided lessons, a block-based coding interface, and story-driven project content.

This file maps the current architecture so an AI agent or new contributor can quickly find:
- where the app starts
- where student-facing lessons are assembled
- how the block builder works
- where persistence and progression live

## Top-Level Layout

### App shell
- `app.py`: Flask startup, blueprint registration, session lifetime, global template context.
- `config.py`: environment variable loading.
- `extensions.py`: shared Flask extensions, currently rate limiting.

### Route layer
- `routes/auth.py`: login, registration, verification, password reset, logout.
- `routes/main.py`: root redirect, dashboard, feedback, activity logging, open coding page.
- `routes/lessons.py`: lesson rendering, lesson completion, challenge submission flow.
- `routes/builder.py`: sketch parsing, builder fragment config, preset loading, standalone IDE, simulator run endpoint.
- `routes/parent.py`: parent dashboard, student account management.
- `routes/admin.py`: admin dashboard, feedback moderation, challenge review, lesson-building tools.

### Core logic
- `utils/auth.py`: user creation, password hashing/checking, email verification, reset flow, parent/student helpers.
- `utils/db_client.py`: Supabase client creation.
- `utils/progression.py`: unlock/completion state for lessons.
- `utils/lessons.py`: canonical lesson order and sidebar grouping.
- `utils/project_registry.py`: auto-discovers `utils/project_*.py` lesson content modules.
- `utils/block_builder_config.py`: converts a preset/project sketch into frontend builder config.
- `utils/block_parser.py`: parses Arduino-like code into block-builder structures and progression steps.
- `utils/block_builder.py`: returns embedded/overlay builder HTML.
- `utils/assembly_guide_flask.py`: renders build-step circuit guides.
- `utils/feedback.py`, `utils/activity.py`, `utils/badges.py`, `utils/challenges.py`: supporting product features.

### Content and UI
- `templates/`: Flask templates for dashboard, auth, lessons, admin, parent, and builder UI.
- `templates/components/arduino_interface.html`: main standalone IDE shell around the block builder.
- `static/js/block_builder.js`: main browser entry point for the block builder runtime.
- `static/js/bb-blocks.js`, `static/js/bb-render.js`, `static/js/bb-validation.js`: block definitions, rendering, validation.
- `static/js/sim-engine.js`: browser simulation support.
- `static/css/`: global styling and block-builder styling.
- `static/graphics/`: lesson images, circuit diagrams, UI assets.

### Lesson content
- `utils/project_one.py` ... `utils/project_sixteen.py`: project metadata, assembly steps, drawer content, and sketch presets.
- `templates/lessons/*.html`: lesson pages and multi-part lesson screens.

### Tests
- `tests/test_auth.py`
- `tests/test_admin.py`
- `tests/conftest.py`

## Main Entry Points

### Server entry point
- `app.py`

What it does:
- validates required env vars
- creates the Flask app
- registers all blueprints
- injects lesson/sidebar/global helpers into templates

### Primary HTTP entry points
- `/` in `routes/main.py`
- `/login`, `/register`, `/verify/<token>` in `routes/auth.py`
- `/dashboard` in `routes/main.py`
- `/lessons/<lesson_key>` in `routes/lessons.py`
- `/builder`, `/preset/<name>`, `/standalone_ide/<preset>`, `/parse`, `/sim/run` in `routes/builder.py`
- `/parent` in `routes/parent.py`
- `/admin` in `routes/admin.py`

### Frontend runtime entry points
- `templates/base.html`: shared shell for most pages.
- `templates/components/arduino_interface.html`: launches Monaco, block builder, serial monitor, drawer UI, and agent checks.
- `static/js/block_builder.js`: initializes block-builder state from `window.BB_CONFIG`.

## Current Logic Flow

### 1. App boot
1. `config.py` loads env vars.
2. `app.py` creates the Flask app.
3. Blueprints are registered.
4. `inject_globals()` runs on template render and pulls unlocked lessons from Supabase-backed progression state.
5. Templates receive sidebar data, lesson lookup helpers, and hover zoom helpers.

### 2. Authentication flow
1. User hits `/login` or `/register`.
2. `routes/auth.py` delegates to `utils/auth.py`.
3. User records live in Supabase via `utils/db_client.py`.
4. Successful login stores `user_id`, `username`, role flags, and welcome-state in session.
5. `seed_first_lesson()` ensures the first lesson is unlocked.
6. Student users go to `/dashboard`; parent users go to `/parent`.

### 3. Student dashboard flow
1. `/dashboard` loads completed lessons, unlocked lessons, and earned badges.
2. It scans `utils.lessons.LESSONS` in order.
3. The first unlocked but incomplete non-challenge lesson becomes the "current lesson".
4. The dashboard template renders progress and badge state.

### 4. Lesson page flow
1. Student opens `/lessons/<lesson_key>`.
2. `routes/lessons.py` fetches lesson metadata from `utils.lessons.get_lesson()`.
3. Unlock status is checked with `utils.progression.is_unlocked()`.
4. Project content is loaded from `utils.project_registry.PROJECTS`.
5. If a project has circuit image + steps, `render_assembly_guide()` generates the assembly guide HTML.
6. If the lesson has a `block_builder` preset:
   - `utils.block_builder.get_builder_html()` generates the floating or embedded builder launcher.
   - drawer/tutorial content is resolved from the project module or legacy content tables.
   - `standalone_ide` URL is built for the lesson page.
7. The lesson template renders:
   - story/instructions
   - assembly guide
   - block builder launcher or IDE
   - drawer steps

### 5. Lesson content loading flow
1. `utils.project_registry.py` scans the `utils` package.
2. Any module named `project_*` with a `PROJECT` dict is registered automatically.
3. Each project module usually provides:
   - `meta`
   - `steps`
   - `drawer`
   - `presets`
4. `utils.lessons.py` separately defines which lesson template and builder preset is used for routing and progression order.

This means lesson content is split across:
- project data modules in `utils/`
- visual page templates in `templates/lessons/`
- route registration/order in `utils/lessons.py`

### 6. Block builder flow
1. A lesson requests `/standalone_ide/<preset>` or `/builder?preset=...`.
2. `routes/builder.py` calls `utils.block_builder_config.build_config()`.
3. `build_config()` resolves the preset from:
   - `PROJECTS[preset]`
   - legacy `PRESETS`
   - a preset nested inside another project
4. The sketch string is parsed:
   - if it contains `//>>`, `parse_steps()` creates progression-mode step configs
   - otherwise `parse_sketch()` creates free-mode global/setup/loop block trees
5. Config JSON is injected into the frontend as `window.BB_CONFIG`.
6. `static/js/block_builder.js` reads that config and initializes browser state.
7. The builder runtime:
   - renders blocks
   - generates Arduino code
   - validates guided steps
   - saves progress to Supabase
   - reloads saved progress when allowed

### 7. Builder/editor sync flow
1. `templates/components/arduino_interface.html` loads the builder fragment and Monaco editor.
2. In blocks mode, the visual workspace is primary.
3. Switching to editor mode copies generated code into Monaco.
4. Switching back to blocks mode sends editor code to `/parse`.
5. `routes/builder.py:/parse` calls `utils.block_parser.parse_sketch()`.
6. Parsed block data is pushed back into the builder workspace with `window.setBlockData()`.

### 8. Progression-mode lesson flow
1. A sketch with `//>>` markers is treated as a step-by-step guided lesson.
2. `parse_steps()` breaks it into labeled steps and derives per-step config.
3. Phantom directives `//??` become required slots.
4. Locked directives `//##` become fixed read-only code blocks.
5. Completed step state is carried forward in browser memory and auto-saved to Supabase.
6. Drawer content in the IDE updates per step using the lesson's drawer metadata.

### 9. Save/load flow
1. `static/js/block_builder.js` saves `blocks_json` to Supabase REST endpoints.
2. Key identity is `username + page`.
3. Free-mode saves store global/setup/loop block trees.
4. Progression-mode saves store:
   - current step index
   - step snapshots in `student_saves`
5. Loading restores the workspace from the saved record.

### 10. Physical device / agent flow
1. `templates/components/arduino_interface.html` polls `http://127.0.0.1:3210/status`.
2. It asks the local Arduino Agent for:
   - available ports
   - compile
   - upload
   - serial start/stop
3. Serial monitor output is streamed from a websocket at `ws://127.0.0.1:3211`.

This is an important architectural boundary:
- Flask handles lesson content, persistence, and builder config.
- A separate local Arduino Agent handles compile/upload/serial access.

### 11. Lesson completion flow
1. Student posts to `/lessons/complete`.
2. `utils.progression.complete_lesson()` marks the lesson complete in Supabase.
3. The next lesson in `LESSON_SEQUENCE` is unlocked.
4. Badge checks run through `utils.badges.check_and_award_badges()`.
5. Student is redirected back to the dashboard.

### 12. Parent flow
1. Parent logs in and is routed to `/parent`.
2. `routes/parent.py` loads linked student accounts.
3. Completion counts are calculated from progression records.
4. Parent can:
   - create student accounts
   - reset student passwords

### 13. Admin flow
1. Admin opens `/admin`.
2. The admin route aggregates:
   - feedback threads
   - challenge submissions
   - activity stats
   - user list and progress
3. Admin tools also expose:
   - preset builder
   - step builder
   - sim builder
4. Admin actions write back to Supabase, sometimes through helper utilities and sometimes directly through REST calls.

## Core Data Boundaries

### Session state
Stored in Flask session:
- `user_id`
- `username`
- `is_parent`
- `is_admin`
- `show_welcome`

### Database-backed state
Stored in Supabase:
- users
- lesson progression
- block builder saves
- feedback threads/messages
- challenge submissions
- parent/student links
- activity data

### File-backed lesson state
Stored in repo files:
- lesson templates
- project metadata
- preset sketches
- drawer content
- circuit/build visuals

## Architectural Notes

### What is centralized
- lesson order: `utils/lessons.py`
- project discovery: `utils/project_registry.py`
- auth/db access: `utils/auth.py`, `utils/db_client.py`
- parsing and builder config: `utils/block_parser.py`, `utils/block_builder_config.py`

### What is split across multiple places
- a lesson's route identity, progression order, and template live in `utils/lessons.py`
- the lesson’s content/data lives in `utils/project_*.py`
- the lesson’s page markup lives in `templates/lessons/*.html`

### Important current coupling
- the builder frontend depends on server-generated `BB_CONFIG`
- the builder save/load path talks directly to Supabase REST from browser JS
- compile/upload do not go through Flask; they go to a local agent process
- lesson pages combine server-side rendered HTML with a JS-heavy IDE shell

## Fast Navigation Guide
- Start app logic: `app.py`
- Student lesson route: `routes/lessons.py`
- Builder route layer: `routes/builder.py`
- Lesson registry/order: `utils/lessons.py`
- Project auto-discovery: `utils/project_registry.py`
- Sketch parsing: `utils/block_parser.py`
- Builder config creation: `utils/block_builder_config.py`
- Frontend IDE shell: `templates/components/arduino_interface.html`
- Frontend builder runtime: `static/js/block_builder.js`
- Auth and users: `utils/auth.py`
- Progression unlocks/completion: `utils/progression.py`

## Short Summary
The app is a Flask + Supabase platform where lesson pages are server-rendered, lesson content is file-driven, and the coding experience is powered by a custom browser block builder. The main logic path is:

`app.py` -> blueprint route -> lesson/project lookup -> builder config generation -> browser block builder runtime -> Supabase save/progression updates -> dashboard/sidebar refresh.
