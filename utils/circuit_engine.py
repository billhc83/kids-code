"""
Circuit Generation Engine

Takes the LLM's logical circuit description (components + connections, no coordinates)
and produces the complete circuit JSON the CircuitRenderer already consumes.

Pipeline:
  1. expand_components   — inject required passives (resistors, pulldowns)
  2. place_components    — assign col/row to every pin via a monotonic cursor
  3. resolve_connections — translate logical refs to breadboard coordinates
  4. build_walkthrough   — generate step-by-step placement text
  5. assemble            — combine everything into final circuit JSON
"""

from utils.circuit_registry import REGISTRY

# ── Constants ──────────────────────────────────────────────────────────────────

START_ROW = 12   # first primary component's primary pin goes here;
                  # required passives extend toward lower rows (away from Arduino)
MAX_ROW   = 30   # breadboard row limit; row 1 = far end, row 30 = Arduino end

# Mirror map: A-E side ↔ F-J side (A↔J, B↔I, C↔H, D↔G, E↔F)
_COL_FLIP = {"A": "J", "B": "I", "C": "H", "D": "G", "E": "F",
             "F": "E", "G": "D", "H": "C", "I": "B", "J": "A"}


def _flip_col(col, side):
    """Return the mirrored column when placing on the F-J side; no-op on A-E."""
    return _COL_FLIP.get(col, col) if side == "FJ" else col


_AE_COLS = list("ABCDE")
_FJ_COLS = list("FGHIJ")
_ALL_COLS = list("ABCDEFGHIJ")


def _half_cols(side):
    return _AE_COLS if side == "AE" else _FJ_COLS


def _rows_full(r_min, r_max, cols):
    """Return all (row, col) cells for a row range × a column list."""
    return {(r, c) for r in range(r_min, r_max + 1) for c in cols}


def get_component_footprint(ctype, pins, side):
    """
    Return the set of (row, col) cells this component type claims.

    Every row a component occupies is marked across ALL columns of its
    breadboard half (A-E or F-J), because all 5 holes in a row are
    electrically connected.  Placing a component body at col D row 17
    is the same electrical node as a pin at col E row 17 — both would
    be a short.  BUTTON is the special case: it straddles both halves,
    so it claims all 10 columns for its rows.
    """
    cols = _half_cols(side)

    if ctype == "LED":
        r_min = min(pins["anode"]["row"], pins["cathode"]["row"])
        r_max = max(pins["anode"]["row"], pins["cathode"]["row"])
        return _rows_full(r_min, r_max, cols)

    if ctype == "RESISTOR":
        r_min = min(pins["pin1"]["row"], pins["pin2"]["row"])
        r_max = max(pins["pin1"]["row"], pins["pin2"]["row"])
        return _rows_full(r_min, r_max, cols)

    if ctype == "BUTTON":
        r_min = min(pins["TL"]["row"], pins["BL"]["row"])
        r_max = max(pins["TL"]["row"], pins["BL"]["row"])
        return _rows_full(r_min, r_max, _ALL_COLS)

    if ctype == "BUZZER":
        # A 12mm buzzer body crosses the DIP gap when placed in the inner column
        # (col E on AE side, col F on FJ side).  Block the full placement half
        # PLUS the single inner column of the opposing half.
        r_min = min(pins["positive"]["row"], pins["negative"]["row"])
        r_max = max(pins["positive"]["row"], pins["negative"]["row"])
        cross_cols = list("ABCDEF") if side == "AE" else list("EFGHIJ")
        return _rows_full(r_min, r_max, cross_cols)

    if ctype == "LDR":
        r_min = min(pins["pin1"]["row"], pins["pin2"]["row"])
        r_max = max(pins["pin1"]["row"], pins["pin2"]["row"])
        return _rows_full(r_min, r_max, cols)

    if ctype == "HC_SR04":
        # The HC-SR04 PCB (~45mm wide) spans the full breadboard width.
        # Block all columns, but only the actual pin rows — the module hangs
        # off the board edge rather than obstructing adjacent rows.
        row_vcc = pins["vcc"]["row"]
        row_gnd = pins["gnd"]["row"]
        r_min = min(row_vcc, row_gnd)
        r_max = max(row_vcc, row_gnd)
        return _rows_full(r_min, r_max, _ALL_COLS)

    if ctype == "SLIDE_SWITCH":
        row_com = pins["com"]["row"]
        return _rows_full(row_com - 1, row_com + 1, cols)

    if ctype == "SERVO":
        rows = [pins[p]["row"] for p in ("signal", "power", "ground") if p in pins]
        if not rows:
            return set()
        return _rows_full(min(rows), max(rows), cols)

    return set()


def get_candidate_pins(spec, cursor, side):
    pins = {}
    for pin_name, pin_def in spec["pins"].items():
        r = cursor + pin_def["row_offset"]
        c = _flip_col(pin_def["col"], side)
        pins[pin_name] = {"col": c, "row": r}
    return pins


def get_passive_candidate_pins(req_type, parent_pins, attach_from, attach_to, side):
    passive_spec = REGISTRY[req_type]
    attach_row = parent_pins[attach_from]["row"]
    passive_cursor = attach_row - passive_spec["pins"][attach_to]["row_offset"]
    pins = {}
    for pin_name, pin_def in passive_spec["pins"].items():
        r = passive_cursor + pin_def["row_offset"]
        c = _flip_col(pin_def["col"], side)
        pins[pin_name] = {"col": c, "row": r}
    return pins


def get_full_candidate_footprint(ctype, spec, cursor, side):
    parent_pins = get_candidate_pins(spec, cursor, side)
    footprint = get_component_footprint(ctype, parent_pins, side)
    for req in spec.get("requires", []):
        passive_pins = get_passive_candidate_pins(
            req["type"], parent_pins, req["attach_from"], req["attach_to"], side
        )
        passive_footprint = get_component_footprint(req["type"], passive_pins, side)
        footprint.update(passive_footprint)
    return footprint


def footprint_overflows(footprint):
    for r, col in footprint:
        if r > MAX_ROW or r < 1:
            return True
    return False


WIRE_COLORS = {
    "gnd":   "#111111",
    "power": "#CC0000",
}

# Signal wires cycle through this palette (one color per wire, in generation
# order) so multiple Arduino <-> component wires stay visually distinguishable.
# Mirrors the palette in static/js/circuit_renderer.js (_assignWireColors).
SIGNAL_COLORS = [
    "#3498DB",  # blue
    "#9B59B6",  # purple
    "#E67E22",  # orange
    "#1ABC9C",  # teal
    "#F1C40F",  # yellow
    "#E91E63",  # pink
    "#00BCD4",  # cyan
    "#8BC34A",  # lime green
]

SIGNAL_COLOR_NAMES = {
    "#3498DB": "blue",
    "#9B59B6": "purple",
    "#E67E22": "orange",
    "#1ABC9C": "teal",
    "#F1C40F": "yellow",
    "#E91E63": "pink",
    "#00BCD4": "cyan",
    "#8BC34A": "lime green",
}


# ── Step 1: Dependency Injection ───────────────────────────────────────────────

def expand_components(components):
    """
    Insert required passive components after each component that needs them.
    Returns an expanded list and a dict mapping injected IDs to their parent info.

    Input:  [{"id": "LED1", "type": "LED", "properties": {"color": "red"}}]
    Output: [<LED1 entry>, <R_LED1 entry>], {"R_LED1": {"parent": "LED1", ...}}
    """
    expanded = []
    injected = {}

    for comp in components:
        expanded.append(comp)
        spec = REGISTRY.get(comp["type"], {})
        for req in spec.get("requires", []):
            passive_id = req["id_pattern"].replace("{id}", comp["id"])
            passive = {
                "id":         passive_id,
                "type":       req["type"],
                "properties": dict(req.get("properties", {})),
                "_injected":  True,
                "_parent_id": comp["id"],
                "_attach_from": req["attach_from"],
                "_attach_to":   req["attach_to"],
            }
            expanded.append(passive)
            injected[passive_id] = {
                "parent_id":   comp["id"],
                "attach_from": req["attach_from"],
                "attach_to":   req["attach_to"],
            }

    return expanded, injected


# ── Step 2: Placement Cursor ────────────────────────────────────────────────────

def place_components(expanded, injected, start_row=START_ROW):
    """
    Walk the expanded component list and assign concrete col/row to every pin.

    Uses two independent placement zones — A-E columns and F-J columns.
    When placing a component would push pins past MAX_ROW, the engine switches
    to the other zone and restarts the cursor there from start_row.
    All column letters are mirrored for the F-J zone (E→F, D→G, A→J, etc.)
    so component footprints stay away from the DIP gap.

    Returns:
        placed      — {comp_id: {"type": ..., "_side": "AE"|"FJ",
                                  "pins": {pin_name: {"col": X, "row": Y}}, ...}}
        place_order — [comp_id, ...] in placement order
    """
    placed = {}
    place_order = []
    cursors  = {"AE": start_row, "FJ": start_row}
    occupied_cells = set()
    active_side = "AE"

    # Place components with a large physical footprint (row_radius set in registry)
    # first so their occupied_cells zone is established before other components are
    # positioned. Injected passives stay immediately after their parent.
    primary     = [c for c in expanded if not c.get("_injected")]
    inj_by_par  = {}
    for c in expanded:
        if c.get("_injected"):
            inj_by_par.setdefault(c["_parent_id"], []).append(c)
    primary.sort(key=lambda c: 0 if REGISTRY.get(c["type"], {}).get("row_radius") else 1)
    ordered = []
    for c in primary:
        ordered.append(c)
        ordered.extend(inj_by_par.get(c["id"], []))

    for comp in ordered:
        cid   = comp["id"]
        ctype = comp["type"]
        spec  = REGISTRY.get(ctype)
        if spec is None:
            raise ValueError(f"Unknown component type '{ctype}' for id '{cid}'")

        if comp.get("_injected"):
            # Required passives: placed relative to the parent's attach pin.
            # Inherit parent's side so columns stay consistent.
            parent_info = placed[comp["_parent_id"]]
            parent_side = parent_info["_side"]
            
            pins = get_passive_candidate_pins(
                ctype, parent_info["pins"], comp["_attach_from"], comp["_attach_to"], parent_side
            )
            
            footprint = get_component_footprint(ctype, pins, parent_side)
            occupied_cells.update(footprint)

            placed[cid] = {
                "id":         cid,
                "type":       ctype,
                "pins":       pins,
                "properties": comp.get("properties", {}),
                "_side":      parent_side,
            }
            place_order.append(cid)
            continue

        # Primary component: respect forced placement side, otherwise use active side.
        forced_side = spec.get("placement_side")
        side     = forced_side if forced_side else active_side
        cursor   = cursors[side]
        switched = False

        while True:
            footprint = get_full_candidate_footprint(ctype, spec, cursor, side)
            if footprint_overflows(footprint):
                # Only one side-switch is allowed per component. Cursors are not
                # updated until a component is successfully placed (see below), so
                # flipping back to an already-tried side would re-check the exact
                # same cursor/occupied_cells state and overflow again — ping-ponging
                # between AE/FJ forever instead of terminating.
                if forced_side or switched:
                    raise ValueError(
                        f"Board space exceeded when placing component '{cid}' ({ctype})"
                    )
                side = "FJ" if active_side == "AE" else "AE"
                active_side = side
                cursor = cursors[side]
                switched = True
                continue

            if occupied_cells.intersection(footprint):
                cursor += 1
            else:
                break

        pins = get_candidate_pins(spec, cursor, side)
        occupied_cells.update(footprint)

        placed[cid] = {
            "id":         cid,
            "type":       ctype,
            "pins":       pins,
            "properties": comp.get("properties", {}),
            "_side":      side,
        }
        place_order.append(cid)
        cursors[side] = cursor + spec["footprint_rows"] + spec["gap_after"]

    return placed, place_order


# ── Step 3: Connection Resolver ─────────────────────────────────────────────────

def _resolve_ref(ref, placed):
    """
    Given a string like "LED1.anode" or "arduino.D8", return either:
      - ("breadboard", col, row)  for a placed component pin
      - ("arduino", pin_name)     for an Arduino endpoint
    """
    parts = ref.split(".", 1)
    if parts[0] == "arduino":
        return ("arduino", parts[1])
    comp_id, pin_name = parts[0], parts[1]
    if comp_id not in placed:
        raise ValueError(f"Cannot resolve ref '{ref}': component '{comp_id}' not placed")
    pin = placed[comp_id]["pins"].get(pin_name)
    if pin is None:
        raise ValueError(f"Cannot resolve ref '{ref}': pin '{pin_name}' not in {comp_id}")
    return ("breadboard", pin["col"], pin["row"])


def _same_node(a, b):
    """
    Two breadboard pins are the same electrical node when they share a row
    and are both on the same side of the DIP gap (A-E or F-J).
    """
    if a[0] != "breadboard" or b[0] != "breadboard":
        return False
    col_a, col_b = a[1], b[1]
    row_a, row_b = a[2], b[2]
    if row_a != row_b:
        return False
    top_half  = set("ABCDE")
    bot_half  = set("FGHIJ")
    return (col_a in top_half and col_b in top_half) or \
           (col_a in bot_half and col_b in bot_half)


def _wire_col_for_endpoint(endpoint, placed, spec_key="wire_col", default="A"):
    """Pick the breadboard column to use as a wire endpoint for a component pin."""
    if endpoint[0] != "breadboard":
        return default
    for cid, info in placed.items():
        spec = REGISTRY.get(info["type"], {})
        if spec.get(spec_key):
            for pin_name, pin in info["pins"].items():
                if pin["col"] == endpoint[1] and pin["row"] == endpoint[2]:
                    return _flip_col(spec[spec_key], info.get("_side", "AE"))
    return default


def _wire_color(from_ep, to_ep, signal_idx):
    """Determine wire color from endpoint types. `signal_idx` selects the
    palette entry for signal wires so successive signal wires differ."""
    combined = " ".join(
        (e[1] if e[0] == "arduino" else "") for e in [from_ep, to_ep]
    )
    if "GND" in combined:
        return WIRE_COLORS["gnd"]
    if any(p in combined for p in ("5V", "VIN", "3V3", "power")):
        return WIRE_COLORS["power"]
    return SIGNAL_COLORS[signal_idx % len(SIGNAL_COLORS)]


_POWER_PINS = {"GND", "5V", "VIN", "3V3"}
_HALF_A     = "ABCDE"
_HALF_F     = "FGHIJ"


def _is_power(ep):
    return ep[0] == "arduino" and ep[1] in _POWER_PINS


def _is_signal(ep):
    """Arduino digital or analog pin (not a power rail)."""
    return ep[0] == "arduino" and not _is_power(ep)


def _pin_at(col, row, placed):
    """Return True if any placed component has a pin at (col, row)."""
    for info in placed.values():
        for pin in info["pins"].values():
            if pin["col"] == col and pin["row"] == row:
                return True
    return False


def _free_col(preferred, row, placed):
    """
    Return `preferred` if it's free at `row`, otherwise find the nearest free
    column on the same breadboard half (A-E or F-J).
    """
    if not _pin_at(preferred, row, placed):
        return preferred
    half = _HALF_A if preferred in _HALF_A else _HALF_F
    idx  = half.index(preferred)
    for delta in range(1, len(half)):
        for sign in (-1, 1):
            i = idx + sign * delta
            if 0 <= i < len(half) and not _pin_at(half[i], row, placed):
                return half[i]
    return preferred  # unreachable in practice


def _gnd_col_for(ep, placed):
    """
    For a breadboard endpoint going to GND/power, return the column to use
    for the wire endpoint. Uses gnd_col from the registry if defined (e.g.
    RESISTOR shifts from col D to col E, mirrored for F-J side). Falls back
    to the pin's own column so the wire lands exactly at the component leg.
    """
    for cid, info in placed.items():
        spec = REGISTRY.get(info["type"], {})
        for pin_name, pin in info["pins"].items():
            if pin["col"] == ep[1] and pin["row"] == ep[2]:
                if "gnd_col" in spec:
                    return _flip_col(spec["gnd_col"], info.get("_side", "AE"))
                return ep[1]  # no spec override — use pin's own column as-is
    return ep[1]


def _fmt_ep(ep):
    if ep[0] == "arduino":
        return f"arduino.{ep[1]}"
    return f"breadboard.{ep[1]}{ep[2]}"


def resolve_connections(logical_connections, placed):
    """
    Translate logical connection references to breadboard coordinates.

    Skips connections where both ends are the same breadboard node (internal jumper).
    Returns a list of wire dicts compatible with CircuitRenderer.

    GND connections are always rerouted through the negative (−) power rail:
      component.gnd  →  breadboard.-1.{row}   (short jumper per component)
      arduino.GND    →  breadboard.-1.30       (single canonical entry, appended last)

    5V connections are always rerouted through the positive (+) power rail:
      breadboard.{col}{row}  →  breadboard.+1.{row}   (short jumper per component)
      arduino.5V             →  breadboard.+1.30       (single canonical entry, appended last)

    This ensures only ONE wire ever leaves the Arduino GND or 5V pin, eliminating
    pin-crowding when multiple components share the same power rail.

    Signal wire endpoint rules:
      arduino → component: landing col shifted to wire_col (keeps pin hole clear).
      component → arduino: departure col shifted to wire_col (avoids component body).
    """
    wires = []
    canonical_wires = []
    gnd_rail_added   = False
    v5_rail_added    = False
    used_gnd_rows    = set()   # rail rows already claimed by a GND jumper
    used_v5_rows     = set()   # rail rows already claimed by a 5V jumper
    signal_wire_idx  = 0       # advances only for true signal wires

    def _free_rail_row(preferred, used_set):
        """
        Return `preferred` if that rail row is unclaimed, otherwise the nearest
        unclaimed row. Row 30 is reserved for the canonical Arduino entry so it
        is skipped here.
        """
        if preferred not in used_set and preferred != 30:
            return preferred
        for delta in range(1, MAX_ROW):
            for candidate in (preferred - delta, preferred + delta):
                if 1 <= candidate <= 29 and candidate not in used_set:
                    return candidate
        return preferred  # unreachable in practice

    for conn in logical_connections:
        from_ep = _resolve_ref(conn["from"], placed)
        to_ep   = _resolve_ref(conn["to"],   placed)

        if _same_node(from_ep, to_ep):
            continue

        # Identify which endpoint is an arduino power pin and which is breadboard.
        if from_ep[0] == "arduino" and _is_power(from_ep) and to_ep[0] == "breadboard":
            arduino_pin, board_ep = from_ep[1], to_ep
        elif to_ep[0] == "arduino" and _is_power(to_ep) and from_ep[0] == "breadboard":
            arduino_pin, board_ep = to_ep[1], from_ep
        else:
            arduino_pin, board_ep = None, None

        if arduino_pin == "GND" and board_ep is not None:
            # Route through -1 rail: short jumper from component pin to rail.
            col = _gnd_col_for(board_ep, placed)
            col = _free_col(col, board_ep[2], placed)
            row = board_ep[2]
            rail_row = _free_rail_row(row, used_gnd_rows)
            used_gnd_rows.add(rail_row)
            wires.append({
                "from":  f"breadboard.{col}{row}",
                "to":    f"breadboard.-1.{rail_row}",
                "color": WIRE_COLORS["gnd"],
            })
            if not gnd_rail_added:
                canonical_wires.append({
                    "from":  "arduino.GND",
                    "to":    "breadboard.-1.30",
                    "color": WIRE_COLORS["gnd"],
                })
                gnd_rail_added = True
            continue

        if arduino_pin == "5V" and board_ep is not None:
            # Route through +1 rail: short jumper from component pin to rail.
            row = board_ep[2]
            col = _free_col(board_ep[1], row, placed)
            rail_row = _free_rail_row(row, used_v5_rows)
            used_v5_rows.add(rail_row)
            wires.append({
                "from":  f"breadboard.{col}{row}",
                "to":    f"breadboard.+1.{rail_row}",
                "color": WIRE_COLORS["power"],
            })
            if not v5_rail_added:
                canonical_wires.append({
                    "from":  "arduino.5V",
                    "to":    "breadboard.+1.30",
                    "color": WIRE_COLORS["power"],
                })
                v5_rail_added = True
            continue

        # Signal wires and other (non-GND/5V) power connections.
        from_str = _fmt_ep(from_ep)
        to_str   = _fmt_ep(to_ep)
        is_signal_wire = False

        if _is_signal(from_ep) and to_ep[0] == "breadboard":
            # Signal wire: arduino → component. Shift landing col to wire_col.
            col = _wire_col_for_endpoint(to_ep, placed, "wire_col")
            to_str = f"breadboard.{col}{to_ep[2]}"
            is_signal_wire = True

        elif _is_signal(to_ep) and from_ep[0] == "breadboard":
            # Signal wire: component → arduino. Shift departure col to wire_col
            # so the wire exits from the far side of the component body.
            col = _wire_col_for_endpoint(from_ep, placed, "wire_col")
            from_str = f"breadboard.{col}{from_ep[2]}"
            is_signal_wire = True

        elif _is_power(from_ep) and to_ep[0] == "breadboard":
            # Other power rail (VIN, 3V3) → component.
            col = _free_col(to_ep[1], to_ep[2], placed)
            to_str = f"breadboard.{col}{to_ep[2]}"

        elif _is_power(to_ep) and from_ep[0] == "breadboard":
            # Component → other power rail (VIN, 3V3).
            col = _gnd_col_for(from_ep, placed)
            col = _free_col(col, from_ep[2], placed)
            from_str = f"breadboard.{col}{from_ep[2]}"

        wires.append({
            "from":  from_str,
            "to":    to_str,
            "color": _wire_color(from_ep, to_ep, signal_wire_idx),
        })
        if is_signal_wire:
            signal_wire_idx += 1

    # Canonical rail entries appended last so walkthrough teaches components
    # before establishing the power rails.
    return wires + canonical_wires


# ── Step 4: Walkthrough Generator ──────────────────────────────────────────────

_COMPONENT_INSTRUCTIONS = {
    "LED": lambda cid, props, pins: (
        f"Put the {props.get('color', '')} LED on the breadboard with "
        f"the long leg (anode) in row {pins['anode']['row']}, "
        f"column {pins['anode']['col']} and the short leg (cathode) in "
        f"row {pins['cathode']['row']}, column {pins['cathode']['col']}.",
        "The long leg is positive — it's called the anode!"
    ),
    "RESISTOR": lambda cid, props, pins: (
        f"Put the {props.get('ohms', '')}Ω resistor on the breadboard with "
        f"one leg in row {pins['pin1']['row']}, column {pins['pin1']['col']} "
        f"and the other leg in row {pins['pin2']['row']}, column {pins['pin2']['col']}.",
        "The resistor limits current so the component doesn't burn out."
    ),
    "BUTTON": lambda cid, props, pins: (
        f"Place the button onto the breadboard across the center gap. "
        f"Top legs in row {pins['TL']['row']}, columns E and F. "
        f"Bottom legs in row {pins['BL']['row']}, columns E and F.",
        "The button bridges the two halves of the breadboard."
    ),
    "BUZZER": lambda cid, props, pins: (
        f"Place the buzzer with the long leg (+) in row {pins['positive']['row']}, "
        f"column {pins['positive']['col']} and the short leg (−) in "
        f"row {pins['negative']['row']}, column {pins['negative']['col']}.",
        "The long leg is positive — mark it with a tiny + on the buzzer."
    ),
    "LDR": lambda cid, props, pins: (
        f"Place the photoresistor (LDR) on the breadboard with one leg in "
        f"row {pins['pin1']['row']}, column {pins['pin1']['col']} and the other "
        f"leg in row {pins['pin2']['row']}, column {pins['pin2']['col']}.",
        "The photoresistor changes resistance based on light — brighter light means lower resistance!"
    ),
    "HC_SR04": lambda cid, props, pins: (
        f"Plug the HC-SR04 sensor into the breadboard with all four pins in "
        f"column {pins['vcc']['col']}: VCC in row {pins['vcc']['row']}, "
        f"TRIG in row {pins['trig']['row']}, ECHO in row {pins['echo']['row']}, "
        f"GND in row {pins['gnd']['row']}.",
        "The two silver circles are the ultrasonic 'eyes' — point them toward your target!"
    ),
    "SLIDE_SWITCH": lambda cid, props, pins: (
        f"Place the slide switch on the breadboard with the centre pin in "
        f"row {pins['com']['row']}, column {pins['com']['col']} "
        f"and the side pin in row {pins['pin2']['row']}, column {pins['pin2']['col']}.",
        "Slide it toward the GND side to turn ON — that closes the circuit."
    ),
}


def _wire_instruction(wire):
    """Generate human-readable wire step from a resolved wire dict."""
    color_names = {
        WIRE_COLORS["gnd"]:   "black",
        WIRE_COLORS["power"]: "red",
        **SIGNAL_COLOR_NAMES,
    }
    color_name = color_names.get(wire["color"], "")

    frm, to = wire["from"], wire["to"]

    def label(ref):
        if ref.startswith("arduino."):
            pin = ref[len("arduino."):]
            if pin == "GND":
                return "the Arduino's GND pin"
            if pin == "5V":
                return "the Arduino's 5V pin"
            return f"Arduino pin {pin}"
        addr = ref[len("breadboard."):]
        if addr.startswith("-1.") or addr.startswith("-2."):
            row = addr[3:]
            return f"the negative (−) rail at row {row}"
        if addr.startswith("+1.") or addr.startswith("+2."):
            row = addr[3:]
            return f"the positive (+) rail at row {row}"
        col = addr[:1]
        row = addr[1:]
        return f"the breadboard at row {row}, column {col}"

    article = "an" if color_name[:1] in "aeiou" else "a"
    instruction = f"Connect {article} {color_name} wire from {label(frm)} to {label(to)}."
    tip = {
        WIRE_COLORS["gnd"]:   "Black wires carry ground — the return path for electricity.",
        WIRE_COLORS["power"]: "Red wires carry power — the positive 5V supply rail.",
    }.get(wire["color"], "This wire carries the signal between Arduino and your component.")

    return instruction, tip


def build_walkthrough(place_order, placed, wires):
    """
    Build the walkthrough steps list for CircuitRenderer.

    Order: component steps first (in placement order), then wire steps.
    """
    steps = []

    for cid in place_order:
        info  = placed[cid]
        ctype = info["type"]
        tmpl  = _COMPONENT_INSTRUCTIONS.get(ctype)
        if tmpl is None:
            continue
        instruction, tip = tmpl(cid, info["properties"], info["pins"])
        steps.append({
            "type":        "component",
            "id":          cid,
            "instruction": instruction,
            "tip":         tip,
        })

    for wire in wires:
        instruction, tip = _wire_instruction(wire)
        steps.append({
            "type":        "wire",
            "from":        wire["from"],
            "to":          wire["to"],
            "instruction": instruction,
            "tip":         tip,
        })

    return steps


# ── Step 5: Assembler ───────────────────────────────────────────────────────────

def assemble(meta, placed, place_order, wires, walkthrough):
    """Combine all engine outputs into the final circuit JSON dict."""
    components = []
    for cid in place_order:
        info = placed[cid]
        entry = {
            "id":         info["id"],
            "type":       info["type"],
            "pins":       info["pins"],
            "properties": info["properties"],
        }
        components.append(entry)

    return {
        "meta":        meta,
        "components":  components,
        "connections": wires,
        "walkthrough": walkthrough,
    }


# ── Public Entry Point ──────────────────────────────────────────────────────────

def generate_circuit(meta, components, logical_connections, start_row=START_ROW):
    """
    Full pipeline: logical description → renderer-ready circuit JSON.

    Args:
        meta                — dict with title, difficulty, etc.
        components          — list of {id, type, properties} from LLM
        logical_connections — list of {from, to} using component.pin notation
        start_row           — breadboard row for first component's primary pin

    Returns:
        circuit JSON dict ready for CircuitRenderer
    """
    expanded, injected = expand_components(components)
    placed, place_order = place_components(expanded, injected, start_row)
    wires = resolve_connections(logical_connections, placed)
    walkthrough = build_walkthrough(place_order, placed, wires)
    return assemble(meta, placed, place_order, wires, walkthrough)
