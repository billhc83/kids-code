from utils.step_builder import build_step, intro_step, rect, circle, line, lbl


META = {
    'title': 'Project 19: The Robot Gatekeeper',
    'circuit_image': 'static/graphics/project_nineteen_circuit.png',
    'banner_image': 'robot_gatekeeper_banner.png',
    'lesson_type': 'progression',
}


# Wiring and component placement steps.
# rect() / circle() / line() coordinates are placeholders —
# update with real pixel coords once the circuit image is available.
STEPS = [
    intro_step("🤖 Project 19 — The Robot Gatekeeper", "Follow the steps to build your circuit."),
    build_step(
        "Plug the servo motor into the breadboard with the signal (orange) wire in row 12 column G, the power (red) wire in row 13 column G, and the ground (brown) wire in row 14 column G.",
        "The servo has three wires — make sure each lands in the correct row!",
        rect(0, 0, 100, 100), greyout=False,
    ),
    build_step(
        "Place the button onto the breadboard across the center gap. Top legs in row 17, columns E and F. Bottom legs in row 19, columns E and F.",
        "The button bridges the two halves of the breadboard.",
        rect(0, 0, 100, 100), greyout=False,
    ),
    build_step(
        "Put the green LED on the breadboard with the long leg (anode) in row 25, column E and the short leg (cathode) in row 24, column E.",
        "The long leg is positive — it's called the anode!",
        rect(0, 0, 100, 100), greyout=False,
    ),
    build_step(
        "Put the 220Ω resistor on the breadboard with one leg in row 24, column D and the other leg in row 20, column D.",
        "The resistor limits current so the component doesn't burn out.",
        rect(0, 0, 100, 100), greyout=False,
    ),
]


SKETCH_PRESET = {
    'sketch': (
        "//>> Declare Your Pins | guided | blocks\n"
        "//## #include <Servo.h>\n"
        "//## Servo gateServo;\n"
        "//?? Store the servo signal pin number\n"
        "int servoPin = 9;\n"
        "//?? Store the button pin number\n"
        "int buttonPin = 4;\n"
        "//?? Store the LED pin number\n"
        "int ledPin = 7;\n"
        "//>> Set Up the Gate | free | blocks\n"
        "void setup() {\n"
        "//##   gateServo.attach(servoPin);\n"
        "//##   pinMode(buttonPin, INPUT_PULLUP);\n"
        "//##   pinMode(ledPin, OUTPUT);\n"
        "//##   gateServo.write(0);\n"
        "}\n"
        "void loop() {\n"
        "}\n"
        "//>> Read the Button | guided | blocks\n"
        "void setup() {\n"
        "//##   gateServo.attach(servoPin);\n"
        "//##   pinMode(buttonPin, INPUT_PULLUP);\n"
        "//##   pinMode(ledPin, OUTPUT);\n"
        "//##   gateServo.write(0);\n"
        "}\n"
        "void loop() {\n"
        "//?? Read the button state into a variable\n"
        "  int buttonState = digitalRead(buttonPin);\n"
        "}\n"
        "//>> Check if Button Pressed | guided | blocks\n"
        "void setup() {\n"
        "//##   gateServo.attach(servoPin);\n"
        "//##   pinMode(buttonPin, INPUT_PULLUP);\n"
        "//##   pinMode(ledPin, OUTPUT);\n"
        "//##   gateServo.write(0);\n"
        "}\n"
        "void loop() {\n"
        "//##   int buttonState = digitalRead(buttonPin);\n"
        "//?? Check if the gate button has been pressed\n"
        "  if (buttonState == LOW) {\n"
        "  }\n"
        "}\n"
        "//>> Open the Gate | free | blocks\n"
        "void setup() {\n"
        "//##   gateServo.attach(servoPin);\n"
        "//##   pinMode(buttonPin, INPUT_PULLUP);\n"
        "//##   pinMode(ledPin, OUTPUT);\n"
        "//##   gateServo.write(0);\n"
        "}\n"
        "void loop() {\n"
        "//##   int buttonState = digitalRead(buttonPin);\n"
        "//##   if (buttonState == LOW) {\n"
        "//##     gateServo.write(90);\n"
        "//##   }\n"
        "}\n"
        "//>> Turn On the Status Light | guided | blocks\n"
        "void setup() {\n"
        "//##   gateServo.attach(servoPin);\n"
        "//##   pinMode(buttonPin, INPUT_PULLUP);\n"
        "//##   pinMode(ledPin, OUTPUT);\n"
        "//##   gateServo.write(0);\n"
        "}\n"
        "void loop() {\n"
        "//##   int buttonState = digitalRead(buttonPin);\n"
        "//##   if (buttonState == LOW) {\n"
        "//##     gateServo.write(90);\n"
        "//?? Signal that the gate is now open\n"
        "    digitalWrite(ledPin, HIGH);\n"
        "//##   }\n"
        "}\n"
        "//>> Hold the Gate Open | guided | blocks\n"
        "void setup() {\n"
        "//##   gateServo.attach(servoPin);\n"
        "//##   pinMode(buttonPin, INPUT_PULLUP);\n"
        "//##   pinMode(ledPin, OUTPUT);\n"
        "//##   gateServo.write(0);\n"
        "}\n"
        "void loop() {\n"
        "//##   int buttonState = digitalRead(buttonPin);\n"
        "//##   if (buttonState == LOW) {\n"
        "//##     gateServo.write(90);\n"
        "//##     digitalWrite(ledPin, HIGH);\n"
        "//?? Wait 2 seconds while the gate stays open\n"
        "    delay(2000);\n"
        "//##   }\n"
        "}\n"
        "//>> Close the Gate | free | blocks\n"
        "void setup() {\n"
        "//##   gateServo.attach(servoPin);\n"
        "//##   pinMode(buttonPin, INPUT_PULLUP);\n"
        "//##   pinMode(ledPin, OUTPUT);\n"
        "//##   gateServo.write(0);\n"
        "}\n"
        "void loop() {\n"
        "//##   int buttonState = digitalRead(buttonPin);\n"
        "//##   if (buttonState == LOW) {\n"
        "//##     gateServo.write(90);\n"
        "//##     digitalWrite(ledPin, HIGH);\n"
        "//##     delay(2000);\n"
        "//##     gateServo.write(0);\n"
        "//##   }\n"
        "}\n"
        "//>> Turn Off the Status Light | guided | blocks\n"
        "void setup() {\n"
        "//##   gateServo.attach(servoPin);\n"
        "//##   pinMode(buttonPin, INPUT_PULLUP);\n"
        "//##   pinMode(ledPin, OUTPUT);\n"
        "//##   gateServo.write(0);\n"
        "}\n"
        "void loop() {\n"
        "//##   int buttonState = digitalRead(buttonPin);\n"
        "//##   if (buttonState == LOW) {\n"
        "//##     gateServo.write(90);\n"
        "//##     digitalWrite(ledPin, HIGH);\n"
        "//##     delay(2000);\n"
        "//##     gateServo.write(0);\n"
        "//?? Turn off the green access light\n"
        "    digitalWrite(ledPin, LOW);\n"
        "//##   }\n"
        "}\n"
        "//>> Mission Complete | open | blocks"
    ),
    'default_view': 'blocks',
    'read_only': False,
    'lock_view': False,
    'fill_values': True,
    'fill_conditions': True,
}


DRAWER_CONTENT = {
    "project_nineteen": {
        "steps": [
            {
                "title": "Step 1 — Declare Your Pins \U0001f527",
                "tip": "Include the Servo library and store your pin numbers as variables.",
                "tabs": {
                    "explain": {
                        "label": "\U0001f4d6 What & Why",
                        "content": "<p>Before you write any instructions, you need to set up a few things at the top of your sketch. First, <code>#include &lt;Servo.h&gt;</code> loads the Servo library — a collection of code that knows how to control a servo motor. Then you create a <strong>Servo object</strong> called <code>gateServo</code> — think of it as a named remote control for your specific motor. Finally, you store pin numbers in integer variables so you can refer to them by name throughout your code.</p>"
                    },
                    "howto": {
                        "label": "\U0001f527 How To",
                        "content": "<p>In this step you will place three integer assignment blocks:</p><ol><li>Find the <strong>Variable assignment</strong> block and set <code>servoPin</code> to <strong>9</strong> — the PWM pin connected to the servo signal wire.</li><li>Add another block for <code>buttonPin</code> set to <strong>4</strong> — the digital pin connected to the button.</li><li>Add a third block for <code>ledPin</code> set to <strong>7</strong> — the digital pin connected to the green LED.</li></ol><p>The <code>#include</code> and <code>Servo gateServo;</code> lines are already locked in — they are boilerplate you do not need to drag.</p>"
                    },
                    "logic": {
                        "label": "\U0001f9e0 Logic",
                        "content": "<p>Think of pin variables like name badges for your components. Instead of writing the pin number every time, you give it a name: <code>servoPin</code>. If you ever rewire the servo to a different pin, you only change one number at the top and the rest of the program updates automatically. This is the same reason a security company labels every door with a name instead of a room number.</p>"
                    }
                }
            },
            {
                "title": "Step 2 — Set Up the Gate ⚙️",
                "tip": "Attach the servo, configure pin modes, and set the starting position.",
                "tabs": {
                    "explain": {
                        "label": "\U0001f4d6 What & Why",
                        "content": "<p>The <code>void setup()</code> function runs once when the Arduino powers on. <code>gateServo.attach(servoPin)</code> tells the Servo library which Arduino pin talks to the motor — without this, <code>write()</code> commands do nothing. <code>pinMode()</code> sets each pin as either an input (reading a button) or an output (driving an LED). The final <code>gateServo.write(0)</code> moves the gate to the closed position so the system always starts correctly.</p>"
                    },
                    "howto": {
                        "label": "\U0001f527 How To",
                        "content": "<p>All four lines in this step are locked in automatically — watch them appear:</p><ol><li><code>gateServo.attach(servoPin)</code> — binds the servo library to pin 9.</li><li><code>pinMode(buttonPin, INPUT_PULLUP)</code> — sets pin 4 as an input with the internal pull-up resistor enabled. Pressed = LOW.</li><li><code>pinMode(ledPin, OUTPUT)</code> — sets pin 7 as an output so you can drive the LED.</li><li><code>gateServo.write(0)</code> — positions the gate arm at 0 degrees (closed) on startup.</li></ol>"
                    },
                    "logic": {
                        "label": "\U0001f9e0 Logic",
                        "content": "<p>Setup is like a security guard's morning checklist before starting their shift: confirm the gate motor is connected, confirm the access button is ready, confirm the indicator light works, and make sure the gate starts in the closed position. You do this once before any visitors arrive — exactly what <code>void setup()</code> is designed for.</p>"
                    }
                }
            },
            {
                "title": "Step 3 — Read the Button \U0001f7e0",
                "tip": "Use digitalRead to check the button state on every loop.",
                "tabs": {
                    "explain": {
                        "label": "\U0001f4d6 What & Why",
                        "content": "<p><code>void loop()</code> runs continuously — thousands of times per second. Each pass, you call <code>digitalRead(buttonPin)</code> to check the button state. Because the pin uses INPUT_PULLUP, it returns <strong>HIGH (1)</strong> when released and <strong>LOW (0)</strong> when pressed. You store this in <code>buttonState</code> so you can make a decision about it in the next step.</p>"
                    },
                    "howto": {
                        "label": "\U0001f527 How To",
                        "content": "<p>Place one <strong>Variable assignment</strong> block at the start of the loop:</p><ol><li>Set the variable name to <code>buttonState</code> (type: <code>int</code>).</li><li>Set the value to <code>digitalRead(buttonPin)</code>.</li></ol><p>Every time loop() runs, this value refreshes — so you always have the latest button reading before deciding what to do.</p>"
                    },
                    "logic": {
                        "label": "\U0001f9e0 Logic",
                        "content": "<p>Imagine a security guard glancing at a sensor panel every second to check if a door has been triggered. Each glance is one pass through <code>loop()</code>, and reading the panel is your <code>digitalRead()</code>. The guard notes the current status before deciding what action to take — storing the reading in <code>buttonState</code> is that note.</p>"
                    }
                }
            },
            {
                "title": "Step 4 — Check if Button Pressed \U0001f50d",
                "tip": "With INPUT_PULLUP, LOW means pressed — your if condition checks for that.",
                "tabs": {
                    "explain": {
                        "label": "\U0001f4d6 What & Why",
                        "content": "<p>Now that you have the button reading, an <code>if</code> statement lets your program choose a path. Because of INPUT_PULLUP, a pressed button gives LOW (0), so the condition is <code>buttonState == LOW</code>. The double equals <code>==</code> means check equality — not assign. The body of the if block is still empty — you will fill it in the next steps, one piece at a time.</p>"
                    },
                    "howto": {
                        "label": "\U0001f527 How To",
                        "content": "<p>Place one <strong>if statement</strong> block after the buttonState line:</p><ol><li>Set the condition to <code>buttonState == LOW</code>.</li><li>Leave the body empty for now — the gate-open sequence fills it in the next steps.</li></ol><p>When you run the sketch here, pressing the button satisfies the condition but nothing visible happens yet — the gate logic comes next.</p>"
                    },
                    "logic": {
                        "label": "\U0001f9e0 Logic",
                        "content": "<p>Think of the if statement as a locked door inside your code. Only the right signal — button pressed = LOW — opens it. Any other reading (HIGH = not pressed) and the system stays idle. The security system only starts the unlock sequence for the correct credential, same as a real vault access panel.</p>"
                    }
                }
            },
            {
                "title": "Step 5 — Open the Gate \U0001f6aa",
                "tip": "Write 90 degrees to the servo to swing the gate arm open.",
                "tabs": {
                    "explain": {
                        "label": "\U0001f4d6 What & Why",
                        "content": "<p><code>gateServo.write(90)</code> commands the servo motor to rotate its shaft to exactly 90 degrees. The SG90 servo moves to that angle and holds it — no repeated commands needed. This is what makes servos special: you specify a <em>position</em>, not a speed. The motor physically moves to 90 degrees and stays there until the next <code>write()</code> call overrides it.</p>"
                    },
                    "howto": {
                        "label": "\U0001f527 How To",
                        "content": "<p>This line is locked in automatically inside the if block:</p><ol><li><code>gateServo.write(90)</code> — rotates the servo shaft to 90 degrees instantly.</li></ol><p>If your physical gate arm does not swing to the expected position, try adjusting the angle (60 to 120 degrees) once you have the servo physically attached and are testing on your desk.</p>"
                    },
                    "logic": {
                        "label": "\U0001f9e0 Logic",
                        "content": "<p>Imagine a drawbridge operator who pulls a lever to exactly a 90-degree position to raise the bridge. The lever clicks into that position and stays — the operator does not keep pulling. <code>servo.write(90)</code> is that lever pull: one command, one position, held until you say otherwise. No continuous force required, just a positional target.</p>"
                    }
                }
            },
            {
                "title": "Step 6 — Turn On the Status Light \U0001f4a1",
                "tip": "Light the green LED to show the gate is open.",
                "tabs": {
                    "explain": {
                        "label": "\U0001f4d6 What & Why",
                        "content": "<p>A servo moving silently is easy to miss. The green LED gives a clear visual signal that the gate is in the open state. <code>digitalWrite(ledPin, HIGH)</code> sends 5 volts to pin 7, which flows through the LED and its 220-ohm resistor, making the LED glow. The LED and servo command run almost simultaneously — both inside the same if block — so they trigger together on every button press.</p>"
                    },
                    "howto": {
                        "label": "\U0001f527 How To",
                        "content": "<p>Place one <strong>digitalWrite</strong> block after the servo write line, still inside the if block:</p><ol><li>Set the pin to <code>ledPin</code>.</li><li>Set the value to <code>HIGH</code>.</li></ol><p>HIGH = 5V = LED on. Press the button and you should see both the servo sweep to 90° and the green LED glow at the same moment.</p>"
                    },
                    "logic": {
                        "label": "\U0001f9e0 Logic",
                        "content": "<p>Think of airport runway lights — when the runway is cleared for landing, the green approach lights turn on at the same time as the gate signal. The LED and servo work as a team: the servo moves the physical gate while the LED broadcasts the status to anyone watching. Two outputs, one event, coordinated by the same if block.</p>"
                    }
                }
            },
            {
                "title": "Step 7 — Hold the Gate Open ⏱️",
                "tip": "Use delay(2000) to keep the gate open for exactly 2 seconds.",
                "tabs": {
                    "explain": {
                        "label": "\U0001f4d6 What & Why",
                        "content": "<p><code>delay(2000)</code> pauses the Arduino program for 2000 milliseconds — exactly 2 seconds. During this pause, the servo stays at 90° and the LED stays on because nothing in the program is changing those values. After the pause ends, the program continues to the next line. The delay gives a visitor time to pass through before the gate closes automatically.</p>"
                    },
                    "howto": {
                        "label": "\U0001f527 How To",
                        "content": "<p>Place one <strong>delay</strong> block after the LED on line, inside the if block:</p><ol><li>Set the milliseconds value to <strong>2000</strong> for a 2-second hold.</li></ol><p>Try different values to feel the difference: 500 for a quick flash, 5000 for a long wait. The delay is your gate-open timer — too short and the gate snaps shut before anyone can pass through!</p>"
                    },
                    "logic": {
                        "label": "\U0001f9e0 Logic",
                        "content": "<p>Think of an automatic door at a supermarket: it opens when it detects you, holds open while you walk through, then closes after a few seconds. The delay is that hold-open timer. Without it, the gate would open and close faster than you could blink. The delay gives the physical world time to catch up with the digital command.</p>"
                    }
                }
            },
            {
                "title": "Step 8 — Close the Gate \U0001f512",
                "tip": "Write 0 degrees to the servo to return the gate to the closed position.",
                "tabs": {
                    "explain": {
                        "label": "\U0001f4d6 What & Why",
                        "content": "<p>After the 2-second hold, a second <code>gateServo.write(0)</code> sends the gate back to the closed position. The motor sweeps to 0 degrees and holds there — the same starting position set in <code>setup()</code>. Notice you are using the exact same function call: <code>servo.write()</code> works identically at any point in the program, moving to whatever angle you specify regardless of where the servo currently sits.</p>"
                    },
                    "howto": {
                        "label": "\U0001f527 How To",
                        "content": "<p>This line is locked in automatically after the delay — watch the gate arm swing back:</p><ol><li><code>gateServo.write(0)</code> — returns the shaft to 0 degrees (closed position).</li></ol><p>The servo immediately snaps to 0 degrees. For a smoother sweep, advanced projects use a for-loop with small angle steps and short delays — but the instant snap works perfectly here.</p>"
                    },
                    "logic": {
                        "label": "\U0001f9e0 Logic",
                        "content": "<p>A security vault door does not stay open — it automatically closes and re-locks after you enter. This single command is the automatic re-lock. The servo remembers its target (90°) until you tell it otherwise. Sending <code>write(0)</code> overrides the previous command and the motor obediently swings back. Two lines, two opposing positions — open then closed.</p>"
                    }
                }
            },
            {
                "title": "Step 9 — Turn Off the Status Light \U0001f534",
                "tip": "Turn the LED off when the gate returns to closed.",
                "tabs": {
                    "explain": {
                        "label": "\U0001f4d6 What & Why",
                        "content": "<p>The green LED should only be on while the gate is open. Now that the servo has returned to 0°, you turn off the LED with <code>digitalWrite(ledPin, LOW)</code>. LOW = 0V = no current through the LED = light off. This completes the full access sequence: button press → gate opens and LED on → 2-second hold → gate closes and LED off. After this line, the if block ends and loop() restarts, ready for the next button press.</p>"
                    },
                    "howto": {
                        "label": "\U0001f527 How To",
                        "content": "<p>Place one <strong>digitalWrite</strong> block after the gate-close servo line, still inside the if block:</p><ol><li>Set the pin to <code>ledPin</code>.</li><li>Set the value to <code>LOW</code>.</li></ol><p>LOW = 0V = LED off. After this line the if block is complete and the gate system is ready for the next press.</p>"
                    },
                    "logic": {
                        "label": "\U0001f9e0 Logic",
                        "content": "<p>Think of a vault status panel: the green light is on only while the door is physically open, and it goes off the moment the door re-latches. The LED and servo are always in sync — open together, closed together. Your code enforces this relationship: every time the servo returns to 0, the LED goes LOW. Two outputs that mirror each other like a matched pair.</p>"
                    }
                }
            },
            {
                "title": "Mission Complete \U0001f389",
                "tip": "Your Robot Gatekeeper is fully operational!",
                "tabs": {
                    "explain": {
                        "label": "\U0001f4d6 What You Built",
                        "content": "<p>You built a servo-powered security gate with full automation! Here is what your system does:</p><ul><li>\U0001f7e0 Reads a push button using INPUT_PULLUP — where LOW means pressed</li><li>\U0001f535 Commands a servo motor to sweep between 0° and 90° on demand</li><li>\U0001f49a Uses a green LED as a real-time open/closed status indicator</li><li>⏱️ Holds the gate open for exactly 2 seconds using delay()</li><li>\U0001f512 Automatically re-closes without any extra input</li></ul>"
                    },
                    "howto": {
                        "label": "\U0001f527 Try This Next",
                        "content": "<p>Ready to level up? Here are some ideas:</p><ul><li>\U0001f534 <strong>Add a red LED</strong> — wire a second LED to pin D5 and light it when the gate is closed (opposite of the green one).</li><li>\U0001f50a <strong>Add a buzzer</strong> — play a short tone when the gate opens to simulate an access-granted beep.</li><li>⏱️ <strong>Tune the hold time</strong> — change the 2000 in delay(2000) to experiment with longer or shorter open windows.</li><li>\U0001f501 <strong>Count entries</strong> — add a counter variable that increments each press and prints to Serial Monitor.</li></ul>"
                    },
                    "logic": {
                        "label": "\U0001f9e0 What You Learned",
                        "content": "<p>Big ideas from this project:</p><ul><li><strong>Servo motors</strong> move to exact angles — they are position-controlled, not speed-controlled.</li><li><strong>The Servo library</strong> abstracts the PWM signal — you just call write(angle).</li><li><strong>INPUT_PULLUP</strong> inverts button logic — pressed = LOW, released = HIGH.</li><li><strong>Output coordination</strong> — multiple components triggered by a single event.</li><li><strong>delay()</strong> controls timing but blocks the whole program — a real trade-off to understand.</li></ul>"
                    },
                    "sim": {
                        "label": "\U0001f3ae Try It",
                        "type": "sim",
                        "sim_config": {}
                    }
                }
            }
        ]
    }
}


CIRCUIT_JSON = {
    "meta": {
        "title": "The Robot Gatekeeper",
        "difficulty": "medium",
        "description": "Build a servo-powered security gate that opens when you press a button, signals with a green LED, then closes again.",
        "learning_goal": "Controlling a servo motor with positional commands and digital inputs",
        "code_hint": "Read the button with INPUT_PULLUP; when pressed, sweep servo to 90, turn LED on, wait 2 seconds, sweep back to 0, turn LED off"
    },
    "components": [
        {
            "id": "SRV1",
            "type": "SERVO",
            "pins": {
                "signal": {"col": "G", "row": 12},
                "power": {"col": "G", "row": 13},
                "ground": {"col": "G", "row": 14}
            },
            "properties": {}
        },
        {
            "id": "BTN1",
            "type": "BUTTON",
            "pins": {
                "TL": {"col": "E", "row": 17},
                "TR": {"col": "F", "row": 17},
                "BL": {"col": "E", "row": 19},
                "BR": {"col": "F", "row": 19}
            },
            "properties": {}
        },
        {
            "id": "LED1",
            "type": "LED",
            "pins": {
                "anode": {"col": "E", "row": 25},
                "cathode": {"col": "E", "row": 24}
            },
            "properties": {"color": "green"}
        },
        {
            "id": "R_LED1",
            "type": "RESISTOR",
            "pins": {
                "pin1": {"col": "D", "row": 24},
                "pin2": {"col": "D", "row": 20}
            },
            "properties": {"ohms": 220}
        }
    ],
    "connections": [
        {"from": "arduino.D9", "to": "breadboard.H12", "color": "#F1C40F"},
        {"from": "breadboard.F13", "to": "breadboard.+1.13", "color": "#CC0000"},
        {"from": "breadboard.F14", "to": "breadboard.-1.14", "color": "#111111"},
        {"from": "arduino.D4", "to": "breadboard.A17", "color": "#3498DB"},
        {"from": "breadboard.G19", "to": "breadboard.-1.19", "color": "#111111"},
        {"from": "arduino.D7", "to": "breadboard.A25", "color": "#9B59B6"},
        {"from": "breadboard.E20", "to": "breadboard.-1.20", "color": "#111111"},
        {"from": "arduino.5V", "to": "breadboard.+1.30", "color": "#CC0000"},
        {"from": "arduino.GND", "to": "breadboard.-1.30", "color": "#111111"}
    ],
    "walkthrough": [
        {
            "type": "component",
            "id": "SRV1",
            "instruction": "Plug the servo motor into the breadboard with the signal (orange) wire in row 12 column G, the power (red) wire in row 13 column G, and the ground (brown) wire in row 14 column G.",
            "tip": "The servo has three wires — make sure each lands in the correct row!"
        },
        {
            "type": "component",
            "id": "BTN1",
            "instruction": "Place the button onto the breadboard across the center gap. Top legs in row 17, columns E and F. Bottom legs in row 19, columns E and F.",
            "tip": "The button bridges the two halves of the breadboard."
        },
        {
            "type": "component",
            "id": "LED1",
            "instruction": "Put the green LED on the breadboard with the long leg (anode) in row 25, column E and the short leg (cathode) in row 24, column E.",
            "tip": "The long leg is positive — it's called the anode!"
        },
        {
            "type": "component",
            "id": "R_LED1",
            "instruction": "Put the 220Ω resistor on the breadboard with one leg in row 24, column D and the other leg in row 20, column D.",
            "tip": "The resistor limits current so the component doesn't burn out."
        },
        {
            "type": "wire",
            "from": "arduino.D9",
            "to": "breadboard.H12",
            "instruction": "Connect a yellow wire from Arduino pin D9 to the breadboard at row 12, column H.",
            "tip": "This wire carries the PWM signal to the servo."
        },
        {
            "type": "wire",
            "from": "breadboard.F13",
            "to": "breadboard.+1.13",
            "instruction": "Connect a red wire from the breadboard at row 13, column F to the positive (+) rail at row 13.",
            "tip": "Red wires carry power — the positive 5V supply rail."
        },
        {
            "type": "wire",
            "from": "breadboard.F14",
            "to": "breadboard.-1.14",
            "instruction": "Connect a black wire from the breadboard at row 14, column F to the negative (−) rail at row 14.",
            "tip": "Black wires carry ground — the return path for electricity."
        },
        {
            "type": "wire",
            "from": "arduino.D4",
            "to": "breadboard.A17",
            "instruction": "Connect a blue wire from Arduino pin D4 to the breadboard at row 17, column A.",
            "tip": "This wire reads the button signal."
        },
        {
            "type": "wire",
            "from": "breadboard.G19",
            "to": "breadboard.-1.19",
            "instruction": "Connect a black wire from the breadboard at row 19, column G to the negative (−) rail at row 19.",
            "tip": "Black wires carry ground — the return path for electricity."
        },
        {
            "type": "wire",
            "from": "arduino.D7",
            "to": "breadboard.A25",
            "instruction": "Connect a purple wire from Arduino pin D7 to the breadboard at row 25, column A.",
            "tip": "This wire drives the status LED."
        },
        {
            "type": "wire",
            "from": "breadboard.E20",
            "to": "breadboard.-1.20",
            "instruction": "Connect a black wire from the breadboard at row 20, column E to the negative (−) rail at row 20.",
            "tip": "This completes the LED circuit through the resistor to ground."
        },
        {
            "type": "wire",
            "from": "arduino.5V",
            "to": "breadboard.+1.30",
            "instruction": "Connect a red wire from the Arduino's 5V pin to the positive (+) rail at row 30.",
            "tip": "This powers the servo motor."
        },
        {
            "type": "wire",
            "from": "arduino.GND",
            "to": "breadboard.-1.30",
            "instruction": "Connect a black wire from the Arduino's GND pin to the negative (−) rail at row 30.",
            "tip": "This completes the ground connection for the whole breadboard."
        }
    ]
}


PROJECT = {
    "meta": META,
    "steps": STEPS,
    "drawer": DRAWER_CONTENT,
    "presets": {
        "default": SKETCH_PRESET,
    },
    "circuit_definition": CIRCUIT_JSON,
}
