
from utils.step_builder import build_step, intro_step, rect, circle, line

META = {
    'title': 'Project 11: Engine System Start',
    'circuit_image': 'static/graphics/project_twelve_circuit.png',
    'banner_image': None,
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

import base64
from pathlib import Path

def img_to_b64(path):
    data = Path(path).read_bytes()
    b64 = base64.b64encode(data).decode()
    ext = Path(path).suffix.lstrip(".")
    return f"data:image/{ext};base64,{b64}"

engine_circuit_b64 = img_to_b64("static/graphics/project_twelve_circuit.png")

DRAWER_CONTENT = {
  "project_eleven": {
    "steps": [
      {
        "title": "Step 1 — Build the Engine Control System 📘",
        "tip": "Create the rules that control when the engine is allowed to run.",
        "tabs": {
          "mission": {
            "label": "🧠 Mission",
            "content": """
<h3>You are building an engine system with rules:</h3>

<p>
- The switch controls the whole system.<br>
- The button starts the engine.<br>
- The engine keeps running until the switch turns OFF.<br>
- If the switch is OFF, nothing runs.<br>
- The "If" blocks are filled in already, no need to change them.
</p>

<p>Your job is to build these rules using blocks.</p>
""",
            "image_b64": engine_circuit_b64
          },

          "wiring": {
            "label": "🔌 Wiring",
            "content": """
<b>Match each part to its pin:</b><br><br>

🔘 Arm Switch → Pin 9<br>
🔴 Engage Button → Pin 7<br>
💡 Engine Light → Pin 2<br>
🔊 Engine Buzzer → Pin 5<br><br>

Find the part in the diagram.<br>
Follow the wire.<br>
Match it to the pin.
"""
          },

          "logic": {
            "label": "🧩 Logic",
            "content": """
<b>🔘 Important Button Rule</b><br><br>

Look at the wiring diagram.<br><br>

If the button connects to GND, choose:<br>
<b>INPUT_PULLUP</b><br><br>

That's how this wiring style works.<br><br>

<b>Understanding The "If" statements:</b><br><br>

The Arduino sees <b>HIGH</b> when the switch is <b>off</b> or the button is <b>not pressed</b><br>
The Arduino sees <b>LOW</b> when the switch is <b>on</b> or the button is <b>pressed</b><br><br>

<b>Think about the flow:</b><br><br>

IF switch is ON<br>
&nbsp;&nbsp;&nbsp;&nbsp;Light ON<br>
&nbsp;&nbsp;&nbsp;&nbsp;IF button pressed<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Engine ON<br><br>

IF switch is OFF (else)<br>
&nbsp;&nbsp;&nbsp;&nbsp;Everything OFF<br><br>

Remember: The switch is the boss.
"""
          }
        }
      },

      {
        "title": "Step 2 — Test Your Engine System 🚀",
        "tip": "Upload your code and verify your engine rules work correctly.",
        "tabs": {
          "complete": {
            "label": "🎉 Congratulations",
            "content": """
<h3>You Built an Engine Control System! 🎉</h3>

<p>
Your logic system is ready. Now it's time to test it.
</p>

<p>
🔌 Connect your Arduino<br>
⬆️ Upload your code<br>
🔘 Turn the switch ON<br>
🔴 Press the button to start the engine<br>
💡 Observe the light and buzzer behavior
</p>

<p>
<b>Check your system:</b><br><br>

✔️ Switch OFF → Everything stays OFF<br>
✔️ Switch ON → System becomes active<br>
✔️ Button Press → Engine activates<br>
✔️ Switch OFF again → Everything shuts down
</p>

<p>
If all of these work, your engine logic is correct!
</p>
"""
          }
        }
      }
    ]
  }
}


SKETCH_PRESET = {
    'sketch': """
//>> Step 1 - Complete the skecth | guided | filtered
void setup() {
//##  pinMode(9, INPUT_PULLUP);   // Arm switch
//?? Define the button pin
  pinMode(7, INPUT_PULLUP);   // Engage button
//##  pinMode(2, OUTPUT);         // Engine light
//?? Defind the buzzer pin
  pinMode(5, OUTPUT);         // Engine buzzer
}

void loop() {
//##  if (digitalRead(9) == LOW) {   // Switch ON
//?? Turn the light on
    digitalWrite(2, HIGH);       // Light ON (armed)

//##    if (digitalRead(7) == LOW) {
//?? Turn the buzzer ON
      digitalWrite(5, HIGH);     // Start engine
//##    } else {
//?? Turn the buzzer OFF
      digitalWrite(5, LOW);
//##    }
//##  } else {                        // Switch OFF
//?? Turn the light OFF
    digitalWrite(2, LOW);         // Light OFF
//?? Turn the buzzer OFF
    digitalWrite(5, LOW);         // Engine OFF
//##  }
//## }

//>> Step 2 - Complete | free
void setup() { }
void loop() { } """,
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