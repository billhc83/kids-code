from utils.step_builder import build_step, intro_step, rect, circle, line, lbl


META = {
    'title': 'Project 18: Drag Race Speed Tracker',
    'circuit_image': 'static/graphics/project_eighteen_circuit.png',
    'banner_image': 'project_eighteen_banner.png',
    'lesson_type': 'progression',
}


# Wiring and component placement steps.
# rect() / circle() / line() coordinates are placeholders —
# update with real pixel coords once the circuit image is available.
STEPS = [
    intro_step(
        "Lets wire up the speed sensor",
        "",
    ),

    build_step(
        """In your first bread board <br>
Place VCC in row 7 column H
Place TRIG in row 8 column H
Place ECHO in row 9 column H
Place GND in row 10 column H""",
        "",
        rect(752, 76, 1273, 355),
        greyout=True,
    ),

    build_step(
        """In your second breadboard <br>
Place VCC in row 15 column H
Place TRIG in row 16 column H
Place ECHO in row 17 column H
Place GND in row 18 column H""",
        "",
        rect(2046, 84, 2575, 363),
        greyout=True,
    ),

    build_step(
        "Place one end of the wire in Arduino Pin 2.<br>Place the other end in row 8, column J.",
        "We are showin the wire in front of the sensor in the picture so we can see it, but make sure it goes into column J",
        line((503, 688), (722, 688), (761, 413), (997, 417), (997, 383), width=25),
        greyout=True,
    ),

    build_step(
        "Place one end of the wire in Arduino Pin 3.<br>Place the other end in row 8, column J.",
        "We are showing the wire in front of the sensor so we can see it,  make sure you actually plug it into column J",
        line((486, 657), (696, 657), (731, 360), (1023, 364), width=25),
        greyout=True,
    ),

    build_step(
        "Place one end of the wire in Arduino Pin 4.<br>Place the other end in row 21, column J.",
        "We are showing the wire in front of the sensor so we can see it,  make sure you actually plug it into column J",
        line((507, 626), (619, 635), (727, 93), (1642, 97), (1642, 411), (2291, 416), (2300, 385), width=25),
        greyout=True,
    ),

    build_step(
        "Place one end of the wire in Arduino Pin 5.<br>Place the other end in Arduino Pin 22.",
        "We are showing the wire in front of the sensor so we can see it,  make sure you actually plug it into column J",
        line((503, 594), (589, 603), (696, 65), (1672, 70), (1672, 358), (2317, 358), width=25),
        greyout=True,
    ),

    build_step(
        "Place one end of the wire in Arduino Pin 5V.<br>Place the other end in the positive / + rail.",
        "",
        line((9, 453), (404, 732), (860, 732), (877, 680), width=25),
        greyout=True,
    ),

    build_step(
        "Place one end of the wire in Arduino Pin GND.<br>Place the other end in the negative / - rail.",
        "",
        line((17, 513), (383, 771), (1371, 767), (1419, 651), width=25),
        greyout=True,
    ),

    build_step(
        "Place one end of the wire in the negative / - rail.<br>Place the other end in the negative / - rail.",
        "",
        line((1561, 659), (1763, 655), width=25),
        greyout=True,
    ),

    build_step(
        "Place one end of the wire in the positive / + rail.<br>Place the other end in the positive / + rail.",
        "",
        line((1569, 686), (1771, 686), width=25),
        greyout=True,
    ),

    build_step(
        "Place one end of the wire in the positive / + rail.<br>Place the other end in Arduino Pin 7.",
        "Make sure the wire is not in front of the sensor",
        line((980, 703), (967, 372), width=25),
        greyout=True,
    ),

    build_step(
        "Place one end of the wire in the positive / + rail.<br>Place the other end in row 20, column J.",
        "Make sure the wire is not in front of the sensor",
        line((2279, 696), (2270, 373), width=25),
        greyout=True,
    ),

    build_step(
        "Place one end of the wire in the negative / - rail.<br>Place the other end in Arduino Pin 10.",
        "Make sure your wire is not in front of the sensor",
        line((1088, 669), (1049, 368), width=25),
        greyout=True,
    ),

    build_step(
        "Place one end of the wire in the negative / - rail.<br>Place the other end in row 23, column J.",
        "Make sure your wire is not in front of the sensor",
        line((2356, 678), (2347, 373), width=25),
        greyout=True,
    ),

]


SKETCH_PRESET = {
    'sketch': """//>> Step 1 — Sensor Pin Variables | guided | blocks

//?? Declare Sensor A trigger pin
int trigA = 2;
//?? Declare Sensor A echo pin
int echoA = 3;
//?? Declare Sensor B trigger pin
int trigB = 4;
//?? Declare Sensor B echo pin
int echoB = 5;

//>> Step 2 — Timing & State Vars | guided | blocks

//?? Set the distance between sensors
float distance = 0.20;
//?? Create a timer for Sensor A
unsigned long timeA = 0;
//?? Track if Sensor A saw something
bool sawA = false;
//## unsigned long timeB = 0;
//## bool sawB = false;

//>> Step 3 — Setup | guided | blocks

void setup() {
  //?? Start the serial monitor
  Serial.begin(9600);
  //?? Set Sensor A trigger as output
  pinMode(trigA, OUTPUT);
  //?? Set Sensor A echo as input
  pinMode(echoA, INPUT);
  //?? Set Sensor B trigger as output
  pinMode(trigB, OUTPUT);
  //?? Set Sensor B echo as input
  pinMode(echoB, INPUT);
  //## Serial.println("Ready!");
}

void loop() {}

//>> Step 4 — Fire Sensor A | guided | blocks

void setup() {}

void loop() {
  //?? Pull Sensor A trigger low to start
  digitalWrite(trigA, LOW);
  //## delayMicroseconds(2);
  //?? Send the Sensor A sound pulse
  digitalWrite(trigA, HIGH);
  //## delayMicroseconds(10);
  //?? End the Sensor A pulse
  digitalWrite(trigA, LOW);
}

//>> Step 5 — Read Sensor A Distance | guided | blocks

void setup() {}

void loop() {
  //## digitalWrite(trigA, LOW);
  //## delayMicroseconds(2);
  //## digitalWrite(trigA, HIGH);
  //## delayMicroseconds(10);
  //## digitalWrite(trigA, LOW);

  //?? Measure echo time from Sensor A
  long durationA = pulseIn(echoA, HIGH);
  //?? Calculate Sensor A distance
  long distanceA = durationA * 0.034 / 2;
}

//>> Step 6 — Fire Sensor B | guided | blocks

void setup() {}

void loop() {
  //## digitalWrite(trigA, LOW);
  //## delayMicroseconds(2);
  //## digitalWrite(trigA, HIGH);
  //## delayMicroseconds(10);
  //## digitalWrite(trigA, LOW);
  //## long durationA = pulseIn(echoA, HIGH);
  //## long distanceA = durationA * 0.034 / 2;

  //?? Pull Sensor B trigger low to start
  digitalWrite(trigB, LOW);
  //## delayMicroseconds(2);
  //?? Send the Sensor B sound pulse
  digitalWrite(trigB, HIGH);
  //## delayMicroseconds(10);
  //?? End the Sensor B pulse
  digitalWrite(trigB, LOW);
}

//>> Step 7 — Read Sensor B Distance | guided | blocks

void setup() {}

void loop() {
  //## digitalWrite(trigA, LOW);
  //## delayMicroseconds(2);
  //## digitalWrite(trigA, HIGH);
  //## delayMicroseconds(10);
  //## digitalWrite(trigA, LOW);
  //## long durationA = pulseIn(echoA, HIGH);
  //## long distanceA = durationA * 0.034 / 2;
  //## digitalWrite(trigB, LOW);
  //## delayMicroseconds(2);
  //## digitalWrite(trigB, HIGH);
  //## delayMicroseconds(10);
  //## digitalWrite(trigB, LOW);

  //?? Measure echo time from Sensor B
  long durationB = pulseIn(echoB, HIGH);
  //?? Calculate Sensor B distance
  long distanceB = durationB * 0.034 / 2;
}

//>> Step 8 — Detect at Sensor A | guided | blocks

void setup() {}

void loop() {
  //## digitalWrite(trigA, LOW);
  //## delayMicroseconds(2);
  //## digitalWrite(trigA, HIGH);
  //## delayMicroseconds(10);
  //## digitalWrite(trigA, LOW);
  //## long durationA = pulseIn(echoA, HIGH);
  //## long distanceA = durationA * 0.034 / 2;
  //## digitalWrite(trigB, LOW);
  //## delayMicroseconds(2);
  //## digitalWrite(trigB, HIGH);
  //## delayMicroseconds(10);
  //## digitalWrite(trigB, LOW);
  //## long durationB = pulseIn(echoB, HIGH);
  //## long distanceB = durationB * 0.034 / 2;

  //?? Check if Sensor A spotted something close
  if (distanceA < 30 && sawA == false) {
    //?? Record the time at Sensor A
    timeA = micros();
    //?? Mark that Sensor A saw the object
    sawA = true;
    //## Serial.println("Saw A");
  }
}

//>> Step 9 — Detect at Sensor B | guided | blocks

void setup() {}

void loop() {
  //## digitalWrite(trigA, LOW);
  //## delayMicroseconds(2);
  //## digitalWrite(trigA, HIGH);
  //## delayMicroseconds(10);
  //## digitalWrite(trigA, LOW);
  //## long durationA = pulseIn(echoA, HIGH);
  //## long distanceA = durationA * 0.034 / 2;
  //## digitalWrite(trigB, LOW);
  //## delayMicroseconds(2);
  //## digitalWrite(trigB, HIGH);
  //## delayMicroseconds(10);
  //## digitalWrite(trigB, LOW);
  //## long durationB = pulseIn(echoB, HIGH);
  //## long distanceB = durationB * 0.034 / 2;
  //## if (distanceA < 30 && sawA == false) {
  //##   timeA = micros();
  //##   sawA = true;
  //##   Serial.println("Saw A");
  //## }

  //?? Check if Sensor B caught the object
  if (distanceB < 30 && sawA == true && sawB == false) {
    //?? Record the time at Sensor B
    timeB = micros();
    //?? Mark that Sensor B saw the object
    sawB = true;
    //## Serial.println("Saw B");
  }
}

//>> Step 10 — Calculate & Show Speed | guided | blocks

void setup() {}

void loop() {
  //## digitalWrite(trigA, LOW);
  //## delayMicroseconds(2);
  //## digitalWrite(trigA, HIGH);
  //## delayMicroseconds(10);
  //## digitalWrite(trigA, LOW);
  //## long durationA = pulseIn(echoA, HIGH);
  //## long distanceA = durationA * 0.034 / 2;
  //## digitalWrite(trigB, LOW);
  //## delayMicroseconds(2);
  //## digitalWrite(trigB, HIGH);
  //## delayMicroseconds(10);
  //## digitalWrite(trigB, LOW);
  //## long durationB = pulseIn(echoB, HIGH);
  //## long distanceB = durationB * 0.034 / 2;
  //## if (distanceA < 30 && sawA == false) {
  //##   timeA = micros();
  //##   sawA = true;
  //##   Serial.println("Saw A");
  //## }
  //## if (distanceB < 30 && sawA == true && sawB == false) {
  //##   timeB = micros();
  //##   sawB = true;
  //##   Serial.println("Saw B");
  //## }

  //?? Check if both sensors caught the object
  if (sawA == true && sawB == true) {
    //## float timeDiff = (timeB - timeA) / 1000000.0;
    //?? Calculate speed from distance and time
    float speed = distance / timeDiff;
    //## Serial.print("Speed m/s: ");
    //?? Display the speed on the monitor
    Serial.println(speed);
    //?? Reset Sensor A for the next race
    sawA = false;
    //## sawB = false;
    //?? Wait one second before the next race
    delay(1000);
  }
}

//>> Mission Complete | open | blocks""",
    'default_view': 'blocks',
    'read_only': False,
    'lock_view': False,
    'fill_values': True,
    'fill_conditions': True,
}


DRAWER_CONTENT = {
    "project_eighteen": {
        "steps": [
            {
                "title": "Step 1 — Sensor Pin Variables 📡",
                "tip": "Give each sensor pin a name so your Arduino knows where to look!",
                "tabs": {
                    "explain": {
                        "label": "📖 What & Why",
                        "content": "<p>Before your speed trap can do anything, it needs to know where its sensors are plugged in! 📡 Every sensor has two wires — one that shouts (trigger) and one that listens (echo).</p><p>Without these labels, your Arduino has no idea which pins to use. 🔌</p>"
                    },
                    "howto": {
                        "label": "🔧 How To",
                        "content": "<p><strong>1. Sensor A trigger pin</strong></p><p>📌 Tell the Arduino which pin Sensor A's trigger wire is plugged into.</p><p>🧱 Use a <strong>Declare number label</strong> block — it creates a named memory box holding a number.</p><p>🔢 Name: <code>trigA</code> | Value: <code>2</code> — the pin where the wire goes.</p><p>✅ Memory box trigA = 2 is ready!</p><hr><p><strong>2. Sensor A echo pin</strong></p><p>📌 Register Sensor A's echo wire pin.</p><p>🧱 Another <strong>Declare number label</strong> block.</p><p>🔢 Name: <code>echoA</code> | Value: <code>3</code>.</p><p>✅ Sensor A's listener is registered! 👂</p><hr><p><strong>3. Sensor B trigger pin</strong></p><p>📌 Register Sensor B's trigger wire pin.</p><p>🧱 <strong>Declare number label</strong> block.</p><p>🔢 Name: <code>trigB</code> | Value: <code>4</code>.</p><p>✅ Sensor B's shouter is ready! 🔊</p><hr><p><strong>4. Sensor B echo pin</strong></p><p>📌 Register Sensor B's echo wire pin.</p><p>🧱 <strong>Declare number label</strong> block.</p><p>🔢 Name: <code>echoB</code> | Value: <code>5</code>.</p><p>✅ Both sensors fully mapped — your Arduino knows exactly where to look! 🏁</p>"
                    },
                    "logic": {
                        "label": "🧠 Logic",
                        "content": "<p>Think of each sensor like a walkie-talkie at the drag strip! 📻 One side shouts, the other listens.</p><p>Before the race starts, the pit crew writes down which radio belongs to which spot — that's exactly what these memory boxes do. 🏎️</p>"
                    }
                }
            },
            {
                "title": "Step 2 — Timing & State Vars ⏱️",
                "tip": "Set up your stopwatches and detection flags before the race begins!",
                "tabs": {
                    "explain": {
                        "label": "📖 What & Why",
                        "content": "<p>The sensor pins are mapped — now your speed trap needs three more things! 📋 It needs to know how far apart the sensors are, an empty stopwatch for Sensor A, and a flag to remember if something already passed through.</p><p>Without these, the calculator has nothing to work with when the object zooms by! ⏱️</p>"
                    },
                    "howto": {
                        "label": "🔧 How To",
                        "content": "<p><strong>1. Distance between sensors</strong></p><p>📌 Tell the Arduino how far apart your two sensors are placed.</p><p>🧱 Use a <strong>Declare decimal label</strong> block — it stores numbers with a decimal point.</p><p>🔢 Name: <code>distance</code> | Value: <code>0.20</code> (sensors are 20 cm apart). Change this if you move them!</p><p>✅ The Arduino knows your track length. 📏</p><hr><p><strong>2. Sensor A timer</strong></p><p>📌 Create an empty stopwatch to record when Sensor A fires.</p><p>🧱 Use a <strong>Declare big number label</strong> block — it holds the very large numbers needed for microsecond time.</p><p>🔢 Name: <code>timeA</code> | Start at <code>0</code> — the watch hasn't started yet.</p><p>✅ Stopwatch timeA is standing by! ⏱️</p><hr><p><strong>3. Sensor A detection flag</strong></p><p>📌 Create a yes/no flag that remembers if Sensor A already spotted something this run.</p><p>🧱 Use a <strong>Declare yes/no label</strong> block — it can only be true or false.</p><p>🔢 Name: <code>sawA</code> | Start at <code>false</code> — nothing has passed yet.</p><p>✅ The flag is down. Sensor A hasn't seen anything yet! 🚩</p><p><em>Locked: timeB and sawB are the matching boxes for Sensor B — pre-filled so you focus on one sensor at a time.</em></p>"
                    },
                    "logic": {
                        "label": "🧠 Logic",
                        "content": "<p>Think of sawA like the starting flag at a drag race! 🏁 Before a car passes, the flag is flat (false). The moment something crosses, the flag shoots up (true).</p><p>That way the timer knows a run already started and won't accidentally record it twice! 🚦</p>"
                    }
                }
            },
            {
                "title": "Step 3 — Setup ⚡",
                "tip": "Setup runs once at startup — every pin gets its job before the race begins!",
                "tabs": {
                    "explain": {
                        "label": "📖 What & Why",
                        "content": "<p>Time to power up the speed trap! ⚡ The setup runs once when your Arduino turns on. It opens the Serial Monitor so you can see results, then tells every sensor pin whether it should shout (OUTPUT) or listen (INPUT).</p><p>Without this step, the pins don't know their jobs and nothing works! 📡</p>"
                    },
                    "howto": {
                        "label": "🔧 How To",
                        "content": "<p><strong>1. Start the serial monitor</strong></p><p>📌 Open the connection between your Arduino and computer so you can read speed results.</p><p>🧱 Use a <strong>Start serial monitor</strong> block.</p><p>🔢 Speed: <code>9600</code> — both sides must use the same number.</p><p>✅ The Serial Monitor is ready to display your speed readings! 💻</p><hr><p><strong>2. Sensor A trigger mode</strong></p><p>📌 Tell the Arduino that Sensor A's trigger pin will send signals OUT.</p><p>🧱 Use a <strong>Set pin mode</strong> block.</p><p>🔢 Pin: <code>trigA</code> | Mode: <code>OUTPUT</code> — this pin SENDS the sound pulse.</p><p>✅ Sensor A's shouter is armed! 🔊</p><hr><p><strong>3. Sensor A echo mode</strong></p><p>📌 Tell the Arduino that Sensor A's echo pin will LISTEN for signals coming back.</p><p>🧱 <strong>Set pin mode</strong> block.</p><p>🔢 Pin: <code>echoA</code> | Mode: <code>INPUT</code>.</p><p>✅ Sensor A's ear is open! 👂</p><hr><p><strong>4. Sensor B trigger mode</strong></p><p>📌 Set Sensor B's trigger pin as a sender.</p><p>🧱 <strong>Set pin mode</strong> block.</p><p>🔢 Pin: <code>trigB</code> | Mode: <code>OUTPUT</code>.</p><p>✅ Sensor B can fire its pulse! 🔊</p><hr><p><strong>5. Sensor B echo mode</strong></p><p>📌 Set Sensor B's echo pin to listen.</p><p>🧱 <strong>Set pin mode</strong> block.</p><p>🔢 Pin: <code>echoB</code> | Mode: <code>INPUT</code>.</p><p>✅ Both sensors fully configured and ready to race! 🏁</p><p><em>Locked: Serial.println prints a startup message — open the Serial Monitor to confirm the board is alive.</em></p>"
                    },
                    "logic": {
                        "label": "🧠 Logic",
                        "content": "<p>Imagine you're the pit crew boss before race day! 🔧 You assign each crew member a job — some wave flags (OUTPUT), some hold stopwatches (INPUT).</p><p>That's setup: every pin gets its role before the action starts. 🏎️</p>"
                    }
                }
            },
            {
                "title": "Step 4 — Fire Sensor A 🔊",
                "tip": "The trigger sequence sends a tiny burst of sound — like a bat hunting in the dark!",
                "tabs": {
                    "explain": {
                        "label": "📖 What & Why",
                        "content": "<p>To check if something is nearby, Sensor A shoots out a tiny burst of sound — too high to hear, but perfect for bouncing off objects! 🦇 This step fires that burst in a very precise pattern: low, then high, then low again.</p><p>Without this exact sequence, the sensor won't fire correctly and no echoes will come back. 📡</p>"
                    },
                    "howto": {
                        "label": "🔧 How To",
                        "content": "<p><strong>1. Clear the trigger</strong></p><p>📌 Make sure the trigger pin is off before firing — like clearing a starting pistol before loading it.</p><p>🧱 Use a <strong>Digital write</strong> block.</p><p>🔢 Pin: <code>trigA</code> | Value: <code>LOW</code> (off) — wipes any leftover signal.</p><p>✅ Trigger is clean and ready.</p><hr><p><strong>2. Fire the pulse</strong></p><p>📌 Turn the trigger ON to shoot the sound burst from the sensor.</p><p>🧱 <strong>Digital write</strong> block.</p><p>🔢 Pin: <code>trigA</code> | Value: <code>HIGH</code> (on) — fires the invisible sound beam.</p><p>✅ Sensor A blasts its pulse! 🔊</p><hr><p><strong>3. End the pulse</strong></p><p>📌 Turn the trigger back OFF to cut the pulse to exactly the right length.</p><p>🧱 <strong>Digital write</strong> block.</p><p>🔢 Pin: <code>trigA</code> | Value: <code>LOW</code>.</p><p>✅ Pulse is short and sharp — sensor is now listening. 👂</p><p><em>Locked: the two delayMicroseconds pauses are tiny waits in millionths of a second — required by the sensor's datasheet.</em></p>"
                    },
                    "logic": {
                        "label": "🧠 Logic",
                        "content": "<p>It's like clapping once near a wall and listening for the echo! 👏 You clap fast — not a long hold, just a quick snap — then go silent so you can hear the bounce-back.</p><p>The sensor does the same: a tiny HIGH pulse, then silence. 🏟️</p>"
                    }
                }
            },
            {
                "title": "Step 5 — Read Sensor A Distance 📏",
                "tip": "The echo time tells you the distance — longer echo means farther away!",
                "tabs": {
                    "explain": {
                        "label": "📖 What & Why",
                        "content": "<p>The sound pulse is flying through the air! 🔊 Now your Arduino listens for the echo to come back and times exactly how long it takes. A nearby object bounces the sound back quickly; a far-away object takes longer.</p><p>This step catches that echo time and turns it into a real distance in centimetres. 📏</p>"
                    },
                    "howto": {
                        "label": "🔧 How To",
                        "content": "<p><strong>1. Measure echo time</strong></p><p>📌 Listen on the echo pin and count how long it stays on — that's the round-trip travel time of the sound.</p><p>🧱 Use a <strong>Pulse in</strong> block stored in a memory box.</p><p>🔢 Pin: <code>echoA</code> | <code>HIGH</code> to count while active | Name the box <code>durationA</code>.</p><p>✅ durationA holds the travel time in microseconds! ⏱️</p><hr><p><strong>2. Calculate distance</strong></p><p>📌 Convert that travel time into a distance in centimetres.</p><p>🧱 Use a <strong>Declare number label</strong> block with math inside.</p><p>🔢 Multiply <code>durationA</code> by <code>0.034</code> (sound speed in cm/µs) then divide by <code>2</code> (sound went THERE and came BACK). Name it <code>distanceA</code>.</p><p>✅ distanceA holds how far the object is in centimetres! 📏</p>"
                    },
                    "logic": {
                        "label": "🧠 Logic",
                        "content": "<p>Imagine shouting across a canyon and timing your echo! 🏔️ If the echo takes 2 seconds, the wall is 1 second of sound away — half the time, because sound went AND came back.</p><p>The sensor does exactly this, just a million times faster with sound you can't hear! 🦇</p>"
                    }
                }
            },
            {
                "title": "Step 6 — Fire Sensor B 🔊",
                "tip": "Sensor B is at the finish line — arm it the same way as Sensor A!",
                "tabs": {
                    "explain": {
                        "label": "📖 What & Why",
                        "content": "<p>Sensor A is armed and listening! 🏁 Now it's Sensor B's turn at the other end of the track. Without Sensor B firing, there's no finish line — and no way to know when the object exits the speed trap.</p><p>This step fires the same burst sequence so Sensor B is ready to catch the finish. 📡</p>"
                    },
                    "howto": {
                        "label": "🔧 How To",
                        "content": "<p><strong>1. Clear Sensor B trigger</strong></p><p>📌 Reset Sensor B's trigger to zero before firing.</p><p>🧱 <strong>Digital write</strong> block.</p><p>🔢 Pin: <code>trigB</code> | Value: <code>LOW</code>.</p><p>✅ Sensor B trigger is clean.</p><hr><p><strong>2. Fire Sensor B pulse</strong></p><p>📌 Send the sound burst from Sensor B.</p><p>🧱 <strong>Digital write</strong> block.</p><p>🔢 Pin: <code>trigB</code> | Value: <code>HIGH</code>.</p><p>✅ Sensor B blasts its pulse at the finish line! 🔊</p><hr><p><strong>3. End Sensor B pulse</strong></p><p>📌 Cut the pulse off cleanly.</p><p>🧱 <strong>Digital write</strong> block.</p><p>🔢 Pin: <code>trigB</code> | Value: <code>LOW</code>.</p><p>✅ Sensor B is now listening for its echo. 👂</p><p><em>Locked: same delayMicroseconds timing as Sensor A — same sensor model, same rules.</em></p>"
                    },
                    "logic": {
                        "label": "🧠 Logic",
                        "content": "<p>The speed trap is like two laser gates at a professional drag strip! 🏎️ One gate is at the start line and one is at the finish — both need to be armed before each run.</p><p>You just armed the finish line! 🏁</p>"
                    }
                }
            },
            {
                "title": "Step 7 — Read Sensor B Distance 📏",
                "tip": "Get Sensor B's distance the same way as Sensor A — then you can compare both!",
                "tabs": {
                    "explain": {
                        "label": "📖 What & Why",
                        "content": "<p>Both sensors are fired and scanning! 🔊 Now we catch Sensor B's echo and calculate the distance at the finish line, just like we did for Sensor A.</p><p>Once both sensors have distance readings every loop, the Arduino can instantly tell when an object crosses each one in sequence. 🏁</p>"
                    },
                    "howto": {
                        "label": "🔧 How To",
                        "content": "<p><strong>1. Measure Sensor B echo time</strong></p><p>📌 Listen on Sensor B's echo pin and time the round-trip sound.</p><p>🧱 <strong>Pulse in</strong> block stored in a memory box.</p><p>🔢 Pin: <code>echoB</code> | <code>HIGH</code> to count while active | Name the box <code>durationB</code>.</p><p>✅ durationB holds Sensor B's travel time! ⏱️</p><hr><p><strong>2. Calculate Sensor B distance</strong></p><p>📌 Convert the echo time into centimetres.</p><p>🧱 <strong>Declare number label</strong> with math inside.</p><p>🔢 <code>durationB * 0.034 / 2</code> — same formula as Sensor A. Name it <code>distanceB</code>.</p><p>✅ Both sensors now have a distance reading every loop — speed trap fully armed! 🏁</p>"
                    },
                    "logic": {
                        "label": "🧠 Logic",
                        "content": "<p>You now have two judges watching the track — one at each end! 🏎️ Every loop, each judge checks: is something close to me right now?</p><p>When both judges see the car in order — A then B — the timer fires. That's the whole trick! 🦇</p>"
                    }
                }
            },
            {
                "title": "Step 8 — Detect at Sensor A 🚩",
                "tip": "The moment an object crosses Sensor A, stamp the time — that's your START!",
                "tabs": {
                    "explain": {
                        "label": "📖 What & Why",
                        "content": "<p>Both sensors are reading distances every loop — but how do you know when something actually zooms through? 🏎️ This step watches Sensor A constantly. The moment something gets closer than 30 centimetres AND it hasn't been detected yet this run, the Arduino stamps the exact time and raises the flag.</p><p>That timestamp is the START of your race clock! ⏱️</p>"
                    },
                    "howto": {
                        "label": "🔧 How To",
                        "content": "<p><strong>1. Check if Sensor A spotted something</strong></p><p>📌 Check two things at once: is something close to Sensor A, AND has it not already been detected this run?</p><p>🧱 Use an <strong>If</strong> block with two conditions joined by AND.</p><p>🔢 <code>distanceA &lt; 30</code> (something within 30 cm) AND <code>sawA == false</code> (first detection only).</p><p>✅ If both are true, the Arduino records the time — otherwise it skips.</p><hr><p><strong>2. Record the time at Sensor A</strong></p><p>📌 Stamp the exact microsecond the object crossed Sensor A into the timeA memory box.</p><p>🧱 Use a <strong>Set label</strong> block with a <strong>Micros</strong> reading inside.</p><p>🔢 micros() gives the current time in microseconds. Store it in <code>timeA</code>.</p><p>✅ timeA now holds the start time of the run! ⏱️</p><hr><p><strong>3. Mark Sensor A as triggered</strong></p><p>📌 Raise the flag so Sensor A won't fire again during this run.</p><p>🧱 <strong>Set label</strong> block.</p><p>🔢 Set <code>sawA</code> to <code>true</code>.</p><p>✅ The start flag is up — Sensor A is done for this run! 🚩</p><p><em>Locked: Serial.println prints a confirmation to the Serial Monitor — useful for watching detections live during testing.</em></p>"
                    },
                    "logic": {
                        "label": "🧠 Logic",
                        "content": "<p>Think of a trip wire at the start of a race track! 🏁 The moment a car breaks the wire, a crew member yells the time into the radio.</p><p>Setting sawA = true is like that crew member shouting GOT IT — so nobody records the start twice! 🔊</p>"
                    }
                }
            },
            {
                "title": "Step 9 — Detect at Sensor B 🏁",
                "tip": "Three conditions must all be true — it's a very precise finish-line judge!",
                "tabs": {
                    "explain": {
                        "label": "📖 What & Why",
                        "content": "<p>Sensor A has stamped the start — now we need the finish! 🏎️ Sensor B watches the far end of the speed trap. This step checks three things every loop: is something close to Sensor B, did Sensor A already fire, and has Sensor B NOT fired yet?</p><p>All three must be true for a valid finish-line crossing. ⏱️</p>"
                    },
                    "howto": {
                        "label": "🔧 How To",
                        "content": "<p><strong>1. Check if Sensor B caught the object</strong></p><p>📌 Confirm something is close to Sensor B, the race started, AND the finish hasn't been recorded yet.</p><p>🧱 <strong>If</strong> block with three conditions joined by AND.</p><p>🔢 <code>distanceB &lt; 30</code> AND <code>sawA == true</code> AND <code>sawB == false</code>.</p><p>✅ Only a real, complete pass triggers this — no false alarms!</p><hr><p><strong>2. Record the time at Sensor B</strong></p><p>📌 Stamp the finish-line crossing time into timeB.</p><p>🧱 <strong>Set label</strong> block with <strong>Micros</strong> inside.</p><p>🔢 micros() captures the exact moment. Store in <code>timeB</code>.</p><p>✅ timeB is the finish time — now we have both! 🏁</p><hr><p><strong>3. Mark Sensor B as triggered</strong></p><p>📌 Raise the Sensor B flag so the finish isn't recorded twice.</p><p>🧱 <strong>Set label</strong> block.</p><p>🔢 Set <code>sawB</code> to <code>true</code>.</p><p>✅ Both timestamps locked in. Speed calculation can begin! 🔒</p><p><em>Locked: Serial.println confirms the finish-line trigger live — pre-filled as a testing helper.</em></p>"
                    },
                    "logic": {
                        "label": "🧠 Logic",
                        "content": "<p>It's just like a stopwatch at a sprint race! ⏱️ You press START when the runner leaves the blocks (Sensor A), and STOP when they cross the tape (Sensor B).</p><p>The condition sawA == true is the key — if nobody pressed START, the STOP doesn't count! 🏃</p>"
                    }
                }
            },
            {
                "title": "Step 10 — Calculate & Show Speed 🚀",
                "tip": "Distance ÷ Time = Speed — the same formula real drag strip engineers use!",
                "tabs": {
                    "explain": {
                        "label": "📖 What & Why",
                        "content": "<p>Both sensors have fired — the data is in! 🏁 The Arduino subtracts the start time from the finish time to get how long the run took, then divides your 20 cm track by that time.</p><p>The result prints live to the screen: real speed in metres per second! Then the trap resets for the next run. 🔄</p>"
                    },
                    "howto": {
                        "label": "🔧 How To",
                        "content": "<p><strong>1. Check if both sensors fired</strong></p><p>📌 Make sure we only calculate when BOTH sensors recorded a hit.</p><p>🧱 <strong>If</strong> block with two AND conditions.</p><p>🔢 <code>sawA == true</code> AND <code>sawB == true</code>.</p><p>✅ The calculator only runs after a complete, valid pass!</p><hr><p><strong>2. Calculate the speed</strong></p><p>📌 Divide the track distance by the time taken to get the speed.</p><p>🧱 <strong>Declare decimal label</strong> block with a divide operation inside.</p><p>🔢 <code>distance</code> (0.20 m) divided by <code>timeDiff</code> (time in seconds). Name it <code>speed</code>.</p><p>✅ speed holds the real speed in metres per second! 🚀</p><hr><p><strong>3. Display the speed</strong></p><p>📌 Print the speed number on the Serial Monitor.</p><p>🧱 <strong>Print line</strong> block.</p><p>🔢 Print the <code>speed</code> label — the actual calculated number.</p><p>✅ Your speed pops up on screen right after the label! 📺</p><hr><p><strong>4. Reset Sensor A</strong></p><p>📌 Put Sensor A's flag back down so the trap is ready for the next object.</p><p>🧱 <strong>Set label</strong> block.</p><p>🔢 Set <code>sawA</code> to <code>false</code>.</p><p>✅ Sensor A is armed for the next run! 🏁</p><hr><p><strong>5. Wait before the next run</strong></p><p>📌 Pause one second so the object is fully clear before the trap resets.</p><p>🧱 <strong>Delay</strong> block.</p><p>🔢 <code>1000</code> milliseconds = 1 second.</p><p>✅ The speed trap resets cleanly — ready for the next challenger! 🔄</p><p><em>Locked: timeDiff converts the gap from microseconds to seconds (÷ 1,000,000). Serial.print prints the label text before the number. sawB = false resets the finish flag.</em></p>"
                    },
                    "logic": {
                        "label": "🧠 Logic",
                        "content": "<p>Speed = Distance ÷ Time — the same maths real race engineers use! 🏎️ If your toy car covers 20 cm in 0.5 seconds, it's going 0.40 m/s.</p><p>The Arduino does all of this in microseconds — your speed trap is a real scientific instrument! 🔬</p>"
                    }
                }
            },
            {
                "title": "Mission Complete 🎉",
                "tip": "Your speed trap is fully operational — time to push some things through!",
                "tabs": {
                    "explain": {
                        "label": "📖 What You Built",
                        "content": "<p>You did it, chief engineer! 🎉 Your speed trap fires two ultrasonic sensors, records the exact crossing time at each one in microseconds, and calculates the real speed of anything that passes through.</p><p>From a toy car to a pencil case — if it moves through the trap, your Arduino clocks it! 🚀</p><ul><li>📡 Detects objects passing through two sensors automatically</li><li>⏱️ Records the exact crossing time at each gate in microseconds</li><li>➗ Calculates real speed using distance ÷ time</li><li>📺 Displays live speed results on the Serial Monitor</li><li>🔄 Resets itself and waits for the next run</li><li>🏎️ Tests the speed of any object you push or roll through!</li></ul><p>You proved you can build a real timing system from scratch — just like engineers do at professional drag strips! 🏁</p>"
                    },
                    "howto": {
                        "label": "🔧 Try This Next",
                        "content": "<p>Now that your speed trap works, here are some ideas to make it even better!</p><ul><li>🟢 <strong>Change the distance</strong> — move your sensors further apart, update the distance value, and see how readings change.</li><li>🟢 <strong>Adjust the threshold</strong> — change &lt; 30 to &lt; 20 in both detection steps and test if it triggers more reliably.</li><li>🟡 <strong>Speed LED</strong> — add an LED that flashes every time a speed is recorded.</li><li>🟡 <strong>Record breaker</strong> — store the fastest speed and print NEW RECORD! whenever it's beaten.</li><li>🔴 <strong>Top 3 leaderboard</strong> — save the three fastest speeds and print the full leaderboard after each run.</li><li>🔴 <strong>Convert to km/h</strong> — multiply the speed by 3.6 and display both m/s and km/h for every run.</li></ul><p>Experimenting is how real drag strip engineers improve their systems! 🔧</p>"
                    },
                    "logic": {
                        "label": "🧠 What You Learned",
                        "content": "<p>This project brought together everything you have been building:</p><ul><li>📡 <strong>Ultrasonic sensing</strong> — how sensors fire a sound pulse and listen for the echo to measure distance</li><li>⏱️ <strong>Microsecond timing</strong> — how micros() captures time precisely enough to measure fast-moving objects</li><li>➗ <strong>Speed formula</strong> — how distance ÷ time gives real speed, just like in maths class</li><li>🚩 <strong>True/false flags</strong> — how yes/no labels stop the same event from being recorded twice</li><li>🔀 <strong>Multi-condition checks</strong> — how AND logic makes sure multiple things are true before acting</li><li>📺 <strong>Serial Monitor output</strong> — how to print live data so you can watch your system work</li><li>🔄 <strong>Reset cycles</strong> — how to clean up after each measurement so the system is ready for the next run</li></ul><p>You are now thinking like a real systems engineer, chief! 🏎️</p>"
                    },
                    "sim": {
                        "label": "🎮 Try It",
                        "type": "sim",
                        "sim_config": {
                            "mode": "components",
                            "components": [
                                {
                                    "id": "sonar_a",
                                    "type": "sonar",
                                    "label": "Start Gate",
                                    "pin": 2,
                                    "labels": {
                                        "safe": "🏁 CLEAR",
                                        "warning": "⚡ INCOMING",
                                        "danger": "🚗 TRIGGERED!"
                                    }
                                },
                                {
                                    "id": "timer1",
                                    "type": "timer",
                                    "label": "Race Timer"
                                },
                                {
                                    "id": "sonar_b",
                                    "type": "sonar",
                                    "label": "Finish Gate",
                                    "pin": 4,
                                    "labels": {
                                        "safe": "🏁 CLEAR",
                                        "warning": "⚡ INCOMING",
                                        "danger": "🏎️ TRIGGERED!"
                                    }
                                }
                            ],
                            "behaviors": [
                                {"when": {"sonar_a": "danger"}, "then": {"timer1": "toggle"}},
                                {"when": {"sonar_b": "danger", "sonar_a": "safe"}, "then": {"timer1": "toggle"}}
                            ]
                        }
                    }
                }
            }
        ]
    }
}


# Two independent HC-SR04 sensors, one per physical breadboard (a speed trap
# needs two separated sensors, not two sensors crammed onto one board).
# circuit_engine.py's generate_circuit() has no dual-board placement support
# (it only ever emits single "breadboard.X" endpoints), so this is hand-authored
# per CIRCUIT_ENGINE.md's Option B — using "layout": "dual_board" and
# "breadboard2.X" endpoints, which circuit_renderer.js does support.
CIRCUIT_JSON = {
    "meta": {
        "title": "Drag Race Speed Tracker",
        "difficulty": "advanced",
        "description": "Measure speed using two ultrasonic sensors to track distance changes over time.",
    },
    "layout": "dual_board",
    "components": [
        {
            "id": "SR1",
            "type": "HC_SR04",
            "board": 1,
            "pins": {
                "vcc":  {"col": "J", "row": 12},
                "trig": {"col": "J", "row": 11},
                "echo": {"col": "J", "row": 10},
                "gnd":  {"col": "J", "row": 9},
            },
            "properties": {},
        },
        {
            "id": "SR2",
            "type": "HC_SR04",
            "board": 2,
            "pins": {
                "vcc":  {"col": "J", "row": 12},
                "trig": {"col": "J", "row": 11},
                "echo": {"col": "J", "row": 10},
                "gnd":  {"col": "J", "row": 9},
            },
            "properties": {},
        },
    ],
    "connections": [
        {"from": "breadboard1.I12", "to": "breadboard1.+1.12", "color": "#CC0000"},
        {"from": "arduino.5V", "to": "breadboard1.+1.30", "color": "#CC0000"},
        {"from": "arduino.D2", "to": "breadboard1.F11", "color": "#3498DB"},
        {"from": "breadboard1.F10", "to": "arduino.D3", "color": "#9B59B6"},
        {"from": "breadboard1.I9", "to": "breadboard1.-1.9", "color": "#111111"},
        {"from": "arduino.GND", "to": "breadboard1.-1.30", "color": "#111111"},
        {"from": "breadboard2.I12", "to": "breadboard2.+1.12", "color": "#CC0000"},
        {"from": "breadboard2.+1.1", "to": "breadboard1.+1.1", "color": "#CC0000"},
        {"from": "arduino.D4", "to": "breadboard2.F11", "color": "#E67E22"},
        {"from": "breadboard2.F10", "to": "arduino.D5", "color": "#1ABC9C"},
        {"from": "breadboard2.I9", "to": "breadboard2.-1.9", "color": "#111111"},
        {"from": "breadboard2.-1.1", "to": "breadboard1.-1.1", "color": "#111111"},
    ],
    "walkthrough": [
        {
            "type": "component", "id": "SR1",
            "instruction": "Plug the first HC-SR04 sensor into breadboard 1 with all four pins in column J: VCC in row 12, TRIG in row 11, ECHO in row 10, GND in row 9.",
            "tip": "The two silver circles are the ultrasonic 'eyes' — point them toward your target!",
        },
        {
            "type": "component", "id": "SR2",
            "instruction": "Plug the second HC-SR04 sensor into breadboard 2 with all four pins in column J: VCC in row 12, TRIG in row 11, ECHO in row 10, GND in row 9.",
            "tip": "The two silver circles are the ultrasonic 'eyes' — point them toward your target!",
        },
        {
            "type": "wire", "from": "breadboard1.I12", "to": "breadboard1.+1.12",
            "instruction": "Connect a short red wire from breadboard 1 column I row 12 to the positive (+) rail at row 12.",
            "tip": "This jumper connects the first sensor's VCC pin to the shared power rail.",
        },
        {
            "type": "wire", "from": "arduino.5V", "to": "breadboard1.+1.30",
            "instruction": "Connect a red wire from the Arduino 5V pin to breadboard 1's positive (+) rail at row 30.",
            "tip": "This powers the positive rail — both sensors get their 5V through here.",
        },
        {
            "type": "wire", "from": "arduino.D2", "to": "breadboard1.F11",
            "instruction": "Connect a blue wire from Arduino pin D2 to breadboard 1 at row 11, column F.",
            "tip": "This wire carries the signal between Arduino and your component.",
        },
        {
            "type": "wire", "from": "breadboard1.F10", "to": "arduino.D3",
            "instruction": "Connect a purple wire from breadboard 1 at row 10, column F to Arduino pin D3.",
            "tip": "This wire carries the signal between Arduino and your component.",
        },
        {
            "type": "wire", "from": "breadboard1.I9", "to": "breadboard1.-1.9",
            "instruction": "Connect a short black wire from breadboard 1 column I row 9 to the negative (−) rail at row 9.",
            "tip": "This jumper connects the first sensor's GND pin to the shared ground rail.",
        },
        {
            "type": "wire", "from": "arduino.GND", "to": "breadboard1.-1.30",
            "instruction": "Connect a black wire from the Arduino GND pin to breadboard 1's negative (−) rail at row 30.",
            "tip": "This powers the ground rail — all sensor GNDs flow back through here.",
        },
        {
            "type": "wire", "from": "breadboard2.I12", "to": "breadboard2.+1.12",
            "instruction": "Connect a short red wire from breadboard 2 column I row 12 to breadboard 2's positive (+) rail at row 12.",
            "tip": "This jumper connects the second sensor's VCC pin to board 2's power rail.",
        },
        {
            "type": "wire", "from": "arduino.D4", "to": "breadboard2.F11",
            "instruction": "Connect an orange wire from Arduino pin D4 to breadboard 2 at row 11, column F.",
            "tip": "This wire carries the signal between Arduino and your component.",
        },
        {
            "type": "wire", "from": "breadboard2.F10", "to": "arduino.D5",
            "instruction": "Connect a teal wire from breadboard 2 at row 10, column F to Arduino pin D5.",
            "tip": "This wire carries the signal between Arduino and your component.",
        },
        {
            "type": "wire", "from": "breadboard2.I9", "to": "breadboard2.-1.9",
            "instruction": "Connect a short black wire from breadboard 2 column I row 9 to breadboard 2's negative (−) rail at row 9.",
            "tip": "This jumper connects the second sensor's GND pin to board 2's ground rail.",
        },
        {
            "type": "wire", "from": "breadboard2.+1.1", "to": "breadboard1.+1.1",
            "instruction": "Connect a red jumper wire from breadboard 2's positive (+) rail at row 1 to breadboard 1's positive (+) rail at row 1.",
            "tip": "This bridge wire links both boards' 5V rails so both sensors share the Arduino's power.",
        },
        {
            "type": "wire", "from": "breadboard2.-1.1", "to": "breadboard1.-1.1",
            "instruction": "Connect a black jumper wire from breadboard 2's negative (−) rail at row 1 to breadboard 1's negative (−) rail at row 1.",
            "tip": "This bridge wire links both boards' rails together so both sensors share the Arduino's GND.",
        },
    ],
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
