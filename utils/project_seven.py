from utils.step_builder import build_step, intro_step, rect, circle

META = {
    'title': 'Project 7: The Automagic Night Light',
    'circuit_image': 'static/graphics/project_seven_circuit.png',
    'banner_image': None,
}

STEPS = [
    intro_step(
        "Let's build our seventh project",
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
        circle(507, 449, radius=60),
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
        "Place one end of the wire in the Arduino Pin GND.<br>"
        "Place the other end in the negative / - rail",
        "Ground wires help complete our circuit loop.",
        rect(590, 496, 691, 526),
        rect(590, 285, 624, 526),
        rect(388, 285, 624, 311),
        greyout=True,
    ),

    build_step(
        "Place one end of the wire in the Arduino Pin A0.<br>"
        "Place the other end in row 15 column J",
        "This wire is listening to the light sensor.",
        rect(906, 210, 952, 265),
        rect(215, 208, 946, 246),
        rect(52, 208, 227, 513),
        greyout=True,
    ),

    build_step(
        "Place one end of the wire in Arduino Pin 5V.<br>"
        "Place the other end in row 18 column J",
        "This wire powers our night light sensor.",
        rect(962, 172, 1010, 260),
        rect(600, 172, 1006, 214),
        rect(600, 6, 645, 214),
        rect(8, 0, 645, 50),
        rect(0, 12, 84, 408),
        greyout=True,
    ),

    build_step(
        "Place one end of the wire in Arduino Pin 13.<br>"
        "Place the other end in row 6 column A",
        "This wire powers our night light LED.",
        rect(740, 435, 831, 571),
        rect(529, 547, 770, 571),
        rect(529, 307, 578, 560),
        rect(402, 307, 578, 331),
        greyout=True,
    ),

    build_step(
        "Place one end of the wire in row 1 column A.<br>"
        "Place the other end in the negative / - rail",
        "This wire completes the LED circuit.",
        rect(641, 433, 768, 530),
        greyout=True,
    ),

    build_step(
        "Place one end of the wire in row 11 column F.<br>"
        "Place the other end in the negative / - rail",
        "This wire completes the sensor circuit.",
        rect(827, 309, 1041, 532),
        greyout=True,
    ),
]

DRAWER_CONTENT = {

    "project_seven": {
    "title": "💡 Automagic Night Light",
    "tip": "Use a light sensor to automatically turn a light on when it gets dark.",
    "tabs": {
        "story": {
            "label": "👷 Mission",
            "content": """
<h3>Build Your Smart Night Light 🌙💡</h3>

<p>
Have you ever noticed how streetlights turn on by themselves at night?
</p>

<p>
Today, you become the engineer 👷
</p>

<p>
Your mission:
</p>

<p>
☀️ During the day → Light stays OFF<br>
🌙 When it gets dark → Light turns ON
</p>

<p>
Your Arduino will watch the light levels and decide what to do — automatically!
</p>

<p>
No buttons. No switches.<br>
Just smart thinking. 🧠✨
</p>
"""
        },
        "code": {
            "label": "💻 Code",
            "content": """
<h3>The Night Light Program</h3>

<pre>
int lightSensor = A0;
int nightLight = 13;

void setup() {
  pinMode(nightLight, OUTPUT);
  Serial.begin(9600);
}

void loop() {
  int brightness = analogRead(lightSensor);
  Serial.println(brightness);

  if (brightness < 300) {
    digitalWrite(nightLight, HIGH);
    Serial.println("It's dark! Light ON 🌙");
  } else {
    digitalWrite(nightLight, LOW);
    Serial.println("Sun is up! Light OFF ☀️");
  }

  delay(100);
}
</pre>

<p>
This program reads light levels and controls the LED automatically.
</p>
"""
        },
        "logic": {
            "label": "🧩 Logic",
            "content": """
<h3>How the System Thinks</h3>

<p>
The Arduino constantly:
</p>

<p>
🔢 Reads the light level<br>
🤔 Compares it to a number<br>
💡 Turns the light ON or OFF<br>
🔁 Repeats forever
</p>

<p>
If it's dark → Light ON 🌙<br>
If it's bright → Light OFF ☀️
</p>

<p>
This is how automatic systems work in the real world!
</p>
"""
        },
        "translation": {
            "label": "🧬 Translation",
            "content": """
<h3>Engineer Breakdown</h3>

<p>
<b>lightSensor = A0</b><br>
This is where the sensor is connected 👁️
</p>

<p>
<b>nightLight = 13</b><br>
This is the light you are controlling 💡
</p>

<p>
<b>analogRead(lightSensor)</b><br>
Reads brightness 🔢<br>
Lower number = darker<br>
Higher number = brighter
</p>

<p>
<b>if (brightness &lt; 300)</b><br>
If it's dark → turn light ON 🌙
</p>

<p>
<b>else</b><br>
If it's bright → turn light OFF ☀️
</p>

<p>
<b>Threshold (300)</b><br>
This number decides when it becomes "night"
</p>

<p>
<b>Input vs Output</b><br>
Sensor = input 👁️<br>
Light = output 💡
</p>
"""
        }
    }
    }
}
SKETCH_PRESET = {
    'sketch': """int lightSensor = A0;
int nightLight = 13;

void setup() {
  pinMode(nightLight, OUTPUT);
  Serial.begin(9600);
}

void loop() {
  int brightness = analogRead(lightSensor);
  Serial.println(brightness);

  if (brightness < 300) {
    digitalWrite(nightLight, HIGH);
    Serial.println("It's dark! Light ON 🌙");
  } else {
    digitalWrite(nightLight, LOW);
    Serial.println("Sun is up! Light OFF ☀️");
  }

  delay(100);
}""",
    'default_view': 'editor',
    'read_only': True,
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