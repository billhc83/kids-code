from utils.step_builder import build_step, intro_step, rect, circle

PAGE_TITLE = "Project 10: The Spy Vault Security Console"
CIRCUIT_IMAGE = "static/graphics/project_ten_circuit.png"

STEPS = [
    intro_step(
        "Protect the Spy Vault",
        "Press the next button for a step by step guide",
    ),
    build_step(
        "Place the LED long leg in row 12, column E.<br>Place the LED short leg in row 11, column E",
        "The long leg is positive — it's called the anode!",
        rect(766, 231, 934, 390),
        greyout=True,
    ),
    build_step(
        "Place one leg of the 220 Ohm resistor in row 11, column D.<br>Place the second leg of the resistor in row 7, column D",
        "The resistor slows down the electricity",
        rect(733, 361, 879, 423),
        circle(540, 208, radius=60),
        greyout=True,
    ),
    build_step(
        "Place Switch 1 on the breadboard.<br>The centre pin goes in row 24 column E<br>The side pin goes in row 25 column E",
        "The switch acts like a key card",
        rect(1034, 280, 1150, 398),
        greyout=True,
    ),
    build_step(
        "Place Switch 2 on the breadboard.<br>The centre pin goes in row 17 column E<br>The side pin goes in row 18 column E",
        "The security locks turn on and off with the switches",
        rect(902, 290, 1013, 396),
        greyout=True,
    ),
    build_step(
        "Place one end of the wire in the Arduino Pin GND.<br>Place the other end in row 7 column E",
        "Ground wires help complete our circuit loop",
        rect(382, 282, 790, 385),
        greyout=True,
    ),
    build_step(
        "Connect Arduino GND to the negative rail.",
        "Ground wires help complete our circuit loop",
        rect(8, 0, 645, 50),
        rect(0, 12, 84, 415),
        rect(424, 0, 668, 184),
        greyout=True,
    ),
    build_step(
        "Place one end of the wire in Arduino Pin 8.<br>Place the other end in row 12 column A",
        "This wire powers our LED. Light On = Access Granted",
        rect(390, 392, 881, 502),
        greyout=True,
    ),
    build_step(
        "Place one end of the wire in Arduino Pin 3.<br>Place the other end in row 17 column A",
        "This is the signal wire for Switch 2",
        rect(924, 437, 979, 564),
        rect(410, 519, 975, 566),
        greyout=True,
    ),
    build_step(
        "Place one end of the wire in Arduino Pin 2.<br>Place the other end in row 24 column A",
        "This is the signal wire for Switch 1",
        rect(1062, 429, 1115, 590),
        rect(410, 542, 1115, 600),
        greyout=True,
    ),
    build_step(
        "Complete the switch loops to the negative rail.",
        "This wire completes our loop for the switches",
        rect(953, 135, 1046, 411),
        rect(1095, 141, 1174, 406),
        greyout=True,
    ),
]