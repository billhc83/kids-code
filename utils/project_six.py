from utils.step_builder import build_step, intro_step, rect, circle

META = {
    'title': 'Project 6: Deep Sea Explorer',
    'circuit_image': 'static/graphics/project_six_circuit.png',
    'banner_image': None,
}

STEPS = [
    intro_step(
        "Let's build our fourth project",
        "Press the next button for a step by step guide",
    ),
    build_step(
        "Place one leg of the photoresistor in row 15, column F.<br>"
        "Place the second leg of the photoresistor in row 18, column F",
        "This is the photoresistor — it is a light sensor.",
        circle(962, 309, radius=45),
        rect(773, 577, 1006, 662),
        greyout=True,
    ),
    build_step(
        "Place one end of the 10k resistor in row 11 column H.<br>"
        "Place the other end of the 10k resistor in row 15 column H",
        "Resistors come in many different sizes.",
        circle(745, 77, radius=55),
        rect(831, 260, 960, 303),
        greyout=True,
    ),
    build_step(
        "Place one end of the wire in the Arduino Pin GND.<br>"
        "Place the other end in row 11 column J",
        "Ground wires help complete our circuit loop.",
        rect(386, 230, 873, 315),
        greyout=True,
    ),
    build_step(
        "Place one end of the wire in the Arduino Pin A0.<br>"
        "Place the other end in row 15 column J",
        "This wire is listening for the signal from the light sensor.",
        rect(906, 210, 952, 265),
        rect(215, 208, 946, 246),
        rect(52, 208, 227, 513),
        greyout=True,
    ),
    build_step(
        "Place one end of the wire in Arduino Pin 5V.<br>"
        "Place the other end in row 18 column J",
        "This wire sends power to our submarine's light sensor.",
        rect(962, 172, 1010, 260),
        rect(600, 172, 1006, 214),
        rect(600, 6, 645, 214),
        rect(8, 0, 645, 50),
        rect(0, 12, 84, 408),
        greyout=True,
    ),
]

DRAWER_CONTENT = {

    "project_six": {
    "title": "🤿 Deep Sea Explorer",
    "tip": "Use a light sensor to detect brightness and send data to your computer.",
    "tabs": {
        "story": {
            "label": "🚢 Mission",
            "content": """
<h3>🚢 Welcome aboard the S.S. Arduino! ⚓</h3>

<p>
Crew, today we dive deep into the ocean 🌊
</p>

<p>
We are entering the <b>Midnight Zone</b> — a place where sunlight cannot reach 🌑
</p>

<p>
As we descend:
</p>

<p>
☀️ Bright = Near the surface<br>
🌑 Dark = Deep ocean… maybe near a Giant Squid! 🦑✨
</p>

<p>
Your submarine has a special sensor 👁️‍🗨️<br>
It can detect how bright or dark it is.
</p>

<p>
Your mission:
</p>

<p>
🔍 Watch the light levels<br>
💻 Read the data on your screen<br>
🌊 Discover how deep you've gone!
</p>

<p>
Lights on, crew… Let's dive! 🤿⚓
</p>
"""
        },
        "code": {
            "label": "📜 Code",
            "content": """
<h3>The Navigation Script</h3>

<pre>
void setup() {
  Serial.begin(9600);
  Serial.println("--- SUBMARINE POWER ON ---");
}

void loop() {
  int oceanLight = analogRead(A0);

  Serial.print("Light Level: ");
  Serial.println(oceanLight);

  if (oceanLight > 400) {
    Serial.println("☀️ SURFACE: I see dolphins! 🐬");
  } else {
    Serial.println("🐙 MIDNIGHT ZONE: Watch for tentacles! ✨");
  }

  delay(600);
}
</pre>

<p>
This program reads the ocean light and reports your depth.
</p>
"""
        },
        "logic": {
            "label": "🧩 Logic",
            "content": """
<h3>How the Submarine Thinks</h3>

<p>
The system constantly:
</p>

<p>
🔢 Reads the light level<br>
💬 Sends the number to the screen<br>
🤔 Decides if it's bright or dark<br>
📡 Sends a message about where you are<br>
🔁 Repeats
</p>

<p>
It's like a real submarine checking its surroundings!
</p>
"""
        },
        "translation": {
            "label": "🧬 Translation",
            "content": """
<h3>Sonar System Breakdown</h3>

<p>
<b>analogRead(A0)</b><br>
Reads the ocean light 🌊<br>
0 = Pitch black 🌑<br>
1023 = Very bright ☀️
</p>

<p>
<b>if (oceanLight > 400)</b><br>
If it's bright → You are near the surface 🐬<br>
If it's dark → You are deep underwater 🐙
</p>

<p>
<b>Serial.print / println</b><br>
Sends messages to your computer 🖥️📡
</p>

<p>
<b>delay(600)</b><br>
Wait a short time before checking again ⏱️
</p>

<p>
<b>The loop</b><br>
Runs forever 🔁<br>
Read → Decide → Report → Repeat
</p>
"""
        }
    }
},
}
SKETCH_PRESET = {
    'sketch': """void setup() {
  Serial.begin(9600);
  Serial.println("--- SUBMARINE POWER ON ---");
}

void loop() {
  int oceanLight = analogRead(A0);

  Serial.print("Light Level: ");
  Serial.println(oceanLight);

  if (oceanLight > 400) {
    Serial.println("☀️ SURFACE: I see dolphins! 🐬");
  } else {
    Serial.println("🐙 MIDNIGHT ZONE: Watch for tentacles! ✨");
  }

  delay(600);
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