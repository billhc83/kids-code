# Circuit Engine & Circuit Renderer

Two systems that together turn a **logical circuit description** ("an LED on
D4, a button on D2") into an **interactive, rendered breadboard diagram** in
the browser — with no hand-placed coordinates and no manually drawn artwork.

```
                     ┌─────────────────────┐
 logical spec  ──────▶   circuit_engine.py  │──────▶  circuit_definition JSON
 (components +        │  (Python, offline/   │        (components w/ col+row,
  connections,        │   import-time)       │         resolved wires,
  no coordinates)      └─────────────────────┘         walkthrough steps)
                                                                │
                                                                ▼
                                                   ┌─────────────────────┐
                                                   │  circuit_renderer.js │
                                                   │  (browser, SVG)      │
                                                   └─────────────────────┘
                                                                │
                                                                ▼
                                                     rendered breadboard,
                                                     Arduino, wires (A*-routed)
```

- **`utils/circuit_engine.py`** — the *placer*. Takes an abstract list of
  components and logical pin-to-pin connections and decides exactly which
  breadboard hole (column + row) every leg lands in, injects passives
  (resistors), routes GND/5V through the power rails, and writes a
  step-by-step walkthrough. Pure Python, no rendering.
- **`static/js/circuit_renderer.js`** — the *artist*. Takes the JSON the
  engine produced and draws it as SVG: the breadboard grid, the Arduino,
  a hand-illustrated symbol for each component type, and wires that are
  pathfound (A*) around component bodies so they never overlap.
- **`utils/circuit_registry.py`** — the shared physical-constants table both
  the engine (placement math) and renderer (symbol geometry / obstacle boxes)
  read from implicitly (the engine reads it directly; the renderer's
  `SYMBOL_RENDERERS` table encodes the same pin layouts independently, see
  "Keeping registry and renderer in sync" below).

The **contract between the two systems is the `circuit_definition` JSON
object**. The engine's only job is to produce a valid one; the renderer's
only job is to draw a valid one. Anything that satisfies the schema below
can be fed to `CircuitRenderer` directly — you don't have to go through the
engine (see "Two ways to build a circuit" below).

---

## The `circuit_definition` JSON contract

```jsonc
{
  "meta": { "title": "...", "difficulty": "easy", "description": "...", ... },
  "components": [
    {
      "id": "LED1",
      "type": "LED",
      "pins": { "anode": {"col": "E", "row": 12}, "cathode": {"col": "E", "row": 11} },
      "properties": { "color": "red" }
    },
    {
      "id": "R_LED1",
      "type": "RESISTOR",
      "pins": { "pin1": {"col": "D", "row": 11}, "pin2": {"col": "D", "row": 7} },
      "properties": { "ohms": 220 }
    }
  ],
  "connections": [
    { "from": "arduino.D4",   "to": "breadboard.A12", "color": "#00AA00" },
    { "from": "breadboard.-1.11", "to": "breadboard.-1.30", "color": "#111111" },
    { "from": "arduino.GND",  "to": "breadboard.-1.30",     "color": "#111111" }
  ],
  "walkthrough": [
    { "type": "component", "id": "LED1", "instruction": "Put the red LED ...", "tip": "..." },
    { "type": "wire", "from": "...", "to": "...", "instruction": "Connect a green wire ...", "tip": "..." }
  ]
}
```

- `components[].pins` — **already resolved** to a breadboard hole
  (`col` = letter A–J, `row` = integer 1–30). This is the field the renderer
  actually draws from; nothing in the renderer does placement.
- `connections[].from` / `.to` — endpoint strings in one of these forms:
  - `"arduino.D4"`, `"arduino.GND"`, `"arduino.5V"`, `"arduino.A0"` — a physical Arduino pin.
  - `"breadboard.A12"` — a standard hole (col + row).
  - `"breadboard.-1.30"` / `"breadboard.+1.5"` — a power-rail hole (`-1`/`-2` = negative rails, `+1`/`+2` = positive rails).
  - `"breadboard2.…"` — same forms, second board, only meaningful when `meta.layout` (top-level `"layout": "dual_board"`) is set.
- `walkthrough[]` — optional, but required for the step-by-step tab. Each
  step is either `type: "component"` (highlights one component) or
  `type: "wire"` (highlights one connection); the renderer's
  `applyHighlight()` greys out everything else on the canvas.

This JSON is exactly what gets embedded as `circuit_def_json` in
[project_base.html](templates/lessons/project_base.html) and handed straight
to `new CircuitRenderer(def, containerId)`.

---

## `circuit_engine.py` — the placement pipeline

Entry point: `generate_circuit(meta, components, logical_connections, start_row=12)`.
Five steps, run in order:

### 1. `expand_components` — dependency injection
Walks the component list and, for any type with a `"requires"` entry in
`circuit_registry.REGISTRY` (currently `LED` and `LDR`, both needing a series
resistor), injects a synthetic component right after it: id `R_{parent_id}`,
type `RESISTOR`, tagged `_injected: True` with `_parent_id`/`_attach_from`/
`_attach_to` so step 2 can place it relative to its parent. **You never
list a resistor yourself** — the LLM prompt and any hand-written spec must
omit them.

### 2. `place_components` — the placement cursor
This is the core algorithm. Two independent "zones" exist — the **A-E half**
and the **F-J half** of the breadboard (the two sides of the centre DIP
gap) — each with its own row cursor starting at `START_ROW` (12).

For each component (large-footprint ones first, so their space is claimed
before smaller ones squeeze in around them):
1. Compute the candidate footprint at the current cursor — every `(row,
   col)` cell the physical part's body would occupy (see
   `get_component_footprint`; a component's *entire row* is claimed across
   its whole board-half, because all 5 holes in a breadboard row are one
   electrical node — you can't place two unrelated things in the same row
   even in different columns).
2. If the footprint has already-occupied cells, bump the cursor by 1 row and
   retry.
3. If the footprint would exceed `MAX_ROW` (30), switch to the other zone
   (unless the component has a hard `placement_side` in the registry, e.g.
   `HC_SR04` is always forced to `"FJ"` because the renderer draws its body
   hanging off the outer edge).
4. Once a legal cursor is found, record concrete `{col, row}` for every pin
   (`get_candidate_pins`), mark the footprint as occupied, and advance the
   zone's cursor past this component plus its registry `gap_after`.
5. Injected passives are placed immediately, relative to the parent's actual
   placement (`get_passive_candidate_pins`), not independently queued.

Column letters are **mirrored** when placed in the F-J zone (`_COL_FLIP`:
A↔J, B↔I, C↔H, D↔G, E↔F) so a component's footprint always sits away from
the centre gap regardless of which side it landed on — the registry only
ever needs to describe pins on the "A-E" convention.

### 3. `resolve_connections` — logical refs → breadboard wires
Translates `"LED1.anode"` / `"arduino.D4"` style refs into concrete wire
endpoints, with three special behaviors:

- **Same-node skip** — if both ends resolve to the same physical row on the
  same board half, no wire is emitted (they're already electrically
  connected through the breadboard itself).
- **GND rerouting** — every component→GND connection is rewritten as a short
  jumper to the nearest **negative rail** hole (`breadboard.-1.{row}`)
  instead of running straight to the Arduino. A single canonical
  `arduino.GND → breadboard.-1.30` wire is appended once at the end. This is
  why an N-component circuit has only *one* wire touching the Arduino's GND
  pin, not N.
- **5V rerouting** — identical logic through the **positive rail**
  (`+1`).
- Signal wires get their landing/departure column shifted to the
  registry's `wire_col` (e.g. LED signal wires always land at column A, not
  directly on the anode pin) so the wire doesn't have to be routed on top of
  the component's own leg.

### 4. `build_walkthrough` — step text generation
Produces one `{type: "component", instruction, tip}` entry per placed part
(from `_COMPONENT_INSTRUCTIONS`, keyed by type) in placement order, followed
by one `{type: "wire", instruction, tip}` entry per resolved wire (colored
black/red/green language derived from the wire's actual color). This is what
drives the "🔧 Step-by-Step" tab's Prev/Next walkthrough in
[project_base.html](templates/lessons/project_base.html).

### 5. `assemble` — final JSON
Just zips `meta` + placed components + wires + walkthrough into the
`circuit_definition` shape described above.

---

## `circuit_registry.py` — the physical constants table

One entry per supported `type` (`LED`, `RESISTOR`, `BUTTON`, `BUZZER`,
`SERVO`, `LDR`, `HC_SR04`, `SLIDE_SWITCH`). Every field is read by the engine
during placement:

| Field | Meaning |
|---|---|
| `footprint_rows` | how many rows this component's *own* body spans, used to advance the cursor after placing it |
| `gap_after` | extra empty rows required after this component before the next one can start (room for a resistor, wiring clearance, etc.) |
| `pins` | `{pin_name: {row_offset, col}}` — position of every pin *relative to the primary pin's cursor row*, on the canonical A-E convention |
| `primary_pin` | which pin's row *is* the cursor position |
| `requires` | list of auto-injected passives (LED/LDR → series/pull-down resistor) |
| `wire_col` | column an Arduino signal wire should land on/depart from (keeps wires off the component's own legs) |
| `gnd_col` | column a GND wire should land on (some parts need this shifted, e.g. RESISTOR shifts from D to E) |
| `placement_side` | forces `"AE"` or `"FJ"` regardless of the active zone (`HC_SR04` only) |

**This file has no logic** — if you add a new component type, this is
where its geometry goes, and `get_component_footprint` in
`circuit_engine.py` needs a matching branch to say which cells it occupies
(a LED/RESISTOR/LDR-shaped part just spans its two pin rows across the
board half; a BUTTON straddles both halves; HC_SR04 spans all columns; etc.).

---

## `circuit_renderer.js` — the SVG artist

### Coordinate system
Everything is drawn in an abstract SVG unit grid, not pixels — `viewBox` is
computed from tracked bounding boxes so it scales to fit whatever got drawn.

- `holeToSVG(col, row, board)` — the one formula that matters:
  `x = BB_ANCHOR.x + (30 - row) + boardOffset`, `y = BB_ANCHOR.y + COL_OFFSETS[col]`.
  Row 30 (nearest the Arduino) maps to the smallest x; row 1 to the largest.
  This is the **only place** breadboard col/row ever gets converted to a
  drawable point — component renderers and wire routing both consume `x,y`
  after this conversion, never col/row directly.
- `pinToSVG(pinName)` — same idea for Arduino header pins (`PIN_DEFS` table:
  physical pin name → offset from `ARD_ANCHOR`).
- `_resolveEndpoint(endpointString)` — parses `"arduino.D4"` /
  `"breadboard.A12"` / `"breadboard.-1.30"` / `"breadboard2.J5"` strings (the
  exact same strings the engine emits in `connections[]`) into `{x, y}`.

### Component symbols — `SYMBOL_RENDERERS`
One function per component `type`, keyed by the same string used in
`circuit_registry.py` and in `components[].type`. Each function receives
`(renderer, pinsSVG, properties)` where `pinsSVG` is *already* the converted
`{x, y}` per pin name (not col/row) — it draws gradients, leads, and body
shapes purely from those points (e.g. `LED`'s rotation angle is derived from
the anode→cathode vector, not stored anywhere). Every symbol also exports a
static `.bbox(pins, props)` used for two things: (a) registering an
**obstacle rectangle** so wires route around the component body, and (b)
punching a hole in the grey-out mask during walkthrough highlighting.

**If you add a new component type to the registry, you must also add a
matching entry to `SYMBOL_RENDERERS` (and its `.bbox`) — the engine will
happily place a type the renderer doesn't know how to draw, and it'll
silently fall back to a plain colored circle.**

### Wire routing — A* over a grid
`render()` draws the breadboard and Arduino body first (`_buildObstacleRegistry`
collects every component's `.bbox()` plus the Arduino body as blocked
rectangles), rasterizes that onto a `GRID_STEP = 0.5`-unit grid
(`_initGrid`), then for each connection runs `_astar(start, end)` — a
4-directional (no diagonals) A* with a turn penalty, so wires prefer
straight runs and hug orthogonal paths without cutting through component
bodies. `_markWireCells` raises the cost of cells a wire has already used
(and their neighbors) so later wires prefer *not* to overlap earlier ones,
without hard-blocking them. `_simplifyWaypoints` collapses runs of collinear
grid cells into a handful of `L`-shaped path points before drawing an SVG
`<path>`.

Wires are drawn in a specific order (`render()`'s `.sort()`): power/ground
wires first, then signal wires shortest-to-longest — this keeps rail wires
predictable and lets shorter signal wires claim direct paths before longer
ones have to route around them.

Two housekeeping passes run on the raw `connections[]` before drawing:
- `_normalizeGroundConnections` — collapses multiple `arduino.GND` wires down
  to rail jumpers + one canonical wire (the renderer does this defensively
  even though the engine already does the same rerouting — so a
  hand-authored `circuit_definition` that *didn't* bother with rail-routing
  still renders cleanly).
- `_assignWireColors` — forces GND wires black and 5V/power wires red
  regardless of what `color` was set, and cycles non-power wires through a
  20-color palette if no `color` was given, so wires stay visually
  distinguishable even in dense circuits.

### Public API
```js
const renderer = new CircuitRenderer(circuitDefinition, 'containerElementId');
renderer.render();                 // draws breadboard + Arduino + components + wires
renderer.applyHighlight(highlights); // [{type:'component', id} | {type:'wire', from, to}] — greys out everything else
renderer.getHighlights();          // connections[] resolved to {from,to,cx,cy,label} — used for click-to-highlight UIs
renderer.describe();               // dumps a plaintext table of every pin/wire + its SVG coords — paste into console for debugging
renderer.toggleDebugOverlay();     // hover-to-inspect grid overlay showing col/row ↔ SVG mapping
```

---

## Two ways to build a circuit for a lesson

### Option A — logical spec, let the engine place it (preferred)
In `utils/project_{name}.py`, add a `circuit_spec` to the `PROJECT` dict:

```python
PROJECT = {
    "meta": META,
    "circuit_spec": {
        "meta": {"title": "...", "difficulty": "easy"},
        "components": [
            {"id": "LED1", "type": "LED", "properties": {"color": "red"}},
        ],
        "connections": [
            {"from": "arduino.D4",   "to": "LED1.anode"},
            {"from": "LED1.cathode", "to": "R_LED1.pin1"},
            {"from": "R_LED1.pin2",  "to": "arduino.GND"},
        ],
    },
    "steps": STEPS,
    "drawer": DRAWER_CONTENT,
    "presets": {"default": SKETCH_PRESET},
}
```
`utils/project_registry.py` detects `circuit_spec` at import time and runs it
through `generate_circuit(...)` automatically, storing the result as
`project["circuit_definition"]` — you never call the engine yourself. Use
exactly the component types and pin names documented at the top of
`utils/circuit_prompt.py` (this is also the reference the LLM prompt itself
is built from — keep both in sync if you touch pin naming).

This is the only path that gets you automatic breadboard placement, GND/5V
rail consolidation, and a generated walkthrough for free — use it for any
new lesson whose circuit is built entirely from registry-supported parts.

### Option B — hand-author `circuit_definition` directly
If the circuit needs a component the registry doesn't support, or exact
manual control over layout, set `PROJECT["circuit_definition"]` directly
instead of `circuit_spec` — the registry's `if spec and "circuit_definition"
not in project"` check means an explicit `circuit_definition` always wins
and skips the engine entirely. It must satisfy the JSON contract above
(concrete `{col, row}` on every pin, fully resolved `connections[]`). This is
more work but the renderer doesn't care where the JSON came from.

### Fallback — no circuit JSON at all (legacy / static image)
If a project defines neither `circuit_spec` nor `circuit_definition`,
[project_base.html](templates/lessons/project_base.html) falls back to
rendering the manually-provided `static/graphics/project_{name}_circuit.png`
image instead of a live SVG (`{% elif circuit_image %}`). This is the older
per-CLAUDE.md convention — new lessons should prefer Option A.

### Dev tools while building/debugging a circuit
All under `/dev/circuit/...`, admin-login required (see project CLAUDE.md
security rules):
- **`/dev/circuit/<project_key>`** — renders that project's live
  `circuit_definition` through `CircuitRenderer`, exactly like the real
  lesson page would.
- **`/dev/circuit/sandbox`** — paste raw circuit JSON and render it
  immediately; the fastest way to iterate on a hand-authored
  `circuit_definition` or to sanity-check engine output without touching a
  project file.
- **`/dev/circuit/compare/<project_key>`** — side-by-side: the project's
  original circuit vs. one freshly generated by `utils/circuit_compare.py`
  (extracts topic/components/pins from the project, sends them to a local
  Ollama model using the `utils/circuit_prompt.py` template, runs the result
  through `generate_circuit`). Populate it with:
  ```
  python -m utils.circuit_compare <project_key>       # one project
  python -m utils.circuit_compare --all               # every project_*.py
  ```
  writes `static/circuit_compare/<project_key>.json`, which the route reads.

### Tests
`tests/test_circuit_engine.py` exercises the placement/resolution pipeline
directly (no renderer, no Flask) — run it after any change to
`circuit_engine.py` or `circuit_registry.py`:
```
pytest tests/test_circuit_engine.py
```

---

## Keeping registry and renderer in sync

The single biggest source of subtle bugs in this system: `circuit_registry.py`
(Python, used for placement) and `SYMBOL_RENDERERS` (JS, used for drawing)
each independently encode **the same pin names and relative geometry** for a
given component type. There is no shared schema file — if you rename a pin
in the registry (e.g. `pin1`→`legA`), you must rename it in the matching
`SYMBOL_RENDERERS` entry too, or the renderer will throw `Cannot read
property 'x' of undefined` the moment it tries to draw that component.
When adding a new component type, always touch all three files together:
`circuit_registry.py` (placement geometry) → `circuit_engine.py`
(`get_component_footprint` branch + `_COMPONENT_INSTRUCTIONS` entry) →
`circuit_renderer.js` (`SYMBOL_RENDERERS` entry + `.bbox`).

---

## Converting an existing project to the circuit engine

Old projects define a static `circuit_image` (Fritzing PNG) and a hand-written
`STEPS` list with pixel-coordinate `rect()`/`circle()` highlights. The goal is
to replace those with a `CIRCUIT_SPEC` so the engine generates the circuit
definition (placement + walkthrough) automatically at startup.

### Step-by-step process

**1. Read the project's `STEPS`** to identify:
- Which components are placed (LED, button, buzzer, LDR, etc.)
- Which Arduino pins are used
- How many GND and power connections exist

**2. Write the `CIRCUIT_SPEC`** — logical only, no coordinates:

```python
CIRCUIT_SPEC = {
    "meta": {
        "title": "Short project title",
        "difficulty": "beginner",   # or "intermediate" / "advanced"
    },
    "components": [
        # List primary components only — resistors are auto-injected
        {"id": "LED",  "type": "LED",    "properties": {"color": "red"}},
        {"id": "BTN",  "type": "BUTTON", "properties": {}},
    ],
    "connections": [
        # Use component.pin notation — see pin reference below
        {"from": "arduino.D8",  "to": "LED.anode"},
        {"from": "R_LED.pin2",  "to": "arduino.GND"},
        {"from": "arduino.D2",  "to": "BTN.TL"},
        {"from": "BTN.BR",      "to": "arduino.GND"},
    ],
}
```

**3. Add `circuit_spec` to the `PROJECT` dict:**

```python
PROJECT = {
    "meta": META,
    "steps": STEPS,           # old STEPS stay — they drive the legacy image tab
    "drawer": DRAWER_CONTENT,
    "chips": CHIPS,
    "presets": { ... },
    "circuit_spec": CIRCUIT_SPEC,   # ← add this
}
```

**4. Verify the engine output** before committing:

```bash
python3 -c "
from utils.circuit_engine import generate_circuit
spec = <paste spec dict here>
result = generate_circuit(spec['meta'], spec['components'], spec['connections'])
print('components:', [c['id'] for c in result['components']])
for w in result['connections']:
    print(f\"  {w['from']} -> {w['to']}  ({w['color']})\")
for s in result['walkthrough']:
    print(f\"  [{s['type']}] {s['instruction']}\")
"
```

Check: every component placed, correct wire count, GND jumpers to rail + one
canonical `arduino.GND → breadboard.-1.30`, walkthrough steps match the physical circuit.

**5. Test in the browser** at `/dev/circuit/<project_key>` (admin login required).

---

### Component pin reference

These are the exact type strings and pin names the engine and renderer understand.
**Do not list resistors in `components`** — `LED` and `LDR` auto-inject them.

| Type | Props | Pins | Notes |
|---|---|---|---|
| `LED` | `color`: red/green/yellow/blue/white | `anode` (long leg +), `cathode` (short leg −) | Auto-injects `R_{id}` (220Ω resistor) |
| `BUTTON` | — | `TL` (top-left, col E), `TR` (top-right, col F), `BL` (bottom-left, col E), `BR` (bottom-right, col F) | TL↔BR is one switch pair; wire signal to TL, GND to BR |
| `SLIDE_SWITCH` | — | `com` (common/wiper → signal), `pin2` (active throw → GND) | `pin1` unused |
| `BUZZER` | — | `positive` (+), `negative` (−) | No resistor needed |
| `SERVO` | — | `signal`, `power`, `ground` | Signal must be a PWM pin (D3/D5/D6/D9/D10/D11) |
| `LDR` | — | `pin1` (5V end), `pin2` (analog junction) | Auto-injects `R_{id}` (10kΩ pull-down) |
| `HC_SR04` | — | `vcc`, `trig` (trigger OUT), `echo` (echo IN), `gnd` | Always placed on FJ side |

**Arduino endpoints:**
- Digital: `arduino.D2` … `arduino.D13` (never D0/D1 — USB reserved)
- Analog: `arduino.A0` … `arduino.A5`
- Power: `arduino.GND`, `arduino.5V`

**Auto-injected resistor IDs** follow the pattern `R_{component_id}`:
- `LED` with id `LED` → resistor id `R_LED` → pins `R_LED.pin1`, `R_LED.pin2`
- `LDR` with id `LDR` → resistor id `R_LDR` → pins `R_LDR.pin1`, `R_LDR.pin2`
- pin1 is always at the component's cathode/junction row; pin2 is toward GND

---

### Standard wiring patterns per component type

```
LED:
  arduino.D{n}   → LED.anode
  R_LED.pin2     → arduino.GND          # resistor auto-injected between cathode and GND

BUTTON (momentary, INPUT_PULLUP):
  arduino.D{n}   → BTN.TL              # signal on TL-BR diagonal
  BTN.BR         → arduino.GND

SLIDE_SWITCH (toggle, INPUT_PULLUP):
  arduino.D{n}   → SW.com
  SW.pin2        → arduino.GND

BUZZER:
  arduino.D{n}   → BUZZ.positive
  BUZZ.negative  → arduino.GND

SERVO:
  arduino.D{pwm} → SRV.signal          # PWM pin required
  arduino.5V     → SRV.power
  arduino.GND    → SRV.ground

LDR (voltage divider):
  arduino.5V     → LDR.pin1
  LDR.pin2       → arduino.A{n}        # read analog voltage at junction
  R_LDR.pin2     → arduino.GND         # pull-down auto-injected

HC_SR04:
  arduino.5V     → SR.vcc
  arduino.GND    → SR.gnd
  arduino.D{n}   → SR.trig             # trigger OUTPUT
  SR.echo        → arduino.D{m}        # echo INPUT, different pin from trig
```

GND and 5V may appear in multiple connections — the engine consolidates them
to one canonical rail wire each. Digital/analog signal pins: one connection each.
