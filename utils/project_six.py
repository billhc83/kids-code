from utils.step_builder import build_step, intro_step, rect, circle

PAGE_TITLE = "Project 6: Deep Sea Explorer"
CIRCUIT_IMAGE = "static/graphics/project_six_circuit.png"

STEPS = [
    intro_step(
        "Activate the submarine sensor!",
        "Press the next button for a step by step guide",
    ),
    build_step(
        "Place one leg of the photoresistor in row 15, column F.<br>"
        "Place the second leg of the photoresistor in row 18, column F",
        "This is the photoresistor — it is a light sensor.",
        circle(962, 309, radius=45),
        rect(773, 577, 1006, 662),
        greyout=True,
    ),
    build_step(
        "Place one end of the 10k resistor in row 11 column H.<br>"
        "Place the other end of the 10k resistor in row 15 column H",
        "Resistors come in many different sizes.",
        circle(745, 77, radius=55),
        rect(831, 260, 960, 303),
        greyout=True,
    ),
    build_step(
        "Place one end of the wire in the Arduino Pin GND.<br>"
        "Place the other end in row 11 column J",
        "Ground wires help complete our circuit loop.",
        rect(386, 230, 873, 315),
        greyout=True,
    ),
    build_step(
        "Place one end of the wire in the Arduino Pin A0.<br>"
        "Place the other end in row 15 column J",
        "This wire is listening for the signal from the light sensor.",
        rect(906, 210, 952, 265),
        rect(215, 208, 946, 246),
        rect(52, 208, 227, 513),
        greyout=True,
    ),
    build_step(
        "Place one end of the wire in Arduino Pin 5V.<br>"
        "Place the other end in row 18 column J",
        "This wire sends power to our submarine's light sensor.",
        rect(962, 172, 1010, 260),
        rect(600, 172, 1006, 214),
        rect(600, 6, 645, 214),
        rect(8, 0, 645, 50),
        rect(0, 12, 84, 408),
        greyout=True,
    ),
]