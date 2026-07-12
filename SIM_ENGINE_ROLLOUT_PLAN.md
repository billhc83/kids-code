# Sim Engine Rollout — Completion Plan

Follow-up to `SIM_ENGINE_ROLLOUT_SPEC.md`, which covers engine Phases 0–3 and five
end-to-end projects (`three`, `twelve`, `thirteen`, `seventeen`, `nineteen`). This doc
scopes what's left to actually finish the rollout: two never-built shared components
(LDR, Serial console), per-project wiring for the seven sketches that still have **no
sim tab at all**, `eighteen`'s harder continuous-polling case, retrofitting the
remaining hand-authored projects, and retiring the old system once nothing depends on
it anymore.

**Current state (verified against code, not the spec's checkmarks alone):**

| Status | Projects |
|---|---|
| On new interpreter (`mode: interpreted`) | `three`, `four`, `six`, `seven`, `eight`, `ten`, `twelve`, `thirteen`, `seventeen`, `eighteen`, `nineteen` |
| Still on hand-authored `behaviors`/`components`, correct as shipped | `eleven`, `fifteen` |
| Already correct on plain `code_driven`, no interpreter needed | `one`, `two`, `sixteen`, `try_it` |
| **No sim tab at all** | `nine` (deferred — needs a content fix first, see Step 3c), `five` |
| Deliberately carved out (bespoke `code_breaker.py`, not the sim system) | `fourteen` |

Steps below are ordered by dependency — each names what it unblocks. Mark items as they
land, same convention as the spec doc.

---

## Step 1 — LDR/light-sensor component + `A0`–`A5` constants

Blocks `six`, `seven`, `eight` entirely, and the `fifteen`/`eighteen`-style sonar
retrofits partially (analog pin naming).

- [x] **1a. Engine.** Add `A0`–`A5` to `utils/sim_engine.py::_CONSTANTS` (currently
  absent — this is why even a hand-resolved `analogRead(A0)` sketch can't be
  `interpret()`-ed today, per the spec's "Discovered, not fixed here" note under 2a).
  Confirm `analogRead()` already resolves against `input_state` the same way
  `digitalRead()` does (it should, per the Phase 0 write-up) — write a direct test if
  not. Mapped to real Uno pin numbers (`A0`=14 … `A5`=19) so they share the same pin
  namespace as digital pins 0–13 rather than colliding with them; confirmed
  `analogRead()` already read `input_state` correctly, no engine change needed there.
- [x] **1b. Frontend LDR component.** Same shape as the existing `sonar` slider (0–100
  range, debounced POST — copy the `sonarDurationUs`/150ms-debounce pattern from
  `seventeen`'s retrofit rather than re-deriving it). New `ldr` case in `buildCol()`,
  wired into `buildInputPayload()`/`pinValueFor()`. Slider is a 0 (dark)–100 (bright)
  brightness UI value, converted to a raw `analogRead()` value (0–1023) via
  `ldrRawValue()` before being sent, same pattern as `sonarDurationUs()`.
- [x] **1c. Tests.** `tests/test_sim_engine.py`: `A0`–`A5` resolve to distinct pin
  numbers; an `analogRead(A0)`-driven if/else resolves against `input_state` correctly
  in both branches. `node --check` on the JS change.

## Step 2 — Serial console UI component

Blocks `six` (console *is* the entire sim, no LED at all) and `five`.

- [x] **2a.** No backend work — `console_lines` already exists in `interpret()`'s
  result (added in 4a). Add a real scrolling monospace output component to
  `sim-engine.js` (`buildCol()` case + an `applyConsole()` that appends `console_lines`
  entries to a scroll region), replacing the current "last line tacked onto the status
  bar" stopgap from 4b. Done as a `console`-type `buildCol()` case (no pin — Serial
  isn't wired to a physical pin, `makeLbl()` already omits the pin badge when one's
  absent) plus `applyConsole(id, lines)`, wired into `initInterpreted`'s `run()` success
  callback.
- [x] **2b.** Confirm the existing status-bar tack-on (from 4b, serving `thirteen`) still
  works or migrate it to the new component too, so there's one console pattern, not two.
  Kept both, gated so only one is ever active per tab: `initInterpreted` now computes
  `consoleComponents` once and, on each result, appends to every `console` component's
  transcript if one exists in `sim_config`, otherwise falls back to the status-bar
  tack-on — `thirteen` (button-only, no `console` component) keeps working unchanged
  without carrying a second live pattern once `five`/`six` add one.

## Step 3 — Wire the plain Phase-0 projects: `four`, `nine`, `ten`

No new engine or component work — Phase 0 already covers all three per the audit table.
Same pattern as `three`'s 1b wiring: add `sim_config: {mode: "interpreted", components:
[...]}` to each project's drawer, matching real pins.

- [x] **3a. `four`.** Identical shape to `three` (single if/else, one button, one
  buzzer instead of an LED) — added the `sim` tab with `mode: interpreted`,
  `button`(pin 2)/`buzzer`(pin 8) components, copy-pasted from `three`'s shape.
- [x] **3b. `ten`.** Two switches read into vars before the `&&` comparison — Phase 0's
  statement-sequencing already handles this; wired `switch`(pin 2)/`switch`(pin
  3)/`led`(pin 8) components. Existing `Serial.println` calls in the sketch are left
  to the Step 2b status-bar fallback (no `console` component added — out of this
  step's scope).
- [x] **3c. `nine`.** **Resolved: skip, deferred as its own follow-up.** User flagged
  that `nine`'s sketch is missing serial-monitor output it's supposed to have (prints
  showing `powerSlot`/`currentEnergy`/on-off status) — checked every commit in git
  history for `utils/project_nine.py` and confirmed it never actually had
  `Serial.print`/`println` calls beyond `Serial.begin`, so there's no prior version to
  restore. User asked to leave `nine` alone entirely for now rather than draft new
  print statements within this step's scope — needs a separate content pass (fix the
  sketch's missing serial output first) before any sim-tab wiring decision is
  revisited.
- [x] **3d. Tests.** End-to-end `interpret()` cases against `four`/`ten`'s real sketches
  (`tests/test_sim_engine.py`), same convention as `three`/`eleven`/`twelve`. `nine`
  excluded per 3c.

## Step 4 — Wire the LDR-dependent projects: `seven`, `six`, `eight`

Depends on Step 1 (LDR) and, for `six`, Step 2 (console).

- [x] **4a. `seven`.** LDR + single if/else + LED — added the `sim` tab with
  `mode: interpreted`, `ldr`(pin 14 / `A0`)/`led`(pin 13) components, same shape as
  `three`'s wiring.
- [x] **4b. `six`.** LDR + Step 2's console component, no LED at all — added
  `ldr`(pin 14)/`console` components; console has no `pin` (Serial isn't wired to a
  physical pin — `makeLbl()` already handles that).
- [x] **4c. `eight` — design decision resolved, no code needed.** The dark branch
  contains its own `delay()`-paced blink+tone loop that must **keep repeating for as
  long as the condition holds**, not just for one `loop()` pass. Traced
  `initInterpreted`'s existing `playSequences()` before building anything: it already
  loops whatever sequence one `interpret()` call returns, client-side, every
  `sequence_duration` ms via its own `setTimeout` self-reschedule, stopping only when
  the *next real input event*'s `applyOutputs()` calls `clearSequencePlayback()`.
  Since `eight`'s dark branch has no state that varies pass to pass, replaying the one
  recorded `{t:0,HIGH}/{t:150,LOW}` timeline forever is behaviorally identical to
  re-invoking `loop()` every pass — option (a) from the original two-way choice, but
  it already existed rather than needing to be built; no `repeat: true` flag (option
  (b)) needed. Confirmed with 4d's repeated-call test.
- [x] **4d. Tests.** End-to-end `interpret()` cases for `seven`/`six`/`eight`'s real
  sketches (`tests/test_sim_engine.py`) — bright/dark for all three (console-line
  assertions for `six`, pin-state assertions for `seven`, sequence assertions for
  `eight`), plus a test that two `interpret()` calls with unchanged `input_state`
  produce byte-identical `pin_sequences`/`sequence_duration` for `eight` (proves the
  client's replay-forever loop in 4c isn't masking any drift).

## Step 5 — Wire `five`

No branching, `Serial.print` × 2 repeating — the "actually simple" one per the audit.

- [x] **5a.** Wire via `mode: interpreted` (not a `code_driven` regex extension — the
  interpreter already emits `console_lines`, no reason to build a second path). Uses
  Step 2's console component; no button/switch/LED components needed at all if the
  sketch has no input — confirmed `initInterpreted` handles a component-less/output-only
  sim tab without erroring: `components` defaults to `[]`, the event-binding loop and
  seed-visuals loop both no-op on an empty array, and `run({}, 'Ready')` still fires
  unconditionally at the end, so the console component gets `console_lines` from the
  seed request with nothing else needed. Added `utils/project_five.py`'s `sim` tab with
  just a single `console` component, same shape as `six`'s console entry minus the LDR.
- [x] **5b.** End-to-end test against the real sketch. `tests/test_sim_engine.py::
  test_five_console_only_no_pin_states` asserts the seed call's `console_lines` match
  setup's banner plus both loop-pass prints, and `pin_states` is empty (no outputs
  wired at all).

## Step 6 — `eighteen`: continuous-polling model + real wiring

The largest remaining piece. 4a already proved the *engine* evaluates `eighteen`'s real
sketch correctly (dual-flag state, `micros()`, speed calc) — this step is purely the
interaction model and frontend, which the spec explicitly deferred as out of scope for
Phase 1.

- [x] **6a. Continuous polling pattern.** Added a self-rescheduling `setTimeout` poll
  loop to `initInterpreted` (`schedulePoll()`/`POLL_INTERVAL_MS` in `sim-engine.js`),
  opt-in via `sim_config.polling: true` so the five click-driven projects already live
  are unaffected (`config.polling` defaults falsy, `schedulePoll()` no-ops). It re-POSTs
  `buildInputPayload()` + the cached `persistState` from inside `run()`'s own
  success/failure callback rather than a bare `setInterval`, so a slow round trip can't
  pile up overlapping requests — matches Step 4c's `playSequences` self-reschedule
  shape. Checked reuse against `eight`'s re-trigger case first, per this step's note:
  they're different mechanisms on purpose — `playSequences` loops a pre-computed
  client-side output timeline with no server round trip, while `eighteen` needs a fresh
  `interpret()` call each tick because its persistent `sawA`/`timeA` state and
  `micros()`-based timing must actually advance server-side between ticks. Left
  `playSequences` untouched.
- [x] **6b. Dual sonar input component.** Verified, no code change needed — every
  sonar code path in `sim-engine.js` (DOM lookups, `inputState`, `buildInputPayload`)
  is keyed off `comp.id`/`comp.pin_echo` inside a `components.forEach`, so two sonar
  entries with distinct ids (`sonar_a`/`sonar_b`) and distinct `pin_echo`s (3, 5) don't
  collide — same precedent as 4c/6a.
- [x] **6c.** Retrofitted `project_eighteen.py`'s `sim_config` from `mode: "components"`
  (hand-authored 3-zone sonar + toggle `timer`) to `mode: "interpreted", polling: true`.
  Dropped the `timer` component (no `initInterpreted()` equivalent) in favor of a
  `console` component (Step 2) so the sketch's own `Serial.println` output ("Saw A" /
  "Saw B" / "Speed m/s: …") is what's shown, matching real hardware instead of a
  separately hand-maintained widget. `sonar_a`/`sonar_b` now carry `pin_trig`/`pin_echo`
  (2/3 and 4/5) matching the real preset sketch's `trigA/echoA/trigB/echoB` pins,
  verified against `SKETCH_PRESET['sketch']` directly. **Correction (found during the
  Step 10 full-implementation pass):** this bullet had been checked off previously but
  the actual file edit was never applied — `project_eighteen.py`'s `sim_config` was
  still the original `mode: "components"`/`behaviors` block (3-zone sonar + toggle
  `timer`), which is also why Step 9a's "clean" grep claim below was wrong. Neither
  `tests/test_sim_engine.py::test_eighteen_*` nor Step 9a's grep are run against a live
  view of this file's actual sim tab — the tests hand-roll their own resolved sketch
  string and never touch `sim_config`. Applied the retrofit described above for real
  this time; re-ran the "clean" grep from 9a and it now genuinely has no
  `"behaviors"`/`mode: "components"` hits anywhere in `utils/project_*.py`.
- [x] **6d.** 150ms — matches the existing sonar/LDR slider debounce already in this
  file and sits inside the spec's ~100–200ms discrete-request comfort zone, so
  click-driven and polling traffic share one tuned constant rather than two. No JS test
  harness exists in this repo (Step 8's opening note) to assert real request cadence, so
  added the engine-level guarantee polling safety actually depends on instead:
  `test_eighteen_repeated_polling_calls_with_unchanged_input_dont_refire_detection` and
  `test_eighteen_polling_cadence_produces_no_errors_and_stable_state` in
  `tests/test_sim_engine.py` run several 150ms-spaced `interpret()` calls and assert no
  errors, no spurious duplicate prints, and idle stability — same convention as 4d's
  repeated-call test for `eight`.

## Step 7 — Retrofit remaining hand-authored projects

Only `eleven` and `fifteen` need this — `one`, `two`, `sixteen` are explicitly
"unaffected, already correct" per the audit and should **not** be touched.

- [x] **7a. `eleven`.** Nested if/else, two digitalRead inputs, no state — Phase 0
  covers it completely already (it's literally 1a's own regression test fixture
  shape). Swapped `behaviors` for `mode: interpreted`, same `switch`/`button`/
  `led`/`buzzer` components and pins unchanged. `test_eleven_*` in
  `tests/test_sim_engine.py` already existed against this exact sketch shape and
  continue to pass — no new engine work needed.
- [x] **7b. `fifteen`.** Sequential if/else then 3-way if/elseif/else on sonar
  distance + `tone()`/`noTone()` — Phase 0 + the sonar/tone primitives Phase 0 +
  Step 1's sonar work already provide everything needed. Swapped `behaviors`
  (hand-authored `safe`/`warning`/`danger` zone strings) for `mode: interpreted`,
  same `sonar`/`led` x3/`buzzer` components and pins, matching `SKETCH_PRESET`
  and `CIRCUIT_SPEC` directly.
- [x] **7c.** Tests for both against their real sketches. `eleven` already had
  `test_eleven_*` (hand-resolved sketch, same convention as twelve/thirteen/
  eighteen). Added `test_fifteen_*` in `tests/test_sim_engine.py` against a
  hand-resolved equivalent of `fifteen`'s Mission Complete sketch: safe zone
  (green on, buzzer off, no `pin_sequences`), no-echo (`duration == 0`) treated
  as safe, warning zone (yellow on, buzzer beeps — asserts the `tone()`/`noTone()`
  pair produces a real `pin_sequences` timeline, not just a flat final state),
  and danger zone (red on, buzzer continuous tone, no `pin_sequences` since
  there's only one write). All 75 tests in the file pass.

## Step 8 — Browser verification (closes every "Not verified" note)

No JS test infrastructure exists, so every piece above ships with automated coverage
only at the `interpret()`/route level, never the actual click/drag experience. Do this
incrementally — after each of Steps 3–7, not as one pass at the end, so a broken
component doesn't stack under the next one:

- [x] Log in as an admin/test user, open each newly-wired lesson's sim tab, and
  exercise every input (click, drag, hold) against every branch the sketch has.
  **Verified for the 6 single-step lessons**: `four`, `ten`, `seven`, `six`, `eight`,
  `five` — all pass after the fixes below. `eleven` is broken independent of this
  rollout (per the user, "needs some major rework") and is out of scope for this
  pass — verify separately once it's fixed. `eighteen` and `fifteen` are multi-part
  lessons whose sim tab only appears in the drawer content of the *last* guided
  block-builder step (`eighteen`'s is nested in the "Mission Complete" entry, index
  10 of 10 steps; `fifteen`'s is "Step 13 — Mission Complete", index 12 of 13).
  **Now verified** (Step 10 full-implementation pass): logged into the live app as
  the dedicated `test` account (user_type `test`), unlocked
  `project_eighteen_part_two`/`project_fifteen_part_two` directly via
  `utils.progression.unlock_lesson` (same call the app itself makes on natural
  completion — surgical, no need to walk 10+ intervening lessons), then
  fast-forwarded each page's block-builder state via a real authenticated
  `POST /api/blocks/save` with `{"current_step": <final index>, "student_saves": []}`
  — the exact mechanism `BB.saveBlocks()` uses, just driven directly instead of by
  placing blocks through 10+ prior steps. Drove a real headless-Chromium session
  (Playwright, already installed in this repo's venv) against the dev server:
  both lessons' drawers opened straight to their Mission Complete step and
  rendered the `Try It` sim tab correctly — `eighteen` showed both HC-SR04 sonar
  sliders (Start/Finish Gate) and a live Serial Monitor; `fifteen` showed the
  distance slider, 3 zone LEDs, and buzzer icon. This pass is *why* the 6c/9a
  correction above exists: browser verification was about to be run against
  `eighteen`'s still-un-retrofitted `sim_config` (`mode: "components"`), which,
  after 9c's removal of the `else { SimEngine.init(...) }` dispatch fallback, would
  have matched neither the `code_driven` nor `interpreted` branch and rendered an
  empty sim tab with no error — caught by re-reading the file before testing, fixed,
  then verified live as above. `fifteen` needed no code changes — it was already
  correct.
  **Bugs found and fixed during this pass — none caught by any `interpret()`-level
  test, since they're all in the client bootstrap/event sequence, not the
  interpreter itself** (`static/js/sim-engine.js` unless noted):
  - `initInterpreted()`'s seed request could fire before the page's async
    block-builder script (`loadBlockBuilder()` in `arduino_interface.html`) finished
    syncing `currentMode`/`window.getGeneratedCode`, sending an *empty* sketch. The
    resulting bogus `pin_modes: {}` response got cached and used to compute every
    subsequent press/release level until some other response happened to correct
    it — silently inverting HIGH/LOW on any `INPUT_PULLUP` pin. Found on `four`:
    holding the button never turned the buzzer on; a fast tap latched it on. Fixed
    by polling briefly for real sketch content before seeding
    (`seedWhenSketchReady()`), plus a `pinModesReady` guard on the button/switch
    handlers.
  - Same seed-call gap, different symptom on `seven`: `analogRead()`'s server-side
    default for a pin absent from `input_state` is a flat raw `0`
    (`utils/sim_engine.py`'s "total darkness"), not the LDR slider's actual
    50%-bright resting position, so the very first paint showed the night light on
    when it should've been off. Fixed by including sonar/LDR's real default
    readings in the seed payload (`buildIdleAnalogPayload()`) — safe to send early
    since, unlike button/switch, they don't need `pin_modes` first.
  - `five` (console-only, zero interactive components) had no way to ever trigger a
    second `run()` after the seed — a code edit sat invisible until the student
    navigated away and back. `_appendRerunButton` (previously wired only to
    `initCodeDriven`) is now generalized to take any rerun callback and offered on
    an `initInterpreted` tab with no button/switch/sonar/ldr components.
  - Unrelated to the sim engine, but blocking verification of *every* lesson's
    drawer: the opening comment in `static/css/drawer.css` contained a literal `*/`
    inside its own prose (`#drawer-*/.drawer-*`), prematurely closing the CSS
    comment and corrupting everything parsed after it — Firefox reported "Ruleset
    ignored due to bad selector," and the drawer's collapse tab rendered as blank,
    unstyled space with nothing clickable. Fixed by rewording the comment to avoid
    the accidental `*/`.
- [x] Specifically confirm: `playSequences` timing for `eight`'s re-trigger loop and
  `eighteen`'s polling don't visually stutter or leak timers on repeated
  clicks/navigation away (check `container._simCleanup` actually fires).
  `eight`'s re-trigger loop verified clean: no stutter/drift across ~15s of looping,
  cleanly restarts on repeated bright/dark toggles, and navigating away mid-loop
  leaves no console errors (`_simCleanup` stops it). **`eighteen`'s polling now
  verified** (Step 10 pass): with the sim tab open and polling active, navigated
  away mid-poll to another lesson and watched network traffic for 2s afterward —
  no stray `/sim/run` requests fired, confirming `_simCleanup` actually stops
  `schedulePoll`'s self-reschedule rather than leaking a `setTimeout`. Also drove
  both sonar sliders to trigger a full detect-A → detect-B → speed-calc → reset
  cycle live; console showed `Ready!` / `Saw A` / `Saw B` / `Speed cm/s:` / the
  numeric value exactly as `interpret()`'s tests predict (two separate
  `console_lines` entries for the `Serial.print`+`Serial.println` pair is
  by-design, not a bug), and the polling loop correctly re-fired a fresh
  detect/reset cycle on the next tick since static sonar readings look identical
  to a new object sitting in the trap — matches real hardware, not a defect.
- [x] Confirm the LDR and second-sonar sliders debounce correctly and don't flood
  `/sim/run` while dragging.
  LDR debounce verified smooth on `six`/`seven` (one request ~150ms after the drag
  stops, not per-pixel). **`eighteen`'s dual-sonar and `fifteen`'s sonar debounce
  now verified** (Step 10 pass): scripted 16-18 rapid slider position changes
  (~20ms apart, well under the 150ms debounce window) via Playwright on both —
  `eighteen` fired only 4 `/sim/run` requests (some of which are its own
  background polling ticks, not drag-related), `fifteen` fired exactly 1. Also
  confirmed `fifteen`'s three zone thresholds fire correctly against the real
  sketch's `distance > 50` / `distance > 20` branches: 80cm → green (safe), 35cm →
  yellow (warning), 20cm → red (danger) — the last one exercises the exact `> 20`
  boundary, where 20 is *not* greater than 20 and correctly falls through to the
  danger `else`, not an off-by-one bug.

## Step 9 — Retire the old system

Only once every shipped project is off `behaviors`/hand-authored `components` mode —
verify with a repo-wide grep, don't assume from this doc's list.

- [x] **9a.** Confirm zero remaining `"behaviors"` keys across `utils/project_*.py`
  (`grep -L` won't help here — grep *for* `"behaviors"` and expect no hits). Also
  grepped for `mode: "components"`/`'mode': 'components'` — no hits either. **Correction
  (Step 10 full-implementation pass):** this was checked off prematurely — the grep
  actually had one hit, `project_eighteen.py` (see 6c's correction above), which this
  step's own note should have caught. Re-ran the grep after fixing 6c for real; clean now.
- [x] **9b.** Deleted `templates/admin/sim_builder.html`, its `/admin/sim-builder`
  route (and `sim_builder()` view) in `routes/admin.py`, and the "🎮 Sim Builder" link
  in `templates/admin/index.html` — confirmed no other references anywhere in the repo
  before deleting.
- [x] **9c.** Removed the hand-authored-`behaviors` client path: `init()` (and the
  `applySonar()`/`SONAR_ZONE_*` helpers it exclusively used) deleted from
  `sim-engine.js`, along with its stale JSDoc references. Checked both `mode` dispatch
  sites first (`templates/components/arduino_interface.html`,
  `templates/try_it_builder.html`) — both had an `else { SimEngine.init(simDiv, cfg); }`
  fallback for any `mode` other than `code_driven`/`interpreted`; removed the fallback
  from both since no shipped config hits it anymore. `initTimeline()` — used only by
  `initCodeDriven()`, never by `init()` — was left in place and just dropped from the
  public `SimEngine` export (nothing outside the module called it directly). `node
  --check` passes on the trimmed file.
- [x] **9d.** Updated `SIM_ENGINE_ROLLOUT_SPEC.md`'s "What becomes obsolete" section to
  record this as done.

## Step 10 — Housekeeping

- [x] Commit the currently-uncommitted Phase 0–3 work (`routes/builder.py`,
  `static/js/sim-engine.js`, the five already-retrofitted `project_*.py` files,
  `utils/sim_engine.py`, the two new test files) — this predates this plan and is
  sitting in the working tree unstaged. Do this as its own commit before starting
  Step 1, so the completion work has a clean base to diff against. **Done** —
  landed as commit `c143882` ("Expand sim engine... with rollout plan/spec updates
  and test coverage"), matching this bullet's file list exactly, before any of
  Steps 1–9's work began.
- [x] Rebuild `utils/kb_build.py` once at the end of this rollout (not after every
  step) — every retrofitted project's drawer content changes, and per this repo's
  cadence convention that index is rebuilt weekly/pre-release, not per edit.
  **Done** — `python -m utils.kb_build` rebuilt `data/help_index.npz`/
  `help_index_meta.json` (321 chunks: 239 auto-derived, 82 hand-authored,
  dim=1536). `tests/test_kb_freshness.py` passes against the new index.

---

## Rough estimate

| Step | Estimate |
|---|---|
| 1 — LDR component + `A0`–`A5` | 1–1.5 days |
| 2 — Serial console component | 0.5–1 day |
| 3 — `four`/`nine`/`ten` wiring (pending `nine` decision) | 1–1.5 days |
| 4 — `seven`/`six`/`eight` wiring (pending `eight` decision) | 1.5–2 days |
| 5 — `five` wiring | 0.5 day |
| 6 — `eighteen` continuous polling + wiring | 2–3 days, high uncertainty |
| 7 — Retrofit `eleven`/`fifteen` | 1 day |
| 8 — Browser verification (spread across 3–7) | 1–1.5 days total |
| 9 — Retire old system | 0.5 day |

**Total: ~9–12 dev-days**, once the two flagged design decisions (`nine`'s no-input
case, `eight`'s re-trigger mechanism — which Step 6 may resolve for free via the same
polling pattern `eighteen` needs) are made rather than deferred again.
