# Block Builder ↔ Editor ↔ Sim Sync — Invariants

The block builder (`static/js/block_builder.js`, `static/js/bb-validation.js`),
the Monaco code editor, and `SimEngine` (`static/js/sim-engine.js`) are three
views over one program. They only agree with each other if these invariants
hold. All were violated at some point during the `/try` build (see
`utils/project_try_it.py`) and each caused a real, user-visible bug. Any
future lesson that mixes an `editor`-view step with blocks or with a
code-driven sim tab will hit the same class of bug unless these are
respected.

## 1. The real namespace is `window._BB`, not `window.BB`

`bb-blocks.js` creates `window._BB`. Code that reads `window.BB` (no
underscore) silently gets `undefined` and fails without error — this hid the
`/try` email gate for an entire task before being caught. Always use
`window._BB`.

## 2. `BB.genCode()` must run before `stepchange`/`bb_step_update` fire

`BB.buildWorkspace(stepIdx)` dispatches `stepchange`, which synchronously
triggers `setMode()`. If the step is entering **editor** view, `setMode()`
immediately reads `getGeneratedCode()` (backed by `#codeout`). If `#codeout`
still holds the *previous* step's code at that point, the editor opens showing
stale content.

Fix applied in `bb-validation.js`: `buildWorkspace()` calls `BB.genCode();`
right after `BB.SECTIONS` is (re)assigned, **before** dispatching
`stepchange`. The later `checkStepComplete(); render(); genCode();` grouping
still runs afterward — this is an added early call, not a replacement.

## 3. `window.setBlockData(data)` must re-render and regenerate code

`setBlockData()` is how editor→blocks sync applies parsed code onto
`BB.SECTIONS`. It must call `BB.render(); BB.genCode();` after assigning
`SECTIONS` (same idiom `resetBlocks()` already uses), or the block palette and
`#codeout` both go stale relative to the code that was just parsed in.

## 4. Editor text does not auto-sync to blocks — you must sync it

Typing in Monaco updates the editor buffer only. `BB.SECTIONS` (and therefore
`#codeout`, `BB.checkStepComplete()`, and the sim's default sketch source)
stay whatever they were last set to until something calls
`window.syncEditorToBlocks()` (in `try_it_builder.html`) — which POSTs the
current editor text to `/try/parse` and applies the result via
`setBlockData()`.

**Any action that validates or displays "the current program" while the
student may be in editor view must trigger this sync first**, not assume
blocks are current:
- Clicking Check Code from editor view syncs before validating
  (`window.bbNext` wrapper in `try_it_builder.html`).
- The sim tab's Run/Re-run button — see §6 below.

## 5. Slot-based step validation cannot check free-typed editor code

`BB.validateStep()` matches placed blocks against phantom **slot IDs**. A
full-text reparse of hand-typed editor code produces fresh blocks with no
slot ID to match, so a `guided` step can never pass when the student types
the answer directly into the editor. For any step where entry view is
`editor` and the student is expected to type free-form code (not just
watch), use `guidance: verify` (`//==` string-comparison against a declared
answer) instead of `guided`.

## 6. Any code-driven consumer must read the *live* source, not just `#codeout`

`SimEngine.initCodeDriven()` originally always read
`window.getGeneratedCode()` (i.e. `#codeout`, the blocks-generated code).
That's wrong whenever the student is currently in editor view — per §4,
`#codeout` is stale until an explicit sync happens, so typing
`digitalWrite(ledPin, HIGH)` vs `LOW`, or moving it between `setup()`/
`loop()`, had no visible effect on the sim.

Fix: `sim-engine.js` now prefers an optional global hook:

```js
var sketch = (window.getCurrentSketch ? window.getCurrentSketch() :
  (window.getGeneratedCode ? window.getGeneratedCode() : '')) || '';
```

`window.getCurrentSketch` is undefined for every existing lesson (all
blocks-only), so their behavior is unchanged. Any template that has an
editor-capable step and a code-driven sim tab should define it:

```js
window.getCurrentSketch = function () {
  if (currentMode === 'editor' && editor) return editor.getValue();
  return window.getGeneratedCode ? window.getGeneratedCode() : '';
};
```

## 7. Monaco viewport calls during `stepchange` must follow `setMode()`'s retry schedule

`setMode()` schedules `editor.layout()` at `[10, 50, 150, 300]`ms after a
mode switch, to catch the final container size once the blocks↔editor
flexbox CSS transition settles. Any other viewport-dependent Monaco call
made synchronously inside the same `stepchange` handler (e.g.
`revealLineInCenter()`, `setPosition()` scroll behavior) computes against a
still-reflowing layout and can leave the visible content scrolled off-screen
even though the cursor position itself is correct. Re-issue such calls on a
matching delay schedule (`[0, 10, 50, 150, 300]`ms), not just once.

## When adding a new lesson that mixes editor + blocks + sim

Check all seven items above. In practice: any step with `view: editor` that
either (a) needs Check Code to work from editor view, or (b) has a
`sim`-type drawer tab, needs the editor→blocks sync (§4) and the
`getCurrentSketch` hook (§6) wired up — copy the pattern from
`templates/try_it_builder.html` rather than re-deriving it.
