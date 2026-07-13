from utils.step_builder import build_step, intro_step, rect, circle
from utils.affiliate_kits import BASIC_KITS


META = {
    'title': 'Project 1: Lights ON!!',
    'circuit_image': 'static/graphics/project_one_circuit.png',
    'banner_image': 'project_one_banner.png',
    'required_kits': BASIC_KITS,
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
<p>Imagine your Arduino is a tiny robot brain 🤖<br>The pins are how it interacts with the world — like arms, ears, and a mouth!</p>
<p>Without pins, the brain would just sit there thinking.<br>Pins let it <b>sense</b> and <b>act</b>.</p>

<h4>👂 The "Ear" Pins (Inputs)</h4>
<p>These pins <b>listen</b> to the world:</p>
<p>❓ Is someone pressing my button?<br>❓ Is it dark in this room?<br>❓ Is there something moving nearby?</p>

<h4>🗣️ The "Mouth" Pins (Outputs)</h4>
<p>These pins <b>talk</b> to your components:</p>
<p>💡 Turn on the light!<br>⚙️ Spin the motor!<br>🎵 Beep-beep!</p>

<h4>Two Ways to Talk</h4>
<p><b>1️⃣ On or Off (Digital)</b><br>Like a light switch — YES or NO 💡</p>
<p><b>2️⃣ A Little Bit (PWM)</b><br>Like a volume knob — dim lights or slow motors 🔉</p>

<hr>
<h4>🔌 This Project's Pin</h4>
<p>Your LED talks to Arduino through <b>Pin 8</b>.<br>Pin 8 is a Mouth pin — it sends power out to turn your light ON! 💡</p>
"""
        },
        "code": {
            "label": "🖥️ Code",
            "content": """
<h3>Your First Sketch — The Rule Book 📖</h3>
<p>Your Arduino code is called a <b>Sketch</b>.<br>It’s the rule book your robot brain follows!</p>
<p>This is your very first project, so we already typed the whole Sketch for you.<br>Let's peek inside and see what it says!</p>

<h4>Your Sketch, Line by Line</h4>
<p><b>pinMode(8, OUTPUT);</b><br>This gets Pin 8 ready to be a Mouth pin, so it can send power out. 🗣️</p>
<p><b>digitalWrite(8, HIGH);</b><br>This tells Pin 8 "Send power now!" — and your LED lights up! 💡</p>

<h4>How It Works</h4>
<p>Every sketch has three main parts:</p>
<p><b>Global</b><br>Sits at the very top, above everything else.<br>This is where you'd keep labels you need everywhere — this project doesn't need any yet!</p>
<p><b>setup()</b><br>Runs once when the Arduino starts.<br>This is where <b>pinMode(8, OUTPUT);</b> gets Pin 8 ready.</p>
<p><b>loop()</b><br>Runs again and again forever.<br>This is where <b>digitalWrite(8, HIGH);</b> keeps telling your LED to stay on.</p>
<p>Want to know what those words actually mean? Check the 🔤 <b>Words to Know</b> tab!</p>
"""
        },
        "words": {
            "label": "🔤 Words to Know",
            "content": """
<h3>🔤 Words to Know</h3>
<p>New words in your Sketch? Let's crack the code! 🕵️</p>

<h4>pinMode</h4>
<p>This tells Arduino "get this pin ready!"<br>It's like putting on your shoes before you run. 👟</p>

<h4>OUTPUT</h4>
<p>This means "this pin will send power out."<br>It's a Mouth pin, ready to talk! 🗣️</p>

<h4>digitalWrite</h4>
<p>This tells a pin exactly what to do right now.<br>It's like flipping a light switch. 🔦</p>

<h4>HIGH</h4>
<p>This means "turn ON! Send power now!" ⚡<br>The opposite is LOW, which means "turn OFF."</p>
"""
        },
        "sim": {
            "label": "🎮 Try It",
            "type": "sim",
            "sim_config": {
                "mode": "code_driven",
                "pins": {"8": {"type": "led", "color": "red", "label": "LED"}},
                "loop_iterations": 1,
                "max_ms": 4000,
            }
        },
        "upload": {
            "label": "🚀 Let's Go!",
            "content": """
<h3>This Is Your First Project — Here's Exactly What To Do! 🚀</h3>
<p>No worries if this is all brand new. Just follow these steps in order.</p>

<h4>1️⃣ Build the circuit</h4>
<p>Use the <b>Build</b> tab to place your LED, resistor, and wires.<br>Follow each step — you don't need your Arduino plugged in yet.</p>

<h4>2️⃣ Check out your Sketch 📖</h4>
<p>The code you see is your <b>Sketch</b> — the rule book we just talked about.<br>It's already written for you! Right now, your job is just to send it to your Arduino.</p>

<h4>3️⃣ Plug in your Arduino 🔌</h4>
<p>Once the circuit is built, plug your Arduino into the computer with its USB cable.</p>

<h4>4️⃣ Look for KidsCode Link 🔗</h4>
<p>Check for <b>● KidsCode Link</b> near your Sketch.<br>If it says <b>Offline</b>, open the KidsCode Link app on your computer, then look again.</p>

<h4>5️⃣ Pick your board 🎯</h4>
<p>Open the dropdown menu and make sure your Arduino is selected.<br>Don't see it? Click <b>Refresh</b> and check again.</p>

<h4>6️⃣ Click Upload ⬆️</h4>
<p>Press the <b>Upload</b> button and watch the messages — they'll let you know when your code has made it onto the Arduino.</p>

<h4>7️⃣ Watch for the light! 💡</h4>
<p>If everything worked, your LED should turn on! If it doesn't, that's okay — check the <b>Tips</b> or ask for help. Every builder hits a snag sometimes!</p>
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
    'default_view': 'editor',
    'read_only': False,
    'lock_view': True,
    'fill_values': True,
    'fill_conditions': True,

}

CHALLENGE_PRESET = {
    'sketch': '...',
    'default_view': 'editor',
}

# Optional — progression sketch for guided block builder projects
PROGRESSION_PRESET = {
    'sketch': '...',  # contains //>> markers
}


CHIPS = [
    "My LED won't light up",
    "My resistor between 11D-7D may be wrong",
    "My GND wire at row 7E feels loose",
    "My Pin 8 wire at row 12A isn't secure",
    "My LED legs in 12E/11E might be swapped",
]

CIRCUIT_SPEC = {
    "meta": {
        "title": "LED Blink",
        "difficulty": "beginner",
    },
    "components": [
        {"id": "LED", "type": "LED", "properties": {"color": "red"}},
    ],
    "connections": [
        {"from": "arduino.D8",   "to": "LED.anode"},
        {"from": "R_LED.pin2",   "to": "arduino.GND"},
    ],
}

PROJECT = {
    "meta": META,
    "steps": STEPS,
    "drawer": DRAWER_CONTENT,
    "chips": CHIPS,
    "presets": {
        "default": SKETCH_PRESET,
        "challenge": CHALLENGE_PRESET,
        "progression": PROGRESSION_PRESET,
    },
    "circuit_spec": CIRCUIT_SPEC,
}