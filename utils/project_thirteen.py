from utils.step_builder import build_step, intro_step, rect, circle, line

PAGE_TITLE = "Project 13: The Reaction Timer"
CIRCUIT_IMAGE = "static/graphics/reaction_timer_circuit.png"

STEPS = [
    intro_step(
        "Measure Your Speed!",
        "Press the next button for a step-by-step guide to building your astronaut training device.",
    ),
    build_step(
        "Place the button onto the breadboard.<br>Place the legs into rows 8 and 10, columns E and F.",
        "Touch the button to start the timer. Press it again to stop it!",
        rect(708, 249, 818, 340),
        greyout=True,
    ),
    build_step(
        "Place one end of the wire in Arduino Pin 2.<br>Place the other end in row 8, column D.",
        "This is the signal for our timer button.",
        line((361, 493), (384, 487), (568, 342), (748, 345), width=20),
        greyout=True,
    ),
    build_step(
        "Place one end of the wire in row 10, column G.<br>Place the other end in the negative (-) rail.",
        "This completes our button loop.",
        line((787, 253), (768, 98), width=20),
        greyout=True,
    ),
    build_step(
        "Place one end of the wire in Arduino Pin GND.<br>Place the other end in the negative (-) rail.",
        "This helps complete our circuit loop.",
        # Coordinate for GND to Rail based on standard layout
        line((621, 113), (356, 249), width=20),
        greyout=True,
    ),
]