"""
Validation tests for the circuit engine.

Strategy: feed each course's logical description through the engine and compare
the output to the hand-built CIRCUIT_DEFINITION already in the project module.
"""

import pytest
from utils.circuit_engine import generate_circuit, expand_components, place_components


# ── Project 1 fixtures ─────────────────────────────────────────────────────────

PROJECT_ONE_COMPONENTS = [
    {"id": "LED", "type": "LED", "properties": {"color": "red"}},
]

PROJECT_ONE_CONNECTIONS = [
    {"from": "arduino.D8",    "to": "LED.anode"},
    {"from": "LED.cathode",   "to": "R_LED.pin1"},
    {"from": "R_LED.pin2",    "to": "arduino.GND"},
]

PROJECT_ONE_META = {"title": "LED Blink", "difficulty": "beginner"}


# ── Helper ─────────────────────────────────────────────────────────────────────

def pins_match(actual_pins, expected_pins, label):
    """Compare two pin dicts, reporting all mismatches."""
    for pin_name, expected in expected_pins.items():
        assert pin_name in actual_pins, f"{label}: pin '{pin_name}' missing"
        actual = actual_pins[pin_name]
        assert actual["col"] == expected["col"], \
            f"{label}.{pin_name}: col {actual['col']} != {expected['col']}"
        assert actual["row"] == expected["row"], \
            f"{label}.{pin_name}: row {actual['row']} != {expected['row']}"


# ── Placement tests ────────────────────────────────────────────────────────────

def test_led_pins_placed_correctly():
    expanded, injected = expand_components(PROJECT_ONE_COMPONENTS)
    placed, order = place_components(expanded, injected, start_row=12)

    pins_match(
        placed["LED"]["pins"],
        {"anode": {"col": "E", "row": 12}, "cathode": {"col": "E", "row": 11}},
        "LED"
    )


def test_resistor_injected_and_placed():
    expanded, injected = expand_components(PROJECT_ONE_COMPONENTS)
    assert any(c["id"] == "R_LED" for c in expanded), "R_LED not injected"

    placed, order = place_components(expanded, injected, start_row=12)
    assert "R_LED" in placed, "R_LED not in placed"

    pins_match(
        placed["R_LED"]["pins"],
        {"pin1": {"col": "D", "row": 11}, "pin2": {"col": "D", "row": 7}},
        "R_LED"
    )


def test_place_order():
    expanded, injected = expand_components(PROJECT_ONE_COMPONENTS)
    _, order = place_components(expanded, injected, start_row=12)
    assert order == ["LED", "R_LED"]


# ── Connection resolution tests ────────────────────────────────────────────────

def test_connections_resolve():
    result = generate_circuit(
        PROJECT_ONE_META,
        PROJECT_ONE_COMPONENTS,
        PROJECT_ONE_CONNECTIONS,
        start_row=12,
    )
    wires = result["connections"]
    # Should have exactly 2 wires (the cathode→pin1 same-node connection is dropped)
    assert len(wires) == 2, f"Expected 2 wires, got {len(wires)}: {wires}"


def test_signal_wire():
    result = generate_circuit(
        PROJECT_ONE_META,
        PROJECT_ONE_COMPONENTS,
        PROJECT_ONE_CONNECTIONS,
        start_row=12,
    )
    wires = {(w["from"], w["to"]): w for w in result["connections"]}
    assert ("arduino.D8", "breadboard.A12") in wires, \
        f"Signal wire not found. Wires: {list(wires.keys())}"
    assert wires[("arduino.D8", "breadboard.A12")]["color"] == "#00AA00"


def test_gnd_wire():
    result = generate_circuit(
        PROJECT_ONE_META,
        PROJECT_ONE_COMPONENTS,
        PROJECT_ONE_CONNECTIONS,
        start_row=12,
    )
    wires = {(w["from"], w["to"]): w for w in result["connections"]}
    assert ("breadboard.E7", "arduino.GND") in wires, \
        f"GND wire not found. Wires: {list(wires.keys())}"
    assert wires[("breadboard.E7", "arduino.GND")]["color"] == "#111111"


# ── Full output match against hand-built project_one definition ────────────────

def test_full_match_project_one():
    from utils.project_one import CIRCUIT_DEFINITION as expected

    result = generate_circuit(
        PROJECT_ONE_META,
        PROJECT_ONE_COMPONENTS,
        PROJECT_ONE_CONNECTIONS,
        start_row=12,
    )

    # Compare component pin positions by type, ignoring ID (engine uses R_{id} scheme,
    # hand-built courses used arbitrary IDs like R1 — geometry is what matters).
    def pin_set(comps):
        """Canonical set of (type, pin_name, col, row) tuples for comparison."""
        s = set()
        for c in comps:
            for pname, pval in c["pins"].items():
                s.add((c["type"], pname, pval["col"], pval["row"]))
        return s

    result_pins   = pin_set(result["components"])
    expected_pins = pin_set(expected["components"])
    assert result_pins == expected_pins, \
        f"Pin position mismatch.\n  engine:   {sorted(result_pins)}\n  expected: {sorted(expected_pins)}"

    # Connections match
    result_wire_set  = {(w["from"], w["to"]) for w in result["connections"]}
    expected_wire_set = {(w["from"], w["to"]) for w in expected["connections"]}
    assert result_wire_set == expected_wire_set, \
        f"Wire mismatch.\n  engine:   {sorted(result_wire_set)}\n  expected: {sorted(expected_wire_set)}"

    # Walkthrough has same number of steps
    assert len(result["walkthrough"]) == len(expected["walkthrough"]), \
        f"Walkthrough length {len(result['walkthrough'])} != {len(expected['walkthrough'])}"


# ── Button placement tests ─────────────────────────────────────────────────────
# Physical: TL at (E, N), TR at (F, N), BL at (E, N+2), BR at (F, N+2)
# Diagonal activation: TL↔BR is one switch pair, BL↔TR is the other.
# Wiring: arduino.D{n} → TL,  BR → arduino.GND  (same TL-BR diagonal).
# No external resistor — Arduino INPUT_PULLUP used in sketch.

BUTTON_COMPONENTS = [
    {"id": "BTN1", "type": "BUTTON", "properties": {}},
]

BUTTON_CONNECTIONS = [
    {"from": "arduino.D2", "to": "BTN1.TL"},
    {"from": "BTN1.BR",    "to": "arduino.GND"},
]


def test_button_pins_placed_correctly():
    expanded, injected = expand_components(BUTTON_COMPONENTS)
    placed, _ = place_components(expanded, injected, start_row=25)

    pins_match(
        placed["BTN1"]["pins"],
        {
            "TL": {"col": "E", "row": 25},
            "TR": {"col": "F", "row": 25},
            "BL": {"col": "E", "row": 27},
            "BR": {"col": "F", "row": 27},
        },
        "BTN1"
    )


def test_button_no_resistor_injected():
    # INPUT_PULLUP — no external resistor for buttons.
    expanded, injected = expand_components(BUTTON_COMPONENTS)
    ids = [c["id"] for c in expanded]
    assert ids == ["BTN1"], f"Button should have no injected passives, got {ids}"


def test_button_gnd_wire_uses_br():
    # GND wire must land on BR (col F, same diagonal as TL signal wire).
    result = generate_circuit(
        {"title": "Button test"},
        BUTTON_COMPONENTS,
        BUTTON_CONNECTIONS,
        start_row=25,
    )
    wires = {(w["from"], w["to"]): w for w in result["connections"]}
    # Signal: arduino → col A at TL's row (25)
    assert ("arduino.D2", "breadboard.A25") in wires, \
        f"Signal wire not found. Wires: {list(wires.keys())}"
    # GND: BR is at F27, gnd_col=G → wire from G27 (free adjacent col, not the pin itself)
    assert ("breadboard.G27", "arduino.GND") in wires, \
        f"GND wire not at G27. Wires: {list(wires.keys())}"


def test_button_cursor_advance():
    # Button footprint=3 rows + gap=2 → next component starts at start_row + 5.
    btn_then_led = [
        {"id": "BTN1", "type": "BUTTON", "properties": {}},
        {"id": "LED1", "type": "LED",    "properties": {"color": "green"}},
    ]
    expanded, injected = expand_components(btn_then_led)
    placed, _ = place_components(expanded, injected, start_row=25)

    # Button TL at 25, footprint 3 + gap 2 = 5 → LED anode at 30.
    assert placed["LED1"]["pins"]["anode"]["row"] == 30, \
        f"Expected LED1 anode at row 30, got {placed['LED1']['pins']['anode']['row']}"


# ── Buzzer placement tests ─────────────────────────────────────────────────────
# Physical: positive at (E, N), negative at (E, N+3) — 4-hole vertical span.
# footprint_rows=4: cursor clears rows N through N+3 before next component.

BUZZER_COMPONENTS = [
    {"id": "BUZ1", "type": "BUZZER", "properties": {}},
]

BUZZER_CONNECTIONS = [
    {"from": "arduino.D9",   "to": "BUZ1.positive"},
    {"from": "BUZ1.negative", "to": "arduino.GND"},
]


def test_buzzer_pins_placed_correctly():
    expanded, injected = expand_components(BUZZER_COMPONENTS)
    placed, _ = place_components(expanded, injected, start_row=12)

    pins_match(
        placed["BUZ1"]["pins"],
        {
            "positive": {"col": "E", "row": 12},
            "negative": {"col": "E", "row": 15},
        },
        "BUZ1"
    )


def test_buzzer_cursor_advance():
    # Buzzer footprint=4 rows + gap=2 → next component starts at start_row + 6 (row 18).
    # But LED1 requires a series resistor on column D. The buzzer occupies columns C, D, E, F
    # on rows 12-15. So the resistor on column D overlaps with the buzzer body.
    # To avoid collision, the LED anode must be advanced to row 21 (resistor at rows 16-20).
    buzzer_then_led = [
        {"id": "BUZ1", "type": "BUZZER", "properties": {}},
        {"id": "LED1", "type": "LED",    "properties": {"color": "red"}},
    ]
    expanded, injected = expand_components(buzzer_then_led)
    placed, _ = place_components(expanded, injected, start_row=12)

    assert placed["LED1"]["pins"]["anode"]["row"] == 21, \
        f"Expected LED1 anode at row 21, got {placed['LED1']['pins']['anode']['row']}"


def test_buzzer_no_injected_passives():
    expanded, injected = expand_components(BUZZER_COMPONENTS)
    ids = [c["id"] for c in expanded]
    assert ids == ["BUZ1"], f"Buzzer should have no injected passives, got {ids}"


# ── SLIDE_SWITCH + BUZZER overlap tests ────────────────────────────────────────
# The BUZZER body has a large circular disc (radius ~2 SVG units) that spans
# across the DIP gap into both E and F columns.  A SLIDE_SWITCH placed at
# overlapping rows on either side MUST be pushed down by the 2D footprint check.

from utils.circuit_engine import get_component_footprint, COL_OFFSETS


def _placed_footprint(placed, cid):
    """Return the set of (row, col) cells occupied by a placed component."""
    info = placed[cid]
    return get_component_footprint(info["type"], info["pins"], info.get("_side", "AE"))


SWITCH_BUZZER_COMPONENTS = [
    {"id": "SW1",  "type": "SLIDE_SWITCH", "properties": {}},
    {"id": "BUZ1", "type": "BUZZER",       "properties": {}},
]


def test_switch_buzzer_no_physical_overlap():
    """Engine must ensure SW1 and BUZ1 footprints don't share any (row, col) cell."""
    expanded, injected = expand_components(SWITCH_BUZZER_COMPONENTS)
    placed, _ = place_components(expanded, injected, start_row=12)

    sw_cells  = _placed_footprint(placed, "SW1")
    buz_cells = _placed_footprint(placed, "BUZ1")

    overlap = sw_cells & buz_cells
    assert not overlap, (
        f"SW1 and BUZ1 footprints overlap at cells: {sorted(overlap)}\n"
        f"  SW1  pins: {placed['SW1']['pins']}\n"
        f"  BUZ1 pins: {placed['BUZ1']['pins']}"
    )


def test_buzzer_switch_no_physical_overlap():
    """Same test but with buzzer first — order must not matter."""
    components = [
        {"id": "BUZ1", "type": "BUZZER",       "properties": {}},
        {"id": "SW1",  "type": "SLIDE_SWITCH", "properties": {}},
    ]
    expanded, injected = expand_components(components)
    placed, _ = place_components(expanded, injected, start_row=12)

    buz_cells = _placed_footprint(placed, "BUZ1")
    sw_cells  = _placed_footprint(placed, "SW1")

    overlap = buz_cells & sw_cells
    assert not overlap, (
        f"BUZ1 and SW1 footprints overlap at cells: {sorted(overlap)}\n"
        f"  BUZ1 pins: {placed['BUZ1']['pins']}\n"
        f"  SW1  pins: {placed['SW1']['pins']}"
    )


def test_two_slide_switches_no_overlap():
    """Two slide switches on the same side must not overlap (as in Project 10)."""
    components = [
        {"id": "SW1", "type": "SLIDE_SWITCH", "properties": {}},
        {"id": "SW2", "type": "SLIDE_SWITCH", "properties": {}},
    ]
    expanded, injected = expand_components(components)
    placed, _ = place_components(expanded, injected, start_row=12)

    sw1_cells = _placed_footprint(placed, "SW1")
    sw2_cells = _placed_footprint(placed, "SW2")

    overlap = sw1_cells & sw2_cells
    assert not overlap, (
        f"SW1 and SW2 footprints overlap at cells: {sorted(overlap)}\n"
        f"  SW1 pins: {placed['SW1']['pins']}\n"
        f"  SW2 pins: {placed['SW2']['pins']}"
    )

