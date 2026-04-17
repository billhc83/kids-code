from utils.step_builder import build_step, intro_step, rect, circle, line, lbl


META = {
    'title': 'Project 17: Magical Harp',
    'circuit_image': 'static/graphics/project_seventeen_circuit.png',
    'banner_image': 'project_seventeen_banner.png',
    'lesson_type': 'progression',
}


# Wiring and component placement steps.
# rect() / circle() / line() coordinates are placeholders —
# update with real pixel coords once the circuit image is available.
STEPS = [
    intro_step(
        "Let put together our musical instument",
        "",
    ),

    build_step(
        "Lets place the sonar sensor.  The diagram shows the wires in column H.  This is so we can see them on the diagram.  We will put the wires in column J for our project.<br>VCC Pin will be in row 23 column H<br>Trig Pin will be in row 24 column H<br> Pin will be in row 25 column H<br>GND Pin will be in row 26 column H",
        "",
        rect(1116, 63, 1673, 425),
        greyout=True,
    ),

    build_step(
        "Place the long leg of the buzzer in row 6, column D.<br>Place the short leg of the buzzer in row 9, column D.",
        "",
        rect(842, 450, 1116, 644),
        greyout=True,
    ),

    build_step(
        "Place one end of the wire in Arduino Pin GND.<br>Place the other end in row 26, column J.",
        "",
        line((466, 345), (537, 348), (685, 252), (1582, 252), (1585, 428), (1475, 425), width=25),
        greyout=True,
    ),

    build_step(
        "Place one end of the wire in Arduino Pin 10.<br>Place the other end in row 25, column J.",
        "",
        line((491, 453), (1448, 459), (1445, 407), width=25),
        greyout=True,
    ),

    build_step(
        "Place one end of the wire in Arduino Pin 9.<br>Place the other end in row 24, column J.",
        "",
        line((474, 483), (1418, 483), (1420, 406), width=25),
        greyout=True,
    ),

    build_step(
        "Place one end of the wire in Arduino Pin 5V.<br>Place the other end in row 23, column J.",
        "",
        line((3, 469), (644, 428), (1407, 428), width=25),
        greyout=True,
    ),

    build_step(
        "Place one end of the wire in Arduino Pin 3.<br>Place the other end in row 6, column A.",
        "",
        line((499, 660), (537, 660), (940, 613), width=25),
        greyout=True,
    ),

    build_step(
        "Place one end of the wire in Arduino Pin GND.<br>Place the other end in row 9, column A.",
        "",
        line((11, 518), (420, 776), (1023, 776), (1017, 614), width=25),
        greyout=True,
    ),

]
DRAWER_CONTENT = {
    "project_seventeen": {
        "steps": [
            {
                "title": "Step 1 - Variables 📦",
                "tip": "Give each magical part a name before the concert begins.",
                "tabs": {
                    "explain": {
                        "label": "📖 What & Why",
                        "content": "<p>🎵 Magical Musician, every part of your harp needs a name before it can help make music.</p><p>In this step, you give name labels to the sensor parts that send and hear the magic sound wave. Without these labels, your Arduino would not know which part should do each job.</p>"
                    },
                    "howto": {
                        "label": "🔧 How To",
                        "content": "<p><strong>1. Declare the trigger pin variable</strong></p><p><strong>Intent:</strong> Your harp needs a name for the pin that sends the magic signal.</p><p><strong>Block:</strong> Use a variable block. It makes a memory box with a label on it.</p><p><strong>Values:</strong> Name it <strong>trigPin</strong> and give it <strong>9</strong>. That is the pin your trigger wire will use in this project.</p><p><strong>Result:</strong> Now your harp knows which pin sends the signal.</p><p><strong>2. Declare the echo pin variable</strong></p><p><strong>Intent:</strong> Your harp also needs a name for the pin that listens for the echo.</p><p><strong>Block:</strong> Use another variable block. This makes a second memory box.</p><p><strong>Values:</strong> Name it <strong>echoPin</strong> and give it <strong>10</strong>. That is the pin that listens for the sound wave coming back.</p><p><strong>Result:</strong> Now your harp knows which pin listens for the echo.</p><p>The buzzer and distance memory boxes are ready for you already so you can focus on the sensor names first.</p>"
                    },
                    "logic": {
                        "label": "🧠 Logic",
                        "content": "<p>🏷️ This is like putting name stickers on three instrument cases before a show. If nothing has a label, you might grab the wrong case when it is time to play.</p>"
                    }
                }
            },
            {
                "title": "Step 2 - Setup Pins 🔌",
                "tip": "Tell each pin if it should talk or listen.",
                "tabs": {
                    "explain": {
                        "label": "📖 What & Why",
                        "content": "<p>✨ Your magical harp has names now, but the parts still need jobs.</p><p>In this step, you tell one pin to send signals and one pin to listen back. Without this, the sensor would not know how to do its magic work.</p>"
                    },
                    "howto": {
                        "label": "🔧 How To",
                        "content": "<p><strong>1. Set the trigger pin as output</strong></p><p><strong>Intent:</strong> The trigger pin needs to send a signal out into the air.</p><p><strong>Block:</strong> Use a <strong>pinMode</strong> block. It tells the Arduino what job a pin should do.</p><p><strong>Values:</strong> Put <strong>trigPin</strong> in the first slot. Choose <strong>OUTPUT</strong> in the second slot because this pin sends the signal.</p><p><strong>Result:</strong> The trigger pin is ready to talk.</p><p><strong>2. Set the echo pin as input</strong></p><p><strong>Intent:</strong> The echo pin needs to listen for the sound wave coming back.</p><p><strong>Block:</strong> Use another <strong>pinMode</strong> block.</p><p><strong>Values:</strong> Put <strong>echoPin</strong> in the first slot. Choose <strong>INPUT</strong> in the second slot because this pin receives the echo.</p><p><strong>Result:</strong> The echo pin is ready to listen.</p>"
                    },
                    "logic": {
                        "label": "🧠 Logic",
                        "content": "<p>🗣️👂 Think of two kids playing echo games. One kid calls out, and the other kid listens for the reply. They cannot both do the same job at the same time.</p>"
                    }
                }
            },
            {
                "title": "Step 3 - Start the Pulse 🌟",
                "tip": "Begin with a quiet signal before sending the magic wave.",
                "tabs": {
                    "explain": {
                        "label": "📖 What & Why",
                        "content": "<p>🎼 Before your harp sends out a sound wave, it needs to begin from a calm starting point.</p><p>This step makes sure the trigger pin starts low first. Without a clean start, the sensor could get mixed up and send a messy signal.</p>"
                    },
                    "howto": {
                        "label": "🔧 How To",
                        "content": "<p><strong>1. Start with the trigger pin low</strong></p><p><strong>Intent:</strong> Your signal needs to begin in the OFF position.</p><p><strong>Block:</strong> Use a <strong>digitalWrite</strong> block. It turns a pin ON or OFF.</p><p><strong>Values:</strong> Put <strong>trigPin</strong> in the first slot. Choose <strong>LOW</strong> in the second slot because LOW means OFF.</p><p><strong>Result:</strong> The trigger pin starts from a quiet, clean beginning.</p><p>The tiny wait line is already set for you because it is too small to notice, but it helps the signal start neatly.</p>"
                    },
                    "logic": {
                        "label": "🧠 Logic",
                        "content": "<p>🎻 This is like lifting your hands into place before plucking the first harp string. You get ready first, then you make the sound.</p>"
                    }
                }
            },
            {
                "title": "Step 4 - Send the Signal 🚀",
                "tip": "Send a tiny burst, then switch it back off.",
                "tabs": {
                    "explain": {
                        "label": "📖 What & Why",
                        "content": "<p>🌬️ Now your magical harp is ready to send its tiny sound wave out into the air.</p><p>This step creates the short signal that the sensor uses to check where your hand is. Without this burst, there would be nothing to bounce back.</p>"
                    },
                    "howto": {
                        "label": "🔧 How To",
                        "content": "<p><strong>1. Send the trigger signal</strong></p><p><strong>Intent:</strong> The sensor needs a quick burst to begin the distance check.</p><p><strong>Block:</strong> Use a <strong>digitalWrite</strong> block.</p><p><strong>Values:</strong> Put <strong>trigPin</strong> in the first slot. Choose <strong>HIGH</strong> because HIGH means ON, and that sends the signal.</p><p><strong>Result:</strong> The sound wave begins its trip.</p><p><strong>2. Turn the trigger signal off</strong></p><p><strong>Intent:</strong> The burst should only last for a tiny moment.</p><p><strong>Block:</strong> Use another <strong>digitalWrite</strong> block.</p><p><strong>Values:</strong> Put <strong>trigPin</strong> in the first slot again. Choose <strong>LOW</strong> so the signal turns off after the burst.</p><p><strong>Result:</strong> The signal is sent cleanly and stops at the right time.</p><p>The tiny timing wait is pre-set for you so the burst is exactly the right size.</p>"
                    },
                    "logic": {
                        "label": "🧠 Logic",
                        "content": "<p>👏 This is like one quick clap in a big room. You clap once, stop, and then wait to hear the sound bounce back.</p>"
                    }
                }
            },
            {
                "title": "Step 5 - Listen for the Echo 👂",
                "tip": "Measure how long the sound wave takes to come back.",
                "tabs": {
                    "explain": {
                        "label": "📖 What & Why",
                        "content": "<p>🔍 Your harp has sent out its sound wave. Now it needs to listen for the bounce.</p><p>This step stores how long the echo takes to come back. Without that time, the harp cannot figure out how close your hand is.</p>"
                    },
                    "howto": {
                        "label": "🔧 How To",
                        "content": "<p><strong>1. Measure the echo duration</strong></p><p><strong>Intent:</strong> The system needs to catch how long the sound wave was travelling.</p><p><strong>Block:</strong> Use a <strong>pulseIn</strong> style sensor-reading block. It waits for the echo and measures the time.</p><p><strong>Values:</strong> Use <strong>echoPin</strong> because that is the pin listening for the echo. Use <strong>HIGH</strong> because the block is measuring the returning signal.</p><p><strong>Result:</strong> The travel time is stored in the <strong>duration</strong> memory box.</p>"
                    },
                    "logic": {
                        "label": "🧠 Logic",
                        "content": "<p>🪨 It is like yelling toward a wall and counting how long it takes to hear your voice bounce back. A fast echo means the wall is close. A slow echo means it is farther away.</p>"
                    }
                }
            },
            {
                "title": "Step 6 - Calculate Distance 📏",
                "tip": "This step turns travel time into real distance.",
                "tabs": {
                    "explain": {
                        "label": "📖 What & Why",
                        "content": "<p>🪄 Your harp knows the travel time now, but time is not the same as distance.</p><p>This step changes that travel time into centimeters. Without this, your harp would have a number, but it would not know how near or far your hand really is.</p>"
                    },
                    "howto": {
                        "label": "🔧 How To",
                        "content": "<p>This step is handled for you because it uses careful maths. One tiny mistake could make the whole harp play the wrong note.</p><p>The line takes the <strong>duration</strong> number and changes it into a distance number. The <strong>0.034</strong> tells us how far sound travels in a tiny slice of time.</p><p>Then the line divides by <strong>2</strong> because the sound wave went out to your hand and came all the way back. We only want the one-way distance from the sensor to your hand.</p><p>When this step is done, the <strong>distance</strong> memory box holds the real distance your harp will use next.</p>"
                    },
                    "logic": {
                        "label": "🧠 Logic",
                        "content": "<p>🏃 Imagine rolling a ball to a wall and timing how long it takes to come back. If it returns super fast, the wall is close. If it takes longer, the wall is farther away.</p>"
                    }
                }
            },
            {
                "title": "Step 7 - Choose the Pitch 🎼",
                "tip": "Turn hand distance into a note your harp can play.",
                "tabs": {
                    "explain": {
                        "label": "📖 What & Why",
                        "content": "<p>🎶 Your harp knows the distance now, but it still needs to turn that distance into music.</p><p>This step chooses a note value from near and far hand positions. Without this step, your harp would measure distance but never turn it into sound.</p>"
                    },
                    "howto": {
                        "label": "🔧 How To",
                        "content": "<p>This step is also handled for you because it uses a special line that changes one number range into another number range.</p><p>The <strong>map</strong> line takes the distance range from <strong>5</strong> to <strong>50</strong> and changes it into a pitch range from <strong>200</strong> to <strong>1000</strong>. That means close hands and far hands can make different notes.</p><p>The smaller distance numbers match one part of the music range, and the bigger distance numbers match another part. This is what makes the harp feel like a real instrument in the air.</p><p>After this step, the <strong>pitch</strong> value is ready for the buzzer to play.</p>"
                    },
                    "logic": {
                        "label": "🧠 Logic",
                        "content": "<p>📐 It is like sliding your finger up and down a ruler and matching each spot to a different piano key. Different places on the ruler give you different sounds.</p>"
                    }
                }
            },
            {
                "title": "Step 8 - Play the Harp 🔊",
                "tip": "Use the buzzer to sing the note you just picked.",
                "tabs": {
                    "explain": {
                        "label": "📖 What & Why",
                        "content": "<p>🌟 This is the big moment. Your magical harp is ready to make music.</p><p>In this step, the buzzer plays the note chosen from your hand distance. Without this step, all the measuring and choosing would happen silently.</p>"
                    },
                    "howto": {
                        "label": "🔧 How To",
                        "content": "<p><strong>1. Play the magic note</strong></p><p><strong>Intent:</strong> The buzzer needs to play the note stored in the pitch memory box.</p><p><strong>Block:</strong> Use a <strong>tone</strong> block. It tells the buzzer to make a sound.</p><p><strong>Values:</strong> Put <strong>buzzer</strong> in the first slot because that is the sound part. Put <strong>pitch</strong> in the second slot because that is the note chosen from the hand distance.</p><p><strong>Result:</strong> Your magical harp plays a note when your hand moves.</p><p>The short delay line is already set for you so the harp has a tiny beat before checking again.</p>"
                    },
                    "logic": {
                        "label": "🧠 Logic",
                        "content": "<p>🎵 This is like finally plucking a harp string after tuning it. All the setup work is done, and now the music can come out.</p>"
                    }
                }
            },
            {
                "title": "Mission Complete 🎉",
                "tip": "Your magical harp is ready to perform.",
                "tabs": {
                    "explain": {
                        "label": "📖 What You Built",
                        "content": "<p>🎉 Amazing work, Magical Musician!</p><p>You built a magical harp that can sense your hand in the air and turn that movement into music.</p><ul><li>🎵 Play notes by moving your hand closer or farther away</li><li>👂 Listen for echoes with the ultrasonic sensor</li><li>📏 Turn travel time into distance</li><li>🎼 Change distance into a musical pitch</li><li>🔊 Play sounds through a buzzer</li></ul><p>You proved that you can build an instrument that feels like real magic but works with smart engineering.</p>"
                    },
                    "howto": {
                        "label": "🔧 Try This Next",
                        "content": "<p>Now that your system works, here are some ideas to make it even better.</p><ul><li>🌈 <strong>Change the note range</strong> Try different pitch numbers to make the harp sound deeper or squeakier.</li><li>⏱️ <strong>Change the beat</strong> Make the delay shorter or longer to change how fast the harp updates.</li><li>💡 <strong>Add lights</strong> Turn on LEDs that glow with different hand positions.</li><li>🎶 <strong>Make note zones</strong> Split the air into sections so each distance plays a special note.</li><li>🎮 <strong>Build a music game</strong> Challenge someone to copy a pattern of notes with their hand moves.</li></ul><p>Experimenting is how real inventors improve their designs.</p>"
                    },
                    "logic": {
                        "label": "🧠 What You Learned",
                        "content": "<p>This project brought together everything you have been building.</p><ul><li>📦 <strong>Memory boxes</strong> Giving important numbers labels so the Arduino can use them later.</li><li>🔌 <strong>Pin jobs</strong> Telling each pin whether it should send or listen.</li><li>🌬️ <strong>Sound pulses</strong> Sending tiny bursts to measure where something is.</li><li>👂 <strong>Echo timing</strong> Measuring how long a sound wave takes to come back.</li><li>📏 <strong>Distance math</strong> Turning travel time into centimeters.</li><li>🎼 <strong>Number mapping</strong> Changing one range of numbers into another range.</li><li>🔁 <strong>Looping</strong> Checking again and again so the harp keeps playing live music.</li></ul><p>You are now thinking like a real magical music engineer.</p>"
                    },
                    "sim": {
                        "label": "🎮 Try It",
                        "type": "sim",
                        "sim_config": {
                            "components": [
                                {"type": "sonar",  "id": "sonar1",    "label": "Musical Sensor", "pin_trig": 9, "pin_echo": 10, "labels": {"safe": "🟢 Higher Pitch", "warning": "🟡 Medium", "danger": "🔴 Lower Pitch"}},
                                {"type": "buzzer", "id": "musmaker",                         "pin": 3, "label": "Music Maker"},
                            ],
                            "behaviors": [
                                {
                                    "when": {"sonar1": "safe"},
                                    "then": {"musmaker": "on", "_stop_beep": "yes"}
                                },
                                {
                                    "when": {"sonar1": "warning"},
                                    "then": {"_stop_beep": "yes", "_beep": "musmaker", "_beep_interval": 300}
                                },
                                {
                                    "when": {"sonar1": "danger"},
                                    "then": {"musmaker": "on", "_stop_beep": "yes"}
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
    'sketch': """//>> Variables | guided | blocks

//?? Declare the trigger pin variable
int trigPin = 9;
//?? Declare the echo pin variable
int echoPin = 10;
//## int buzzer = 3;
//## long duration;
//## int distance;

//>> Setup Pins | guided | blocks

void setup() {
  //?? Set the trigger pin as output
  pinMode(trigPin, OUTPUT);
  //?? Set the echo pin as input
  pinMode(echoPin, INPUT);
}

void loop() {
}

//>> Start the Pulse | guided | blocks

void setup() {
  //## pinMode(trigPin, OUTPUT);
  //## pinMode(echoPin, INPUT);
}

void loop() {
  //?? Start with the trigger pin low
  digitalWrite(trigPin, LOW);
  //## delayMicroseconds(2);
}

//>> Send the Signal | guided | blocks

void setup() {
  //## pinMode(trigPin, OUTPUT);
  //## pinMode(echoPin, INPUT);
}

void loop() {
  //## digitalWrite(trigPin, LOW);
  //## delayMicroseconds(2);

  //?? Send the trigger signal
  digitalWrite(trigPin, HIGH);
  //## delayMicroseconds(10);
  //?? Turn the trigger signal off
  digitalWrite(trigPin, LOW);
}

//>> Listen for the Echo | guided | blocks

void setup() {
  //## pinMode(trigPin, OUTPUT);
  //## pinMode(echoPin, INPUT);
}

void loop() {
  //## digitalWrite(trigPin, LOW);
  //## delayMicroseconds(2);
  //## digitalWrite(trigPin, HIGH);
  //## delayMicroseconds(10);
  //## digitalWrite(trigPin, LOW);

  //?? Measure the echo duration
  duration = pulseIn(echoPin, HIGH);
}

//>> Calculate Distance | free | blocks

void setup() {
  //## pinMode(trigPin, OUTPUT);
  //## pinMode(echoPin, INPUT);
}

void loop() {
  //## digitalWrite(trigPin, LOW);
  //## delayMicroseconds(2);
  //## digitalWrite(trigPin, HIGH);
  //## delayMicroseconds(10);
  //## digitalWrite(trigPin, LOW);
  //## duration = pulseIn(echoPin, HIGH);
  //## distance = duration * 0.034 / 2;
}

//>> Choose the Pitch | free | blocks

void setup() {
  //## pinMode(trigPin, OUTPUT);
  //## pinMode(echoPin, INPUT);
}

void loop() {
  //## digitalWrite(trigPin, LOW);
  //## delayMicroseconds(2);
  //## digitalWrite(trigPin, HIGH);
  //## delayMicroseconds(10);
  //## digitalWrite(trigPin, LOW);
  //## duration = pulseIn(echoPin, HIGH);
  //## distance = duration * 0.034 / 2;
  //## int pitch = map(distance, 5, 50, 200, 1000);
}

//>> Play the Harp | guided | blocks

void setup() {
  //## pinMode(trigPin, OUTPUT);
  //## pinMode(echoPin, INPUT);
}

void loop() {
  //## digitalWrite(trigPin, LOW);
  //## delayMicroseconds(2);
  //## digitalWrite(trigPin, HIGH);
  //## delayMicroseconds(10);
  //## digitalWrite(trigPin, LOW);
  //## duration = pulseIn(echoPin, HIGH);
  //## distance = duration * 0.034 / 2;
  //## int pitch = map(distance, 5, 50, 200, 1000);

  //?? Play the magic note
  tone(buzzer, pitch);
  //## delay(50);
}

//>> Mission Complete | open | blocks | reset | fill:true

int trigPin = 9;
int echoPin = 10;
int buzzer = 3;

long duration;
int distance;

void setup() {
  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);
}

void loop() {
 
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  
  duration = pulseIn(echoPin, HIGH);


  distance = duration * 0.034 / 2;


  int pitch = map(distance, 5, 50, 200, 1000);

  tone(buzzer, pitch);

  delay(50);
}
""",
    'default_view': 'blocks',
    'read_only': False,
    'lock_view': False,
    'fill_values': True,
    'fill_conditions': True,
}





PROJECT = {
    "meta": META,
    "steps": STEPS,
    "drawer": DRAWER_CONTENT,
    "presets": {
        "default": SKETCH_PRESET,
    }
}
