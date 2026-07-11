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
| On new interpreter (`mode: interpreted`) | `three`, `twelve`, `thirteen`, `seventeen`, `nineteen` |
| Still on hand-authored `behaviors`/`components`, correct as shipped | `eleven`, `fifteen`, `eighteen` |
| Already correct on plain `code_driven`, no interpreter needed | `one`, `two`, `sixteen`, `try_it` |
| **No sim tab at all** | `four`, `nine`, `ten`, `six`, `seven`, `eight`, `five` |
| Deliberately carved out (bespoke `code_breaker.py`, not the sim system) | `fourteen` |

Steps below are ordered by dependency — each names what it unblocks. Mark items as they
land, same convention as the spec doc.

---

## Step 1 — LDR/light-sensor component + `A0`–`A5` constants

Blocks `six`, `seven`, `eight` entirely, and the `fifteen`/`eighteen`-style sonar
retrofits partially (analog pin naming).

- [ ] **1a. Engine.** Add `A0`–`A5` to `utils/sim_engine.py::_CONSTANTS` (currently
  absent — this is why even a hand-resolved `analogRead(A0)` sketch can't be
  `interpret()`-ed today, per the spec's "Discovered, not fixed here" note under 2a).
  Confirm `analogRead()` already resolves against `input_state` the same way
  `digitalRead()` does (it should, per the Phase 0 write-up) — write a direct test if
  not.
- [ ] **1b. Frontend LDR component.** Same shape as the existing `sonar` slider (0–100
  range, debounced POST — copy the `sonarDurationUs`/150ms-debounce pattern from
  `seventeen`'s retrofit rather than re-deriving it). New `ldr` case in `buildCol()`,
  wired into `buildInputPayload()`/`pinValueFor()`.
- [ ] **1c. Tests.** `tests/test_sim_engine.py`: `A0`–`A5` resolve to distinct pin
  numbers; an `analogRead(A0)`-driven if/else resolves against `input_state` correctly
  in both branches. `node --check` on the JS change.

## Step 2 — Serial console UI component

Blocks `six` (console *is* the entire sim, no LED at all) and `five`.

- [ ] **2a.** No backend work — `console_lines` already exists in `interpret()`'s
  result (added in 4a). Add a real scrolling monospace output component to
  `sim-engine.js` (`buildCol()` case + an `applyConsole()` that appends `console_lines`
  entries to a scroll region), replacing the current "last line tacked onto the status
  bar" stopgap from 4b.
- [ ] **2b.** Confirm the existing status-bar tack-on (from 4b, serving `thirteen`) still
  works or migrate it to the new component too, so there's one console pattern, not two.

## Step 3 — Wire the plain Phase-0 projects: `four`, `nine`, `ten`

No new engine or component work — Phase 0 already covers all three per the audit table.
Same pattern as `three`'s 1b wiring: add `sim_config: {mode: "interpreted", components:
[...]}` to each project's drawer, matching real pins.

- [ ] **3a. `four`.** Identical shape to `three` (single if/else, one button, one LED) —
  should be close to a copy-paste of `three`'s `sim_config`.
- [ ] **3b. `ten`.** Two switches read into vars before the `&&` comparison — Phase 0's
  statement-sequencing already handles this; wire switch+switch+LED components.
- [ ] **3c. `nine`.** **Design decision needed before wiring:** `nine`'s sketch has no
  live input — `String powerSlot` is a hardcoded constant, not something a student
  clicks. There's nothing to interact with in a sim tab built on the current
  button/switch/sonar/LDR component set. Options: (a) skip `nine` — leave it without a
  sim tab, documented as a second carve-out alongside `fourteen`, since "everything
  code driven" doesn't obviously imply "everything gets an interactive sim tab" when
  there's no input to drive; (b) add a dropdown/select component that lets the student
  pick the `powerSlot` value and re-runs `interpret()` on selection. Resolve this before
  spending engine time on it — don't default to (b) without confirming it's worth the
  new component type for one project.
- [ ] **3d. Tests.** End-to-end `interpret()` cases against each real (directive-stripped)
  sketch, same convention as `three`/`eleven`/`twelve`.

## Step 4 — Wire the LDR-dependent projects: `seven`, `six`, `eight`

Depends on Step 1 (LDR) and, for `six`, Step 2 (console).

- [ ] **4a. `seven`.** LDR + single if/else + LED — straightforward once Step 1 lands.
- [ ] **4b. `six`.** LDR + Step 2's console component, no LED at all.
- [ ] **4c. `eight` — design decision needed.** The dark branch contains its own
  `delay()`-paced blink+tone loop that must **keep repeating for as long as the
  condition holds**, not just for one `loop()` pass. The engine's existing
  timed-sequence mechanism (2a) only produces a sequence for a *single* `loop()`
  pass, capped by `_MAX_LOOP_MS` — it doesn't re-trigger. Two ways to close this gap:
  (a) client-side: after a sequence finishes playing, `initInterpreted` re-POSTs the
  *same* `input_state` automatically (as if simulating another `loop()` iteration) and
  keeps looping the animation as long as the condition is still true, stopping when a
  fresh POST reports no sequence; (b) engine-side: teach `interpret()` to detect
  "branch re-entered with unchanged input, same sequence produced" and return an
  explicit `repeat: true` flag so the client doesn't need to guess. Prefer (a) — it's
  pure frontend, no engine change, and mirrors how `eighteen`'s continuous polling
  (Step 6) will work anyway, so the two hard cases converge on one pattern instead of
  two. Confirm this before starting; don't build (b) speculatively.
- [ ] **4d. Tests.** End-to-end `interpret()` cases for `seven`/`six`/`eight`'s real
  sketches; for `eight`, a test that re-invoking with unchanged `input_state` still
  produces the identical sequence (proves the re-trigger loop is stable, not
  drifting).

## Step 5 — Wire `five`

No branching, `Serial.print` × 2 repeating — the "actually simple" one per the audit.

- [ ] **5a.** Wire via `mode: interpreted` (not a `code_driven` regex extension — the
  interpreter already emits `console_lines`, no reason to build a second path). Uses
  Step 2's console component; no button/switch/LED components needed at all if the
  sketch has no input — confirm `initInterpreted` handles a component-less/output-only
  sim tab without erroring before assuming this is a non-issue.
- [ ] **5b.** End-to-end test against the real sketch.

## Step 6 — `eighteen`: continuous-polling model + real wiring

The largest remaining piece. 4a already proved the *engine* evaluates `eighteen`'s real
sketch correctly (dual-flag state, `micros()`, speed calc) — this step is purely the
interaction model and frontend, which the spec explicitly deferred as out of scope for
Phase 1.

- [ ] **6a. Continuous polling pattern.** `eighteen`'s sketch polls both sonars every
  loop pass with no wait for a click — unlike every other `initInterpreted` project so
  far, which is click-triggered one-shot. Add a `setInterval`-driven poll loop to
  `initInterpreted` (opt-in via a `sim_config` flag, e.g. `polling: true`, so it doesn't
  change behavior for the five click-driven projects already live) that re-POSTs
  current input + cached `state` on a fixed cadence and re-paints results. Reuse this
  same mechanism for Step 4c's `eight` re-trigger case if the pattern fits — check
  before building two similar-but-different polling loops.
- [ ] **6b. Dual sonar input component.** `eighteen` needs two independent sonar
  sliders sending raw pulse durations on their own `pin_echo`s (`sonar_a`, `sonar_b`) —
  the existing sonar component from `seventeen`'s 5b retrofit is single-instance;
  confirm it already supports multiple sonar components per sim tab (it likely does,
  since components are keyed by `id`/`pin`, but verify rather than assume).
- [ ] **6c.** Retrofit `project_eighteen.py`'s `sim_config` from `mode: "components"`
  (the old `timer`/hand-authored config) to `mode: "interpreted", polling: true`.
- [ ] **6d.** Test the polling cadence doesn't spam `/sim/run` unreasonably — pick an
  interval (the spec's discrete-request-latency comfort zone was ~100–200ms; polling
  every loop pass at that rate is a meaningfully different load profile than
  click-triggered requests — confirm this is acceptable or throttle further).

## Step 7 — Retrofit remaining hand-authored projects

Only `eleven` and `fifteen` need this — `one`, `two`, `sixteen` are explicitly
"unaffected, already correct" per the audit and should **not** be touched.

- [ ] **7a. `eleven`.** Nested if/else, two digitalRead inputs, no state — Phase 0
  covers it completely already (it's literally 1a's own regression test fixture
  shape). Swap `behaviors` for `mode: interpreted`, same components.
- [ ] **7b. `fifteen`.** Sequential if/else then 3-way if/elseif/else on sonar
  distance + `tone()`/`noTone()` — "matches well" per the audit, needs Phase 0 +
  the sonar/tone primitives Phase 0 + Step 1's sonar work already provide. Retrofit
  after `seventeen`'s sonar-slider pattern (Step 1/5b precedent) is confirmed stable.
- [ ] **7c.** Tests for both against their real sketches.

## Step 8 — Browser verification (closes every "Not verified" note)

No JS test infrastructure exists, so every piece above ships with automated coverage
only at the `interpret()`/route level, never the actual click/drag experience. Do this
incrementally — after each of Steps 3–7, not as one pass at the end, so a broken
component doesn't stack under the next one:

- [ ] Log in as an admin/test user, open each newly-wired lesson's sim tab, and
  exercise every input (click, drag, hold) against every branch the sketch has.
- [ ] Specifically confirm: `playSequences` timing for `eight`'s re-trigger loop and
  `eighteen`'s polling don't visually stutter or leak timers on repeated
  clicks/navigation away (check `container._simCleanup` actually fires).
- [ ] Confirm the LDR and second-sonar sliders debounce correctly and don't flood
  `/sim/run` while dragging.

## Step 9 — Retire the old system

Only once every shipped project is off `behaviors`/hand-authored `components` mode —
verify with a repo-wide grep, don't assume from this doc's list.

- [ ] **9a.** Confirm zero remaining `"behaviors"` keys across `utils/project_*.py`
  (`grep -L` won't help here — grep *for* `"behaviors"` and expect no hits).
- [ ] **9b.** Delete `templates/admin/sim_builder.html` and its route(s) in
  `routes/admin.py` (or wherever it's mounted — confirm before deleting).
- [ ] **9c.** Remove the hand-authored-`behaviors` client path (`init()` in
  `sim-engine.js`) once nothing references it — check `mode` dispatch sites first;
  don't delete `init()` while any template still calls it.
- [ ] **9d.** Update `SIM_ENGINE_ROLLOUT_SPEC.md`'s "What becomes obsolete" section to
  record this as done.

## Step 10 — Housekeeping

- [ ] Commit the currently-uncommitted Phase 0–3 work (`routes/builder.py`,
  `static/js/sim-engine.js`, the five already-retrofitted `project_*.py` files,
  `utils/sim_engine.py`, the two new test files) — this predates this plan and is
  sitting in the working tree unstaged. Do this as its own commit before starting
  Step 1, so the completion work has a clean base to diff against.
- [ ] Rebuild `utils/kb_build.py` once at the end of this rollout (not after every
  step) — every retrofitted project's drawer content changes, and per this repo's
  cadence convention that index is rebuilt weekly/pre-release, not per edit.

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
