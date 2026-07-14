# Teacher Project-Authoring Tool — Design Spec

Status: proposal — locking down the design so schema/build work can start. Extends
[`2026-07-13-school-teacher-infra-design.md`](2026-07-13-school-teacher-infra-design.md)'s
"open design space" section, which this doc replaces with concrete decisions.

## Branch caveat (carries over from the parent doc, now more specific)

This design depends on invariants documented in `BLOCK_BUILDER_SYNC.md`, which exists on
`main`/`try-page-infra` but **not** on `dev1`. Confirmed directly: `static/js/sim-engine.js:670`
on `dev1` still reads `window.getGeneratedCode()` unconditionally — the `getCurrentSketch()`
mode-aware fallback the doc prescribes (invariant #6) is not applied here yet. If this authoring
tool embeds a live sim preview for teachers (reasonable, since it lets a teacher test-drive the
lesson exactly as a student would before publishing), that gap needs fixing first, or the preview
will show stale code whenever a teacher is in editor view. Recommend merging that fix (or
`main` generally) before starting build, not rediscovering the same bug a second time.

## The one finding that reshapes the whole design

The existing `/lesson-sketch` skill (`.claude/commands/lesson-sketch.md`) does two genuinely
different kinds of work, and they should **not** both become teacher-facing UI:

1. **Pedagogical judgment** — where should step boundaries fall, is this line the "new concept"
   or "boilerplate," what should the phantom hint say. This is real teaching skill; a teacher UI
   should absolutely put this in the teacher's hands.
2. **Mechanical bookkeeping** — re-deriving each step's cumulative `void setup(){}`/`void
   loop(){}` block from scratch, by hand, every single step (`.claude/commands/lesson-sketch.md:262-264`
   explicitly instructs the skill to "maintain a running list"). Per `utils/block_parser.py:758-762`,
   this is a hard runtime rule (globals append, setup/loop replace-if-present) with **zero
   validation anywhere in the pipeline** — get one line wrong or out of order and the workspace
   silently shows broken/missing code with no error, for student and teacher alike.

Category 2 is pure liability if exposed as manual teacher work — it's exactly the kind of
fiddly, invisible-until-it-breaks bookkeeping a non-engineer is least equipped to get right, and
literally nothing downstream catches the mistake. **Decision: the tool must never ask a teacher
to type `//##` lines or reconstruct cumulative setup/loop by hand.** It computes that
automatically from a single source of truth (below). Everything a teacher does through the UI is
category-1 work: sequencing, classification (this line is a phantom vs. given), and hint/content
writing.

## Authoring flow: "one true sketch, then progressive reveal"

Rejected the alternative (teacher builds up code step-by-step, typing only "what's new this
step" with no upfront whole-program view) because it defers correctness-checking to the end —
errors in an early step aren't discoverable until the teacher has typed several more steps on
top of them. Instead:

1. **Pick a circuit.** Teacher selects an existing, physically-verified circuit from the current
   catalog of built-in projects (its `circuit_definition`, wiring diagram, and component/pin
   list) as-is. **No new circuit-authoring tooling is being built** — this reuses what
   `utils/circuit_engine.py` / `utils/project_registry.py:16-29` already resolve for the 19
   built-in projects. This is what "the circuit is locked" cashes out to concretely: a teacher
   picks *which* existing circuit, not a new one.
2. **Write one complete, correct sketch** (globals + `setup()` + `loop()`) against that circuit,
   in a real code editor (Monaco, same as the student editor view). This is the single source of
   truth for the whole lesson — no directives yet, just working Arduino-ish code using the block
   vocabulary the platform already supports (`static/js/bb-blocks.js:60-263`, ~30 statement/call
   types — a teacher isn't inventing new Arduino API coverage, only recombining known blocks).
   Validated server-side via `parse_sketch()` (Lark grammar, `utils/arduino.lark`) before moving
   on — a sketch that doesn't parse cleanly never reaches the step-building screen. This also
   answers the "sketch sourcing" question left open in the parent doc: not a curated pick-list,
   not fully-open-against-arbitrary-wiring — one teacher-written sketch, hard-validated against
   the block grammar, free to use any wiring-legal combination of the locked circuit's pins.
3. **Cut it into steps**, not reorder it. Because the sketch is already correct top-to-bottom,
   the teacher's only job is choosing *where the boundaries go* — a linear sequence of cut
   points over the statement list the parser already breaks the sketch into, not free
   drag-and-drop reordering. This mirrors what `//>>` boundaries do today, minus the two things
   currently guessed by the LLM skill:
   - **If/else-if/else chains cannot be split incorrectly.** The tool detects branch structures
     server-side (same grammar that already recognizes them) and refuses a cut that would leave
     part of a chain in one step and part in another — enforced, not advisory, closing the gap
     where `.claude/commands/lesson-sketch.md:315-377`'s splitting rule is currently just
     LLM-followed instructions with no code behind it.
   - **Cumulative setup/loop is generated, not authored.** For step *N*, the backend emits
     "everything already taught through step *N-1*, as locked lines, plus this step's new
     lines" automatically. The teacher never sees or edits `//##` bookkeeping directly.
4. **Classify each new line in a step**: phantom (student places it — teacher writes a short
   hint) or given/locked (shown pre-placed). This directly replaces the fuzzy heuristic table in
   `.claude/commands/lesson-sketch.md:268-313` (first-N-pins-phantom, `delay()` phantom-if-
   "educationally-meaningful", etc.) with the person who actually knows what this lesson is
   teaching making the call directly, one toggle per line, instead of an LLM guessing intent
   from syntax. Hint-text writing (`.claude/commands/lesson-sketch.md:415-436`) stays manual —
   it's short-form pedagogical writing that has to know the lesson's narrative, which can't be
   derived from the code.
5. **Per-step view/guidance is constrained by the UI, not left to break silently.** `guided`
   mode is only offered for `view: blocks` steps; if a teacher wants a step to be typed in the
   editor, the tool only offers `verify` (declared expected text) or `open` (free exploration,
   no check) — `guided`+`editor` (the documented silent-break combo, `BLOCK_BUILDER_SYNC.md` §5)
   is not a selectable combination, full stop. A step with zero phantoms auto-classifies `free`;
   the trailing `Mission Complete` step is auto-appended, non-editable, matching the existing
   fixed convention (`.claude/commands/lesson-sketch.md:380-396`).
6. **Publish-time validation**: the tool materializes the actual `//>>`/`//??`/`//##`-annotated
   sketch string and round-trips it through the real `parse_steps()` server-side before allowing
   publish. If that doesn't reproduce the expected statement/phantom counts — e.g. it would fall
   into the silent line-scan fallback that currently swallows phantoms unnoticed on a malformed
   chunk (`utils/block_parser.py:464-498`) — publishing is blocked with a specific error, never
   silently degraded the way a hand-edited file could be today.

### Troubleshoot lessons are a separate, much simpler path

Per `.claude/commands/lesson-sketch.md:31-77`, a troubleshoot lesson is just: circuit + one
complete *broken* sketch, wrapped in two fixed `open` steps ("Find the Bug" / "Mission
Complete") with zero phantom/lock decisions. The tool should offer "lesson type: guided build
vs. debug challenge" as the first choice, and route debug-challenge straight to a raw-sketch
textarea + the two auto-generated wrapper steps — none of the step-cutting/classification UI
above applies.

## Content (drawer) authoring

Per-step tabs (`explain`/`howto`/`logic`, 4th `sim` tab on the final step, distinct 3-tab shape
for a troubleshoot lesson's first step) are **scaffolded, not blank and not auto-written**:
- `howto` starts pre-populated with a numbered stub line per phantom in that step, seeded from
  the hint text the teacher already wrote in step 4 above (e.g. "1. [hint] — explain what this
  block does and why it goes here") — the teacher expands it, doesn't start from nothing.
- `explain`/`logic` start as empty fields with placeholder guidance text describing what belongs
  there (what/why; a real-world analogy) — not fabricated example content, since inventing
  placeholder "content" risks a teacher accidentally shipping filler prose.
- **Step-count parity is enforced server-side at publish time** — sketch step count must equal
  drawer step count, exactly. Today this check exists only as an instruction to the LLM skill
  (`.claude/commands/lesson-drawer.md:206`) with nothing enforcing it in code; since the tool
  now controls both artifacts, this becomes a real validation, not an honor system.
- Freeform rich-text prose generation (an "AI assist" draft button) is explicitly **out of scope
  for v1** — flagging it as a plausible v2, not building it now, to avoid shipping
  unreviewed-content risk in the first version of a tool aimed at non-engineers.

## Data model (extends the parent doc's schema)

```
authored_projects
  id, organization_id (fk), created_by (teacher user_id), project_key (slug, unique),
  lesson_type ('guided' | 'debug'), circuit_source_key (references an existing built-in
  project's resolved circuit_definition — copied at creation, not re-resolved live, so a later
  change to the built-in project doesn't retroactively alter a teacher's published lesson),
  status ('draft' | 'published' | 'archived'), created_at, updated_at, published_at

  draft_data (jsonb)      -- working state: the one-true-sketch text, statement-level cut
                             points, phantom/locked classification + hints, drawer content
                             in progress. Freely mutable, never served to students.
  published_data (jsonb)  -- the fully materialized PROJECT-shape dict (meta/steps/drawer/
                             presets), frozen at publish time via the validation pipeline above.
  published_version (int) -- bumped each publish
```

**Why draft/published are separate, not one mutable row**: a project can be `project_assignments`-
referenced by students mid-course. If a teacher tweaks wording in `draft_data` and that
instantly changed what an already-working student saw mid-step, it could invalidate progress
they'd already made against the old step boundaries. Publishing is an explicit, atomic
draft→published copy (only after the round-trip validation in step 6 passes) — students always
see a stable `published_data` snapshot until the teacher deliberately republishes.

**Loading path**: `utils/project_registry.py`'s `PROJECTS` dict is populated once at import time
via `pkgutil.iter_modules` over the filesystem — there's no hook for DB-backed entries today.
Add a second, separate lookup: file-based `PROJECTS` stays exactly as-is (the curated/built-in
catalog), and anything resolving a `project_key` for an *assignment* (`routes/builder.py`'s
`/preset/<name>` and friends) checks `authored_projects.published_data` by key when the file-based
dict misses, rather than merging into the same global dict at import time — avoids needing any
process-restart-on-publish semantics, at the cost of every teacher-authored-project lookup being
one extra indexed query instead of a dict hit. That cost is negligible next to correctness.

## Decisions made by default, flagged for pushback

These aren't neutral implementation details — noting them explicitly since "lock down" shouldn't
mean "decided unilaterally without saying so":

- **Circuits are scoped to the existing built-in catalog only** — no new circuit-design surface
  for teachers in v1. If schools need genuinely custom wiring (not just a custom sketch on
  existing wiring), that's a materially bigger, separate piece of work not covered here.
- **Authored projects are org-scoped, not shared across orgs** (`organization_id` on the table,
  no cross-org visibility). No "marketplace" of teacher-shared lessons in v1 — revisit if that
  turns out to be a real ask.
- **No AI-assisted content drafting in v1** — scaffolded stubs only, teacher writes the prose.

## Implementation walkthrough — screens, routes, materialization

Branch note update (2026-07-13): `dev1` now has `main` merged in (`git merge-base --is-ancestor
main HEAD` confirms it). `static/js/sim-engine.js:594-595` now reads the `getCurrentSketch()`
fallback and `BLOCK_BUILDER_SYNC.md` is present in the tree — the live-preview blocker flagged
above is resolved, nothing to fix before Screen 5 (preview) below.

This section grounds the flow in the actual existing routes so the reuse seams are concrete, not
aspirational. Two existing patterns do almost all the heavy lifting:
- `routes/builder.py:40-62` (`/demo/builder`) shows the exact recipe for handing a `//>>`-
  annotated sketch to the real block-builder UI: `parse_steps(sketch)` → wrap in a `config` dict
  → `json.dumps(...).replace('</', '<\/')` → `render_template("block_builder_fragment.html",
  config=config_json)`. The teacher preview/publish screens reuse this verbatim, just sourcing
  the sketch from `authored_projects.draft_data` instead of a hardcoded string.
- `routes/builder.py:73-79` (`POST /parse`) shows the exact recipe for validating raw sketch
  text server-side (`parse_sketch(code, ...)`, Lark grammar). The sketch-editor screen's
  "Validate" action is this same call, teacher-scoped.

New blueprint `routes/teacher_authoring.py`, `teacher_authoring_bp`, `url_prefix="/teacher/projects"`,
every route decorated `@login_required @teacher_required` (same decorators `routes/teacher.py`
already uses) plus an ownership check (`authored_projects.created_by == session["user_id"]`,
or `organization_id` membership once org roles exist) on every `<id>`-scoped route.

| Route | Method | Purpose |
|---|---|---|
| `/teacher/projects` | GET | List this teacher's `authored_projects` (draft + published), entry point linked from `templates/teacher.html`. "+ New Project" → next row. |
| `/teacher/projects/new` | GET, POST | Screen 1: title, lesson type (`guided`\|`debug`), circuit picker. Circuit choices = `[k for k, p in PROJECTS.items() if p.get('circuit_definition')]`, the exact same set `routes/dev.py:24` already computes for the admin circuit sandbox. POST creates the `authored_projects` row (`status='draft'`), copies the chosen project's `circuit_definition` + circuit image path into `draft_data.circuit` (frozen at creation, per the parent doc's "copied, not re-resolved live" decision). |
| `/teacher/projects/<id>/sketch` | GET | Screen 2: Monaco editor + read-only circuit reference panel (pins/components from `draft_data.circuit`). |
| `/teacher/projects/<id>/sketch/validate` | POST | `{code}` → runs `parse_sketch(code)`. On failure: `{ok: false, errors: [{line, message}]}`. On success: `{ok: true, statements: {global: [...], setup: [...], loop: [...]}, branch_spans: [...]}` — the flat per-section statement list (already what the grammar/transformer produces per block) plus detected if/else-if/else chain ranges, computed once here so Screen 3 can grey out illegal cut points client-side without re-parsing. |
| `/teacher/projects/<id>/steps` | POST | Screen 3: persists cut points + per-statement phantom/given classification + hints + per-step guidance/view into `draft_data.steps`. Server re-validates no cut splits a `branch_spans` entry before accepting. |
| `/teacher/projects/<id>/preview` | GET, `?step=N` | Materializes the annotated sketch through the current step (algorithm below), runs it through `parse_steps()`, returns the same `config` shape `/demo/builder` builds — rendered via `block_builder_fragment.html`, i.e. **the teacher previews using the literal student-facing component**, not a mock. |
| `/teacher/projects/<id>/drawer` | POST | Screen 4: per-step `{explain, howto, logic}` (+`sim` on final step) content, saved into `draft_data.drawer`. Step list comes from `draft_data.steps` (Screen 3's output) — there's no separate step-count field to drift out of sync with, closing the gap where today's parity check (`lesson-drawer.md:206`) is advisory-only. |
| `/teacher/projects/<id>/publish` | POST | Screen 5b: runs the full validation pipeline, and on success copies `draft_data` → materialized `published_data`, bumps `published_version`, sets `status='published'`. Returns specific field-level errors on failure (never a partial publish). |

### Materialization algorithm (draft state → annotated sketch string)

This is the concrete mechanism behind "the tool generates cumulative setup/loop, the teacher
never types `//##` bookkeeping." For each step *i* in `draft_data.steps`, in order:

1. Emit the header: `//>> {label} | {guidance} | {view}`.
2. **Global section**: emit only *this step's newly-classified* global statements (as `//??
   {hint}` + line for phantom, `//## {line}` for given). Nothing else — per
   `utils/block_parser.py:758-762`'s own accumulation rule, the parser appends each chunk's
   global output onto a running total automatically, so re-listing earlier globals here would
   double them.
3. **Setup / loop sections**: if this step introduces *no* new setup or loop content, omit both
   wrappers entirely (carries forward the previous cumulative state, matching the "global-only
   chunk" convention). Otherwise, emit `void setup() { ... }` / `void loop() { ... }` containing:
   *every statement taught in this section by any step up to and including this one* — prior
   steps' statements as `//## {line}` (now "given," since the student already learned them),
   this step's newly-classified statements as phantom or given per the teacher's Screen 3
   choices. This full re-list, every time, is exactly the bookkeeping `.claude/commands/lesson-
   sketch.md:262-264` currently asks an LLM to do by hand — here it's a straight loop over
   `draft_data.steps[0..i]`, mechanically correct by construction, no judgment involved.
4. Append the fixed trailing `//>> Mission Complete | open | blocks` step with no code, always,
   non-editable in the UI.

The publish pipeline (and the `/preview` route, for live-as-you-build feedback) both run this
same materialization function, then round-trip the result through `parse_steps()` — so a teacher
sees the real, final rendering at every preview click, not a simulated approximation of it.

### Debug-challenge path (shorter)

Lesson type `debug` skips Screens 3–4's step-cutting/classification UI entirely. Screen 2's
sketch editor is relabeled "paste the broken sketch," and the materializer just wraps it
verbatim in the two fixed steps: `//>> Find the Bug | open | editor` (full broken sketch, no
directives) then `//>> Mission Complete | open | blocks`. Drawer (Screen 4) uses the distinct
3-tab shape (`Challenge`/`Try It`/graduated `Hints`) per `.claude/commands/lesson-drawer.md`'s
troubleshoot branch instead of `explain`/`howto`/`logic`.

## Suggested build order

1. Backend: statement-level sketch parsing/segmentation service (wraps existing
   `parse_sketch()`/`parse_steps()`), the cut-point + classification data model, and the
   publish-time validation/materialization pipeline — no UI yet, provable via tests against
   known-good sketches from the 19 existing projects (round-trip an existing lesson's sketch
   through segmentation and confirm the materialized output matches the hand-authored original).
2. `authored_projects` table + dual-lookup change in the project-resolution path (small, additive,
   doesn't touch existing file-based projects).
3. Teacher UI: sketch entry + circuit picker → step-cutting/classification screen → drawer
   scaffolding screen → publish. Reuses the existing block-builder JS/Monaco components for
   preview (per §3 of the research this depended on — the JS consumes the same parsed-config
   shape regardless of source, so no renderer rewrite needed).
4. Live preview-as-student (exercises the sim-engine gap flagged at the top — fix or merge that
   first).
