from utils.step_builder import build_step, intro_step, rect, circle


META = {
    'title': 'Project 1: Lights ON!!',
    'circuit_image': 'static/graphics/project_one_circuit.png',
    'banner_image': None,
}

STEPS = [
    intro_step(
        "Let's build our first project",
        "Press the next button for a step by step guide",
    ),
    build_step(
        "Place the LED long leg in row 12, column E.<br>"
        "Place the LED short leg in row 11, column E",
        "The long leg is positive — it's called the anode!",
        rect(708, 175, 899, 331),
        greyout=True,
    ),
    build_step(
        "Place one leg of the 220 ohm resistor in row 11, column D.<br>"
        "Place the second leg of the resistor in row 7, column D",
        "The resistor slows down the electricity.",
        rect(693, 324, 825, 363),
        circle(492, 154, radius=60),
        greyout=True,
    ),
    build_step(
        "Place one end of the wire in the Arduino GND Pin.<br>"
        "Place the other end in row 7, column E",
        "The wires are like roads for electricity.",
        rect(375, 231, 740, 339),
        greyout=True,
    ),
    build_step(
        "Place one end of the wire in the Arduino Pin 8.<br>"
        "Place the other end in row 12, column A",
        "The wires are like roads for electricity.",
        rect(346, 350, 844, 453),
        greyout=True,
    ),
]

DRAWER_CONTENT = {

    "project_one": {
    "title": "💭 New Ideas: Pins & Code",
    "tip": "Understand how your Arduino connects to the world and follows instructions.",
    "tabs": {
        "pins": {
            "label": "🤖 Pins",
            "content": """
<h3>Meet the Pins — Your Arduino's Body!</h3>

<p>
Imagine your Arduino is a tiny robot brain 🤖<br>
The pins are how it interacts with the world — like arms, ears, and a mouth!
</p>

<p>
Without pins, the brain would just sit there thinking.<br>
Pins let it <b>sense</b> and <b>act</b>.
</p>

<h4>👂 The "Ear" Pins (Inputs)</h4>
<p>
These pins <b>listen</b> to the world:
</p>
<p>
❓ Is someone pressing my button?<br>
❓ Is it dark in this room?<br>
❓ Is there something moving nearby?
</p>

<h4>🗣️ The "Mouth" Pins (Outputs)</h4>
<p>
These pins <b>talk</b> to your components:
</p>
<p>
💡 Turn on the light!<br>
⚙️ Spin the motor!<br>
🎵 Beep-beep!
</p>

<h4>Two Ways to Talk</h4>
<p>
<b>1️⃣ On or Off (Digital)</b><br>
Like a light switch — YES or NO 💡
</p>

<p>
<b>2️⃣ A Little Bit (PWM)</b><br>
Like a volume knob — dim lights or slow motors 🔉
</p>
"""
        },
        "code": {
            "label": "🖥️ Code",
            "content": """
<h3>Your First Sketch — The Rule Book 📖</h3>

<p>
Your Arduino code is called a <b>Sketch</b>.<br>
It’s the rule book your robot brain follows!
</p>

<p>
Think of it like a recipe or a checklist:
</p>

<p>
📋 First, I gather my tools<br>
(Setting up the pins)
</p>

<p>
📋 Next, I do my work<br>
(Turning lights on, moving motors)
</p>

<p>
📋 Then, I repeat forever<br>
(The Arduino keeps running the same rules)
</p>

<h4>How It Works</h4>
<p>
Every sketch has two main parts:
</p>

<p>
<b>setup()</b><br>
Runs once when the Arduino starts.<br>
This is where you prepare everything.
</p>

<p>
<b>loop()</b><br>
Runs again and again forever.<br>
This is where your robot does its job.
</p>

<p>
Think of it like this:
</p>

<p>
Start → Prepare → Work → Repeat 🔁
</p>
"""
        }
    }
}
}

SKETCH_PRESET = {
    'sketch': """void setup() {
  pinMode(8, OUTPUT);
}

void loop() {
  digitalWrite(8, HIGH);
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