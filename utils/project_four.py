from utils.step_builder import build_step, intro_step, rect, circle

PAGE_TITLE = "Project 4: Space Station Launch Button"
CIRCUIT_IMAGE = "static/graphics/project_four_circuit.png"

STEPS = [
    intro_step(
        "Activate the launch button!!",
        "Press the next button for a step by step guide",
    ),
    build_step(
        "Place the buzzer long leg in row 12, column E.<br>"
        "Place the buzzer short leg in row 12, column F",
        "This is the launch alarm.",
        circle(823, 287, radius=55),
        circle(846, 565, radius=55),
        circle(882, 55, radius=55),
        greyout=True,
    ),
    build_step(
        "Place the button onto the breadboard.<br>"
        "Button leg → row 18 column e<br>"
        "Button leg → row 18 column f<br>"
        "Button leg → row 20 column e<br>"
        "Button leg → row 20 column f",
        "The button will control the launch alarm.",
        rect(905, 224, 1010, 360),
        greyout=True,
    ),
    build_step(
        "Place one end of the wire in the Arduino Pin GND.<br>"
        "Place the other end in the negative / - rail",
        "The wires are like roads for electricity.",
        rect(352, 91, 648, 270),
        greyout=True,
    ),
    build_step(
        "Place one end of the wire in the Arduino Pin 8.<br>"
        "Place the other end in row 12 column A",
        "This wire sends the power to our launch alarm.",
        rect(376, 353, 846, 452),
        greyout=True,
    ),
    build_step(
        "Place one end of the wire in the Arduino Pin 2.<br>"
        "Place the other end in row 18 column A",
        "This wire is listening for the button to be pressed.",
        rect(905, 387, 960, 543),
        rect(369, 469, 924, 542),
        greyout=True,
    ),
    build_step(
        "Place one end of the wire in row 12 column J.<br>"
        "Place the other end in the negative / - rail",
        "This wire connects our circuit back to the Arduino.",
        rect(673, 100, 844, 219),
        greyout=True,
    ),
    build_step(
        "Place one end of the wire in row 20 column J.<br>"
        "Place the other end in the negative / - rail",
        "This wire completes our loop — it connects our button back to the Arduino.",
        rect(928, 95, 1013, 224),
        greyout=True,
    ),
]