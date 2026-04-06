from utils.step_builder import build_step, intro_step, rect, circle

META = {
    'title': 'Project 3: Mad Scientist Button Machine',
    'circuit_image': 'static/graphics/project_three_circuit.png',
    'banner_image': None,
}

STEPS = [
    intro_step(
        "Let's build our third project",
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

DRAWER_CONTENT = {

    "project_three": {
    "title": "🧪 Mad Scientist Lab",
    "tip": "Use a button to control your light like a powerful energy experiment.",
    "tabs": {
        "story": {
            "label": "🧠 Story",
            "content": """
<h3>Welcome to the Mad Scientist Laboratory! 🧠⚡</h3>

<p>
Strange machines are buzzing… wires are glowing… and something amazing is about to happen!
</p>

<p>
In this experiment, <b>YOU</b> are the mad scientist 😈
</p>

<p>
Your mission:
</p>

<p>
👉 Press the button — The crystal wakes up and the light turns ON 💡<br>
✋ Let go — The crystal goes back to sleep 😴
</p>

<p>
You are teaching the machine to <b>listen to you</b>.
</p>

<p>
Press = ON<br>
Release = OFF
</p>

<p>
Mwahahaha! You are in control of the experiment! 🧪⚡
</p>
"""
        },
        "code": {
            "label": "🖥️ Code",
            "content": """
<h3>The Experiment Code</h3>

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
This is the rule book your machine follows.
</p>
"""
        },
        "logic": {
            "label": "🧩 Logic",
            "content": """
<h3>How the Machine Thinks</h3>

<p>
The Arduino is constantly asking:
</p>

<p>
❓ "Is the button pressed?"
</p>

<p>
If YES → Turn the light ON 💡<br>
If NO → Turn the light OFF 🌑
</p>

<p>
This decision happens over and over again, super fast!
</p>
"""
        },
        "translation": {
            "label": "🧬 Translation",
            "content": """
<h3>Scientist Code Translation</h3>

<p>
<b>pinMode(8, OUTPUT);</b><br>
Door 8 sends electricity to the crystal 💡
</p>

<p>
<b>pinMode(2, INPUT_PULLUP);</b><br>
Door 2 listens for the button 🔘
</p>

<p>
<b>digitalRead(2)</b><br>
Is the button pressed?<br>
LOW = pressed 😄<br>
HIGH = not pressed 😴
</p>

<p>
<b>digitalWrite(8, HIGH);</b><br>
Turn the crystal ON! 💥
</p>

<p>
<b>digitalWrite(8, LOW);</b><br>
Turn the crystal OFF 🌑
</p>

<p>
<b>The loop</b><br>
Runs forever like a bubbling experiment 🧪♻️<br>
Check → Decide → Glow → Repeat!
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
    'default_view': 'editor',
    'read_only': True,
    'lock_view': True,
    'fill_values': True,
    'fill_conditions': True,
}

CHALLENGE_PRESET = {
    'sketch': '...',
    'default_view': 'builder',
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