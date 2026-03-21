from utils.step_builder import build_step, intro_step, rect, circle, line, lbl

PAGE_TITLE = "Project 12: Night Patrol Alarm"
CIRCUIT_IMAGE = "static/graphics/project_thirteen_circuit.png"
BANNER_IMAGE = "static/graphics/patrol_alarm.png"

STEPS = [
    intro_step(
        "Lets Light This Car UP!!!",
        "Press the next button for a step by step guide",
    ),
    build_step(
        "Place the long leg of the LED in row 18, column E.<br>Place the short leg in row 17, column E",
        "Make sure your lights are in the right order.",
        rect(876, 175, 971, 344),
    ),
    build_step(
        "Place the long leg of the LED in row 24, column E.<br>Place the short leg in row 23, column E.",
        "Red, then Blue!",
        rect(994, 181, 1083, 347),
    ),
    build_step(
        "Place the long leg of the LED in row 30, column E.<br>Place the short leg in row 29, column E",
        "The Clear Strobe goes last.",
        rect(1093, 168, 1203, 343),
    ),
    build_step(
        "Add the 220 ohm resistors for each LED to protect them.",
        "Resistors slow down the electricity.",
        rect(805, 318, 940, 376),
        rect(929, 305, 1056, 376),
        rect(1047, 300, 1171, 370),
    ),
    build_step(
        "Place the button onto the breadboard across the center gap.",
        "This is the Master Power Button.",
        rect(719, 244, 812, 347),
    ),
    build_step(
        "Wire the LEDs to Pins 8, 6, and 4.",
        "Red = Pin 8, Blue = Pin 6, Clear = Pin 4.",
        line((366, 358), (933, 364)),
        line((1048, 401), (364, 411)),
        line((1165, 399), (370, 449)),
    ),
    build_step(
        "Wire the Button to Pin 12.",
        "This wire sends the signal to the Arduino.",
        line((749, 347), (366, 284)),
    ),
    build_step(
        "Complete the Ground (GND) connections.",
        "Finish the circuit loop to the negative rail.",
        line((621, 113), (356, 249)),
        line((788, 263), (766, 106)),
        line((844, 337), (806, 106)),
        line((956, 333), (962, 111)),
        line((1075, 336), (1078, 103)),
    ),
]