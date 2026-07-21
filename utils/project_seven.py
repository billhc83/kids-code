from utils.step_builder import build_step, intro_step, rect, circle
from utils.affiliate_kits import BASIC_KITS

META = {
    'title': 'Project 7: The Automagic Night Light',
    'circuit_image': 'static/graphics/project_seven_circuit.png',
    'banner_image': 'project_seven_banner.png',
    'required_kits': BASIC_KITS,
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
        "steps": [
            {
                "title": "Program the Night Light 💡",
                "tip": "Watch the numbers scroll by so you can see exactly what your Arduino sees.",
                "tabs": {
                    "explain": {
                        "label": "📖 What & Why",
                        "content": (
                            "<p>Streetlights never need someone to flip their switch. They watch the sky and decide on their own. 🌙</p>"
                            "<p>Today you build that same trick into your night light, using the sensor plug and the light plug on your Arduino.</p>"
                            "<p>Without this step, your light would just sit there forever. It would never check the light number, so it could never decide anything on its own.</p>"
                            "<p>Once this step runs, your Arduino checks the light number by itself, over and over, forever.</p>"
                        )
                    },
                    "howto": {
                        "label": "🔧 How To",
                        "content": (
                            "<p>This whole program is built for you and locked in place, because getting a light sensor and a light to work together takes many exact steps in the right order. 🔒</p>"
                            "<p>The first two lines set up the light plug and turn on the messages your Arduino sends back to you, so you can watch what it is thinking. 💬</p>"
                            "<p>Then your Arduino asks the sensor plug one question: how much light is hitting it right now? It stores the answer as the light number and prints it so you can see it too. 🔢</p>"
                            "<p>Next it checks the light number against 300, the darkness number for this exact sensor and resistor pair. Your 10k resistor and photoresistor were picked so daylight always lands above 300 and true darkness always lands below it. 🌗</p>"
                            "<p>If the light number is under 300, the light plug switches on and it prints \"It's dark! Light ON.\" If it is 300 or higher, the light plug switches off and it prints \"Sun is up! Light OFF.\" instead. 💡</p>"
                            "<p>Last, it waits a tenth of a second before checking again, so it is always watching. ⏱️</p>"
                            "<p>Everything you just read is now running for real. In the next step, you get to reach in and start changing it yourself. 🛠️</p>"
                        )
                    },
                    "logic": {
                        "label": "🧠 Logic",
                        "content": (
                            "<p>Think of the sensor as a scout standing outside every second, holding up a number to show how bright it is right now. 🔦</p>"
                            "<p>The darkness number, 300, is a line drawn in the sand. Any number below that line means dark, any number at or above it means bright. 📏</p>"
                            "<p>Your Arduino checks the scout's number against that line again and again, so the moment it crosses the line, the light flips right away. ⚡</p>"
                        )
                    }
                }
            },
            {
                "title": "Mission Complete 🎉",
                "tip": "Your night light is fully operational!",
                "tabs": {
                    "explain": {
                        "label": "📖 What You Built",
                        "content": (
                            "<p>🎉 Great work, Engineer! You just finished a night light that runs entirely on its own.</p>"
                            "<p>Your circuit and code work together to watch the world and react to it, no buttons needed.</p>"
                            "<ul>"
                            "<li>🌙 Turns the light ON the moment it gets dark</li>"
                            "<li>☀️ Turns the light OFF the moment it gets bright again</li>"
                            "<li>👁️ Reads the light number from your sensor plug every tenth of a second</li>"
                            "<li>💬 Prints what it sees so you can watch it think in real time</li>"
                            "</ul>"
                            "<p>You proved you can build a system that senses, decides, and acts, all by itself.</p>"
                        )
                    },
                    "howto": {
                        "label": "🔧 Try This Next",
                        "content": (
                            "<p>Now that your system works, here are some ideas to make it even better.</p>"
                            "<ul>"
                            "<li>🔆 <strong>Make it more sensitive</strong> Lower the darkness number from 300 to something like 200, so the light waits for true darkness before turning on.</li>"
                            "<li>⏱️ <strong>Speed it up or slow it down</strong> Change the 100 at the end to a bigger or smaller number to check the light more or less often.</li>"
                            "<li>🔊 <strong>Add a buzzer</strong> Wire in a buzzer and make it beep once the moment the light turns on.</li>"
                            "<li>🌈 <strong>Add a second light</strong> Wire up a second LED that turns on only when it gets extremely dark, using a lower darkness number than your first light.</li>"
                            "<li>🎮 <strong>Build a light-up alarm</strong> Combine this with a button so the night light only runs after someone presses the button first, like a real security system.</li>"
                            "</ul>"
                            "<p>Experimenting is how real engineers improve their designs.</p>"
                        )
                    },
                    "logic": {
                        "label": "🧠 What You Learned",
                        "content": (
                            "<p>This project brought together everything you have been building.</p>"
                            "<ul>"
                            "<li>👁️ <strong>Sensing the world</strong> Your Arduino can read a number straight from a real sensor plug, not just from code you typed in.</li>"
                            "<li>🔢 <strong>Reading a live number</strong> That sensor reading changes every moment, so your Arduino has to keep asking for a fresh one.</li>"
                            "<li>📏 <strong>Setting a line to act on</strong> Picking one exact number to check against lets your Arduino make a clear yes-or-no decision.</li>"
                            "<li>🔀 <strong>Choosing between two paths</strong> Your code can do one thing when a check is true and a completely different thing when it is false.</li>"
                            "<li>🔁 <strong>Watching forever</strong> Wrapping all of this in a loop means your night light never stops paying attention.</li>"
                            "</ul>"
                            "<p>You are now thinking like an engineer.</p>"
                        )
                    },
                    "sim": {
                        "label": "🎮 Try It",
                        "type": "sim",
                        "sim_config": {
                            "mode": "interpreted",
                            "components": [
                                {"type": "ldr", "id": "ldr1", "pin": 14, "label": "Light Sensor"},
                                {"type": "led", "id": "led1", "color": "red", "pin": 13, "label": "Night Light"},
                            ],
                        }
                    }
                }
            }
        ]
    }
}
SKETCH_PRESET = {
    'sketch': """//>> Program the Night Light 💡 | free | editor
//## int lightSensor = A0;
//## int nightLight = 13;

void setup() {
  //## pinMode(nightLight, OUTPUT);
  //## Serial.begin(9600);
}

void loop() {
  //## int brightness = analogRead(lightSensor);
  //## Serial.println(brightness);
  //## if (brightness < 300) {
  //##   digitalWrite(nightLight, HIGH);
  //##   Serial.println("It's dark! Light ON \U0001F319");
  //## }
  //## else {
  //##   digitalWrite(nightLight, LOW);
  //##   Serial.println("Sun is up! Light OFF ☀️");
  //## }
  //## delay(100);
}

//>> Mission Complete | open | editor | reset | fill:true

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
    Serial.println("It's dark! Light ON \U0001F319");
  } else {
    digitalWrite(nightLight, LOW);
    Serial.println("Sun is up! Light OFF ☀️");
  }

  delay(100);
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
    "I placed my LED legs in the wrong rows",
    "My 220Ω resistor isn't in row5 D",
    "My photoresistor is in the wrong rows",
    "I can't find my ground wire on the - rail",
    "My A0 wire isn't plugged into row15 J",
]

CIRCUIT_SPEC = {
    "meta": {
        "title": "The Automagic Night Light",
        "difficulty": "beginner",
    },
    "components": [
        {"id": "LED", "type": "LED", "properties": {"color": "red"}},
        {"id": "LDR", "type": "LDR", "properties": {}},
    ],
    "connections": [
        {"from": "arduino.D13", "to": "LED.anode"},
        {"from": "R_LED.pin2", "to": "arduino.GND"},
        {"from": "arduino.5V",  "to": "LDR.pin1"},
        {"from": "LDR.pin2",    "to": "arduino.A0"},
        {"from": "R_LDR.pin2",  "to": "arduino.GND"},
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