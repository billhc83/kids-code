# Sim Engine Rollout — Implementation Spec (v2)

**Status: assessment only. Nothing in this doc has been built. This supersedes v1 —
kept in git history (see `git log -- SIM_ENGINE_ROLLOUT_SPEC.md`) for the abandoned
hand-authored-behaviors plan.**

## The mandate that changed this doc

Every sim tab must be **derived from the actual sketch**, for every project — the 9
already-shipped ones included. No hand-authored `behaviors` dict may describe circuit
logic that a human typed by hand and that can silently drift from what the sketch
really does. If the student edits the sketch, the sim must reflect that.

This kills both halves of the v1 plan:

- **`code_driven` mode (`utils/sim_engine.py`)** is not actually code-driven today —
  it's a regex replay. It extracts every `digitalWrite`/`delay` call in source order
  and plays them back **with zero awareness of `if`/`else`/`digitalRead`/`analogRead`**.
  For an output-only blink sketch (`one`, `two`, `sixteen`) that's fine — there's no
  branching to get wrong. For anything with a conditional, it's actively misleading:
  fed `project_three`'s button sketch, it would extract both the `HIGH` and `LOW`
  `digitalWrite(8, ...)` calls and just toggle them in sequence, regardless of button
  state.
- **Interactive `behaviors` DSL** (hand-authored `when`/`then` rules, authored via the
  `/admin` Sim Builder GUI) is code-*independent* by construction — a human reads the
  sketch, decides what it does, and writes a separate JSON description of that belief.
  It ships already wrong in at least one case (see [Bug found during this audit](#bug-found-during-this-audit-project_seventeen)),
  and the GUI that produces it has no way to represent anything beyond flat AND rules
  (see audit below) — no `else`, no `OR`, no state, no arithmetic.

Net effect: **there is currently no real interpreter anywhere in this codebase.**
Building one is the actual scope of "everything code driven," not a per-project content
task.

---

## Audit: what every project's sketch actually needs

Read directly off each project's `SKETCH_PRESET['sketch']` (not the authored `sim_config`,
which is frequently a poor match for it — see the "authored vs. real" column).

### Already shipped with hand-authored `behaviors` (9 projects)

| Project | Inputs | Conditional shape | Persistent state | Special ops | Authored `behaviors` vs. real sketch | Interpreter tier needed |
|---|---|---|---|---|---|---|
| `eleven` | digitalRead ×2 (switch, button) | nested if/else | none | — | matches well | **Phase 0** |
| `twelve` | digitalRead ×1 (button) | single if/else | none, but a hardcoded 3-LED delay chase is baked into the branch | — | approximates via `_sequence`/`_interval` authoring macros; diverges if sketch timing is edited | **Phase 0 + timed-sequence** |
| `thirteen` | digitalRead ×1 (button) | nested if, `running` flag gates a `millis()` timer | `bool running` + `millis()`-based elapsed time | `millis()` | collapses real reaction-timer logic to a press-to-toggle; timing itself isn't modeled | **Phase 1** (virtual clock) |
| `fifteen` | sonar (`pulseIn`) | sequential if/else then 3-way if/elseif/else on distance | none (recomputed each loop) | `tone()`/`noTone()`, `pulseIn()` | matches well | **Phase 0 + sonar/tone primitives** |
| `sixteen` | none | none | none | — | N/A — already plain `code_driven`, correct as-is | none (unaffected) |
| `seventeen` | sonar → continuous `distance` | **none at all** — sketch is a continuous `map()` into `tone()` pitch, no branches | none | `tone()`, `pulseIn()`, `map()` | **wrong** — authored behaviors copy-paste project fifteen's 3-zone scheme onto a sketch that has no zones | **Phase 2** (continuous value mapping) |
| `eighteen` | sonar ×2 → `distanceA`/`distanceB` | 3 flat sequential ifs with `&&` | `sawA`/`sawB` bool flags + `micros()` deltas for a speed calc | `micros()`, arithmetic | diverges significantly — authored rules only toggle a display, the real two-flag timing state machine and speed math aren't represented | **Phase 1** (virtual clock + arithmetic) |
| `nineteen` | digitalRead ×1 (button) | single if, no else | continuous servo position, not a tracked int/bool | `Servo.attach()/.write()` | **`sim_config` is a literal empty `{}`** — tab exists, unwired | **Phase 3** (new actuator primitive) |
| `try_it` (`/try`) | n/a | n/a | n/a | n/a | doesn't use `behaviors` at all — already calls the same regex `sim_engine.run()` as `code_driven` projects | none (already on the "derive from sketch" model, same limits as Phase-0-less `sim_engine.py`) |

`templates/admin/sim_builder.html` (the authoring GUI) has no way to express `else`,
`OR`, negation, or any persistent state — only flat conjunctive (AND-only) input→output
rules. It becomes dead weight once `sim_config` is derived from the sketch instead of
hand-typed; nothing is left for a human to author for any project harder than `eleven`.

### Bug found during this audit (`project_seventeen`)

Currently live and wrong, independent of this whole rearchitecture: `seventeen`'s
authored `behaviors` implement 3 discrete safe/warning/danger zones (copied from
`fifteen`), but `seventeen`'s actual sketch has no zones — it's a continuous
`map(distance, ...) → tone(buzzer, pitch)`. Any student who reads the code and then
plays with the sim today sees behavior that doesn't match what they just read. Worth
a standalone fix regardless of what happens with the rest of this doc.

### Not yet built (11 projects, from v1's scope)

Re-verified directly against each sketch (not the earlier tier writeup, which
undersold several of these):

| Project | Inputs | Conditional shape | Persistent state | Special ops | Interpreter tier needed |
|---|---|---|---|---|---|
| `one` | none | none (steady-on) | none | — | none (unaffected, already correct) |
| `two` | none | none (blink) | none | — | none (unaffected, already correct) |
| `three` | digitalRead ×1 (button) | single if/else | none | — | **Phase 0** |
| `four` | digitalRead ×1 (button) | single if/else (identical shape to `three`) | none | — | **Phase 0** |
| `nine` | **none — hardcoded `String powerSlot` constant**, no live input at all | if/elseif/elseif/else on **String equality**, then a second if/else on the derived int | `int currentEnergy` (set once per loop from the string chain) | String comparison | **Phase 0** — flagged because this was called "trivial, no conditions" in v1 and is not: the regex replay would grab both `digitalWrite` calls unconditionally, same failure mode as `three` |
| `ten` | digitalRead ×2 (switches), read into vars first, then compared | `if (LockA == 1 && LockB == 1)` — variable indirection, not inline `digitalRead()` | none beyond the two locals | — | **Phase 0** (needs statement-sequencing / variable assignment before the read is used in a condition) |
| `six` | analogRead (LDR) | single if/else | none | `Serial.println` — **and no `digitalWrite`/LED at all**, output is text-only | **Phase 0 + LDR primitive + serial console** (this one needs the console regardless of Tier-5 scoping — there's no other output) |
| `seven` | analogRead (LDR) | single if/else | none | — | **Phase 0 + LDR primitive** |
| `eight` | analogRead (LDR) | single if/else, but the "dark" branch contains an inner `delay()`-paced blink+tone loop that must keep repeating for as long as the condition holds | none | `tone()`/`noTone()` | **Phase 0 + LDR primitive + re-triggerable timed sequence** (harder than `seven`: this is not one instantaneous state, it's "keep animating while true, stop when false") |
| `five` | none | none | none | `Serial.println` × 2, repeating | **Serial console + `code_driven` extraction of `Serial.print`** (no interpreter branching needed — this one's actually simple) |
| `fourteen` | **text entry** (`Serial.available()`/`readString()`), not a component the student clicks | `for` loop over string indices, `if (likeness == 5)` | `int likeness`, `bool solved`, persisted across each submitted guess | String indexing, `for` loop, array-like comparison | **out of category** — see below |

`fourteen` needs an event model (submit a line of text → run to next input-wait point)
and language features (String indexing, `for` loops) that none of the other 19 projects
need at all. It already has a working bespoke implementation
(`utils/code_breaker.py`'s `serial_monitor()`, rendered directly in
`templates/lessons/project_fourteen_part_one.html`, not through the drawer `sim` tab
system). Building general string/`for`-loop/serial-input interpretation into the shared
engine, for exactly one project, when that project's UX already works, is a real
scope/value tradeoff — **flagging for a decision, not resolving it here**: either carve
`fourteen` out as a permanent exception to "everything code driven," or accept it as the
single most expensive item in this whole rollout for zero net new functionality.

---

## Target architecture

### Decided: server-side interpreter (Python)

Extend `utils/sim_engine.py` into a real interpreter. Every discrete interaction
(button press/release, switch toggle) POSTs current input state to `/sim/run` and gets
back resulting output state. Slider-style inputs (LDR) debounce — fire on drag-release
or a short idle window, not per-pixel-of-drag — so this stays a low-frequency POST
pattern, not a stream.

Rejected the client-side (JS) alternative despite the latency win, for two concrete
reasons specific to this repo:

- **No JS test infrastructure exists at all** (`tests/` is pytest-only — no
  `package.json`, no JS test runner). A parser/evaluator is exactly the code that most
  needs unit tests for edge cases (operator precedence, comparison semantics); shipping
  one in JS means building test tooling from scratch before it can be trusted, while a
  Python one drops straight into the existing suite — `tests/test_circuit_engine.py`
  already tests another declarative parser/resolver (`utils/circuit_engine.py`) in this
  exact style.
- **A client-side interpreter doesn't actually avoid a second implementation** — the
  existing no-branching `code_driven` replay stays in Python either way (no reason to
  move it), so "interpret in JS" would mean two implementations of overlapping language
  subsets to keep in sync, which is the exact drift risk this whole rearchitecture
  exists to kill.

Discrete-interaction round trips (~100–200ms) are normal web-app click latency and not
a concern. The debounce requirement on slider-driven components (LDR) is the one real
cost of this choice and should be designed in from the start of the LDR component work,
not bolted on after.

### Capability phases (engine-side, independent of any one project)

Each phase is additive. A project needs the lowest phase that covers everything in its
sketch (see audit tables above for which projects land where).

- **Phase 0 — core interpreter.** Global variables (`int`, `bool`, `String` constants),
  `pinMode` (`INPUT`/`INPUT_PULLUP`/`OUTPUT`), `digitalRead`/`analogRead` resolved
  against live simulated input component state, `if`/`else if`/`else` with comparison
  (`==`, `!=`, `<`, `>`, `<=`, `>=`) and logical (`&&`, `||`) operators, `String`
  equality, statement sequencing (assign-then-use, like `ten`'s `LockA`/`LockB`),
  `digitalWrite`, `tone()`/`noTone()` as instantaneous on/off, `delay()` treated as
  inert pacing. Covers `three`, `four`, `nine`, `ten`, plus retrofitting `eleven` and
  most of `fifteen`.
- **New component: LDR/light-sensor slider.** Same shape as the existing `sonar`
  component (0–100 range slider bucketed into named zones) — `sonar` is the precedent
  to copy. Needed by `six`, `seven`, `eight`, and retrofitting `fifteen`/`seventeen`.
- **New component: Serial console.** Scrolling monospace output area, driven by
  `Serial.print`/`Serial.println` extraction. Needed by `five`, `six` (no LED at all —
  the console *is* the entire sim), optionally `nine`/`ten`/`fifteen` for flavor text.
- **Timed-sequence / re-triggerable timeline.** For branches that contain their own
  `delay()`-paced loop (blink-while-dark in `eight`, the hardcoded LED chase in
  `twelve`): re-run the branch's own mini-timeline on a loop for as long as the
  triggering condition holds, cancel and restart if the input changes mid-cycle.
- **Phase 1 — virtual clock.** `millis()`/`micros()` backed by an actual running clock
  (real or simulated time), persistent variable state across evaluations, arithmetic on
  time deltas. Needed by `thirteen` (reaction timer) and `eighteen` (dual-sonar speed
  calc). Meaningfully harder than Phase 0 — this is a stepping simulation, not
  instantaneous re-evaluation.
- **Phase 2 — continuous value mapping.** `map()` and continuous (not discrete-zone)
  output, e.g. sonar distance → tone pitch. Needed by `seventeen`. Also the natural home
  for any future `analogWrite`/PWM-dimming project.
- **Phase 3 — new actuator: Servo.** New visual component (rotating dial/arm) plus
  interpreter support for `Servo.attach()`/`.write(angle)` as distinct from
  `digitalWrite`. Needed only by `nineteen`, which currently has no working sim at all.
- **Out of category — serial *input* events.** Needed only by `fourteen`. See the
  carve-out discussion above; recommend resolving this as a scope decision before
  counting it into any estimate.

### What becomes obsolete

- `templates/admin/sim_builder.html` (Sim Builder GUI) — nothing left to author by hand
  once `sim_config` is just a components/pins declaration (visual mapping only) and all
  logic comes from interpreting the live sketch.
- The `behaviors` key in `sim_config` entirely, once every shipped project is retrofitted.
- Until full retrofit lands, `code_driven` and `behaviors` project configs still need to
  coexist — this doc doesn't assume a big-bang cutover.

---

## Revised effort estimate

Materially larger than v1's "~3–4 dev-days total." v1 estimated per-project content
authoring; this is an engine build.

| Item | Estimate |
|---|---|
| Phase 0 core interpreter (parser + evaluator + live input wiring, in `utils/sim_engine.py`), single implementation | 3–5 days |
| LDR/light-sensor component | 0.5–1 day (direct `sonar` copy per v1's original note) |
| Serial console component (output-only) | 1–1.5 days |
| Timed-sequence / re-triggerable timeline extension | 1–2 days |
| Per-project wiring once Phase 0 + LDR + console exist (`three`, `four`, `nine`, `ten`, `six`, `seven`, `eight`, `five`, retrofit `eleven`/`fifteen`/`sixteen`(no-op)) | ~0.5 day × 10 ≈ 5 days |
| Phase 1 — virtual clock (`thirteen`, `eighteen` retrofit) | 2–3 days |
| Phase 2 — continuous mapping (`seventeen` retrofit, fixes the live bug too) | 1–2 days |
| Phase 3 — Servo actuator (`nineteen`, currently totally unwired) | 1–2 days |
| `fourteen` — only if the carve-out is rejected | 3+ days, high uncertainty |

**Rough total excluding `fourteen`: 3–4 dev-weeks**, not days — roughly an order of
magnitude past v1's estimate, because v1 was scoping content authoring against an
engine that (incorrectly) was assumed to already handle conditionals.

## Recommended order, if this proceeds

Step 1 below is itself too large to build as one unit, so it's cut into sub-pieces.
Building one sub-piece at a time; each is marked as it lands.

1. Build Phase 0 + LDR + console together in `utils/sim_engine.py` (they're used by
   almost every remaining project). This alone unblocks `three`, `four`, `nine`, `ten`,
   `six`, `seven`, `five`, and retrofits `eleven` and `sixteen` (no-op).
   - [x] **1a. Core interpreter (parser + evaluator).** `utils/sim_engine.py`: new
     `interpret(sketch, input_state) -> {pin_states, pin_modes}`, additive alongside the
     existing regex-replay `run()` (untouched, still used where it's wired up). Tokenizer
     + recursive-descent parser (tagged-tuple AST, same style as `circuit_engine.py`) +
     tree-walking evaluator. Covers: global `int`/`bool`/`String` vars, `pinMode`
     (including the `INPUT_PULLUP` case the old `_extract_pin_modes` regex missed),
     `digitalRead`/`analogRead` resolved against a passed-in `input_state` dict,
     `if`/`else if`/`else` with `==`, `!=`, `<`, `>`, `<=`, `>=`, `&&`, `||`, `!`, String
     equality, statement sequencing (assign-then-use), `digitalWrite`, `tone`/`noTone`
     as instantaneous on/off, `delay()` as an inert no-op. Runs `setup()` once then
     `loop()` once against a fixed input snapshot — no timeline, matching the target
     architecture's discrete request/response model, not animation replay.
     Tests: `tests/test_sim_engine.py` (13 cases) — runs the real `project_three`
     sketch plus a hand-resolved `project_eleven`-shaped sketch (nested if/else, two
     inputs) through both branches of each condition, including the
     `test_eleven_button_pressed_but_switch_off_stays_off` case that the old
     regex-replay engine gets wrong by construction. Also covers globals, statement
     sequencing (`ten`'s pattern), String equality (`nine`'s pattern), else-if chains,
     the INPUT-pin write guard, and that unsupported syntax (e.g. `for`) raises a clear
     `ValueError` rather than misbehaving silently. `python -m pytest tests/ -q` run
     clean except two pre-existing, unrelated failures (`test_admin.py` cohort KeyError,
     `test_kb_freshness.py` hash mismatch, `test_circuit_engine.py` import error) —
     none touch `sim_engine.py` and none were introduced by this change.
     **Not done yet, deliberately out of scope for this piece:** wiring `interpret()`
     into `/sim/run`/`/try/sim` (needs a new `input_state` field in the request
     contract), the `sim-engine.js` click/drag handlers that would send that state, the
     multi-step `//>>`-preset → "current resolved sketch" question for step-scaffolded
     projects like `eleven`, arithmetic operators, and Serial console / LDR / timed-
     sequence / virtual-clock support. Those are the next sub-pieces.
   - [x] **1b. Live input wiring — `/sim/run` + `sim-engine.js`.** `routes/builder.py`'s
     `/sim/run` now branches on `sim_config.mode`: `"interpreted"` calls
     `interpret(sketch, input_state)` (threading the new `input_state` field straight
     from the request body); anything else keeps going through the untouched regex-replay
     `run()`, so existing `code_driven` tabs are unaffected. `static/js/sim-engine.js`
     gets a third init function, `initInterpreted(container, simConfig)`, alongside the
     existing `init()` (hand-authored `behaviors`, client-only) and `initCodeDriven()`
     (timeline replay): it renders the same interactive button/switch/LED/buzzer
     components as `init()`, but every press/release/toggle POSTs the *current* sketch
     (via the same `window.getCurrentSketch()` hook `initCodeDriven` already uses) plus
     the current input pin values to `/sim/run` and paints the returned `pin_states` —
     no local rule table, so a sketch edit is reflected on the next click with no other
     wiring. Input pin values are derived from `pin_modes` the server reports back (from
     the sketch's own `pinMode()` calls) rather than hardcoded — an initial seed request
     with `input_state: {}` runs before any click is possible, so the interpreter's own
     idle defaults (`INPUT_PULLUP` idle = HIGH, plain `INPUT` idle = LOW) are learned
     before the first real payload is built, and both paths agree at rest. Both templates
     that dispatch on `sim_config.mode` (`templates/components/arduino_interface.html`,
     `templates/try_it_builder.html`) got the added `else if (cfg.mode === 'interpreted')`
     branch. `project_three`'s drawer got a real `"sim"` tab (`mode: "interpreted"`,
     button on pin 2, LED on pin 8) as an end-to-end proof this actually renders through
     the registry — it's the one project from the "Not yet built" audit table wired this
     piece; `four`/`nine`/`ten` are still unwired (separate "per-project wiring" line
     item in the estimate table, not bundled into this engine piece).
     Tests: `tests/test_sim_run_route.py` (6 cases, Flask test client) — asserts
     `mode: "interpreted"` dispatches to `interpret()` against `project_three`'s real
     sketch (button pressed/not-pressed), that a missing `input_state` key doesn't crash
     and falls back to idle defaults, that a sketch `interpret()` rejects still returns
     400 with an `error` key, that `sim_config` *without* `mode: "interpreted"` still
     produces the old timeline shape (`duration`/`components`, no `pin_states`) —
     regression guard that 1b didn't disturb `code_driven` tabs — and that the route
     still enforces `login_required`. `python -m pytest tests/ -q` run clean except the
     same three pre-existing failures noted under 1a, plus one new expected one:
     `test_kb_freshness.py`'s corpus-hash check now also fails because `project_three.py`'s
     drawer content changed (the new sim tab) and the KB index hasn't been rebuilt —
     per this repo's convention, `utils/kb_build.py` is rebuilt on a weekly/pre-release
     cadence, not after every drawer-content edit, so this is left as-is.
     **Not verified:** no live browser check — `/lessons/project_three` requires a
     logged-in session plus Supabase-backed `is_unlocked`/`get_completed_lessons` calls
     that aren't mocked in this pass, and (as noted under 1a) there's no JS test
     infrastructure in this repo to exercise `initInterpreted` itself. What *is* verified:
     `utils/project_registry.py` loads `project_three`'s new `sim` tab and it
     `json.dumps`-serialises cleanly (confirmed via the registry directly), the backend
     dispatch is unit-tested against the real sketch, and `node --check` confirms
     `sim-engine.js` has no syntax errors. Manually clicking the button in a real browser
     session is the next thing to do before calling this fully proven.
     **Not done yet, deliberately out of scope for this piece:** the multi-step `//>>`-
     preset → "current resolved sketch" question for `eleven` (still open, same as under
     1a — `initInterpreted` calls the same `getCurrentSketch()` hook `initCodeDriven`
     already relied on, so this piece doesn't make that question harder or easier, just
     defers it again), wiring `four`/`nine`/`ten` (needs their own `sim_config`
     `components` entries, no engine work), arithmetic operators, and Serial console /
     LDR / timed-sequence / virtual-clock support.
2. Add the timed-sequence extension → unblocks `eight`, retrofits `twelve`.
   - [x] **2a. Engine — timed-sequence recording in `interpret()`.**
     `utils/sim_engine.py`: `_Env` gained a per-call virtual clock (`self.t`,
     starts at 0 every `interpret()` call — not the persistent Phase 1 clock,
     see below) and a per-pin write history (`self.sequence`). `delay(ms)`,
     previously fully inert, now advances `env.t` (capped at a new
     `_MAX_LOOP_MS = 4000` soft ceiling so a pathological sketch can't produce
     an unbounded pass). `digitalWrite`/`tone`/`noTone` now go through a
     shared `_record_write(env, pin, state)` helper that both sets
     `env.outputs[pin]` (unchanged) and appends `(env.t, state)` to that
     pin's history. After `loop()` runs, `interpret()` collapses each pin's
     history (same timestamp → keep the last write) and — only if a pin ends
     up with more than one distinct timestamp, i.e. a branch actually paced
     itself with `delay()` rather than just writing once — includes it in a
     new `pin_sequences` dict plus a `sequence_duration` (the pass's total
     `env.t`). Purely additive: `pin_states`/`pin_modes` are unchanged, and
     both new keys are simply absent when nothing in the pass was
     delay-paced (e.g. `project_three`'s existing sim tab — no pin in it is
     ever written twice per pass, so its responses are byte-for-byte the
     same as before this change).
     Tests: `tests/test_sim_engine.py` (+11 cases) — direct mechanism tests
     (single write with no delay → no sequence; two writes at the same
     timestamp collapse to no sequence; a delay-paced write produces the
     right `{t, state}` pairs and duration; a `delay()` argument that's a
     global variable, not just a literal, still advances the clock
     correctly), plus two project-shaped sketches: a hand-resolved
     equivalent of `project_twelve`'s real Step-1 chunk (same pins — 12
     button, 8/6/4 LEDs — and 150ms delays as the real sketch) asserting the
     button-held case produces the expected staggered 0/150 → 150/300 →
     300/450 chase across all three LEDs with `sequence_duration == 450`,
     and the released case produces no sequence at all (steady off); and a
     sketch shaped like `project_eight`'s dark-branch blink+tone (if/else,
     one branch delay-paced, the other steady) using `digitalRead` in place
     of `analogRead`/`A0`. `tests/test_sim_run_route.py` (+1 case) confirms
     `pin_sequences`/`sequence_duration` round-trip through `/sim/run`
     untouched (int pin keys become string keys via Flask's `jsonify`, same
     as the existing `pin_states` assertions). `python -m pytest tests/ -q`
     run clean except the same three pre-existing failures noted under 1a/1b
     (`test_admin.py` cohort KeyError, `test_kb_freshness.py` hash mismatch,
     `test_circuit_engine.py` import error) — none touch `sim_engine.py` and
     none were introduced by this change; no drawer content changed in this
     piece, so `test_kb_freshness.py`'s failure is pre-existing, not newly
     caused here.
     **Discovered, not fixed here:** `utils/sim_engine.py::_CONSTANTS` has no
     `A0`–`A5` entries, so `project_eight`'s *real* sketch (`int crystalPin =
     A0;`) can't be `interpret()`-ed yet — that's why 2a's eight-shaped test
     uses `digitalRead` instead of the real `analogRead`/`A0` sketch. Fixing
     this is bundled with the separate "LDR/light-sensor component" line
     item in the estimate table, not this piece.
     **Not done yet, deliberately out of scope for this piece — this is
     2b:** nothing in `static/js/sim-engine.js` reads `pin_sequences` yet
     (`initInterpreted` still only applies `pin_states` instantaneously), so
     no sim tab actually loops a chase/blink client-side today even though
     the engine can now produce one. `project_twelve`'s sim tab is still on
     the old hand-authored `behaviors`/`_sequence`/`_interval` macro — not
     retrofitted to `mode: "interpreted"` yet. `project_eight` has no sim
     tab at all (also blocked on the LDR component + `A0` gap above,
     regardless of 2b).
   - [x] **2b. Frontend playback + `project_twelve` retrofit.**
     `static/js/sim-engine.js`'s `initInterpreted` now checks every result
     for a `pin_sequences` key: pins present there are looped client-side
     (`playSequences()`, a `setTimeout`-chain / self-rescheduling pattern —
     same shape as `initTimeline`'s `playOnce()` for `code_driven` tabs,
     re-implemented locally rather than shared code because `initTimeline`
     works off a pre-built multi-component timeline keyed by component,
     while this one is keyed by pin against a live per-request result);
     everything else still applies `pin_states` once, unchanged from 1b.
     Pending handles are tracked in closure-scoped `seqHandles`/
     `seqLoopHandle` and torn down by `clearSequencePlayback()` at the top
     of every `applyOutputs()` call (so a new click/toggle cancels and
     replaces any in-flight chase, not just future ones) and from
     `container._simCleanup`. `project_twelve`'s sim tab swapped from
     `behaviors`/`_sequence`/`_interval` to `sim_config: {mode:
     "interpreted", components: [...]}` — same four components (button pin
     12, three LEDs on 8/6/4), `behaviors` key dropped entirely — the same
     role `project_three` played for step 1b, this time proving the
     timed-sequence half of the engine end-to-end rather than just
     instantaneous pin_states.
     Verified directly (not through a new automated test — 2a's tests
     already cover `interpret()`'s sequence mechanism against a
     twelve-shaped hand-resolved sketch, and there's still no JS test
     infra per 1a/1b): resolved `project_twelve`'s real Step-1 sketch (all
     `//##`/`//??` directives stripped, matching what the block
     builder/editor would actually send) through `interpret()` directly —
     switch pressed (`{12: 0}`) returns exactly the expected staggered
     chase (`pin_sequences: {8: [{t:0,HIGH},{t:150,LOW}], 6:
     [{t:150,HIGH},{t:300,LOW}], 4: [{t:300,HIGH},{t:450,LOW}]}`,
     `sequence_duration: 450`), switch released (`{12: 1}`) returns steady
     `LOW` on all three with no `pin_sequences` key at all — confirming the
     JS's `if (sequences[c.pin]) return;` / `else apply steady state`
     branch in `applyOutputs()` is exercised by exactly the values this
     retrofit will actually receive. Also confirmed
     `utils/project_registry.py` loads `project_twelve`'s updated sim tab
     (now under its Step 2 drawer entry) and the whole project
     `json.dumps`-serialises cleanly, and `node --check
     static/js/sim-engine.js` passes. `python -m pytest tests/ -q` run
     clean except the same `test_admin.py` cohort KeyError (pre-existing,
     unrelated) and `test_kb_freshness.py` hash mismatch (expected —
     `project_twelve.py`'s drawer content changed and, per this repo's
     kb-build cadence convention, the KB index isn't rebuilt per
     drawer-content edit).
     **Not verified:** no live browser click-through of `project_twelve`'s
     sim tab — same login/Supabase gating noted as not verified under 1b,
     unchanged by this piece.
   - [x] **3. Decide the `fourteen` carve-out question.** Decision: carve `fourteen`
     out permanently as a documented exception to "everything code driven." Its
     bespoke `utils/code_breaker.py::serial_monitor()` implementation, rendered
     directly in `templates/lessons/project_fourteen_part_one.html`, already works
     for students today and doesn't go through the shared drawer `sim` tab system at
     all. Extending `utils/sim_engine.py`'s interpreter with String indexing, `for`
     loops, and a serial-*input* event model (submit-a-line → run-to-next-input-wait)
     — language features no other one of the 19 other projects needs — was estimated
     at 3+ days with high uncertainty, for zero net new student-facing functionality.
     Not pursued. If `fourteen`'s bespoke implementation is ever revisited (bug,
     redesign, or a second project independently needing the same language features),
     re-open this decision rather than defaulting back to "build it into the shared
     engine."
4. Phase 1 (virtual clock) → retrofits `thirteen`, `eighteen`.
   - [x] **4a. Engine — persistent state & millis()/micros().** `utils/sim_engine.py`:
     `interpret()` gained `state=None` and `now_ms=None` params. Previously every call
     re-ran global-var-init + `setup()` + `loop()` from scratch, which only worked
     because nothing needed to remember anything between clicks. Now: `state` (the
     `_state` dict a *previous* call returned) skips re-running globals/`setup()`
     entirely and restores `vars`/`pin_modes`/`epoch_ms` instead — matching real
     Arduino semantics (globals + setup() run once at power-on, loop() repeats
     forever) — so a `running` flag or a `startTime` captured from `millis()` survives
     into the next discrete request/response instead of resetting every time.
     `millis()`/`micros()` now resolve against `now_ms - epoch_ms` (`now_ms` defaults
     to real `time.time()*1000`, overridable for tests). Also added in this piece,
     all needed by `thirteen`/`eighteen`'s real sketches: arithmetic operators
     (`+ - * / %`, unary `-`, C-style int/int truncation-toward-zero for `/`), float
     literals (`\d+\.\d+`) and the `long`/`unsigned long`/`float` types, `pulseIn()`
     (reads the pulse "duration" directly from `input_state` keyed by the echo pin —
     same pattern as `digitalRead`/`analogRead`, consistent with the "derive from the
     sketch" mandate), `delayMicroseconds()` as an inert no-op (same treatment `delay()`
     got before Phase 0's timed-sequence work — negligible next to the ms-scale
     per-pass clock), and `Serial.begin()`/`Serial.print()`/`Serial.println()` —
     `begin` is a no-op, `print`/`println` append `str(arg)` to a new
     `console_lines` result key. This is *not* the dedicated scrolling Serial console
     component the spec describes for `five`/`six` — just enough surface for a
     sketch that only outputs text (like `thirteen`'s reaction time) to show
     something.
     Tests: `tests/test_sim_engine.py` (+15 cases) — arithmetic, unary minus, float
     division, `unsigned long`/`long` parsing, `pulseIn` reading from `input_state`,
     `delayMicroseconds`/`Serial.begin` as no-ops, `Serial.println` → `console_lines`,
     a regression guard that callers who never pass `state` keep the pre-Phase-1
     "rerun everything every time" behaviour, **and two end-to-end cases against real
     project sketches** (hand-resolved, directives stripped, matching what the block
     builder sends — same convention as `eleven`/`twelve` in earlier pieces):
     `project_thirteen`'s actual reaction-timer sketch across three chained
     `interpret()` calls (press → release → press again, 500ms apart via `now_ms`)
     correctly prints `"500"` — the exact cross-call `millis()` case no prior engine
     version could represent at all; and **`project_eighteen`'s actual, unmodified
     Step 10 sketch** (dual sonar, `sawA`/`sawB`/`timeA`/`timeB` persistent flags,
     `micros()`, the float speed calculation) across three chained calls, correctly
     detecting Sensor A, then Sensor B 500ms later with `sawA` carried over from the
     previous call, printing `"Speed m/s: "` / `"0.4"`, resetting both flags, and
     re-arming for a second run. `tests/test_sim_run_route.py` (+1 case) confirms the
     route round-trips a `state` blob end-to-end (a `counter` global only reaches 2
     across two POSTs if `state` actually persisted server-side, not just accepted).
     `python -m pytest tests/ -q` clean except the same three pre-existing failures
     noted under 1a/1b/2a/2b (`test_admin.py` cohort KeyError, `test_circuit_engine.py`
     import error, `test_kb_freshness.py` hash mismatch — now also legitimately stale
     because `project_thirteen.py`'s drawer content changed in 4b below, per this
     repo's kb-build cadence convention).
   - [x] **4b. Route + frontend wiring, `thirteen` retrofit.** `routes/builder.py`'s
     `/sim/run` now threads an optional `state` field from the request body straight
     into `interpret()`. `static/js/sim-engine.js`'s `initInterpreted` caches the
     server's returned `_state` in a closure variable and sends it back as `state` on
     every subsequent call — except when the sketch text itself has changed since the
     last call, which resets it to `null` (a fresh "power-on"), mirroring a real
     re-upload; without that reset, adding a *new* global after state was already
     captured would hit `interpret()`'s "Unknown identifier" error, since globals only
     initialise on a call with no prior state — same graceful-error fallback the
     interpreter already provides for any other unsupported edit, not a new failure
     mode. `console_lines`, when present, gets its last line appended to the existing
     status bar text — no new UI component. `project_thirteen`'s sim tab dropped its
     hand-authored `behaviors`/`timer`-toggle config for `mode: "interpreted"` +
     a single button component (pin 2) — the `timer` component/toggle had no real
     backing logic even before this (purely a client-side visual), so it's dropped
     rather than carried forward for a UX nothing was actually driving.
     Verified: `utils/project_registry.py` loads `project_thirteen`'s updated sim tab
     and the whole project `json.dumps`-serialises cleanly; `node --check
     static/js/sim-engine.js` passes; `tests/test_sim_run_route.py`'s new state
     round-trip case exercises the exact route path the browser now depends on.
     **Not verified:** no live browser click-through (same login/Supabase gating
     noted as not verified under 1b/2b, unchanged by this piece).
     **Deliberately not done in this piece — `eighteen`'s actual sim_config/frontend
     wiring:** 4a proves the *engine* correctly evaluates `eighteen`'s real sketch
     end-to-end (persistent dual-flag state, `micros()`, the speed calc), but wiring
     it up as a real sim tab is a materially different, larger job than `thirteen`'s:
     `thirteen` fits the existing discrete click-and-release button model perfectly
     (the sketch only ever reacts to a button's own press/release), but `eighteen`'s
     real behavior is a *continuously running* sensor loop — a real board polls both
     sonars every pass without waiting for a student to click anything, and the
     current frontend has no polling/animation-loop pattern at all, only
     click-triggered one-shot requests. Also needed: a real "sonar" input component
     (a slider or similar, per the spec's "New component: LDR/light-sensor slider"
     line item's `sonar`-is-the-precedent note) wired to send raw pulse durations,
     not the discrete button/switch/LED/buzzer components `initInterpreted` supports
     today. Building a continuous-polling interaction model and a new sonar input
     component is real scope beyond "Phase 1, virtual clock" — flagging as the next
     sub-piece rather than shipping an untested guess at either.
5. Phase 2 (continuous mapping) → retrofits `seventeen`, fixing the live bug as a
   side effect.
   - [x] **5a. Engine — `map()` + continuous `tone()` pitch capture.**
     `utils/sim_engine.py`: `map()` is now a supported builtin in `_eval_call`
     — Arduino's `long`-typed five-argument range remap
     (`(x-in_min)*(out_max-out_min)/(in_max-in_min)+out_min`), with every
     argument narrowed via `int()` first (Python's `int()` on a `float`
     already truncates toward zero, matching the implicit `float`→`long`
     narrowing a real Arduino sketch gets when passing e.g. `distance` —
     `map()`'s own parameter types, not a re-derivation) and the final
     division also truncating toward zero (same convention the `/` operator
     already used, not Python's floor-dividing `//`). `in_min == in_max`
     raises `ValueError` (division by zero) rather than crashing opaquely.
     This was the single missing piece blocking `interpret()` from running
     `seventeen`'s real sketch at all — it previously raised `'map()' is
     not supported by the sim interpreter yet` unconditionally.
     Separately, `tone(pin, frequency)` no longer collapses its frequency
     argument to a bare on/off write: `_record_write()` gained an optional
     `frequency` param, `_Env` gained a `frequencies` dict (`{pin: hz}`,
     last `tone()` call per pin), and `interpret()`'s result gains a new
     `pin_frequencies` key — populated only for pins that ended the pass
     actively toning (`pin_states[pin] == 'HIGH'`), so a `noTone()`'d or
     never-toned pin doesn't leak a stale frequency. `pin_states`/
     `pin_sequences` are unchanged (a toning pin is still `'HIGH'` for
     on/off-driven UI like an LED) — purely additive, same pattern 2a's
     `pin_sequences` and 4a's `console_lines` followed.
     Tests: `tests/test_sim_engine.py` (+10 cases) — `map()` mechanics
     (basic remap, float-argument truncation, both range endpoints,
     zero-span `ValueError`), `tone()`/`noTone()` frequency capture
     (populated, cleared by `noTone()`, absent when no frequency arg is
     given), and **three end-to-end cases against `project_seventeen`'s
     real, unmodified Mission Complete sketch** (hand-fed a `pulseIn`
     duration computed as the sketch's own `distance = duration * 0.034 /
     2` formula inverted) proving a near-hand distance maps to pitch 200,
     a far-hand distance maps to pitch 1000, and five distances spanning
     the sensor's range produce five *distinct, monotonically increasing*
     pitches — the concrete regression guard against the audit's "Bug
     found during this audit" (the old `behaviors` config could only ever
     emit one of 3 fixed zone states, never a continuum).
     `tests/test_sim_run_route.py` (+1 case) confirms `pin_frequencies`
     round-trips through `/sim/run` untouched (string pin keys via
     `jsonify`, same convention as the existing `pin_states` assertions).
     `python -m pytest tests/ -q --ignore=tests/test_circuit_engine.py` run
     clean except the same two pre-existing failures noted under 1a/1b/2a/
     2b/4a/4b (`test_admin.py` cohort KeyError, `test_kb_freshness.py` hash
     mismatch — now also legitimately stale because `project_seventeen.py`'s
     drawer content changed in 5b below, per this repo's kb-build cadence
     convention); `test_circuit_engine.py`'s pre-existing collection error
     (unrelated `COL_OFFSETS` import) is excluded the same way prior pieces
     noted it, not newly introduced here.
   - [x] **5b. Frontend — sonar input + buzzer pitch readout, `seventeen`
     retrofit.** `static/js/sim-engine.js`'s `initInterpreted` gains sonar
     as a real input component (previously only `init()`'s hand-authored
     path supported it) and a continuous pitch readout on `buzzer`
     components:
     - `buildCol()`'s `buzzer` case gains a small Hz readout div
       (`<id>-hz`), blank unless `applyBuzzerFreq()` (new, alongside
       `applyBuzzer()`) sets it — harmless no-op for every buzzer in every
       other mode/project, since nothing writes to it unless a result
       carries `pin_frequencies`.
     - `applyOutputs()` reads the new `pin_frequencies` result key and
       calls `applyBuzzerFreq()` per buzzer pin, same lookup pattern
       already used for `pin_states`/`pin_sequences`.
     - A new `sonarDurationUs(distanceCm)` helper converts the slider's
       user-facing cm value into a raw pulse *duration* in microseconds
       (`distanceCm * 2 / 0.034`) — the same physical signal a real
       HC-SR04 puts on its echo pin, which the sketch's own `pulseIn()`/
       math turns back into cm; this is sensor physics, not a copy of any
       one sketch's logic, matching how `pinValueFor()` already supplies a
       raw HIGH/LOW level rather than a pre-interpreted "pressed" state.
       `buildInputPayload()` sends this on the component's `pin_echo`.
     - The slider's `input` event updates the visible readout and fires
       `sonarPingFlash()` immediately (local, free), but the actual
       `/sim/run` POST is debounced 150ms after the last drag movement —
       the "Slider-style inputs... debounce" requirement the Target
       architecture section called out in advance, now actually built
       (this is the first slider-driven `initInterpreted` component; LDR
       will follow the same pattern).
     - The zone badge under a sonar component (`buildCol`'s `-zone`
       element, "🟢 SAFE" etc.) is a leftover of `init()`'s 3-zone
       `behaviors` model; `initInterpreted` now hides it on init rather
       than leaving a label nothing here ever updates — there are no zones
       in continuous mode, on either the input or output side.
     `utils/project_seventeen.py`'s sim tab dropped its hand-authored
     `behaviors` (the 3-zone config the audit flagged as wrong — copy-
     pasted from `fifteen` onto a sketch that has no zones at all) and its
     `labels` override (now unused, nothing reads sonar zone labels in
     `interpreted` mode) for `sim_config: {mode: "interpreted", components:
     [...]}` — same `sonar1`/`musmaker` component ids and pins as before,
     so nothing about the circuit/UI layout changed, only how the pitch is
     computed (from the live sketch, not a hand-typed belief about it).
     Verified: `node --check static/js/sim-engine.js` passes;
     `utils/project_registry.py` loads `project_seventeen`'s updated sim
     tab and the whole project (and every other project) `json.dumps`-
     serialises cleanly.
     **Not verified:** no live browser click-through/drag-through — same
     login/Supabase gating noted as not verified under every prior piece's
     frontend half (1b/2b/4b), unchanged here. No audio actually plays;
     `pin_frequencies` only drives a numeric Hz readout, not a real Web
     Audio tone — flagged as a nice-to-have, not attempted in this piece
     (scope: "continuous value mapping," not "sound").
6. Phase 3 (Servo) → wires up `nineteen` for the first time.
   - [x] **6. Engine + frontend + `nineteen` wiring, in one piece (unlike 1/2/4/5,
     this phase had no engine-only sub-step worth splitting out — Servo needed
     both halves before any sketch using it could be proven end-to-end, and
     `nineteen` is the only project that needs it).**
     `utils/sim_engine.py`: `#include <...>` (and any other `#`-prefixed
     preprocessor line) is now stripped alongside `//` comments in
     `_strip_comments` — previously an unhandled `#` crashed the tokenizer
     with "Unexpected character '#'" before Servo support could even be
     reached. `Servo` joins `_TYPE_KEYWORDS`, so `Servo gateServo;` parses as
     an ordinary global vardecl with no changes needed to the parser itself.
     A `Servo`-typed vardecl doesn't go into `env.vars` (it's not a plain
     value) — it registers the object in a new `env.servo_pins` dict
     (`{var_name: pin_or_None}`), restored from Phase 1 `state` exactly like
     `pin_modes`, since `.attach()` normally only runs once in `setup()` and
     the binding must survive into later discrete `interpret()` calls the
     same way an already-configured `pinMode()` does. `_eval_call` gained
     generic dotted-call dispatch: any `<var>.attach(pin)` / `<var>.write(angle)`
     where `<var>` is a known servo name binds the pin or records the write —
     `.write()` before `.attach()` raises a clear `ValueError` rather than
     silently no-op'ing. Servo writes go through a new `_record_servo_write`,
     the same per-pin write-history mechanism `_record_write` already used
     for `digitalWrite`/`tone` (2a), but on a separate angle-valued channel
     since a servo's state isn't binary HIGH/LOW: `interpret()`'s result
     gains `servo_angles` (`{pin: angle}`, last write this pass) and
     `servo_sequences` (`{pin: [{t, angle}, ...]}`, present only when a pin
     was written more than once at distinct simulated timestamps — same
     collapsing rule and `sequence_duration` field `pin_sequences` already
     uses, so `nineteen`'s open-hold-close gate, which paces itself with a
     `delay(2000)` between two `.write()` calls, produces a timed sequence
     "for free" from infrastructure 2a already built). `pin_states`/
     `pin_sequences`/`_state` are unchanged in shape; `servo_pins` is simply
     a new key inside `_state`, same pattern `4a` used for `pin_modes`.
     `static/js/sim-engine.js`: new `servo` component — a housing + rotating
     arm SVG (`servoSVG`), painted by a new `applyServo(id, angle)` that sets
     the arm's `rotate()` transform (offset -90° so `write(90)`, the SG90's
     natural rest angle nearly every servo sketch starts at, points the arm
     straight up rather than sideways) and updates a degree readout — same
     shape as `buzzer`'s Hz readout from 5b. `buildCol` gained a `servo`
     case; it's output-only, so no `buildInputPayload()`/`pinValueFor()`
     changes were needed (mirrors `led`/`buzzer`, not `button`/`switch`/
     `sonar`). `applyOutputs()` now also reads `servo_angles`/
     `servo_sequences` — a pin present in `servo_angles` but absent because
     no `.write()` happened this pass (e.g. `nineteen`'s un-pressed idle
     loop, which has no `else`) is left alone rather than reset to some
     default, matching how a missing `pin_states` entry already implicitly
     means "stays at its last-painted state." `playSequences()` (the
     `setTimeout`-chain chase player from 2b) now takes a second
     `servoSequences` argument and loops angle timelines on the identical
     schedule as pin timelines — both channels read from the same single
     `/sim/run` response, so a press that lights the LED *and* sweeps the
     gate animates both in lockstep. `project_nineteen.py`'s Mission
     Complete sim tab, previously a literal empty `sim_config: {}` (audit
     table: "tab exists, unwired" — the only project in the whole 20-project
     set with no working sim at all), is now `mode: "interpreted"` with
     three components: `servo1` (pin 9), `button1` (pin 4), `led1` (pin 7) —
     matching the real circuit's wiring 1:1.
     Tests: `tests/test_sim_engine.py` (+13 cases) — mechanism tests
     (`#include` stripped without crashing the tokenizer, single write → no
     sequence, delay-paced double write → correct `{t, angle}` pairs +
     `sequence_duration`, write-before-attach raises `ValueError`, a
     declared-but-never-written servo produces neither `servo_angles` nor
     `servo_sequences`, the servo/pin binding survives a `state`-restored
     call the same way `pin_modes` does, `_state` stays JSON-safe), plus
     **four end-to-end cases against `project_nineteen`'s real, unmodified
     gate sketch** (hand-resolved — directives stripped, same convention as
     eleven/twelve/thirteen/eighteen, since raw multi-step presets have
     `//##`-commented code that only becomes real code after the block
     builder resolves it — see BLOCK_BUILDER_SYNC.md): idle (button
     released, pullup default HIGH) reports the gate steady-closed at
     `servo_angles: {9: 0}` with no sequence; a press produces exactly
     `servo_sequences: {9: [{t:0,angle:90},{t:2000,angle:0}]}` in lockstep
     with `pin_sequences: {7: [{t:0,state:HIGH},{t:2000,state:LOW}]}` for
     the status LED, both at `sequence_duration: 2000`; a release call
     chained via `state` after a press does nothing that pass (no `else`
     branch exists) rather than resetting the gate to some default; and the
     real sketch's `.attach()` call is confirmed learned into
     `_state['servo_pins']`. `tests/test_sim_run_route.py` (+2 cases)
     confirm `servo_sequences`/`servo_angles`/`sequence_duration` round-trip
     through `/sim/run` untouched (string pin keys via `jsonify`, same
     convention as every prior piece's route test), and that a write-before-
     attach sketch still returns 400 with an `error` key through the route,
     not just the bare interpreter. `python -m pytest tests/ -q
     --ignore=tests/test_circuit_engine.py` run clean except the same two
     pre-existing failures every prior piece has noted (`test_admin.py`
     cohort KeyError, unrelated; `test_kb_freshness.py` hash mismatch —
     legitimately stale again because `project_nineteen.py`'s drawer content
     changed, per this repo's kb-build cadence convention, not rebuilt here).
     `node --check static/js/sim-engine.js` passes; `utils/project_registry.py`
     loads `project_nineteen`'s updated sim tab and every project in the
     registry (all 21) `json.dumps`-serialises cleanly.
     **Not verified:** no live browser click-through — same login/Supabase
     gating noted as not verified under every prior piece's frontend half
     (1b/2b/4b/5b), unchanged here. The servo arm's rotation direction/
     starting pose was chosen to look right for a `write(90)`-centered
     sketch (this repo's only Servo project) but hasn't been eyeballed in an
     actual browser.

Steps 4–6 retrofit already-shipped, already-working-enough-for-a-kid content; they're
lower urgency than 1–2, which unblock brand-new lessons.
