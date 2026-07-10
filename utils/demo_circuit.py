"""
utils/demo_circuit.py — the one shared "LED + resistor on pin 13" circuit
definition used anywhere KidsCode shows an illustrative (non-interactive)
breadboard diagram via CircuitRenderer, rather than a real lesson's
circuit_image + wiring STEPS.

Used by:
  - templates/splash.html (marketing demo, unauthenticated)
  - utils/project_try_it.py (drawer "The Circuit" tab on /try)

Both represent the same physical circuit as the /try sketch's SimEngine
config (LED on pin 13), so one definition keeps them from drifting apart.
"""

LED_DEMO_CIRCUIT = {
    "components": [
        {
            "id": "LED1", "type": "LED",
            "pins": {"anode": {"col": "E", "row": 12}, "cathode": {"col": "E", "row": 11}},
            "properties": {"color": "red"}
        },
        {
            "id": "R1", "type": "RESISTOR",
            "pins": {"pin1": {"col": "D", "row": 11}, "pin2": {"col": "D", "row": 7}},
            "properties": {"ohms": 220}
        }
    ],
    "connections": [
        {"from": "arduino.D13", "to": "breadboard.A12", "color": "#00AA00"},
        {"from": "breadboard.E7", "to": "arduino.GND", "color": "#111111"}
    ]
}
