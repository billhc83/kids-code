from utils.step_builder import build_step, intro_step, rect, circle

PAGE_TITLE = "Project 3: Mad Scientist Button Machine"
CIRCUIT_IMAGE = "static/graphics/project_three_circuit.png"

STEPS = [
    intro_step(
        "Let's light the energy crystal",
        "Press the next button for a step by step guide",
    ),
    build_step(
        "Place the LED long leg in row 12, column E.<br>"
        "Place the LED short leg in row 11, column E",
        "The long leg is positive — it's called the anode!",
        rect(733, 194, 903, 319),
        greyout=True,
    ),
    build_step(
        "Place one leg of the 220 ohm resistor in row 11, column D.<br>"
        "Place the second leg of the resistor in row 7, column D",
        "The resistor slows down the electricity.",
        rect(691, 307, 834, 368),
        circle(500, 161, radius=50),
        greyout=True,
    ),
    build_step(
        "Place the button onto the breadboard.<br>"
        "Button leg → row 18 e<br>"
        "Button leg → row 18 f<br>"
        "Button leg → row 20 e<br>"
        "Button leg → row 20 f",
        "The button will let us control the energy crystal.",
        rect(905, 224, 1010, 360),
        greyout=True,
    ),
    build_step(
        "Place one end of the wire in the Arduino Pin GND.<br>"
        "Place the other end in the negative / - rail",
        "The wires are like roads for electricity.",
        rect(328, 82, 639, 271),
        greyout=True,
    ),
    build_step(
        "Place one end of the wire in the Arduino Pin 8.<br>"
        "Place the other end in row 12 column A",
        "This wire sends the power to the energy crystal (light).",
        rect(357, 350, 838, 448),
        greyout=True,
    ),
    build_step(
        "Place one end of the wire in the Arduino Pin 2.<br>"
        "Place the other end in row 18 column A",
        "This wire is listening for the button to be pressed.",
        rect(929, 398, 952, 500),
        rect(382, 486, 952, 540),
        greyout=True,
    ),
    build_step(
        "Place one end of the wire in row 7 column E.<br>"
        "Place the other end in the negative / - rail",
        "This wire connects our circuit back to the Arduino.",
        rect(660, 101, 760, 340),
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