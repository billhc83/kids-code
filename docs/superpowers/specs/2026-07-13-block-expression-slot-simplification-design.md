# Block Builder Expression-Slot Simplification — Design Spec

Status: proposal — no code changes yet. Captures the interaction-model design converged on in
conversation on 2026-07-13, evidenced against every sketch in the current 19-lesson corpus
(`utils/project_*.py` + `utils/project_try_it.py`).

## Origin

This grew out of auditing `static/js/bb-blocks.js`'s `BB.BLOCKS` vocabulary while scoping a
shared block-vocabulary schema (relevant to
[`2026-07-13-teacher-authoring-design.md`](2026-07-13-teacher-authoring-design.md)'s reference to
a future parameter-editing feature). The finding here stands on its own, independent of the
teacher-authoring work — it's a simplification of the block builder's core interaction model for
every student, not just teacher-authored content. It happens to also make a future shared schema
much smaller and cleaner to describe, since the thing being described gets structurally simpler.

## The problem, evidenced

`BB.BLOCKS`'s `t: 'expr'` input type is a fully recursive expression-tree slot: clicking it opens
the global block palette, the student places any of the ~11 expr-capable block types
(`math`, `analogread`, `digitalread`, `pulsein`, `millis`, `micros`, `random`, `map`, `constrain`,
`servoread`, `value`) into it, and that placed block can itself contain further open `expr`
slots — recursion to arbitrary depth, per `bb-render.js`'s `renderExprSlot`/`renderExprBlock` and
`block_parser.py`'s `exChildren`/`children` tree handling. This is the richest interaction pattern
in the block builder, and it exists at ~15 input points across the schema. Auditing every real
sketch in production shows actual usage is far narrower than the mechanism allows for:

| Slot | Real usage across all 19 lessons |
|---|---|
| `delay` ms, `delaymicroseconds` us | 100% bare numeric literal. Zero variables, zero composition, no exceptions. |
| `tone` Freq | Mostly literal; one case (`project_seventeen`) uses a bare variable (`pitch`) — never a nested call. |
| `notone` Pin, `analogwrite` Value, `servowrite` Angle, `serialprint` Value | Bare literal or bare variable only. Zero nested composition. (`analogwrite` has zero real usages at all — no evidence either way, but no reason to diverge from the pattern.) |
| `if`/`while`/`for` condition operands (`leftExpr`/`rightExpr`/`leftExpr2`/`rightExpr2`) | 100% bare literal or bare variable on both sides, every condition, every lesson. Every sensor-driven condition (`if (brightness < 300)`) is preceded by a separate assignment (`int brightness = analogRead(...)`) — the condition itself never embeds the read. |
| `map`/`constrain` Val | `map`'s one real usage (`map(distance, 5, 50, 200, 1000)`, `project_seventeen`) is a bare variable. `constrain` has zero real usage but is structurally identical. |
| `pulsein` Pin/Value, `random` Min/Max | Already flat (`vartext`/`sel`, `number`) — no `expr` slot exists on these today. |
| `math` A/B | The one genuine exception: real 2-level nesting exists — `distance = duration * 0.034 / 2` (ultrasonic formula, `project_fifteen`/`seventeen`/`eighteen`) and `time = millis() - startTime` (elapsed-timer pattern, `project_thirteen`). Both are decomposable (see below), but they're the only real evidence for recursion anywhere in the corpus. |

Net: of ~15 places the schema offers full recursive expression-building, exactly one pattern in
one block (`math`, chained arithmetic) is the only real justification for recursion at all.
Everything else is flat literal-or-variable in 100% of real usage, but pays the same interaction
cost — click a slot, get "click an expression to fill the slot," hunt an 11-item palette, place a
block, then fill that block's own fields — that a single inline text field would cost zero times.

## Converged design: four rules

**1. Composition happens only at assignment, never at use.** Any function-style "leaf" value
(`analogRead`, `digitalRead`, `pulseIn`, `millis`, `micros`, `servoread`, `map`, `constrain`,
`random`, `Serial.readString`/`available`) is placed exactly once, as the Value of an
`intvar`/`longvar`/`setvar`/`stringvar` block — never nested inside another call, never passed
directly to `delay`/`tone`/`analogWrite`/etc. Everywhere else in the vocabulary, a value is
referenced by the name it was already given. This is not a new convention — it's already how
every sensor read in the corpus works (`int brightness = analogRead(...)` then
`if (brightness < 300)`); this rule just makes it the *only* path, closing the unused alternative.
**Why**: removes the recursive block-picker interaction from every consumer slot without losing
any real capability — nothing in the corpus ever uses the alternative.

**2. Conditions are always flat.** `leftExpr`/`rightExpr`/`leftExpr2`/`rightExpr2` on
`if`/`while`/`for` become plain `vartext` fields (literal or variable name), same widget already
used for `pinmode`'s Pin field. Falls directly out of rule 1 — whatever's being compared was
already named by an assignment before the comparison.

**3. Chained arithmetic is one variadic block, not nested blocks.** `math` changes from a fixed
3-input block (`A, op, B`) to a variadic one: `terms: [flat, flat, ...]`, `ops: [sel, sel, ...]`
(length `ops` = length `terms` − 1), with a "+ term" button to append another operator/operand
pair. **Why not rule-1's temp-variable convention for this case**: naming is a real cognitive cost
for kids, and an ad hoc `temp`/`now` variable that exists purely for the tool's benefit adds noise
unrelated to the lesson. A variadic chain keeps `duration * 0.034 / 2` as one block that reads
like the formula, at zero added naming burden. **Correctness requirement**: codegen must
parenthesize by build order, not rely on raw C++ operator precedence — reduce left-to-right,
wrapping each step: `((A op1 B) op2 C) op3 D`. This matters concretely: the corpus's other
2-level case, `(timeB - timeA) / 1000000.0`, mixes precedence (`/` binds tighter than `-` in real
C++); a naive flat concatenation of chain terms would silently compute a different number than
what the kid built. Left-to-right-with-parens reproduces the correct result regardless of which
operators get chained, matching "do them in the order I placed them."

`millis()`/`micros()` as a math operand (rule 3's edge case) is **not** folded into the chain —
those go through rule 1's assignment convention instead (`long now = millis(); time = now -
startTime;`), because a 0-arg function call isn't a flat term and doesn't belong in a chain meant
for literals/variables.

**4. Physical pin fields lock to `sel`, not free-typed `vartext`.** `pinmode`, `digitalwrite`,
`tone`, `servoattach`'s Pin fields (and `notone`'s, once flattened per rule 1's table) change from
`vartext` to `sel`, sourced from the same `BB.getOptions('DIGITAL_PIN_OPTIONS')` merge already
used to populate `vartext`'s suggestion dropdown today (`bb-blocks.js:287-301`) — no new plumbing,
`sel` rendering already calls `getOptions()` whenever `inp.o` is a string key (`bb-render.js:68`,
`:692`). **Evidence**: every real pin value across all 19 lessons is either a bare literal from
the standard UNO pin set (`pinMode(2, ...)`) or a declared variable that was itself assigned one
of those literals at global scope (`pinMode(buttonPin, ...)`) — never anything outside that
dynamically-merged set. **Why this is a fourth, separate rule and not part of 1-3**: it's the
mirror image of them — rules 1-3 found `expr` slots that were too flexible (recursion offered,
never used); this finds a `vartext` slot that's too flexible in the other direction (free-typing
offered, never used beyond the suggested set). It's additive and independently shippable — nothing
else in this spec depends on it. **What stays `vartext`**: any field referencing an arbitrary,
lesson-specific identifier a kid named themselves — `setvar`'s Var, `servoattach`/`servowrite`/
`servoread`'s Servo name, `increment`'s Var. Those can't be pre-enumerated the way a fixed physical
pin set can, so their free-typing is real, not accidental.

## Per-block schema changes

| Block | Field | Current type | New type |
|---|---|---|---|
| `delay` | ms | `expr` | `vartext` |
| `delaymicroseconds` | us | `expr` | `vartext` |
| `tone` | Freq | `expr` | `vartext` |
| `notone` | Pin | `expr` | `sel` (two steps: flattens per rule 1 like every other consumer slot, then locks per rule 4 like every other Pin field — `notone`'s Pin was the one schema outlier on both counts) |
| `analogwrite` | Value | `expr` | `vartext` |
| `servowrite` | Angle | `expr` | `vartext` |
| `serialprint` | Value | `expr` | `vartext` |
| `map` | Val | `expr` | `vartext` |
| `constrain` | Val | `expr` | `vartext` |
| `intvar`/`longvar`/`setvar`/`stringvar` | Value | `expr` | stays `expr`, but bounded to depth 1 (see below) |
| `math` | A, op, B | fixed 3-input | variadic `{terms, ops}`, both flat |
| `ifblock`/`elseifclause`/`whileloop`/`forloop` | condition operands | `expr` (leftExpr/rightExpr/leftExpr2/rightExpr2) | flat `vartext`-style fields |
| `pulsein`, `random` | Pin/Value, Min/Max | already flat | unchanged |
| `pinmode`, `digitalwrite`, `tone`, `servoattach` | Pin | `vartext` | `sel` (rule 4) |

After this, the only block whose Value slot can still hold something other than a literal or
variable is the producer family (`intvar`/`longvar`/`setvar`/`stringvar`) — and even there,
nesting is capped at depth 1: the Value is a literal/variable, OR exactly one leaf call (now with
guaranteed-flat arguments per the table above), OR the new variadic math chain (also flat). No
block anywhere nests two levels deep anymore.

## Math block redesign

- Data shape: `{ terms: [t0, t1, ...], ops: [op0, op1, ...] }`, `ops.length === terms.length - 1`.
  New math blocks seed with 2 terms / 1 op (today's default shape).
- UI: "+ term" button appends `{term: '', op: '+'}`; reuses the exact existing pattern already in
  the codebase for "+ else if" (`bb-render.js:745-747`, `mkact('+ else if', function () {
  block.elseifs.push(...); render(); })`) — not a new interaction, a second use of one that
  already exists.
- Codegen: `terms.reduce((acc, term, i) => i === 0 ? term : '(' + acc + ' ' + ops[i-1] + ' ' +
  term + ')')`.

## Condition redesign

- `renderCondExprSlot`'s palette-hunt interaction (`bb-render.js:1010-1032`) is removed for all
  four operand positions, replaced by the same inline `vartext` input used everywhere else
  (including the focus-dump fix from the companion finding — the dropdown should not appear until
  the student types, not on bare click/focus).
- `bb-validation.js`'s `compareExpr`/`compareCondition` (lines 92-97, 213) can drop recursive
  structural comparison for condition operands entirely — becomes a flat string compare, same as
  any other `vartext` field's guided-mode check.
- `arduino.lark`/`block_parser.py`'s `condition()` transformer needs **no grammar change**. The
  grammar keeps parsing whatever text is actually there — this matters for backward compatibility
  (see Migration below) and means the flatness constraint is enforced by what the interactive UI
  *offers to build*, not by rejecting deeper text at parse time. Safer than a hard parser-side
  restriction that could break on existing content.

## What this doesn't change

- `arduino.lark` grammar stays as-is — still structurally parses arbitrary nesting.
- Locked (`//##`) line behavior stays as-is (see Migration — they're unaffected regardless).
- `pulsein`/`random` inputs stay as-is (already flat).

## Migration / backward compatibility

Important asymmetry that shrinks the real migration surface: `block_parser.py`'s `locked()`
transformer (`utils/block_parser.py:61-69`) never structurally parses `//##` lines into typed
block dicts — it keeps them as opaque raw-text `codeblock` entries, full stop, regardless of what
they contain. Most of the 2-level-math occurrences found in the corpus are repeated `//##` copies
across cumulative steps (per the accumulation rule in `CLAUDE.md`) and are therefore **entirely
unaffected** by this change — they're opaque echoed text today and stay opaque echoed text.

The real migration surface is only the *first, unlocked* occurrence of each deep formula — the
one line that's actually structurally parsed (via the full grammar, to build a phantom's `master`
solution for guided-mode matching). Concretely, two formulas in the whole corpus need hand
conversion:
- `distance = duration * 0.034 / 2` (`project_fifteen`, `project_seventeen`, `project_eighteen`)
  → convert to the new variadic math chain (rule 3).
- `time = millis() - startTime` (`project_thirteen`) → convert to the assignment convention
  (rule 1): `long now = millis(); time = now - startTime;`.

No other lesson in the corpus touches 2-level math, so no other lesson's phantom content needs
conversion. This should be confirmed line-by-line for those two lessons specifically before
shipping the `math` schema change, not assumed from this grep pass alone.

## Producer Value slot — the category/block chooser

Once rules 1-3 land, the producer blocks' Value slot is the only place a student still chooses
"what kind of thing is this." Real usage splits cleanly by the producer's own declared type —
nothing in the corpus assigns a String-typed read to a numeric variable or vice versa — so the
chooser is scoped per producer type rather than one undifferentiated list:

| Producer | Categories offered |
|---|---|
| `intvar`/`longvar` | Sensor (`analogRead`, `digitalRead`, `pulseIn`), Timer (`millis`, `micros`), Calculate (Math chain, `map`, `constrain`), Random, Servo Position (`servoread`) |
| `stringvar` | Typed Input (`Serial.readString`) — the only non-literal option; doesn't need a category level |

It's a **two-level tree — Category, then Block within category** — not one flat dropdown,
specifically because the flat version only stays short in guided/full mode (where it's filtered to
near-nothing anyway, see below); in `open` mode, where the full breadth must be reachable, one flat
list of ~9 items is exactly the kind of "big list right out of the gate" problem the `vartext`
dropdown fix (see build order) was already solving elsewhere. Two short levels (5 categories, 1-3
blocks each) stay scannable where one long list wouldn't.

**The tree behaves differently by guidance mode, but it's the same tree — never two separate
implementations:**

- **`open` mode** (the only one of the four guidance modes — `guided`/`full`/`free`/`open` — with
  no phantom/master driving expectations): the Value field defaults to a plain `vartext` input,
  identical to every other flattened slot in this spec. A "+" escape-hatch button (`mkact`, same
  reused pattern as "+ term" and "+ else if") reveals the full Category → Block tree only when a
  student wants something beyond literal/variable. Keeps the 90% case at zero added chrome, same
  principle as every other rule in this spec.
- **`guided`/`full` mode**: the tree is presented directly, as the phantom's required action — no
  flat-default, no escape hatch, because this field *is* a phantom with a known master answer, and
  every other phantom type in the system already requires an active placement click regardless of
  how constrained the choice is (a phantom `pinmode` block isn't auto-placed just because the
  master is known). The categories/blocks offered are filtered via the same `expectedExTypes`
  mechanism `updatePalette` already uses today (`bb-render.js:162-174`) — often narrowing to
  exactly one valid category with one block inside. **Both levels stay visible and clickable even
  when filtered to a single option at each level** — deliberately not collapsed to one click,
  because clicking through "this is a Sensor reading" before landing on which sensor function
  builds category-level familiarity as its own small piece of the learning, not just
  tool-generated friction. This was a specific call to preserve, not an oversight: the value of a
  phantom isn't in the difficulty of the choice, it's in the repetition of actively choosing.

**Why not skip the tree in guided/full when the answer is already known**: because nothing else in
the system does that. Every phantom — locked-vs-placed, `pinmode`, `digitalwrite`, any block type
— already requires the student to click it into place even when the palette is filtered down to
one legal option. Auto-rendering the Value-kind chooser's answer would make it the one exception to
a convention the rest of the block builder enforces consistently, for no real gain — the filtered
tree costs the same one-or-two clicks a filtered-palette phantom placement already costs today.

## Suggested build order

1. **`vartext` focus-dump fix** (companion finding, not part of this spec's core change but
   should ship first): remove the unfiltered dropdown dump on bare click/focus in both
   `bb-render.js` render paths (~line 78-124, ~line 639-685); keep the existing prefix-filter
   behavior that already fires on the first keystroke. Small, standalone, immediate win.
2. **Flatten the 9 single-slot consumer/leaf fields** (`delay`, `delaymicroseconds`, `tone`,
   `notone`, `analogwrite`, `servowrite`, `serialprint`, `map`, `constrain`) — same mechanical
   change repeated 9 times. Testable by regenerating every existing lesson's code and diffing
   against current output — should be byte-identical for every real (100% literal/variable) usage
   in the corpus.
3. **Flatten conditions** (`leftExpr`/`rightExpr`/`leftExpr2`/`rightExpr2` → `vartext`) across
   `if`/`while`/`for`. Bigger blast radius (touches every lesson with a branch) but the same
   "generated code should be identical for every real usage" test strategy applies, since the
   corpus was already 100% flat.
4. **Variadic math redesign** — new data shape, new "+ term" button (reusing the "+ else if"
   pattern), new left-to-right-parenthesized codegen. Requires the two hand-conversions identified
   above before/alongside this step.
5. **Producer Value-slot chooser** — two-level Category → Block tree (see above), mode-aware
   (flat-default + "+" escape hatch in `open`; direct, `expectedExTypes`-filtered tree, both levels
   always clickable, in `guided`/`full`). Depends on rules 1-3 already landing, since the category
   taxonomy assumes consumer/condition slots are already flat — nothing left to disambiguate a leaf
   call's own arguments against.
6. **Pin fields → `sel`** (rule 4): `pinmode`, `digitalwrite`, `tone`, `servoattach`, `notone`.
   Independent of steps 2-5 — can ship anytime, including before them. Lowest-risk change in this
   spec: it only removes invalid inputs a kid could previously mistype, it doesn't change what a
   valid input looks like or how generated code reads, so there's no corpus content to migrate.

## Decisions made by default, flagged for pushback

- **Locked (`//##`) lines are left unconverted, permanently opaque text** — no attempt to
  retroactively restructure historical locked content into the new flat/variadic shape, since
  they were never structured to begin with and changing that isn't required for this simplification
  to work.
- **`constrain`'s flattening is speculative** — no real lesson exercises it; the change is made on
  structural-consistency grounds (identical shape to `map`, which does have a real usage) rather
  than corpus evidence.
