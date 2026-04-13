
from utils.step_builder import build_step, intro_step, rect, circle, line,lbl

META = {
    'title': 'Project 15: Backup Alarm',
    'circuit_image': "static/graphics/project_fifteen_circuit.png",
    'banner_image': 'project_fifteen_banner.png',
}

STEPS =[
    build_step(
        "Place the long leg of the LED in row 6, column E.<br>Place the short leg of the LED in row 5, column E.",
        "LED stands for light emitting diode.",
        rect(793, 291, 1039, 524),
        labels=[lbl("Long", pos=(959, 490), font_size=16), lbl("Short", pos=(808, 493), font_size=16)],
        greyout=True,
    ),

    build_step(
        "Place the long leg of the LED in row 12, column E.<br>Place the short leg of the LED in row 11, column E.",
        "LED's only work in one direction. Thats why we make sure the short and long leg are in the right spot.",
        rect(954, 296, 1209, 519),
        labels=[lbl("Long", pos=(1115, 495), font_size=16), lbl("Short", pos=(966, 493), font_size=16)],
        greyout=True,
    ),

    build_step(
        "Place the long leg of the LED in row 18, column E.<br>Place the short leg of the LED in row 17, column E.",
        "LED Lifespan, these mini lights can last over 25,000 hours",
        rect(1118, 313, 1370, 534),
        labels=[lbl("Long", pos=(1284, 505), font_size=16), lbl("Short", pos=(1130, 502), font_size=16)],
        greyout=True,
    ),

    build_step(
        "Place one leg of the __ resistor in row 1, column D.<br>Place the other leg in row 5, column D.",
        "Resistors have a color code to show their value!",
        rect(736, 493, 947, 625),
        labels=[lbl("220 Ohm", pos=(776, 599), font_size=16)],
        greyout=True,
    ),

    build_step(
        "Place one leg of the __ resistor in row 7, column D.<br>Place the other leg in row 11, column D.",
        "Each color represents a number, which helps us understand how much resistance a resistor has",
        rect(923, 486, 1108, 630),
        labels=[lbl("220 Ohm", pos=(957, 608), font_size=16)],
        greyout=True,
    ),

    build_step(
        "Place one leg of the __ resistor in row 13, column D.<br>Place the other leg in row 17, column D.",
        "The bigger the resistance, the harder it is for electricity to pass!",
        rect(1089, 469, 1260, 632),
        greyout=True,
    ),

    build_step(
        "Place the VCC pin of the distance sensor in row 23, column H.<br>"
        "Place the Gnd pin of the distance sensor in row 26, column H.",
        "VCC provides power (5V) and GND is the ground connection.",
        rect(1171, 99, 1671, 404),
        greyout=True,
    ),

    build_step(
        "Place one end of the wire in Arduino Pin GND.<br>Place the other end in row 26, column F.",
        "",
        line((476, 353), (541, 353), (688, 252), (1587, 250), (1584, 430), (1469, 430), width=10),
        greyout=True,
    ),

    build_step(
        "Place one end of the wire in Arduino Pin 5V.<br>Place the other end in row 23, column F.",
        "",
        line((12, 476), (639, 428), (1397, 428), width=10),
        greyout=True,
    ),

    build_step(
        "Place one end of the wire in Arduino Pin 10.<br>Place the other end in row 25, column F.",
        "",
        line((490, 457), (1450, 459), (1450, 426), width=10),
        greyout=True,
    ),

    build_step(
        "Place one end of the wire in Arduino Pin 9.<br>Place the other end in row 24, column F.",
        "",
        line((512, 582), (935, 584), (935, 625), width=10),
        greyout=True,
    ),

    build_step(
        "Place one end of the wire in Arduino Pin 5.<br>Place the other end in row 12, column A.",
        "",
        line((500, 611), (654, 611), (654, 750), (1096, 748), (1094, 615), width=10),
        greyout=True,
    ),

    build_step(
        "Place one end of the wire in Arduino Pin 4.<br>Place the other end in row 18, column A.",
        "",
        line((507, 635), (625, 637), (627, 777), (1267, 779), (1260, 611), width=10),
        greyout=True,
    ),

    build_step(
        "Place one end of the wire in Arduino Pin GND.<br>Place the other end in the negative / - rail.",
        "",
        line((17, 524), (361, 700), (810, 702), width=10),
        greyout=True,
    ),

    build_step(
        "Place one end of the wire in row 1, column A.<br>Place the other end in the negative / - rail.",
        "",
        line((793, 608), (839, 700), width=10),
        greyout=True,
    ),

    build_step(
        "Place one end of the wire in row 7, column A.<br>Place the other end in the negative / - rail.",
        "",
        line((959, 613), (1005, 702), width=10),
        greyout=True,
    ),

    build_step(
        "Place one end of the wire in row 18, column A.<br>Place the other end in the negative / - rail.",
        "",
        line((1115, 611), (1168, 707), width=10),
        greyout=True,
    ),

]

DRAWER_CONTENT = {

 "project_fifteen": {
  "steps": [

{
    "title": "Step 1 — System Memory 📦",
    "tip": "Set up your system’s memory so it knows what everything is.",
    "tabs": {
        "explain": {
            "label": "📖 What & Why",
            "content": "<p>Before your backup alarm can work, it needs to know what parts it is using. We store this information in <b>variables</b>.</p><br><p>Each variable acts like a label for a part of your system:</p><ul><li>📡 <b>trigPin</b> → sends out a signal to measure distance - Pin 9<br><br></li><li>👂 <b>echoPin</b> → listens for the signal bouncing back - Pin 10<br><br></li><li>🔊 <b>buzzerPin</b> → makes sound when objects are close - Pin 3<br><br></li><li>💡 <b>greenLED</b>, <b>yellowLED</b>, <b>redLED</b> → show safe, warning, and danger zones - Pins 4, 5 and 6<br><br></li><li>⏱ <b>duration</b> → stores how long the signal takes to return - Set to 0<br><br></li><li>📏 <b>distance</b> → stores how far away an object is - Set to 0</li></ul><p>Without these, your system wouldn’t know what anything is!</p>"
        },
        "howto": {
            "label": "🔧 How To",
            "content": "<p>1. Create containers (variables) for each part of your system.</p><p>2. Give each one the exact name shown in the instructions.</p><p>3. Assign each pin a number so your board knows where things are connected.</p><p>4. Create containers for <b>duration</b> and <b>distance</b> to store sensor data.</p><p>These variables will be used in almost every step, so they must be correct!</p>"
        },
        "logic": {
            "label": "🧠 Logic",
            "content": "<p>Think of this like labeling wires in a car. If everything is labeled clearly, the system can react quickly and correctly. If not, things get confusing fast!</p>"
        }
    }
},

{
    "title": "Step 2 — Activate the System ⚙️",
    "tip": "Tell your system what each part is supposed to do.",
    "tabs": {
        "explain": {
            "label": "📖 What & Why",
            "content": "<p>Now that your system knows the parts, you need to tell it how each one behaves using <b>pin modes</b>.</p><br><p>There are two main types:</p><ul><li>📤 <b>OUTPUT</b> → sends signals (LEDs, buzzer, trigger pin)<br><br></li><li>📥 <b>INPUT</b> → receives signals (echo pin)</li></ul><p>This step prepares your system so it can send and receive information properly.</p>"
        },
        "howto": {
            "label": "🔧 How To",
            "content": "<p>1. Go into the <b>setup</b> section.</p><p>2. Set each pin to the correct mode:</p><ul><li>Trigger, buzzer, and LEDs → OUTPUT</li><li>Echo pin → INPUT</li></ul><p>3. Turn on communication with the screen so you can see information later.</p><p>This step only runs once when the system starts.</p>"
        },
        "logic": {
            "label": "🧠 Logic",
            "content": "<p>Imagine plugging in devices at home. Some devices send signals (like a remote), while others receive them (like a TV). If you mix them up, nothing works correctly!</p>"
        }
    }
},

{
    "title": "Step 3 — Prepare the Sensor 📡",
    "tip": "Reset the sensor before sending a signal.",
    "tabs": {
        "explain": {
            "label": "📖 What & Why",
            "content": "<p>The ultrasonic sensor works by sending out a sound wave and listening for it to return.</p><br><p>Before sending a new signal, we must make sure the trigger is turned <b>OFF</b> first.</p><p>This clears any leftover signal so the next reading is accurate.</p><br><p>We also wait a very tiny amount of time to let the sensor settle.</p>"
        },
        "howto": {
            "label": "🔧 How To",
            "content": "<p>1. Inside the loop, turn the trigger pin OFF.</p><p>2. Add a very short delay so the sensor resets properly. Lets use 2 microseconds.</p><p>This prepares the sensor for a clean measurement.</p>"
        },
        "logic": {
            "label": "🧠 Logic",
            "content": "<p>Think of this like taking a deep breath before speaking. You reset first, then send a clear signal. Without resetting, your readings can get messy and unreliable.</p>"
        }
    }
},

{
    "title": "Step 4 — Send the Signal 🚀",
    "tip": "Send out a quick signal to measure distance.",
    "tabs": {
        "explain": {
            "label": "📖 What & Why",
            "content": "<p>Now it's time for your sensor to send out a signal!</p><br><p>The ultrasonic sensor works by sending a tiny burst of sound that travels through the air.</p><p>To do this, we briefly turn the <b>trigger pin ON</b>, then turn it OFF again.</p><br><p>This creates a short pulse — like a quick clap — that starts the measurement.</p><p>The timing of this pulse is very important, so we only leave it on for a very tiny amount of time.</p>"
        },
        "howto": {
            "label": "🔧 How To",
            "content": "<p>1. Turn the trigger pin ON.</p><p>2. Wait a very short time (just enough for the signal to send). Lets use 10 microseconds.</p><p>3. Turn the trigger pin OFF again.</p><p>This creates the pulse that tells the sensor to begin measuring distance.</p>"
        },
        "logic": {
            "label": "🧠 Logic",
            "content": "<p>Like using a walkie-talkie:  You press the button and say something quickly, then you let go to listen If you hold the button down the whole time, you can’t hear the other person at all.</p><p>👉 The trigger pulse is like pressing the button quickly, then letting go so you can listen.</p>"
        }
    }
},

{
    "title": "Step 5 — Listen for the Echo 👂",
    "tip": "Measure how long it takes for the signal to return.",
    "tabs": {
        "explain": {
            "label": "📖 What & Why",
            "content": "<p>After sending the signal, your sensor listens for it to come back.</p><br><p>The sound wave travels forward, hits an object, and bounces back to the sensor.</p><p>We measure how long this takes using a special function.</p><br><p>This time is stored in a variable called <b>duration</b>.</p><p>The longer the time, the farther away the object is.</p>"
        },
        "howto": {
            "label": "🔧 How To",
            "content": "<p>1. Use the echo pin to listen for the returning signal.</p><p>2. Store the time it takes in the <b>duration</b> variable.</p><p>This value will be used to calculate distance in the next step.</p>"
        },
        "logic": {
            "label": "🧠 Logic",
            "content": "<p>This is like yelling and waiting for your echo. If it comes back quickly, the wall is close. If it takes longer, the wall is farther away.</p>"
        }
    }
},

{
    "title": "Step 6 — Calculate Distance 📏",
    "tip": "Turn time into a real-world distance.",
    "tabs": {
        "explain": {
            "label": "📖 What & Why",
            "content": "<p>Now we turn the time measurement into distance!</p><br><p>Sound travels at a known speed through the air. By using this speed, we can convert the time into how far away something is.</p><br><p>We divide the result by 2 because the sound travels to the object <b>and back</b>.</p><br><p><b>But what if we don’t hear anything back?</b></p><p>If no echo is received, it means nothing was detected. In that case, we treat the object as being very far away.</p><br><p>This final value is stored in the <b>distance</b> variable.</p>"
        },
        "howto": {
            "label": "🔧 How To",
            "content": "<p>1. Check if a duration was received.</p><p>2. If not, set distance to a large value (like 999).</p><p>3. Otherwise, convert duration into distance using the formula.</p><p>4. Store the result in the <b>distance</b> variable.</p><p>This gives your system real-world information it can react to.</p>"
        },
        "logic": {
            "label": "🧠 Logic",
            "content": "<p>Imagine timing how long it takes for a ball to bounce off a wall and come back.</p><p>If you hear the bounce, you can calculate how far away the wall is.</p><p><b>If you don’t hear anything</b>, it probably means the wall is too far away — so you assume it's far.</p>"
        }
    }
},

{
    "title": "Step 7 — Safe Zone Check 🟢",
    "tip": "Decide when everything is safe.",
    "tabs": {
        "explain": {
            "label": "📖 What & Why",
            "content": "<p>Your system now knows the distance — but it needs to decide what that means.</p><br><p>We use an <b>if statement</b> to check conditions.</p><p>This lets the system ask a question like:</p><p><b>“Is the object far enough away to be safe?”</b></p><br><p>If the answer is YES, the system will enter the safe zone.</p><p>This is the first decision your system makes.</p>"
        },
        "howto": {
            "label": "🔧 How To",
            "content": "<p>1. Create an <b>if</b> condition.</p><p>2. Check if the distance is greater than the safe value.</p><p>We chose 50 because it’s a middle distance that makes the alarm react at a useful time — not too early and not too late.</p><p>3. Open the block where your safe actions will go.</p><p>This tells your system when everything is safe.</p>"
        },
        "logic": {
            "label": "🧠 Logic",
            "content": "<p>This is like checking your surroundings before stepping back. If nothing is close, you’re safe to move.</p>"
        }
    }
},

{
    "title": "Step 8 — Safe Zone Response 🟢",
    "tip": "Show that everything is safe.",
    "tabs": {
        "explain": {
            "label": "📖 What & Why",
            "content": "<p>When the system detects a safe distance, it should clearly show that everything is okay.</p><br><p>We do this by:</p><ul><li>💡 Turning the <b>green LED ON</b></li><li>⚫ Turning the other LEDs OFF</li><li>🔇 Keeping the buzzer silent</li></ul><p>This gives clear feedback to the driver: no danger detected.</p>"
        },
        "howto": {
            "label": "🔧 How To",
            "content": "<p>1. Turn the buzzer OFF so there is no sound.</p><p>2. Turn the green LED ON.</p><p>3. Turn the yellow and red LEDs OFF.</p><p>Make sure every light is controlled so there is no confusion.</p>"
        },
        "logic": {
            "label": "🧠 Logic",
            "content": "<p>Think of a traffic light. Green means go — everything is clear. No sound, no warning, just safe movement.</p>"
        }
    }
},

{
    "title": "Step 9 — Warning Zone Check 🟡",
    "tip": "Detect when things are getting closer.",
    "tabs": {
        "explain": {
            "label": "📖 What & Why",
            "content": "<p>Not everything is either safe or dangerous — sometimes you're getting close.</p><br><p>We use an <b>else if</b> statement to check a second condition.</p><p>This only runs if the first condition (safe zone) was NOT true.</p><br><p>Now the system asks:</p><p><b>“Is the object getting close, but not too close?”</b></p><p>This creates a middle warning zone.</p>"
        },
        "howto": {
            "label": "🔧 How To",
            "content": "<p>1. Add an <b>else if</b> after your first condition.</p><p>2. Check if the distance is greater than the warning threshold.</p><p>3. Let use 20 for this number.  That means its closer than 50 but not too close.</p><p>This creates a second level of awareness in your system.</p>"
        },
        "logic": {
            "label": "🧠 Logic",
            "content": "<p>This is like a yellow traffic light. You’re not in danger yet, but you need to pay attention and slow down.</p>"
        }
    }
},

{
    "title": "Step 10 — Warning Response 🟡",
    "tip": "Alert the driver with a repeating beep.",
    "tabs": {
        "explain": {
            "label": "📖 What & Why",
            "content": "<p>When an object is getting close, the system should warn the driver — but not panic yet.</p><br><p>We do this using a <b>buzzer</b> that turns ON and OFF repeatedly.</p><p>This creates a beeping sound.</p><br><p>The pattern works like this:</p><ul><li>🔊 Turn sound ON</li><li>⏳ Wait</li><li>🔇 Turn sound OFF</li><li>⏳ Wait again</li></ul><p>This repeating pattern creates the familiar \"beep... beep...\" warning sound.</p><br><p>We also turn on the yellow LED to show caution.</p>"
        },
        "howto": {
            "label": "🔧 How To",
            "content": "<p>1. Turn the buzzer ON using a tone.  We will use a frequency of 1000 Hz. This frequency decided the tone the buzzer will make.</p><p>2. Wait for a short amount of time. 300 ms.</p><p>3. Turn the buzzer OFF.</p><p>4. Wait again.  300 ms.</p><p>5. Set the LEDs so only the yellow light is ON. and the other two are off.</p><p>This creates a repeating warning signal.</p>"
        },
        "logic": {
            "label": "🧠 Logic",
            "content": "<p>This is like a car slowly getting closer to something. The system says: \"Be careful… something is getting close.\" The repeating sound grabs attention without causing panic.</p>"
        }
    }
},

{
    "title": "Step 11 — Danger Zone 🚨",
    "tip": "Trigger a constant alert when too close.",
    "tabs": {
        "explain": {
            "label": "📖 What & Why",
            "content": "<p>If the object is very close, the system must react immediately.</p><br><p>This is the <b>danger zone</b>.</p><p>Instead of beeping, the buzzer stays ON continuously to create urgency.</p><br><p>We also turn on the red LED to clearly show danger.</p><p>This tells the driver: <b>STOP NOW!</b></p>"
        },
        "howto": {
            "label": "🔧 How To",
            "content": "<p>1. Add an <b>else</b> block for when no other conditions are true.</p><p>2. Turn the buzzer ON and keep it ON. Lets use a frequency of 1500 now so our buzzer makes a higher pitched sound.</p><p>3. Turn the red LED ON.</p><p>4. Turn the other LEDs OFF.</p><p>This creates a strong, clear danger signal.</p>"
        },
        "logic": {
            "label": "🧠 Logic",
            "content": "<p>This is like a loud alarm going off when you're about to hit something. No more warnings — it’s time to stop immediately!</p>"
        }
    }
},

{
    "title": "Step 12 — System Loop 🔁",
    "tip": "Keep the system running smoothly.",
    "tabs": {
        "explain": {
            "label": "📖 What & Why",
            "content": "<p>Your system runs over and over again inside a loop.</p><br><p>Without a small pause, it would run too fast and could cause unstable readings.</p><p>We add a short delay to give the system time to reset before the next measurement.</p><br><p>This makes the sensor more stable and reliable.</p>"
        },
        "howto": {
            "label": "🔧 How To",
            "content": "<p>1. At the end of the loop, add a small delay. Lets use 50 ms.</p><p>2. This delay should be short — just enough to stabilize the system.</p><p>3. The loop will then repeat automatically.</p><p>This keeps your system running smoothly.</p>"
        },
        "logic": {
            "label": "🧠 Logic",
            "content": "<p>Think of this like blinking your eyes. You don’t constantly stare without pause — small breaks help everything stay clear and stable.</p>"
        }
    }
},
{
    "title": "Step 13 — Mission Complete 🎉",
    "tip": "Your backup alarm system is fully operational!",
    "tabs": {
        "explain": {
            "label": "📖 What You Built",
            "content": "<p>🚗 Congratulations, Engineer!</p><br><p>You successfully designed and built a <b>smart backup alarm system</b> — just like the ones used in real cars.</p><br><p>Your system can:</p><ul><li>📡 Measure distance using an ultrasonic sensor</li><li>🧠 Make decisions based on that distance</li><li>💡 Show safe, warning, and danger zones using LEDs</li><li>🔊 Alert the driver using sound patterns</li></ul><p>You didn’t just write code — you built a real-world system that senses, thinks, and reacts.</p>"
        },
        "howto": {
            "label": "🔧 Try This Next",
            "content": "<p>Now that your system works, try improving it!</p><br><p>Here are some ideas:</p><ul><li>⚡ Change the distance values to make the system more or less sensitive</li><li>🔊 Make the beeping faster as objects get closer</li><li>🌈 Add more LEDs for smoother distance levels</li><li>📺 Display the distance on a screen</li><li>🎮 Turn it into a game or challenge system</li></ul><p>Experimenting is how real engineers improve their designs!</p>"
        },
        "logic": {
            "label": "🧠 What You Learned",
            "content": "<p>This project brought together everything you’ve been learning:</p><ul><li>📦 Variables to store important information</li><li>⚙️ Setup to prepare your system</li><li>📡 Sensors to collect real-world data</li><li>🧠 Logic to make decisions (if / else if / else)</li><li>💡 Outputs to respond with lights and sound</li><li>🔁 Loops to keep everything running continuously</li></ul><br><p>This is how real systems work — input → thinking → output.</p><p>You are now thinking like an engineer. 🚀</p>"
        },
        "sim": {
            "label": "🎮 Try It",
            "type": "sim",
            "sim_config": {
                "components": [
                    {"type": "sonar",  "id": "sonar1",    "label": "Distance Sensor", "pin_trig": 9, "pin_echo": 10},
                    {"type": "led",    "id": "greenLED",  "color": "green",  "pin": 4, "label": "Safe"},
                    {"type": "led",    "id": "yellowLED", "color": "yellow", "pin": 5, "label": "Warning"},
                    {"type": "led",    "id": "redLED",    "color": "red",    "pin": 6, "label": "Danger"},
                    {"type": "buzzer", "id": "buz1",                         "pin": 3, "label": "Buzzer"},
                ],
                "behaviors": [
                    {
                        "when": {"sonar1": "safe"},
                        "then": {"greenLED": "on", "yellowLED": "off", "redLED": "off", "buz1": "off", "_stop_beep": "yes"}
                    },
                    {
                        "when": {"sonar1": "warning"},
                        "then": {"greenLED": "off", "yellowLED": "on", "redLED": "off", "_stop_beep": "yes", "_beep": "buz1", "_beep_interval": 400}
                    },
                    {
                        "when": {"sonar1": "danger"},
                        "then": {"greenLED": "off", "yellowLED": "off", "redLED": "on", "buz1": "on", "_stop_beep": "yes"}
                    },
                ]
            }
        }
    }
 }
    ]
  }
}

SKETCH_PRESET = {   
        'sketch': """
//>> Step 1 - Define Global Variables | guided | blocks | filter:true

//?? Define trigPin
int trigPin = 9;

//?? Define echoPin
int echoPin = 10;

//?? Define buzzerPin
int buzzerPin = 3;

//?? Define greenLED
int greenLED = 4;

//?? Define yellowLED
int yellowLED = 5;

//?? Define redLED
int redLED = 6;

//?? Define duration
long duration = 0;

//?? Define distance
int distance = 0;

void setup() {
    }
void loop() {
    }

//>> Step 2 - Setup the System | guided

void setup() {
  //?? Set trigPin as OUTPUT
  pinMode(trigPin, OUTPUT);

  //?? Set echoPin as INPUT
  pinMode(echoPin, INPUT);

  //?? Set buzzerPin as OUTPUT
  pinMode(buzzerPin, OUTPUT);

  //?? Set greenLED as OUTPUT
  pinMode(greenLED, OUTPUT);

  //?? Set yellowLED as OUTPUT
  pinMode(yellowLED, OUTPUT);

  //?? Set redLED as OUTPUT
  pinMode(redLED, OUTPUT);

  Serial.begin(9600);
}

void loop() {
}

//>> Step 3 - Prepare Sensor | guided

void loop() {
  //?? Set trigPin LOW
  digitalWrite(trigPin, LOW);

  //?? Small delay
  delayMicroseconds(2);
}

//>> Step 4 - Send Pulse | guided

void loop() {
  //## digitalWrite(trigPin, LOW);
  //## delayMicroseconds(2);

  //?? Set trigPin HIGH
  digitalWrite(trigPin, HIGH);

  //?? Wait 10 microseconds
  delayMicroseconds(10);

  //?? Set trigPin LOW
  digitalWrite(trigPin, LOW);
}

//>> Step 5 - Read Echo | free

void loop() {
  //## digitalWrite(trigPin, LOW);
  //## delayMicroseconds(2);
  //## digitalWrite(trigPin, HIGH);
  //## delayMicroseconds(10);
  //## digitalWrite(trigPin, LOW);

  //## Read duration from echoPin
  duration = pulseIn(echoPin, HIGH);
}

//>> Step 6 - Calculate Distance | guided | blocks | filter:true

void loop() {
  //## digitalWrite(trigPin, LOW);
  //## delayMicroseconds(2);
  //## digitalWrite(trigPin, HIGH);
  //## delayMicroseconds(10);
  //## digitalWrite(trigPin, LOW);
  //## duration = pulseIn(echoPin, HIGH);

  //?? If no echo received
  if (duration == 0) {
    //?? Set distance to a far value
    distance = 999;
  }
  else {
    //## distance = duration * 0.034 / 2;
  }
}

//>> Step 7 - Safe Zone Check | guided | blocks | filter:true

void loop() {
  //## digitalWrite(trigPin, LOW);
  //## delayMicroseconds(2);
  //## digitalWrite(trigPin, HIGH);
  //## delayMicroseconds(10);
  //## digitalWrite(trigPin, LOW);
  //## duration = pulseIn(echoPin, HIGH);
  //## if (duration == 0) {
  //##   distance = 999;
  //## }
  //## else {
  //##   distance = duration * 0.034 / 2;
  //## }

  //?? If distance > 50
  if (distance > 50) {
  }
}

//>> Step 8 - Safe Zone Output | guided

void loop() {
  //## digitalWrite(trigPin, LOW);
  //## delayMicroseconds(2);
  //## digitalWrite(trigPin, HIGH);
  //## delayMicroseconds(10);
  //## digitalWrite(trigPin, LOW);
  //## duration = pulseIn(echoPin, HIGH);
  //## if (duration == 0) {
  //##   distance = 999;
  //## }
  //## else {
  //##   distance = duration * 0.034 / 2;
  //## }
  //## if (distance > 50) {

  //?? Turn buzzer OFF
  noTone(buzzerPin);

  //?? Turn green LED ON
  digitalWrite(greenLED, HIGH);

  //?? Turn yellow LED OFF
  digitalWrite(yellowLED, LOW);

  //?? Turn red LED OFF
  digitalWrite(redLED, LOW);

  //## }
}

//>> Step 9 - Warning Zone Check | guided | blocks | filter:true

void loop() {
  //## digitalWrite(trigPin, LOW);
  //## delayMicroseconds(2);
  //## digitalWrite(trigPin, HIGH);
  //## delayMicroseconds(10);
  //## digitalWrite(trigPin, LOW);
  //## duration = pulseIn(echoPin, HIGH);
  //## if (duration == 0) {
  //##   distance = 999;
  //## }
  //## else {
  //##   distance = duration * 0.034 / 2;
  //## }
  //## if (distance > 50) {
  //##   noTone(buzzerPin);
  //##   digitalWrite(greenLED, HIGH);
  //##   digitalWrite(yellowLED, LOW);
  //##   digitalWrite(redLED, LOW);
  //## }

  //?? Else if distance > 20
  else if (distance > 20) {
  }
}

//>> Step 10 - Warning Zone Output | guided | filter:true

void loop() {
  //## digitalWrite(trigPin, LOW);
  //## delayMicroseconds(2);
  //## digitalWrite(trigPin, HIGH);
  //## delayMicroseconds(10);
  //## digitalWrite(trigPin, LOW);
  //## duration = pulseIn(echoPin, HIGH);
  //## if (duration == 0) {
  //##   distance = 999;
  //## }
  //## else {
  //##   distance = duration * 0.034 / 2;
  //## }
  //## if (distance > 50) {
  //##   noTone(buzzerPin);
  //##   digitalWrite(greenLED, HIGH);
  //##   digitalWrite(yellowLED, LOW);
  //##   digitalWrite(redLED, LOW);
  //## }
  //## else if (distance > 20) {

  //?? Turn buzzer ON (1000 Hz)
  tone(buzzerPin, 1000);

  //?? Delay 300 ms
  delay(300);

  //?? Turn buzzer OFF
  noTone(buzzerPin);

  //?? Delay 300 ms
  delay(300);

  //?? Turn green LED OFF
  digitalWrite(greenLED, LOW);

  //?? Turn yellow LED ON
  digitalWrite(yellowLED, HIGH);

  //?? Turn red LED OFF
  digitalWrite(redLED, LOW);

  //## }
}

//>> Step 11 - Danger Zone | guided | blocks | filter:true

void loop() {
  //## digitalWrite(trigPin, LOW);
  //## delayMicroseconds(2);
  //## digitalWrite(trigPin, HIGH);
  //## delayMicroseconds(10);
  //## digitalWrite(trigPin, LOW);
  //## duration = pulseIn(echoPin, HIGH);
  //## if (duration == 0) {
  //##   distance = 999;
  //## }
  //## else {
  //##   distance = duration * 0.034 / 2;
  //## }
  //## if (distance > 50) {
  //##   noTone(buzzerPin);
  //##   digitalWrite(greenLED, HIGH);
  //##   digitalWrite(yellowLED, LOW);
  //##   digitalWrite(redLED, LOW);
  //## }
  //## else if (distance > 20) {
  //##   tone(buzzerPin, 1000);
  //##   delay(300);
  //##   noTone(buzzerPin);
  //##   delay(300);
  //##   digitalWrite(greenLED, LOW);
  //##   digitalWrite(yellowLED, HIGH);
  //##   digitalWrite(redLED, LOW);
  //## }

  //?? Else (very close)
  else {

    //?? Turn buzzer ON (1500 Hz)
    tone(buzzerPin, 1500);

    //?? Turn green LED OFF
    digitalWrite(greenLED, LOW);

    //?? Turn yellow LED OFF
    digitalWrite(yellowLED, LOW);

    //?? Turn red LED ON
    digitalWrite(redLED, HIGH);
  }
}

//>> Step 12 - Loop Delay | guided

void loop() {
  //## digitalWrite(trigPin, LOW);
  //## delayMicroseconds(2);
  //## digitalWrite(trigPin, HIGH);
  //## delayMicroseconds(10);
  //## digitalWrite(trigPin, LOW);
  //## duration = pulseIn(echoPin, HIGH);
  //## if (duration == 0) {
  //##   distance = 999;
  //## }
  //## else {
  //##   distance = duration * 0.034 / 2;
  //## }
  //## if (distance > 50) {
  //##   noTone(buzzerPin);
  //##   digitalWrite(greenLED, HIGH);
  //##   digitalWrite(yellowLED, LOW);
  //##   digitalWrite(redLED, LOW);
  //## }
  //## else if (distance > 20) {
  //##   tone(buzzerPin, 1000);
  //##   delay(300);
  //##   noTone(buzzerPin);
  //##   delay(300);
  //##   digitalWrite(greenLED, LOW);
  //##   digitalWrite(yellowLED, HIGH);
  //##   digitalWrite(redLED, LOW);
  //## }
  //## else {
  //##   tone(buzzerPin, 1500);
  //##   digitalWrite(greenLED, LOW);
  //##   digitalWrite(yellowLED, LOW);
  //##   digitalWrite(redLED, HIGH);
  //## }

  //?? Small delay for stability
  delay(50);
}

//>> Step 13 - Complete System | open

void loop() {
  //## digitalWrite(trigPin, LOW);
  //## delayMicroseconds(2);
  //## digitalWrite(trigPin, HIGH);
  //## delayMicroseconds(10);
  //## digitalWrite(trigPin, LOW);
  //## duration = pulseIn(echoPin, HIGH);
  //## if (duration == 0) {
  //##   distance = 999;
  //## }
  //## else {
  //##   distance = duration * 0.034 / 2;
  //## }
  //## if (distance > 50) {
  //##   noTone(buzzerPin);
  //##   digitalWrite(greenLED, HIGH);
  //##   digitalWrite(yellowLED, LOW);
  //##   digitalWrite(redLED, LOW);
  //## }
  //## else if (distance > 20) {
  //##   tone(buzzerPin, 1000);
  //##   delay(300);
  //##   noTone(buzzerPin);
  //##   delay(300);
  //##   digitalWrite(greenLED, LOW);
  //##   digitalWrite(yellowLED, HIGH);
  //##   digitalWrite(redLED, LOW);
  //## }
  //## else {
  //##   tone(buzzerPin, 1500);
  //##   digitalWrite(greenLED, LOW);
  //##   digitalWrite(yellowLED, LOW);
  //##   digitalWrite(redLED, HIGH);
  //## }
  //## delay(50);
//##}
"""
    }



CHALLENGE_PRESET = {
    'sketch': '...',
    'default_view': 'blocks',
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