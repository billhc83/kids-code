# Block Builder — On-Screen Interaction Model

How a student actually builds a program in Blocks view: what they see, what
they click, what changes color, and what happens next. This is the general
interaction model used across every lesson's Blocks view — not just `/try`,
which only shows a narrow slice of it.

Everything is **click-to-select, then click-to-place. Nothing is
drag-and-drop.**

---

## The workspace has three panels

**Global**, **setup()**, and **loop()** — shown as three stacked,
collapsible panels. Only one is open at a time; the others collapse down to
just their header. Clicking a header opens that panel and shows its blocks.

---

## Two ways a spot becomes "armed" for placement

At any moment, exactly one spot in the workspace is "armed" — visibly
highlighted to show that whatever gets clicked next in the **bucket** (the
panel of ready-made blocks on the left) will land there.

### 1. Guided slots — blue box → purple

Some steps mark exact spots that need a specific block: a dashed **blue**
box with a "+" and a short hint (e.g. "Wait half a second"). Click it: the
box turns solid **purple** and pulses gently — that's the armed state.
Click a block in the bucket: it drops straight into that purple box,
replacing it. One click on the slot, one click in the bucket — two clicks
total, done.

### 2. Open placement — click a panel or a thin "+" line

On steps that aren't scripted this tightly, there's no blue box waiting.
Instead the student either clicks the panel itself (Global / setup() /
loop()) to arm "add to the end of this panel," or clicks one of the thin
"+" insertion lines that sit between every pair of existing blocks (and
before the first / after the last) to arm "insert exactly here." Click a
block in the bucket next, and it lands at that spot.

If nothing is armed and the student clicks a bucket block, nothing happens
— a message tells them to pick a spot first.

---

## Going inside if / for / while blocks

An if, for, or while block has its own body — its own mini workspace
nested inside it, with its own thin "+" insertion lines. Placing the
if/for/while block itself is one placement; putting anything *inside* it is
a separate, second placement — click inside its body first to arm that
spot, then click a block from the bucket.

---

## Filling in a value — a block inside a block

Some blocks have a blank built into them: `delay`'s wait time, or either
side of an if's comparison. That blank shows as its own small empty box
inside the block, separate from the block itself. Click that inner box: it
lights up in a different color than the purple slot-selected state (so it
visibly reads as "this is a value, not a block spot"). The bucket then
switches to show a special "Expressions" section — numbers, sensor
readings, math, and so on. Click one there, and it drops into that inner
box. If the value itself has its own blank inside it (like a math operation
with two numbers), the same click-the-inner-box, pick-from-Expressions
pattern repeats one level deeper.

So a block with a blank in it is always at least two clicks to fully build:
one to place the block, one more for each blank inside it.

---

## Removing a block

Every placed block has a small **×** button. Clicking it deletes that block
outright — it does **not** turn back into a blue "+" slot. If that spot was
a required guided slot, the step now shows an error ("missing block") and
there's no way to get the original hint back except resetting.

---

## Reset

Reset undoes an entire step at once, not one block at a time — it wipes
whatever's been built on the current step and rebuilds it exactly as it
started (guided slots included). There's a confirmation prompt, since it
throws away all progress on that step. There's no per-block undo.

---

## Reordering

Placed blocks have small up/down arrows to move them earlier or later
within their panel — separate from placing or removing.

---

## Not every step works the same way

How much of the above shows up depends on the step:

- **Wide open** — no guided slots at all, just click a panel or a "+" line
  and build freely.
- **Tightly scripted (guided)** — specific blue boxes waiting for specific
  blocks, checked against a correct answer when the student taps
  Complete Step.
- **Pre-built, confirm-as-you-go** — the whole structure is already there
  and the student re-places/confirms each piece.
- **Locked** — all blocks are pre-placed and read-only; the step just plays
  through automatically, nothing to click.
- **Not blocks at all** — the student types real code by hand in the editor
  instead, and what they typed is checked directly rather than matching
  blocks.

Which panel is open by default when a step first loads is also decided per
step — normally wherever that step's guided slots live, but a step can be
told explicitly which panel to open instead.

---

## What `/try` shows vs. what a full project shows

`/try` only ever uses one flat panel (loop()), a couple of guided slots,
and one value-fill (`delay`'s wait time). It never shows: open/free
placement, going inside an if/for/while body, building a condition,
removing a block, or resetting a step. A real lesson with an if/else step
or a loop step uses all of the pieces `/try` skips.
