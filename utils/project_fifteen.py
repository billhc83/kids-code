from utils.step_builder import build_step, intro_step, rect, circle, line, lbl

PAGE_TITLE = "Project X: Title"
CIRCUIT_IMAGE = "static/graphics/project_fifteen_circuit.png"

STEPS = [
    build_step("",
                ""),

    build_step(
        "Place the long leg of the LED in row 6, column E.<br>Place the short leg of the LED in row 5, column E.",
        "LED stands for light emitting diode.",
        rect(793, 291, 1039, 524),
        labels=[lbl("Long", pos=(959, 490), font_size=16), lbl("Short", pos=(808, 493), font_size=16)],
        greyout=True,
    ),

    build_step(
        "Place the long leg of the LED in row 12, column E.<br>Place the short leg of the LED in row 11, column E.",
        "LED's only work in one direction. Thats why we make sure the short and long leg are in the right spot.",
        rect(954, 296, 1209, 519),
        labels=[lbl("Long", pos=(1115, 495), font_size=16), lbl("Short", pos=(966, 493), font_size=16)],
        greyout=True,
    ),

    build_step(
        "Place the long leg of the LED in row 18, column E.<br>Place the short leg of the LED in row 17, column E.",
        "LED Lifespan, these mini lights can last over 25,000 hours",
        rect(1118, 313, 1370, 534),
        labels=[lbl("Long", pos=(1284, 505), font_size=16), lbl("Short", pos=(1130, 502), font_size=16)],
        greyout=True,
    ),

    build_step(
        "Place one leg of the __ resistor in row 1, column D.<br>Place the other leg in row 5, column D.",
        "Resistors have a color code to show their value!",
        rect(736, 493, 947, 625),
        labels=[lbl("220 Ohm", pos=(776, 599), font_size=16)],
        greyout=True,
    ),

    build_step(
        "Place one leg of the __ resistor in row 7, column D.<br>Place the other leg in row 11, column D.",
        "Each color represents a number, which helps us understand how much resistance a resistor has",
        rect(923, 486, 1108, 630),
        labels=[lbl("220 Ohm", pos=(957, 608), font_size=16)],
        greyout=True,
    ),

    build_step(
        "Place one leg of the __ resistor in row 13, column D.<br>Place the other leg in row 17, column D.",
        "The bigger the resistance, the harder it is for electricity to pass!",
        rect(1089, 469, 1260, 632),
        greyout=True,
    ),

    build_step(
        "Place the VCC pin of the distance sensor in row 23 column H"
        "Place the Gnd pin of the distance sensor in row 26 column H",
        rect(1171, 99, 1671, 404),
        greyout=True,
    ),

    build_step(
        "Place one end of the wire in Arduino Pin GND.<br>Place the other end in row 26, column F.",
        "",
        line((476, 353), (541, 353), (688, 252), (1587, 250), (1584, 430), (1469, 430), width=10),
        greyout=True,
    ),

    build_step(
        "Place one end of the wire in Arduino Pin 5V.<br>Place the other end in row 23, column F.",
        "",
        line((12, 476), (639, 428), (1397, 428), width=10),
        greyout=True,
    ),

    build_step(
        "Place one end of the wire in Arduino Pin 10.<br>Place the other end in row 25, column F.",
        "",
        line((490, 457), (1450, 459), (1450, 426), width=10),
        greyout=True,
    ),

    build_step(
        "Place one end of the wire in Arduino Pin 9.<br>Place the other end in row 24, column F.",
        "",
        line((493, 483), (1421, 483), (1418, 423), width=10),
        greyout=True,
    ),

    build_step(
        "Place one end of the wire in Arduino Pin 6.<br>Place the other end in row 6, column A.",
        "",
        line((512, 582), (935, 584), (935, 625), width=10),
        greyout=True,
    ),

    build_step(
        "Place one end of the wire in Arduino Pin 5.<br>Place the other end in row 12, column A.",
        "",
        line((500, 611), (654, 611), (654, 750), (1096, 748), (1094, 615), width=10),
        greyout=True,
    ),

    build_step(
        "Place one end of the wire in Arduino Pin 4.<br>Place the other end in row 18, column A.",
        "",
        line((507, 635), (625, 637), (627, 777), (1267, 779), (1260, 611), width=10),
        greyout=True,
    ),

    build_step(
        "Place one end of the wire in Arduino Pin GND.<br>Place the other end in the negative / - rail.",
        "",
        line((17, 524), (361, 700), (810, 702), width=10),
        greyout=True,
    ),

    build_step(
        "Place one end of the wire in row 1, column A.<br>Place the other end in the negative / - rail.",
        "",
        line((793, 608), (839, 700), width=10),
        greyout=True,
    ),

    build_step(
        "Place one end of the wire in row 7, column A.<br>Place the other end in the negative / - rail.",
        "",
        line((959, 613), (1005, 702), width=10),
        greyout=True,
    ),

    build_step(
        "Place one end of the wire in row 18, column A.<br>Place the other end in the negative / - rail.",
        "",
        line((1115, 611), (1168, 707), width=10),
        greyout=True,
    ),

]