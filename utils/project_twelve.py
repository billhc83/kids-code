

from utils.step_builder import build_step, intro_step, rect, circle, line

META = {
    'title': 'Project 12: Night Patrol Alarm',
    'circuit_image': 'static/graphics/project_thirteen_circuit.png',
    'banner_image': "static/graphics/patrol_alarm.png",
}

STEPS = [
    intro_step(
        "Let's build our twelfth project",
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

import base64
from pathlib import Path

def img_to_b64(path):
    data = Path(path).read_bytes()
    b64 = base64.b64encode(data).decode()
    ext = Path(path).suffix.lstrip(".")
    return f"data:image/{ext};base64,{b64}"

patrol_alarm_b64 = img_to_b64("static/graphics/project_thirteen_circuit.png")

DRAWER_CONTENT = {

 "project_twelve": {
        "title": "📘 Light Bar Control Guide",
        "tip": "Build the flashing pattern that controls the patrol light bar.",
        "tabs": {
            "mission": {
                "label": "🧠 Mission",
                "content": """
<h3>You are building the patrol vehicle light bar system.</h3>
<p>The light bar must flash in a clear pattern so people can see the vehicle at night.</p>
<p>
- The switch controls the whole system.<br>
- If the button is OFF → all lights stay OFF.<br>
- If the button is ON (pressed) → the flashing pattern begins.<br>
- The lights flash one at a time.<br>
- The pattern repeats again and again.
</p>
<p>Each light flash must use a short pause.<br>
At Night Patrol Academy we use: <b>delay(150)</b><br>
Use this delay after each light turns ON and turns OFF.</p>
<p>Your job is to build the flashing pattern using blocks.</p>
""",
                "image_b64": patrol_alarm_b64
            },
            "wiring": {
                "label": "🔌 Wiring",
                "content": """
<b>Match each part to its pin:</b><br><br>
🔘 Master Button → Pin 12<br>
🔴 Red Light → Pin 8<br>
🔵 Blue Light → Pin 6<br>
⚪ Clear Strobe Light → Pin 4<br><br>
Find the part in the diagram.<br>
Follow the wire.<br>
Match it to the pin.
"""
            },
            "logic": {
                "label": "🧩 Logic",
                "content": """
<b>🔘 Button Input Rule</b><br><br>
If the Button connects to GND, choose:<br>
<b>INPUT_PULLUP</b><br><br>
<b>Understanding the Button:</b><br><br>
HIGH = Button OFF (not pressed)<br>
LOW = Button ON (pressed)<br><br>
<b>Think about the pattern:</b><br><br>
IF button is ON (pressed)<br>
&nbsp;&nbsp;&nbsp;&nbsp;Red ON → delay → Red OFF<br>
&nbsp;&nbsp;&nbsp;&nbsp;Blue ON → delay → Blue OFF<br>
&nbsp;&nbsp;&nbsp;&nbsp;Clear ON → delay → Clear OFF<br><br>
IF button is OFF (else)<br>
&nbsp;&nbsp;&nbsp;&nbsp;All lights OFF<br><br>
Remember: The button controls everything.
"""
            }
        }
    }
}

SKETCH_PRESET = {
    'sketch': """
int switchPin = 12;

int redLED = 8;
int blueLED = 6;
int clearLED = 4;

void setup()
{
  pinMode(switchPin, INPUT_PULLUP);
  pinMode(redLED, OUTPUT);
  pinMode(blueLED, OUTPUT);
  pinMode(clearLED, OUTPUT);
}

void loop()
{
  if (digitalRead(switchPin) == LOW)
  {
    // Red flash
    digitalWrite(redLED, HIGH);
    delay(150);
    digitalWrite(redLED, LOW);

    // Blue flash
    digitalWrite(blueLED, HIGH);
    delay(150);
    digitalWrite(blueLED, LOW);

    // Clear flash
    digitalWrite(clearLED, HIGH);
    delay(150);
    digitalWrite(clearLED, LOW);
  }
  else
  {
    // Switch OFF → everything OFF
    digitalWrite(redLED, LOW);
    digitalWrite(blueLED, LOW);
    digitalWrite(clearLED, LOW);
  }
}""",
    'default_view': 'blocks',
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