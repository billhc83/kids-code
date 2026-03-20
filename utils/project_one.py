from utils.step_builder import build_step, intro_step, rect, circle

PAGE_TITLE = "Project 1: Lights ON!!"
CIRCUIT_IMAGE = "static/graphics/project_one_circuit.png"

STEPS = [
    intro_step(
        "Let's build our first project",
        "Press the next button for a step by step guide",
    ),
    build_step(
        "Place the LED long leg in row 12, column E.<br>"
        "Place the LED short leg in row 11, column E",
        "The long leg is positive — it's called the anode!",
        rect(708, 175, 899, 331),
        greyout=True,
    ),
    build_step(
        "Place one leg of the 220 ohm resistor in row 11, column D.<br>"
        "Place the second leg of the resistor in row 7, column D",
        "The resistor slows down the electricity.",
        rect(693, 324, 825, 363),
        circle(492, 154, radius=60),
        greyout=True,
    ),
    build_step(
        "Place one end of the wire in the Arduino GND Pin.<br>"
        "Place the other end in row 7, column E",
        "The wires are like roads for electricity.",
        rect(375, 231, 740, 339),
        greyout=True,
    ),
    build_step(
        "Place one end of the wire in the Arduino Pin 8.<br>"
        "Place the other end in row 12, column A",
        "The wires are like roads for electricity.",
        rect(346, 350, 844, 453),
        greyout=True,
    ),
]