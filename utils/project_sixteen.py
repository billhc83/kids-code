from turtle import setup

from utils.step_builder import build_step, intro_step, rect, circle, line, lbl


META = {
    'title': 'Project 16: Broken Blinker',
    'circuit_image': 'static/graphics/project_sixteen_circuit.png',
    'banner_image': 'project_sixteen_banner.png',
    'lesson_type': 'troubleshoot',
}


# Wiring and component placement steps.
# rect() / circle() / line() coordinates are placeholders —
# update with real pixel coords once the circuit image is available.
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


SKETCH_PRESET = {
    'sketch': """//>> Find the Bug | verify | blocks | palette:intvar,pinmode,digitalwrite,delay,value
int ledPin = 13;

void setup() {
  pinMode(ledPin, INPUT);
}
void loop() {
  digitalWrite(ledPin, LOW);
}

//==

int ledPin = 13;

void setup() {
  pinMode(ledPin, OUTPUT);
}

void loop() {
  digitalWrite(ledPin, HIGH);
  delay(1000);
  digitalWrite(ledPin, LOW);
  delay(1000);
}
//>> Mission Complete | open | blocks | reset | fill:true

int ledPin = 13;

void setup() {
  pinMode(ledPin, OUTPUT);
}

void loop() {
  digitalWrite(ledPin, HIGH);
  delay(1000);
  digitalWrite(ledPin, LOW);
  delay(1000);
}""",

    'default_view': 'blocks',
    'read_only': False,
    'lock_view': False,
    'fill_values': True,
    'fill_conditions': True,
}


DRAWER_CONTENT = {
    "project_sixteen": {
        "steps": [
            {
                "title": "Find the Bug 🔍",
                "tip": "Read the code like a detective — look for clues line by line! 🕵️",
                "tabs": {
                    "explain": {
                        "label": "🎯 The Challenge",
                        "content": (
                            "<p>The drone fleet is ready to fly, but the head engineer has a big problem! 🛸</p>"
                            "<p>The drone lights should blink on and off to show the pilots everything is working. ✅</p>"
                            "<p>Right now, the light stays OFF the whole time and never blinks. 😟</p>"
                            "<p>A working drone light should blink ON for one second, then OFF for one second — over and over!</p>"
                            "<p>Your mission: read the code, find what's broken, and fix it. 🔧</p>"
                            "<p>The drones are waiting to launch — it's all up to you, Code Detective!</p>"
                        )
                    },
                    "sim": {
                        "label": "🎮 Try It",
                        "type": "sim",
                        "sim_config": {
                            "mode": "code_driven",
                            "pins": {"13": {"type": "led", "color": "red", "label": "Drone Light"}},
                            "loop_iterations": 4,
                            "max_ms": 12000,
                        }
                    },
                    "howto": {
                        "label": "💡 Hints",
                        "content": (
                            "<p><strong>Hint 1:</strong> There are TWO things wrong in this code! 🕵️ "
                            "Start by looking at the setup section — is the LED pin set up the right way?</p>"
                            "<p><strong>Hint 2:</strong> Check the <code>pinMode</code> line — should the drone light "
                            "be set to INPUT or OUTPUT? 💡 Also look at the loop — does it have everything a blink needs?</p>"
                            "<p><strong>Hint 3:</strong> The <code>pinMode</code> is set to INPUT, but an LED needs OUTPUT "
                            "to light up! 🔌 Also, the loop only has LOW — a blink needs HIGH, a delay, LOW, and another delay too. ⏱️</p>"
                        )
                    }
                }
            },
            {
                "title": "Mission Complete 🎉",
                "tip": "Your drone light is fixed and blinking — great detective work! 🛸",
                "tabs": {
                    "explain": {
                        "label": "📖 What You Built",
                        "content": (
                            "<p>Outstanding detective work, Engineer! 🎉 You found the bugs and got the drones flying!</p>"
                            "<p>Your drone light system now blinks perfectly, just like a real aircraft warning light. 🛸</p>"
                            "<ul>"
                            "<li>🔍 Read code line by line to spot what was wrong</li>"
                            "<li>🔌 Fixed the pin so it can SEND electricity to the LED</li>"
                            "<li>💡 Made the LED turn ON with HIGH</li>"
                            "<li>⏱️ Added delays so the blink happens at the right speed</li>"
                            "<li>🔄 Made the LED turn OFF with LOW so the full blink works</li>"
                            "<li>✅ Fixed TWO bugs in one mission!</li>"
                            "</ul>"
                            "<p>You proved that you can read code, find mistakes, and fix them like a real engineer! 🚀</p>"
                        )
                    },
                    "howto": {
                        "label": "🔧 Try This Next",
                        "content": (
                            "<p>Now that your drone light works, here are some ideas to make it even better. 🔧</p>"
                            "<ul>"
                            "<li>⚡ <strong>Faster Blink:</strong> Change the delay numbers to make the light blink super fast!</li>"
                            "<li>🐢 <strong>Slower Blink:</strong> Try a big delay number — how slow can you make it blink?</li>"
                            "<li>💡 <strong>Two LEDs:</strong> Add a second LED that blinks the opposite way — when one is ON, the other is OFF!</li>"
                            "<li>🔢 <strong>SOS Pattern:</strong> Make the light blink 3 times fast, then 3 times slow, just like a distress signal!</li>"
                            "<li>🎨 <strong>Colour Change:</strong> Swap in a different colour LED — what happens?</li>"
                            "<li>🎮 <strong>Button Control:</strong> Can you add a button that makes the blink speed change when you press it?</li>"
                            "</ul>"
                            "<p>Experimenting is how real engineers improve their designs. 🛸</p>"
                        )
                    },
                    "logic": {
                        "label": "🧠 What You Learned",
                        "content": (
                            "<p>This mission brought together everything you need to be a code detective! 🕵️</p>"
                            "<ul>"
                            "<li>🔍 <strong>Reading code:</strong> Looking at each line carefully to understand what the computer is doing</li>"
                            "<li>🔌 <strong>OUTPUT pins:</strong> Setting a pin to OUTPUT so it can send electricity to an LED</li>"
                            "<li>💡 <strong>HIGH and LOW:</strong> Turning a pin ON with HIGH and OFF with LOW</li>"
                            "<li>⏱️ <strong>delay():</strong> Making the Arduino wait a moment before running the next line</li>"
                            "<li>🔄 <strong>Blinking pattern:</strong> Using HIGH + delay + LOW + delay to make a light blink</li>"
                            "<li>🐛 <strong>Bug fixing:</strong> Finding mistakes in code and changing them to make things work</li>"
                            "</ul>"
                            "<p>You are now thinking like a real code detective engineer! 🚀</p>"
                        )
                    },
                    "sim": {
                        "label": "🎮 Try It",
                        "type": "sim",
                        "sim_config": {
                            "mode": "code_driven",
                            "pins": {"13": {"type": "led", "color": "red", "label": "Drone Light"}},
                            "loop_iterations": 4,
                            "max_ms": 12000,
                        }
                    }
                }
            }
        ]
    }
}


PROJECT = {
    "meta": META,
    "steps": STEPS,
    "drawer": DRAWER_CONTENT,
    "presets": {
        "default": SKETCH_PRESET,
    }
}
