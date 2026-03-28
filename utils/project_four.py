
from utils.step_builder import build_step, intro_step, rect, circle

META = {
    'title': 'Project 4: Space Station Launch Button',
    'circuit_image': 'static/graphics/project_four_circuit.png',
    'banner_image': None,
}

STEPS = [
    intro_step(
        "Let's build our fourth project",
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

DRAWER_CONTENT = {

    "project_four": {
    "title": "🚀 Space Station Launch",
    "tip": "Use a button to trigger a buzzer like a real rocket launch system.",
    "tabs": {
        "story": {
            "label": "👨‍🚀 Story",
            "content": """
<h3>Welcome to the Space Station! 🚀</h3>

<p>
Astronaut, today is a very important mission 👨‍🚀👩‍🚀
</p>

<p>
You are helping launch a rocket into space!
</p>

<p>
Inside the rocket is a powerful computer that watches everything and keeps the mission safe.
Wires run through the rocket like space roads, carrying important signals.
</p>

<p>
When it's time to launch...
</p>

<p>
👉 YOU press the launch button 🔘<br>
🚨 The system wakes up<br>
🔊 BEEEEEEEEEP! The launch alarm sounds!
</p>

<p>
This warns everyone — the rocket is about to lift off!
</p>

<p>
Get ready… <b>LAUNCH!</b> 🚀✨
</p>
"""
        },
        "code": {
            "label": "🖥️ Code",
            "content": """
<h3>The Launch Program</h3>

<pre>
void setup() {
  pinMode(8, OUTPUT);
  pinMode(2, INPUT_PULLUP);
}

void loop() {
  if (digitalRead(2) == LOW) {
    digitalWrite(8, HIGH);
  } else {
    digitalWrite(8, LOW);
  }
}
</pre>

<p>
This is the rocket’s control system.
</p>
"""
        },
        "logic": {
            "label": "🧩 Logic",
            "content": """
<h3>How the Rocket Thinks</h3>

<p>
The system constantly checks:
</p>

<p>
❓ "Is the launch button pressed?"
</p>

<p>
If YES → Sound the alarm 🔊🚨<br>
If NO → Stay quiet 😴
</p>

<p>
This happens over and over again, super fast — just like a real spacecraft computer!
</p>
"""
        },
        "translation": {
            "label": "🧬 Translation",
            "content": """
<h3>Space Code Translation</h3>

<p>
<b>setup()</b><br>
Pin 8 powers the rocket buzzer 🔊🚀<br>
Pin 2 listens for your launch button 👆
</p>

<p>
<b>loop()</b><br>
Check the button 👀
</p>

<p>
Pressed → Buzzer ON (engine roaring!) 🛸<br>
Not pressed → Buzzer OFF (rocket resting) 😴
</p>

<p>
The system repeats forever:<br>
Check → Decide → Sound → Repeat 🔁
</p>
"""
        }
    }
},
}
SKETCH_PRESET = {
    'sketch': """void setup() {
  pinMode(8, OUTPUT);
  pinMode(2, INPUT_PULLUP);
}

void loop() {
  if (digitalRead(2) == LOW) {
    digitalWrite(8, HIGH);
  } else {
    digitalWrite(8, LOW);
  }
}""",
    'default_view': 'editor'
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