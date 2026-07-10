# Sim Engine Rollout — Implementation Spec

Goal: add a `sim` drawer tab to every project that is missing one.

## Current state

9 of 20 projects already have a sim tab: `eleven, twelve, thirteen, fifteen, sixteen,
seventeen, eighteen, nineteen, try_it`.

**11 are missing it: `one, two, three, four, five, six, seven, eight, nine, ten, fourteen`.**

No template or backend work is needed for any tier below. `templates/components/arduino_interface.html`
already renders any drawer tab with `"type": "sim"` generically (line ~528), and
`routes/builder.py` / `routes/try_it.py` already POST `{sketch, sim_config}` to
`utils/sim_engine.py` project-agnostically. All 11 missing projects have exactly **one**
drawer step (`DRAWER_CONTENT[...]["steps"]` has a single entry), so each project needs
exactly one `sim` key added to one `tabs` dict.

Two sim modes exist today:
- **`code_driven`** — server parses `digitalWrite`/`delay` out of the fixed sketch. Config is
  just a `pins` dict. See `utils/sim_engine.py` and the `sim_config` in `project_sixteen.py`.
- **interactive `behaviors`** — client-side `when/then` rules against components the student
  clicks (`static/js/sim-engine.js`). Authored via the `/admin` Sim Builder GUI
  (`templates/admin/sim_builder.html`), which generates the Python dict to paste in.

`sim-engine.js` currently supports these component types only: `led`, `button`, `switch`,
`buzzer`, `timer`, `sonar`.

### Fixed infra bug (applies to every tier, not project-specific)

`routes/builder.py`'s `/sim/run` was missing `@csrf.exempt`, so every `code_driven` sim
click (any tier) failed with a CSRF 400 that the frontend surfaced as a generic
"Simulation error — check your code and try again." — this had nothing to do with any
individual project's `sim_config` and would have hit the 9 pre-existing sim tabs too, the
first time someone actually clicked run. Root cause: `templates/components/arduino_interface.html`
(the standalone IDE the lesson pages embed) doesn't extend `base.html`, so it has no
`<meta name="csrf-token">` / fetch-interceptor — its sibling POST routes `/parse` and
`/api/blocks/save` were already `@csrf.exempt` for this exact reason; `/sim/run` just missed
the same treatment when it was added. Fixed by adding `@csrf.exempt` above `@login_required`
on `sim_run()`, matching the existing pattern. If a future tier's interactive `behaviors`
sim (client-side, no server round-trip) ever needs a new POST endpoint, exempt it the same
way up front rather than rediscovering this.

**Second infra bug, same symptom class — `code_driven` sim ignored live editor edits.**
`sim-engine.js`'s `initCodeDriven` reads the sketch via
`window.getCurrentSketch ? window.getCurrentSketch() : window.getGeneratedCode()`.
`templates/try_it_builder.html` (`/try`) defines `getCurrentSketch` correctly —
`if (currentMode === 'editor' && editor) return editor.getValue();` else fall back to
`getGeneratedCode()` (the blocks-generated `#codeout` text). But
`templates/components/arduino_interface.html` — the actual IDE embedded on real lesson
pages — never defined `getCurrentSketch` at all, so it always fell through to
`getGeneratedCode()`, i.e. the sim ran against the last blocks output instead of whatever
was typed in the code editor. This silently breaks the sim for **any** project with
`'default_view': 'editor'` (like `one`/`two`), since the student never touches blocks at
all. Fixed by copying the same `getCurrentSketch` definition into
`arduino_interface.html` (near its `editor`/`currentMode` declarations). Check for this
same gap before assuming a `code_driven` sim's staleness is a `sim_config` problem —
compare `arduino_interface.html` against `try_it_builder.html` first for any
editor/blocks-mode plumbing difference like this one.

---

## Tier 1 — trivial, code_driven (no new component)

**Projects:** `one` ✅, `two` ✅, `nine`

Plain `digitalWrite` + `delay` LED blink/pattern — identical shape to the existing
`project_sixteen` sim. `pins` config only, no behaviors to author.

- Effort: ~15–20 min each
- Pattern to copy: `project_sixteen.py` `sim_config` (`"mode": "code_driven", "pins": {...},
  "loop_iterations": 4, "max_ms": 12000`)
- File touched: one edit to each `utils/project_{name}.py`, inside the existing single
  `tabs` dict (add a `"sim"` sibling to `explain`/`howto`/`logic`)

### Implementation notes from `one`/`two` (read this before doing `nine`)

- **`one` and `two` don't use the `"steps": [...]` DRAWER_CONTENT shape** that
  `project_sixteen` uses — their `DRAWER_CONTENT["project_{name}"]` has `"tabs"` sitting
  directly under the project key, no `"steps"` wrapper. This is NOT a blocker: both
  `routes/lessons.py` (the live `/lessons/...` render path) and `routes/builder.py`
  (`/preset`, `/standalone_ide`) do `drawer_content.get("steps") or [drawer_content]`
  before calling `normalize_drawer_steps`, so a flat dict is transparently treated as a
  one-entry steps list. `normalize_drawer_steps` then does
  `[{'id': k, **v} for k, v in s['tabs'].items()]`, which spreads `"type"` and
  `"sim_config"` through untouched. Net effect: **just add the `"sim"` key as a sibling
  inside whatever `"tabs"` dict already exists** — flat or stepped, same recipe, zero
  template/route changes needed either way. Check which shape a given project uses before
  assuming you need to add a `"steps"` wrapper; you don't.
- **`sim_engine.py` is fully generic** — it regex-parses `pinMode`/`digitalWrite`/`delay`
  straight out of whatever sketch string is active (`utils/sim_engine.py`), so the only
  per-project work is getting `sim_config.pins` (pin number → type/color/label) right to
  match the project's actual sketch. No Python changes outside the one `project_{name}.py`
  edit.
- **Steady-on sketches (no `delay()` in `loop()`, like `one`)**: `run()` has a guard
  (`sim_engine.py` ~line 169) that appends a synthetic 1ms delay when a loop has zero
  delays, so it won't spin forever — but this also means duration ends up tiny (a few ms)
  regardless of `loop_iterations`/`max_ms`. Those two keys are cosmetic no-ops for
  steady-on projects; don't spend time tuning them, any reasonable value works since the
  LED just shows "on" from t=0.
- **Blinking sketches (has `delay()`, like `two`)**: `duration = loop_iterations × sum of
  delays per loop`. Pick `loop_iterations`/`max_ms` so the sim shows a handful of full
  cycles without needlessly long timelines (`two` uses `loop_iterations: 4`, `max_ms: 8000`
  for a 2×500ms blink = 4000ms actual duration, well under the cap).
- Verify a `sim_config` by running `utils/sim_engine.py`'s `run(sketch, sim_config)`
  directly against the project's `SKETCH_PRESET['sketch']` and eyeballing the returned
  timeline before touching the browser — faster than a full UI smoke test and catches pin
  number / pinMode mismatches immediately.

## Tier 2 — low, interactive behaviors, 1 input

**Projects:** `three`, `four`

Single `digitalRead(button)` → LED (`three`) or buzzer (`four`). `button`+`led`/`buzzer` are
both supported component types.

- Effort: ~20–30 min each
- Pattern to copy: `project_eleven.py` `sim_config` (`"components": [...], "behaviors":
  [{"when": {...}, "then": {...}}, ...]`)
- Use the `/admin` Sim Builder GUI to generate the behaviors dict, then paste into the one
  `tabs` dict per project

## Tier 3 — low, interactive behaviors, 2 inputs

**Projects:** `ten`

Two `digitalRead(switch)` AND'd → LED (vault-lock logic). `switch`+`led` supported; just 4
behavior rules (both off, A only, B only, both on).

- Effort: ~30 min
- Same GUI-authored pattern as Tier 2, one extra input component and 2 extra rules

## Tier 4 — blocked on a new sim-engine component: light sensor (LDR)

**Projects:** `six`, `seven`, `eight`

All three gate logic on `analogRead()` from a photoresistor/LDR (`six`: ocean light level,
`seven`: night-light auto-on, `eight`: crystal alarm + `tone()`). `sim-engine.js` has no
light-sensor component today.

**Precedent exists** — `sonar` already implements the exact shape needed: a 0–100 range
`<input type="range">` slider (`static/js/sim-engine.js` ~line 268–285) whose value is
bucketed into named zones (`applySonar`, ~line 504–515) that behaviors match against as
discrete states, the same way `button`/`switch` states are matched. Building `ldr` is "do
the sonar pattern again," not a design from scratch.

**One-time engine build (`static/js/sim-engine.js`):**
1. `ldrSVG(id)` — new SVG markup for a photoresistor component (mirror `sonarSVG`, ~line 118)
2. Register in the render switch (~line 248–253): `case 'ldr': wrap.innerHTML = ldrSVG(...)`
3. Default state init (~line 309–313): add an `ldr` branch (e.g. default `"dim"`)
4. Slider wiring (~line 268–285, ~505–507): reuse the existing slider block, relabel units
   (raw `analogRead` 0–1023, or simplified 0–100 "brightness %")
5. `applyLDR(id, zone)` — zone bucketing + visual update (mirror `applySonar`, ~line 504–515);
   decide zone thresholds per lesson (e.g. `dark` / `dim` / `bright`) — expose as
   `sim_config` data (`comp.labels`) like sonar does, so each lesson can set its own cutoffs
   without further JS changes
6. Wire into the `apply` switch (~line 424–428): `case 'ldr': applyLDR(id, newState); break;`

- Engine effort: **4–8 hours** (design zone thresholds, SVG asset, wire through render/state/apply,
  test against `BLOCK_BUILDER_SYNC.md` invariants since these lessons don't use editor-sync steps
  so risk is low but should still be smoke-tested)
- Per-lesson effort once built: ~30 min × 3 (author `behaviors` referencing `ldr` zone states,
  same GUI/paste workflow as Tier 2/3)
- `eight` additionally uses `tone()` for the alarm — already covered by the existing `buzzer`
  component (on/off is sufficient; no separate "tone" component needed)

---

## Tier 5 — blocked on a new sim-engine component: serial monitor

**Projects:** `five`, `fourteen`

*(Amended: originally scoped as "not a fit" — on review, both can be served by a new sim
component that mimics a serial monitor, matching how these lessons actually work.)*

- `five` ("Secret Spy Data Beam") teaches `Serial.print`/serial communication. `STEPS = None`,
  no `circuit_image` — there's no breadboard to visualize, but a scrolling text-console
  component is a natural fit for what the lesson *does* simulate.
- `fourteen` ("Codebreaker") already has a bespoke interactive serial-monitor cipher puzzle via
  `utils/code_breaker.py`'s `serial_monitor()` helper, rendered directly in
  `templates/lessons/project_fourteen_part_one.html` — not through the drawer `sim` tab system
  at all. Bringing it under the standard `sim` tab means porting that existing UX into
  `sim-engine.js` as a first-class component type rather than a template-level one-off.

**One-time engine build (`static/js/sim-engine.js`):**
1. `serialSVG(id)` / a console-style DOM block (scrolling monospace output area + optional
   input line) — reuse the visual language and JS behavior already proven in
   `utils/code_breaker.py`'s `serial_monitor()` (see its JS string-building for print/line
   semantics) rather than inventing new UX
2. Register a `case 'serial':` in the render switch, alongside `led`/`button`/etc.
3. New "print" event type in the `behaviors`/timeline model — this is the one piece that's
   genuinely new (existing `when/then` behaviors mutate component *state*; a serial component
   needs to *append lines*), so the behavior DSL needs a small extension (e.g. `"then":
   {"serial": {"print": "ACCESS GRANTED"}}`) rather than pure state-swap
4. For `code_driven` mode (relevant to `five`, which is pure `Serial.print` from a fixed
   sketch): extend `utils/sim_engine.py` to also extract `Serial.print`/`Serial.println`
   calls into timeline events, mirroring the existing `digitalWrite`/`delay` extraction
   (`_extract_ops`, ~line 93–114)

- Engine effort: **1–1.5 days** — larger than Tier 4 because it needs a genuinely new event
  type (appended lines vs. state toggles) on both the JS and Python (`sim_engine.py`) sides,
  not just a new visual component reusing existing plumbing
- Per-lesson effort once built:
  - `five`: ~30–45 min (code_driven — extract `Serial.print` calls from the existing sketch)
  - `fourteen`: ~1–2 hours — this is a port/migration of an already-working bespoke puzzle
    (cipher matching, answer validation) into the generic component, not a fresh design; the
    cipher-matching logic in `code_breaker.py` needs to be reconciled with the `behaviors` DSL
    or kept as a template-level override. **Recommend confirming whether porting `fourteen` is
    worth it at all** — its existing implementation already works; the only benefit of
    migrating it is consistency with the drawer `sim` tab pattern, not new functionality.

---

## Total effort estimate

| Tier | Projects | One-time engine work | Per-lesson work | Tier total |
|---|---|---|---|---|
| 1 | one, two, nine | — | 15–20 min × 3 | ~1 hr |
| 2 | three, four | — | 20–30 min × 2 | ~1 hr |
| 3 | ten | — | 30 min | ~0.5 hr |
| 4 | six, seven, eight | 4–8 hrs (LDR component) | 30 min × 3 | ~6–10 hrs |
| 5 | five, fourteen | 1–1.5 days (serial component + `sim_engine.py` extension) | 30–45 min + 1–2 hrs | ~1.5–2 days |

**Grand total, all 11 projects: roughly 3–4 dev-days.**
**Grand total, Tiers 1–4 only (defer serial component): ~1–1.5 dev-days.**

## Recommended implementation order

1. Tiers 1–3 first (six projects, ~2.5 hrs, pure content authoring, no risk)
2. Tier 4 (build the LDR component once, then three lessons ride on it)
3. Tier 5 last, and only after confirming `fourteen`'s migration is wanted — its current
   bespoke implementation already works, so this tier is the one place where "add the sim
   tab" is a UX-consistency call rather than filling a functional gap
