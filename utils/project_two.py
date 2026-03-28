from utils.step_builder import build_step, intro_step, rect, circle


META = {
    'title': 'Project 2: Blinking Beacon',
    'circuit_image': 'static/graphics/project_one_circuit.png',
    'banner_image': None,
}

STEPS = [
    intro_step(
        "Let's build our second project",
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

    "project_two": {
    "title": "🚨 Blinking Beacon",
    "tip": "Learn how to make your light turn on and off over and over again.",
    "tabs": {
        "goal": {
            "label": "🎯 Goal",
            "content": """
<h3>Your Mission</h3>

<p>
🚨 Make your light blink on and off like a lighthouse! 🚨
</p>

<p>
Your Arduino will:
</p>

<p>
💡 Turn the light ON<br>
⏱️ Wait<br>
🌑 Turn the light OFF<br>
⏱️ Wait<br>
🔁 Repeat forever!
</p>
"""
        },
        "timing": {
            "label": "⏱️ Timing",
            "content": """
<h3>The "Wait" Command</h3>

<p>
Imagine playing <b>"Red Light, Green Light"</b>.<br>
When you hear "Red Light"... you FREEZE!
</p>

<p>
The Arduino does the same thing using:
</p>

<p>
<b>delay()</b>
</p>

<p>
This tells the robot brain to stop and do nothing for a short time.
</p>

<p>
<b>Examples:</b><br>
delay(1000) = Wait 1 second<br>
delay(500) = Wait half a second (faster blinking!)
</p>
"""
        },
        "loop": {
            "label": "🔄 Loop",
            "content": """
<h3>The "Forever" Loop</h3>

<p>
The <b>loop()</b> is like a hamster wheel 🐹<br>
It never stops running!
</p>

<p>
The Arduino:
</p>

<p>
1️⃣ Turns the light ON 💡<br>
2️⃣ Waits ⏱️<br>
3️⃣ Turns the light OFF 🌑<br>
4️⃣ Waits ⏱️<br>
5️⃣ Jumps back to the top 🔁
</p>

<p>
This is how blinking happens — over and over again!
</p>
"""
        },
        "logic": {
            "label": "💡 Logic",
            "content": """
<h3>The Code Secret</h3>

<p>
<b>digitalWrite(8, LOW);</b>
</p>

<p>
In your first project, you used <b>HIGH</b> to turn the light ON.<br>
Now you're using <b>LOW</b> to turn it OFF.
</p>

<p>
<b>HIGH</b> = Electricity flows (Light ON 💡)<br>
<b>LOW</b> = Electricity stops (Light OFF 🌑)
</p>

<p>
Think of it like a water tap 🚰:<br>
HIGH = Water ON<br>
LOW = Water OFF
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
  delay(500);

  digitalWrite(8, LOW);
  delay(500);
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