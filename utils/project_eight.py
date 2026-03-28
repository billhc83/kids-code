
from utils.step_builder import build_step, intro_step, rect, circle

META = {
    'title': 'Project 8: The Dragon\'s Crystal Alarm',
    'circuit_image': 'static/graphics/project_eight_circuit.png',
    'banner_image': None,
}

STEPS = [
    intro_step(
        "Let's build our eighth project",
        "Press the next button for a step by step guide",
    ),
    
    build_step(
        "Place the LED long leg in row 6, column E.<br>"
        "Place the LED short leg in row 5, column E",
        "The long leg is positive — it's called the anode!",
        rect(651, 232, 841, 382),
        greyout=True,
    ),

    build_step(
        "Place one leg of the 220 Ohm resistor in row 5, column D.<br>"
        "Place the second leg of the resistor in row 1, column D",
        "The resistor slows down the electricity.",
        rect(629, 356, 766, 435),
        circle(500, 499, radius=60),
        greyout=True,
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
        "Place one end of the 10k Ohm resistor in row 11 column H.<br>"
        "Place the other end in row 15 column H",
        "Resistors come in many different sizes.",
        circle(745, 77, radius=55),
        rect(831, 260, 960, 303),
        greyout=True,
    ),

    build_step(
        "Place the buzzer long leg in row 25, column E.<br>"
        "Place the buzzer short leg in row 28, column E",
        "This is the alarm buzzer.",
        circle(1161, 382, radius=60),
        circle(1113, 95, radius=60),
        circle(1215, 584, radius=60),
        greyout=True,
    ),

    build_step(
        "Place one end of the wire in the Arduino Pin GND.<br>"
        "Place the other end in the negative / - rail",
        "Ground wires complete the circuit.",
        rect(590, 496, 691, 526),
        rect(590, 285, 624, 526),
        rect(388, 285, 624, 311),
        greyout=True,
    ),

    build_step(
        "Place one end of the wire in the Arduino Pin A0.<br>"
        "Place the other end in row 15 column J",
        "This wire reads the light sensor.",
        rect(906, 210, 952, 265),
        rect(215, 208, 946, 246),
        rect(52, 208, 227, 513),
        greyout=True,
    ),

    build_step(
        "Place one end of the wire in Arduino Pin 5V.<br>"
        "Place the other end in row 18 column J",
        "This wire powers the sensor.",
        rect(962, 172, 1010, 260),
        rect(600, 172, 1006, 214),
        rect(600, 6, 645, 214),
        rect(8, 0, 645, 50),
        rect(0, 12, 84, 408),
        greyout=True,
    ),

    build_step(
        "Place one end of the wire in Arduino Pin 8.<br>"
        "Place the other end in row 25 column A",
        "This wire powers the buzzer.",
        rect(1107, 445, 1157, 594),
        rect(526, 565, 1147, 594),
        rect(522, 405, 554, 590),
        rect(396, 401, 554, 435),
        greyout=True,
    ),

    build_step(
        "Place one end of the wire in Arduino Pin 13.<br>"
        "Place the other end in row 6 column A",
        "This wire powers the LED.",
        rect(740, 435, 831, 571),
        rect(529, 547, 770, 571),
        rect(529, 307, 578, 560),
        rect(402, 307, 578, 331),
        greyout=True,
    ),

    build_step(
        "Place one end of the wire in row 1 column A.<br>"
        "Place the other end in the negative / - rail",
        "Completes the LED circuit.",
        rect(641, 433, 768, 530),
        greyout=True,
    ),

    build_step(
        "Place one end of the wire in row 11 column F.<br>"
        "Place the other end in the negative / - rail",
        "Completes the sensor circuit.",
        rect(827, 309, 1041, 532),
        greyout=True,
    ),

    build_step(
        "Place one end of the wire in row 28 column A.<br>"
        "Place the other end in the negative / - rail",
        "Completes the buzzer circuit.",
        rect(1153, 433, 1233, 543),
        greyout=True,
    ),
]

DRAWER_CONTENT = {

    "project_eight": {
    "title": "🏰 Dragon's Crystal Alarm",
    "tip": "Use a light sensor to trigger both a light and sound alarm system.",
    "tabs": {
        "story": {
            "label": "🐉 Mission",
            "content": """
<h3>Defend the Kingdom! 🏰</h3>

<p>
A powerful treasure — the <b>Golden Gear</b> — must be protected! ⚙️✨
</p>

<p>
You are the royal engineer 🧙‍♂️
</p>

<p>
Your task is to build a magical alarm system using a crystal sensor.
</p>

<p>
If a shadow passes over the crystal...
</p>

<p>
🚨 The alarm activates!<br>
💡 The light flashes like dragon fire<br>
🔊 The dragon ROARS!
</p>

<p>
No thief will escape! ⚔️🐉
</p>
"""
        },
        "code": {
            "label": "💻 Code",
            "content": """
<h3>The Alarm Spell</h3>

<pre>
int crystalPin = A0;
int firePin = 13;
int roarPin = 8;

void setup() {
  pinMode(firePin, OUTPUT);
  pinMode(roarPin, OUTPUT);
  Serial.begin(9600);
}

void loop() {
  int lightLevel = analogRead(crystalPin);

  if (lightLevel < 350) {
    digitalWrite(firePin, HIGH);
    tone(roarPin, 800);
    delay(150);

    digitalWrite(firePin, LOW);
    noTone(roarPin);
    delay(150);
  } else {
    digitalWrite(firePin, LOW);
    noTone(roarPin);
    delay(100);
  }
}
</pre>

<p>
This program watches for shadows and activates an alarm system.
</p>
"""
        },
        "logic": {
            "label": "🧩 Logic",
            "content": """
<h3>How the Alarm Thinks</h3>

<p>
The system constantly:
</p>

<p>
👁️ Reads light from the crystal<br>
🌑 Detects if it suddenly gets dark<br>
🚨 Activates the alarm<br>
🔁 Repeats
</p>

<p>
If shadow detected → FLASH + SOUND ⚡<br>
If clear → Stay quiet 😴
</p>
"""
        },
        "translation": {
            "label": "🧠 Translation",
            "content": """
<h3>Spell Breakdown</h3>

<p>
<b>analogRead(crystalPin)</b><br>
Reads the crystal's light 🔮<br>
Lower number = darker (shadow!)
</p>

<p>
<b>if (lightLevel &lt; 350)</b><br>
Shadow detected → trigger alarm ⚠️
</p>

<p>
<b>digitalWrite(firePin, HIGH/LOW)</b><br>
Turns the LED ON and OFF 💡<br>
Creates a flashing effect
</p>

<p>
<b>tone(roarPin, 800)</b><br>
Makes the buzzer roar at 800 Hz 🔊🐉
</p>

<p>
<b>noTone(roarPin)</b><br>
Stops the sound
</p>

<p>
<b>delay(150)</b><br>
Controls how fast the alarm flashes ⏱️
</p>

<p>
<b>System Behavior</b><br>
Sensor → Decision → Light + Sound → Repeat 🔁
</p>
"""
        }
    }
    }
}
SKETCH_PRESET = {
    'sketch': """int crystalPin = A0;
int firePin = 13;
int roarPin = 8;

void setup() {
  pinMode(firePin, OUTPUT);
  pinMode(roarPin, OUTPUT);
  Serial.begin(9600);
}

void loop() {
  int lightLevel = analogRead(crystalPin);

  if (lightLevel < 350) {
    digitalWrite(firePin, HIGH);
    tone(roarPin, 800);
    delay(150);

    digitalWrite(firePin, LOW);
    noTone(roarPin);
    delay(150);
  } else {
    digitalWrite(firePin, LOW);
    noTone(roarPin);
    delay(100);
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