from utils.step_builder import build_step, intro_step, rect, circle, line

PAGE_TITLE = "Project 11: Engine System Start"
CIRCUIT_IMAGE = "static/graphics/project_twelve_circuit.png"

STEPS = [
    intro_step(
        "Engage Engines!!!!",
        "Press the next button for a step by step guide",
    ),
    build_step(
        "Place the center pin of the switch in row 4, column H.<br>"
        "Place the side pin of the switch in row 5, column H",
        "This is the Engine Armed switch. Nothing happens unless we arm the engines.",
        rect(601, 216, 719, 310),
    ),
    build_step(
        "Place the first leg in row 24, column E.<br>"
        "Place the second leg in row 23, column E.<br>"
        "Place the third leg in row 8 column E.<br>"
        "Place the last leg in row 10 column E",
        "This button starts the engine.",
        rect(719, 239, 811, 350),
    ),
    build_step(
        "Place the long leg of the buzzer in row 14, column E.<br>"
        "Place the short leg of the buzzer in row 14, column F",
        "This is our engine — press the start button to hear it come to life.",
        rect(799, 222, 909, 344),
        circle(922, 37),
        line((917, 56), (861, 248)),
        circle(1034, 563),
        line((1043, 550), (850, 314)),
    ),
    build_step(
        "Place the long leg of the LED in row 22, column E.<br>"
        "Place the short leg of the LED in row 21, column E",
        "This is the light that tells us the engines are armed and ready to start.",
        rect(935, 175, 1069, 347),
        line((919, 57), (995, 317)),
        line((1040, 542), (1011, 330)),
        circle(922, 44),
        circle(1043, 561),
    ),
    build_step(
        "Place one leg of the 220 Ohm resistor in row 21, column D.<br>"
        "Place the second leg of the resistor in row 17, column D",
        "The resistor slows down the electricity.",
        rect(871, 307, 1034, 384),
        circle(1047, 52),
        line((1038, 75), (952, 340)),
    ),
    build_step(
        "Place one end of the wire into Arduino Pin 9.<br>"
        "Place the other end in row 5 column I.",
        "This wire lets the Arduino see the position of the switch.",
        line((370, 340), (723, 341), (722, 209), (680, 208)),
    ),
    build_step(
        "Place one end of the wire into Arduino Pin 7.<br>"
        "Place the other end into row 8 column B",
        "This wire lets the Arduino see if the button is pressed.",
        line((372, 393), (752, 378)),
    ),
    build_step(
        "Place one end of the wire into Arduino Pin 5.<br>"
        "Place the other end of the wire into row 14 column D.<br>"
        "The side pin goes in row 24 column E",
        "This wire powers our engine.",
        line((370, 427), (858, 430), (855, 337)),
    ),
    build_step(
        "Place one end of the wire in the Arduino Pin 2.<br>"
        "Place the other end in row 22 column A",
        "This wire powers our Engines armed light.",
        line((364, 486), (537, 487), (536, 529), (1012, 532), (1007, 393)),
    ),
    build_step(
        "Place one end of the wire in Arduino Pin GND.<br>"
        "Place the other end in the negative / - rail",
        "This wire helps complete our circuit.",
        line((369, 244), (446, 251), (444, 113), (622, 118)),
    ),
    build_step(
        "Place one end of the wire in row 4 column J.<br>"
        "Place the other end in the negative / - rail",
        "This wire completes our switch circuit.",
        line((667, 199), (652, 110)),
    ),
    build_step(
        "Place one end of the wire in row 10 column J.<br>"
        "Place the other end in the negative / - rail",
        "This wire completes our button circuit.",
        line((783, 202), (768, 110)),
    ),
    build_step(
        "Place one end of the wire in row 14 column J.<br>"
        "Place the other end in the negative / - rail",
        "This wire completes our buzzer circuit.",
        line((860, 204), (843, 103)),
    ),
    build_step(
        "Place one end of the wire in row 17 column E.<br>"
        "Place the other end in the negative / - rail",
        "This wire completes our light circuit.",
        line((915, 331), (922, 106)),
    ),
]