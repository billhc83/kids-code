
from utils.step_builder import build_step, intro_step, rect, circle, line
from utils.affiliate_kits import BASIC_KITS

META = {
    'title': 'Project 11: Engine System Start',
    'circuit_image': 'static/graphics/project_twelve_circuit.png',
    'banner_image': 'jet_engine_start.png',
    'required_kits': BASIC_KITS,
}

STEPS = [
    intro_step(
        "Let's build our eleventh project",
        "Press the next button for a step by step guide",
    ),

    build_step(
        "Place the center pin of the switch in row 4, column H.<br>"
        "Place the side pin of the switch in row 5, column H",
        "This is the Engine Armed switch. Nothing happens unless we arm the engines.",
        rect(601, 216, 719, 310),
    ),
    build_step(
        "Place the first leg in row 24, column E.<br>"
        "Place the second leg in row 23, column E.<br>"
        "Place the third leg in row 8 column E.<br>"
        "Place the last leg in row 10 column E",
        "This button starts the engine.",
        rect(719, 239, 811, 350),
    ),
    build_step(
        "Place the long leg of the buzzer in row 14, column E.<br>"
        "Place the short leg of the buzzer in row 14, column F",
        "This is our engine — press the start button to hear it come to life.",
        rect(799, 222, 909, 344),
        circle(922, 37),
        line((917, 56), (861, 248)),
        circle(1034, 563),
        line((1043, 550), (850, 314)),
    ),
    build_step(
        "Place the long leg of the LED in row 22, column E.<br>"
        "Place the short leg of the LED in row 21, column E",
        "This is the light that tells us the engines are armed and ready to start.",
        rect(935, 175, 1069, 347),
        line((919, 57), (995, 317)),
        line((1040, 542), (1011, 330)),
        circle(922, 44),
        circle(1043, 561),
    ),
    build_step(
        "Place one leg of the 220 Ohm resistor in row 21, column D.<br>"
        "Place the second leg of the resistor in row 17, column D",
        "The resistor slows down the electricity.",
        rect(871, 307, 1034, 384),
        circle(1047, 52),
        line((1038, 75), (952, 340)),
    ),
    build_step(
        "Place one end of the wire into Arduino Pin 9.<br>"
        "Place the other end in row 5 column I.",
        "This wire lets the Arduino see the position of the switch.",
        line((370, 340), (723, 341), (722, 209), (680, 208)),
    ),
    build_step(
        "Place one end of the wire into Arduino Pin 7.<br>"
        "Place the other end into row 8 column B",
        "This wire lets the Arduino see if the button is pressed.",
        line((372, 393), (752, 378)),
    ),
    build_step(
        "Place one end of the wire into Arduino Pin 5.<br>"
        "Place the other end of the wire into row 14 column D.<br>"
        "The side pin goes in row 24 column E",
        "This wire powers our engine.",
        line((370, 427), (858, 430), (855, 337)),
    ),
    build_step(
        "Place one end of the wire in the Arduino Pin 2.<br>"
        "Place the other end in row 22 column A",
        "This wire powers our Engines armed light.",
        line((364, 486), (537, 487), (536, 529), (1012, 532), (1007, 393)),
    ),
    build_step(
        "Place one end of the wire in Arduino Pin GND.<br>"
        "Place the other end in the negative / - rail",
        "This wire helps complete our circuit.",
        line((369, 244), (446, 251), (444, 113), (622, 118)),
    ),
    build_step(
        "Place one end of the wire in row 4 column J.<br>"
        "Place the other end in the negative / - rail",
        "This wire completes our switch circuit.",
        line((667, 199), (652, 110)),
    ),
    build_step(
        "Place one end of the wire in row 10 column J.<br>"
        "Place the other end in the negative / - rail",
        "This wire completes our button circuit.",
        line((783, 202), (768, 110)),
    ),
    build_step(
        "Place one end of the wire in row 14 column J.<br>"
        "Place the other end in the negative / - rail",
        "This wire completes our buzzer circuit.",
        line((860, 204), (843, 103)),
    ),
    build_step(
        "Place one end of the wire in row 17 column E.<br>"
        "Place the other end in the negative / - rail",
        "This wire completes our light circuit.",
        line((915, 331), (922, 106)),
    ),
]

CIRCUIT_SPEC = {
    "meta": {
        "title": "Engine System Start",
        "difficulty": "intermediate",
    },
    "components": [
        {"id": "SW", "type": "SLIDE_SWITCH", "properties": {}},
        {"id": "BTN", "type": "BUTTON", "properties": {}},
        {"id": "LED", "type": "LED", "properties": {"color": "red"}},
        {"id": "BUZZ", "type": "BUZZER", "properties": {}},
    ],
    "connections": [
        {"from": "arduino.D9", "to": "SW.com"},
        {"from": "SW.pin2", "to": "arduino.GND"},
        {"from": "arduino.D7", "to": "BTN.TL"},
        {"from": "BTN.BR", "to": "arduino.GND"},
        {"from": "arduino.D2", "to": "LED.anode"},
        {"from": "R_LED.pin2", "to": "arduino.GND"},
        {"from": "arduino.D5", "to": "BUZZ.positive"},
        {"from": "BUZZ.negative", "to": "arduino.GND"},
    ],
}

from utils.circuit_engine import generate_circuit

engine_circuit_definition = generate_circuit(
    CIRCUIT_SPEC["meta"], CIRCUIT_SPEC["components"], CIRCUIT_SPEC["connections"]
)

DRAWER_CONTENT = {
  "project_eleven": {
    "steps": [
      {
        "title": "Step 1 — Wire Up Your Controls 🔌",
        "tip": "Tell the Arduino which parts send signals IN and which parts it controls.",
        "tabs": {
          "explain": {
            "label": "📖 What & Why",
            "content": """
<p>You're in the pilot seat! ✈️ Before your engine can do anything, the Arduino needs to know about each part on your dashboard.</p>
<p>Two parts send information <b>IN</b> to the Arduino — the Arm Switch and the Engage Button. Two parts get commands sent <b>OUT</b> — the Engine Light and the Engine Buzzer.</p>
<p>Without this step, the Arduino can't hear your switch flip, and it can't tell the light or buzzer what to do.</p>
<p>Next up: you get to turn the light and buzzer ON for the very first time! 💡🔊</p>
""",
            "circuit_definition": engine_circuit_definition
          },
          "howto": {
            "label": "🔧 How To",
            "content": """
<p><b>Match each part to its pin:</b></p>
<p>
🔘 Arm Switch → Pin 9<br>
🔴 Engage Button → Pin 7<br>
💡 Engine Light → Pin 2<br>
🔊 Engine Buzzer → Pin 5
</p>
<p>You'll place two blocks yourself:</p>
<ol>
<li>An <b>input</b> block for the Arm Switch on <b>Pin 9</b> — this tells the Arduino "listen to this pin."</li>
<li>An <b>output</b> block for the Engine Light on <b>Pin 2</b> — this tells the Arduino "you control this pin."</li>
</ol>
<p>The Engage Button (Pin 7) and Engine Buzzer (Pin 5) are already locked in for you — they work exactly the same way, just for the other two parts.</p>
<p>🔘 <b>Special rule:</b> Both the switch and the button connect to GND on the diagram, so they both use a special input called <b>INPUT_PULLUP</b>. That's just how this wiring style talks to the Arduino.</p>
""",
          },
          "logic": {
            "label": "🧠 Logic",
            "content": """
<p>Think of a walkie-talkie. 📻 Some buttons let you <b>talk</b> — those are your outputs (the light, the buzzer). Some let you <b>listen</b> — those are your inputs (the switch, the button).</p>
<p>Before you can use a walkie-talkie at all, you have to turn it on and set it to the right mode. That's exactly what this step does for every part on your dashboard.</p>
""",
          }
        }
      },

      {
        "title": "Step 2 — Light the Engine 💡🔊",
        "tip": "Turn the engine light and buzzer ON — no rules yet, just prove they work!",
        "tabs": {
          "explain": {
            "label": "📖 What & Why",
            "content": """
<p>Time for your first win, pilot! 🎉 Before you teach the engine any rules, let's prove the light and buzzer actually work.</p>
<p>This step turns the Engine Light and Engine Buzzer <b>ON</b> — no switch, no button, no conditions. Just ON.</p>
<p>Why start here? Because if something's wired wrong, you want to know <i>now</i> — before you bury it inside a bunch of rules.</p>
<p>Next, you'll wrap these same two blocks inside your first rule so they only turn on when the engine is armed.</p>
<p>🎮 <b>Try It:</b> Open the sim tab. Watch the Engine Light and Engine Buzzer — they should both switch on immediately, with no switch or button needed. That's your proof the wiring works!</p>
""",
          },
          "howto": {
            "label": "🔧 How To",
            "content": """
<p>You'll place two blocks:</p>
<ol>
<li><b>Turn the engine light on.</b> Use an output block set to the Engine Light pin, value <b>HIGH</b>. HIGH means "full power" — the light glows.</li>
<li><b>Turn the engine buzzer on.</b> Use an output block set to the Engine Buzzer pin, value <b>HIGH</b>. Same idea — HIGH means "make sound."</li>
</ol>
<p>Result: as soon as your code runs, the light glows and the buzzer sounds — every single time, no conditions needed yet.</p>
""",
          },
          "sim": {
            "label": "🎮 Try It",
            "type": "sim",
            "sim_config": {
              "mode": "interpreted",
              "components": [
                {"type": "led",    "id": "led1", "color": "red", "pin": 2, "label": "Engine Light"},
                {"type": "buzzer", "id": "buz1", "pin": 5, "label": "Engine Buzzer"},
              ]
            }
          }
        }
      },

      {
        "title": "Step 3 — Only Run When Armed 🔐",
        "tip": "Wrap your light and buzzer in a rule — they should only turn on if the switch is armed.",
        "tabs": {
          "explain": {
            "label": "📖 What & Why",
            "content": """
<p>Great work, pilot — the light and buzzer work. But right now they're on <i>all the time</i>, even if nobody armed the aircraft. That's not safe!</p>
<p>This step adds your first rule: the light and buzzer should only run <b>if the Arm Switch is ON</b>. If it's OFF, everything should shut off instead.</p>
<p>You're not writing new light/buzzer code — you're taking the two blocks you already built in Step 2 and wrapping them inside a rule.</p>
<p>Next step teaches the engine one more rule: needing the Engage Button too.</p>
<p>🎮 <b>Try It:</b> Open the sim tab and flip the Arm Switch OFF. Watch the light and buzzer both go dark. Flip it back ON — they turn back on. That's a big change from Step 2, where they were always on no matter what — now the switch is the boss!</p>
""",
          },
          "howto": {
            "label": "🔧 How To",
            "content": """
<p>You'll place one new block, plus reuse two you already built:</p>
<ol>
<li><b>Check if the Arm Switch is on.</b> Use an "if" block that checks the switch pin. Because of INPUT_PULLUP, ON actually reads as <b>LOW</b> — a little backwards, but that's how this wiring works.</li>
<li>Inside that "if," your Step 2 light-on and buzzer-on blocks slot right in — you already built them, just wrap them in here.</li>
<li><b>Turn the light off</b> and <b>turn the buzzer off</b> in the "else" part — these run only when the switch is OFF. Both use value <b>LOW</b>, which means "no power."</li>
</ol>
""",
          },
          "sim": {
            "label": "🎮 Try It",
            "type": "sim",
            "sim_config": {
              "mode": "interpreted",
              "components": [
                {"type": "switch", "id": "sw1",  "pin": 9, "label": "Arm Switch"},
                {"type": "led",    "id": "led1", "color": "red", "pin": 2, "label": "Engine Light"},
                {"type": "buzzer", "id": "buz1", "pin": 5, "label": "Engine Buzzer"},
              ]
            }
          }
        }
      },

      {
        "title": "Step 4 — Press to Start 🔴",
        "tip": "The buzzer should only sound if the switch is armed AND the button is pressed.",
        "tabs": {
          "explain": {
            "label": "📖 What & Why",
            "content": """
<p>One rule down, one to go! Right now, arming the switch turns the light <i>and</i> the buzzer on together. But a real engine shouldn't roar just because it's armed — it should wait for you to press Start. 🔴</p>
<p>This step adds a second rule <i>inside</i> the first one: the buzzer only sounds if the Engage Button is pressed too. The light stays simple — it just means "armed."</p>
<p>This is your last rule. After this, your whole engine system is complete!</p>
<p>🎮 <b>Try It:</b> Arm the switch — the light turns on, but now the buzzer stays silent. Press the Engage Button — the buzzer joins in! Release the button — buzzer stops, light stays on. Compare that to Step 3, where arming the switch was enough to sound the buzzer all by itself — now it needs your button press too.</p>
""",
          },
          "howto": {
            "label": "🔧 How To",
            "content": """
<p>Everything from Steps 1–3 is already locked in place. You'll place one new block:</p>
<ol>
<li><b>Check if the Engage Button is pressed.</b> Use an "if" block that checks the button pin. Just like the switch, pressed reads as <b>LOW</b> because of INPUT_PULLUP.</li>
<li>Inside that "if," the buzzer-on block is already locked for you — turning the buzzer to HIGH.</li>
<li><b>Turn the buzzer off</b> in the matching "else" — this runs when the switch is armed but the button isn't pressed. Value <b>LOW</b> means silent.</li>
</ol>
<p>Notice the Engine Light block from Step 3 stays right where it was — outside this new rule. The light only cares about the switch; the buzzer now cares about both.</p>
""",
          },
          "sim": {
            "label": "🎮 Try It",
            "type": "sim",
            "sim_config": {
              "mode": "interpreted",
              "components": [
                {"type": "switch", "id": "sw1",  "pin": 9, "label": "Arm Switch"},
                {"type": "button", "id": "btn1", "pin": 7, "label": "Engage Button"},
                {"type": "led",    "id": "led1", "color": "red", "pin": 2, "label": "Engine Light"},
                {"type": "buzzer", "id": "buz1", "pin": 5, "label": "Engine Buzzer"},
              ]
            }
          }
        }
      },

      {
        "title": "Mission Complete 🎉",
        "tip": "Your Engine System is fully operational!",
        "tabs": {
          "explain": {
            "label": "📖 What You Built",
            "content": """
<p>Mission complete, pilot! 🛫 You built a real engine control system from scratch.</p>
<p>Your aircraft now:</p>
<ul>
<li>🔘 Knows the exact moment the Arm Switch flips ON or OFF</li>
<li>💡 Lights up the Engine Light only while armed</li>
<li>🔴 Waits for your Engage Button before making a sound</li>
<li>🔊 Sounds the Engine Buzzer only when BOTH the switch and button say go</li>
<li>🛑 Shuts everything off the instant you disarm the switch</li>
</ul>
<p>You proved you can build rules that depend on more than one part working together — that's real pilot-level thinking!</p>
""",
          },
          "howto": {
            "label": "🔧 Try This Next",
            "content": """
<p>Now that your system works, here are some ideas to make it even better.</p>
<ul>
<li>💡 <b>Add a warning light</b> — light up a second LED whenever the switch is armed but the button hasn't been pressed yet.</li>
<li>⏱️ <b>Add a startup delay</b> — make the buzzer wait half a second after the button press before sounding, like a real engine spinning up.</li>
<li>🔊 <b>Change the buzzer pattern</b> — instead of one steady tone, make it beep twice when the engine starts.</li>
<li>🎚️ <b>Add a second switch</b> — require TWO switches armed before the button does anything, like a real two-key launch system.</li>
<li>🚦 <b>Build a shutdown sequence</b> — when the switch turns OFF, flash the light three times before going dark instead of snapping off instantly.</li>
</ul>
<p>Experimenting is how real pilots improve their aircraft.</p>
""",
          },
          "logic": {
            "label": "🧠 What You Learned",
            "content": """
<p>This project brought together everything you've been building.</p>
<ul>
<li>🔌 <b>Inputs vs. outputs</b> — some parts talk to the Arduino, some parts the Arduino controls.</li>
<li>🔘 <b>INPUT_PULLUP</b> — a wiring style where "pressed" or "on" actually reads as LOW.</li>
<li>🎁 <b>Reward-first testing</b> — proving your outputs work before wrapping them in rules.</li>
<li>🔐 <b>Nested rules</b> — a rule inside another rule, so the buzzer needs BOTH the switch AND the button.</li>
<li>🧩 <b>Reusing blocks</b> — wrapping code you already built into a bigger rule instead of rewriting it.</li>
</ul>
<p>You're now thinking like a real pilot — checking every system before you commit to launch. 🚀</p>
""",
          },
          "sim": {
            "label": "🎮 Try It",
            "type": "sim",
            "sim_config": {
              "mode": "interpreted",
              "components": [
                {"type": "switch", "id": "sw1",  "pin": 9, "label": "Arm Switch"},
                {"type": "button", "id": "btn1", "pin": 7, "label": "Engage Button"},
                {"type": "led",    "id": "led1", "color": "red", "pin": 2, "label": "Engine Light"},
                {"type": "buzzer", "id": "buz1", "pin": 5, "label": "Engine Buzzer"},
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
//>> Setup Pins | guided | blocks

void setup() {
  //?? Set the arm switch pin as an input
  pinMode(9, INPUT_PULLUP);
  //## pinMode(7, INPUT_PULLUP);
  //?? Set the engine light pin as an output
  pinMode(2, OUTPUT);
  //## pinMode(5, OUTPUT);
}

void loop() {
}

//>> Reward-First: Light the Engine | guided | blocks

void setup() {
  //## pinMode(9, INPUT_PULLUP);
  //## pinMode(7, INPUT_PULLUP);
  //## pinMode(2, OUTPUT);
  //## pinMode(5, OUTPUT);
}

void loop() {
  //?? Turn on the engine light
  digitalWrite(2, HIGH);
  //?? Turn on the engine buzzer
  digitalWrite(5, HIGH);
}

//>> Capture: Only Run When Armed | guided | blocks

void setup() {
  //## pinMode(9, INPUT_PULLUP);
  //## pinMode(7, INPUT_PULLUP);
  //## pinMode(2, OUTPUT);
  //## pinMode(5, OUTPUT);
}

void loop() {
  //?? Check if the arm switch is on
  if (digitalRead(9) == LOW) {
    //## digitalWrite(2, HIGH);
    //## digitalWrite(5, HIGH);
  }
  //## else {
    //?? Turn off the engine light
    digitalWrite(2, LOW);
    //?? Turn off the engine buzzer
    digitalWrite(5, LOW);
  //## }
}

//>> Capture: Buzzer Needs the Button Too | guided | blocks

void setup() {
  //## pinMode(9, INPUT_PULLUP);
  //## pinMode(7, INPUT_PULLUP);
  //## pinMode(2, OUTPUT);
  //## pinMode(5, OUTPUT);
}

void loop() {
  //## if (digitalRead(9) == LOW) {
    //## digitalWrite(2, HIGH);
    //?? Check if the start button is pressed
    if (digitalRead(7) == LOW) {
      //## digitalWrite(5, HIGH);
    }
    //## else {
      //?? Turn off the engine buzzer
      digitalWrite(5, LOW);
    //## }
  //## }
  //## else {
    //## digitalWrite(2, LOW);
    //## digitalWrite(5, LOW);
  //## }
}

//>> Mission Complete | open | blocks
""",
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
    "My switch on row 4H won't turn on",
    "No sound from buzzer at 14E",
    "LED at 22E isn't glowing",
    "Resistor on row 21D is loose",
    "Wire from Pin 9 to row 5I is loose",
]

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
