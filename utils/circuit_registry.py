"""
Component Registry — static physical properties for every supported component.
No logic. Just constants.

Row/column conventions (matching circuit_renderer.js holeToSVG):
  col  — letter A-J (A-E on top half, F-J on bottom half of breadboard)
  row  — integer 1-30, increasing TOWARD the Arduino

Offsets are relative to the component's primary pin placement:
  row_offset > 0 → toward Arduino (higher row number)
  row_offset < 0 → away from Arduino (lower row number)
"""

REGISTRY = {
    "LED": {
        "footprint_rows": 2,  # rows occupied by the primary component (anode to cathode)
        "gap_after": 4,       # must be >= 4: resistor extends 4 rows back from cathode;
                              # gap < 4 causes resistor collision + GND wire conflict with next LED
        "primary_pin": "anode",
        "pins": {
            "anode":   {"row_offset": 0,  "col": "E"},
            "cathode": {"row_offset": -1, "col": "E"},
        },
        "requires": [
            {
                "type": "RESISTOR",
                "id_pattern": "R_{id}",
                "properties": {"ohms": 220},
                "attach_from": "cathode",  # parent pin the passive connects to
                "attach_to":   "pin1",     # passive primary pin that goes at the same row
            }
        ],
        "wire_col": "A",    # column used for Arduino signal wire endpoint
    },

    "RESISTOR": {
        "footprint_rows": 4,  # rows spanned from pin1 to pin2 (pin2 = pin1_row - 4)
        "gap_after": 1,
        "primary_pin": "pin1",
        "pins": {
            "pin1": {"row_offset": 0,  "col": "D"},
            "pin2": {"row_offset": -4, "col": "D"},
        },
        "gnd_col": "E",     # column used for GND wire endpoint (must be free in pin2's row)
    },

    "BUTTON": {
        # Physical 4-pin tactile switch straddling the DIP gap.
        # Footprint: 3 rows tall (TL→BL offset +2), 3 holes wide (E, gap, F).
        # Diagonal activation: TL↔BR is one switch pair, BL↔TR is the other.
        # Signal and GND must land on the SAME diagonal so pressing closes the circuit.
        # No external resistor — Arduino INPUT_PULLUP handles the pull-up internally.
        # Wiring: arduino.D{n} → TL,  BTN.BR → arduino.GND  (TL-BR diagonal).
        "footprint_rows": 3,  # rows N, N+1, N+2 occupied (TL at N, BL at N+2)
        "gap_after": 2,
        "primary_pin": "TL",
        "straddles_dip_gap": True,
        "pins": {
            "TL": {"row_offset": 0, "col": "E"},
            "TR": {"row_offset": 0, "col": "F"},
            "BL": {"row_offset": 2, "col": "E"},
            "BR": {"row_offset": 2, "col": "F"},
        },
        "wire_col": "A",
        "gnd_col":  "G",    # GND wire lands at col G (free adjacent col on F-J side), not on BR's col F
    },

    "BUZZER": {
        # Physical buzzer: 2 pins (+/-) spanning 4 breadboard holes.
        # Vertical orientation: positive at row N, negative at row N+3 (same column).
        # Can also be placed horizontally straddling E→F (same physical pin spacing).
        # footprint_rows=4: cursor must clear all 4 occupied rows (N through N+3).
        "footprint_rows": 4,
        "gap_after": 2,
        "primary_pin": "positive",
        "pins": {
            "positive": {"row_offset": 0, "col": "E"},
            "negative": {"row_offset": 3, "col": "E"},
        },
        "wire_col": "A",
    },

    "SERVO": {
        "footprint_rows": 3,
        "gap_after": 2,
        "off_breadboard": True,
        "primary_pin": "signal",
        "pins": {
            "signal": {"row_offset": 0, "col": "G"},
            "power":  {"row_offset": 1, "col": "G"},
            "ground": {"row_offset": 2, "col": "G"},
        },
    },

    "LDR": {
        # Photoresistor (light-dependent resistor) in a voltage divider.
        # pin1 (5V end) at cursor row, pin2 (analog junction) 3 rows above.
        # Auto-injects a 10kΩ pull-down resistor from pin2 toward GND,
        # same pattern as LED's series resistor.
        "footprint_rows": 4,  # rows N through N-3
        "gap_after": 4,       # space for the pull-down resistor below
        "primary_pin": "pin1",
        "pins": {
            "pin1": {"row_offset": 0,  "col": "E"},  # 5V end
            "pin2": {"row_offset": -3, "col": "E"},  # analog read / pull-down junction
        },
        "requires": [
            {
                "type": "RESISTOR",
                "id_pattern": "R_{id}",
                "properties": {"ohms": 10000},
                "attach_from": "pin2",
                "attach_to":   "pin1",
            }
        ],
        "wire_col": "A",
    },

    "HC_SR04": {
        # HC-SR04 ultrasonic distance sensor.  The renderer draws the sensor body
        # extending DOWNWARD from col J (the outermost FJ column), so pins must
        # always land in col J.  Pins are defined as col "A" so the flip system
        # converts them to col J when placed on the FJ side.
        # "placement_side": "FJ" forces the engine to always use the FJ zone.
        # Signal wires land at col E → flips to col F (inner FJ), keeping wires
        # on the correct breadboard half and away from the sensor pins.
        "footprint_rows": 4,      # VCC at row N, TRIG N-1, ECHO N-2, GND N-3
        "gap_after": 4,
        "primary_pin": "vcc",
        "placement_side": "FJ",   # always place on FJ so pins land at col J
        "pins": {
            "vcc":  {"row_offset": 0,  "col": "A"},  # col A → flips to J on FJ
            "trig": {"row_offset": -1, "col": "A"},
            "echo": {"row_offset": -2, "col": "A"},
            "gnd":  {"row_offset": -3, "col": "A"},
        },
        "wire_col": "E",    # signal wires land at col E → flips to F (inner FJ)
        "gnd_col":  "A",    # GND wire at own pin col A → flips to J on FJ
    },

    "SLIDE_SWITCH": {
        # SPDT slide switch (e.g. Same Sky SLW-883935-2A-D).
        # 3 pins in a single column, 3 consecutive breadboard rows.
        # Only com + pin2 are wired; pin1 (away from Arduino) is left unconnected.
        # Always wired with INPUT_PULLUP: LOW = switch ON, HIGH = switch OFF.
        # Wiring: com → Arduino signal (wire_col A), pin2 → GND (negative rail).
        "footprint_rows": 3,
        "gap_after": 2,
        "primary_pin": "com",
        "pins": {
            "pin1": {"row_offset": -1, "col": "E"},  # unused throw (away from Arduino)
            "com":  {"row_offset":  0, "col": "E"},  # common / wiper → Arduino signal
            "pin2": {"row_offset":  1, "col": "E"},  # active throw → GND
        },
        "wire_col": "A",
        "gnd_col":  "E",
    },
}
