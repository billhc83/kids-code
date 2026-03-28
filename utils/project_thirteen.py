
from utils.step_builder import build_step, intro_step, rect, circle, line

META = {
    'title': 'Project 13: The Reaction Timer',
    'circuit_image': 'static/graphics/reaction_timer_circuit.png',
    'banner_image': None,
}

STEPS = [
    intro_step(
        "Let's build our thirteenth project",
        "Press the next button for a step by step guide",
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

import base64
from pathlib import Path

def img_to_b64(path):
    data = Path(path).read_bytes()
    b64 = base64.b64encode(data).decode()
    ext = Path(path).suffix.lstrip(".")
    return f"data:image/{ext};base64,{b64}"

timer_circuit_b64 = img_to_b64("static/graphics/reaction_timer_circuit.png")

DRAWER_CONTENT = {

 "project_thirteen": {
    "title": "⏱️ Reaction Timer",
    "tip": "Measure how fast someone reacts using a button and timing in milliseconds.",
    "tabs": {
        "story": {
            "label": "🧪 Mission",
            "content": """
<h3>Welcome to the Arduino Reaction Lab! 🧪</h3>

<p>
Today, you will build a <b>reaction timer</b> — just like scientists use to measure reflexes.
</p>

<p>
Your mission:
</p>

<p>
🔘 Press the button as fast as you can<br>
⏱️ The Arduino will measure your reaction time<br>
💻 Watch the results on your computer
<p>
Ready… Set… React!
</p>
""",
                "image_b64": timer_circuit_b64
        },
        "code": {
            "label": "💻 Code",
            "content": """
<h3>The Reaction Timer Program</h3>

<pre>
int button = 2;

int running = 0;

unsigned long startTime = 0;
unsigned long time = 0;

void setup() {
  pinMode(button, INPUT_PULLUP);
  Serial.begin(9600);
}

void loop() {

  if (digitalRead(button) == LOW) {

    if (running == 0) {
      startTime = millis();
      running = 1;
    }
    else {
      time = millis() - startTime;
      Serial.println(time);
      running = 0;
    }

    delay(300);
  }

}
</pre>

<p>
This program measures the time between the first press and the next press of the button.
</p>
"""
        },
        "logic": {
            "label": "🧩 Logic",
            "content": """
<h3>How the Timer Thinks</h3>

<p>
The Arduino constantly:
</p>

<p>
🔘 Watches the button<br>
🤔 Checks if this is the first or second press<br>
⏱️ Measures elapsed time using <b>millis()</b><br>
💻 Sends the reaction time to the computer<br>
🔁 Waits for the next test
</p>

<p>
First press → Start timer<br>
Second press → Stop timer & record reaction
</p>
"""
        },
        "translation": {
            "label": "🧬 Translation",
            "content": """
<h3>Breaking Down the Code</h3>

<p>
<b>pinMode(button, INPUT_PULLUP)</b><br>
Configures the button as an input with a built-in pull-up resistor 🔘
</p>

<p>
<b>digitalRead(button)</b><br>
Reads if the button is pressed (LOW) or not pressed (HIGH)
</p>

<p>
<b>running</b><br>
Tracks whether the timer is running (0 = stopped, 1 = running) 🧩
</p>

<p>
<b>millis()</b><br>
Returns the number of milliseconds since the Arduino started ⏱️
</p>

<p>
<b>time = millis() - startTime</b><br>
Calculates elapsed time between first and second press
</p>

<p>
<b>Serial.println(time)</b><br>
Displays the reaction time on the computer 💻
</p>

<p>
<b>delay(300)</b><br>
Prevents accidental double counting from bouncing button presses ⏱️
</p>
"""
        }
    }
 }
}

SKETCH_PRESET = {
    'sketch': """
int button = 2;

int running = 0;

unsigned long startTime = 0;
unsigned long time = 0;

void setup() {
  pinMode(button, INPUT_PULLUP);
  Serial.begin(9600);
}

void loop() {

  if (digitalRead(button) == LOW) {

    if (running == 0) {
      startTime = millis();
      running = 1;
    }
    else {
      time = millis() - startTime;
      Serial.println(time);
      running = 0;
    }

    delay(300);
  }

}""",
    'default_view': 'editor',
    'fill_conditions': True,
        'fill_values': False,
}

CHALLENGE_PRESET = {
    'sketch': '...',
    'default_view': 'editor',
}

# Optional — progression sketch for guided block builder projects
PROGRESSION_PRESET = {
    'sketch': '...',  # contains //>> markers
}
PROJECT = {
    "meta": META,
    "steps": STEPS,
    "drawer": DRAWER_CONTENT,
    "presets": {
        "default": SKETCH_PRESET,
        "challenge": CHALLENGE_PRESET,
        "progression": PROGRESSION_PRESET,
    }
}