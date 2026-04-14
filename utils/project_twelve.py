

from utils.step_builder import build_step, intro_step, rect, circle, line

META = {
    'title': 'Project 12: Night Patrol Alarm',
    'circuit_image': 'static/graphics/project_thirteen_circuit.png',
    'banner_image': "static/graphics/patrol_alarm.png",
}

STEPS = [
    intro_step(
        "Let's build our twelfth project",
        "Press the next button for a step by step guide",
    ),
    build_step(
        "Place the long leg of the LED in row 18, column E.<br>Place the short leg in row 17, column E",
        "Make sure your lights are in the right order.",
        rect(876, 175, 971, 344),
    ),
    build_step(
        "Place the long leg of the LED in row 24, column E.<br>Place the short leg in row 23, column E.",
        "Red, then Blue!",
        rect(994, 181, 1083, 347),
    ),
    build_step(
        "Place the long leg of the LED in row 30, column E.<br>Place the short leg in row 29, column E",
        "The Clear Strobe goes last.",
        rect(1093, 168, 1203, 343),
    ),
    build_step(
        "Add the 220 ohm resistors for each LED to protect them.",
        "Resistors slow down the electricity.",
        rect(805, 318, 940, 376),
        rect(929, 305, 1056, 376),
        rect(1047, 300, 1171, 370),
    ),
    build_step(
        "Place the button onto the breadboard across the center gap.",
        "This is the Master Power Button.",
        rect(719, 244, 812, 347),
    ),
    build_step(
        "Wire the LEDs to Pins 8, 6, and 4.",
        "Red = Pin 8, Blue = Pin 6, Clear = Pin 4.",
        line((366, 358), (933, 364)),
        line((1048, 401), (364, 411)),
        line((1165, 399), (370, 449)),
    ),
    build_step(
        "Wire the Button to Pin 12.",
        "This wire sends the signal to the Arduino.",
        line((749, 347), (366, 284)),
    ),
    build_step(
        "Complete the Ground (GND) connections.",
        "Finish the circuit loop to the negative rail.",
        line((621, 113), (356, 249)),
        line((788, 263), (766, 106)),
        line((844, 337), (806, 106)),
        line((956, 333), (962, 111)),
        line((1075, 336), (1078, 103)),
    ),
]

from utils.image_utils import img_to_b64

patrol_alarm_b64 = img_to_b64("static/graphics/project_thirteen_circuit.png")

DRAWER_CONTENT = {
  "project_twelve": {
    "steps": [
      {
        "title": "Step 1 — Build the Light Bar System 📘",
        "tip": "Create the flashing pattern that controls the patrol light bar.",
        "tabs": {
          "mission": {
            "label": "🧠 Mission",
            "content": """
<h3>You are building the patrol vehicle light bar system.</h3>

<p>The light bar must flash in a clear pattern so people can see the vehicle at night.</p>

<p>
- The switch controls the whole system.<br>
- If the button is OFF → all lights stay OFF.<br>
- If the button is ON (pressed) → the flashing pattern begins.<br>
- The lights flash one at a time.<br>
- The pattern repeats again and again.
</p>

<p>
Each light flash must use a short pause.<br>
At Night Patrol Academy we use: <b>delay(150)</b><br>
Use this delay after each light turns ON and turns OFF.
</p>

<p>Your job is to build the flashing pattern using blocks.</p>
""",
            "image_b64": patrol_alarm_b64
          },

          "wiring": {
            "label": "🔌 Wiring",
            "content": """
<b>Match each part to its pin:</b><br><br>

🔘 Master Button → Pin 12<br>
🔴 Red Light → Pin 8<br>
🔵 Blue Light → Pin 6<br>
⚪ Clear Strobe Light → Pin 4<br><br>

Find the part in the diagram.<br>
Follow the wire.<br>
Match it to the pin.
"""
          },

          "logic": {
            "label": "🧩 Logic",
            "content": """
<b>🔘 Button Input Rule</b><br><br>

If the Button connects to GND, choose:<br>
<b>INPUT_PULLUP</b><br><br>

<b>Understanding the Button:</b><br><br>

HIGH = Button OFF (not pressed)<br>
LOW = Button ON (pressed)<br><br>

<b>Think about the pattern:</b><br><br>

IF button is ON (pressed)<br>
&nbsp;&nbsp;&nbsp;&nbsp;Red ON → delay → Red OFF<br>
&nbsp;&nbsp;&nbsp;&nbsp;Blue ON → delay → Blue OFF<br>
&nbsp;&nbsp;&nbsp;&nbsp;Clear ON → delay → Clear OFF<br><br>

IF button is OFF (else)<br>
&nbsp;&nbsp;&nbsp;&nbsp;All lights OFF<br><br>

Remember: The button controls everything.
"""
          }
        }
      },

      {
        "title": "Step 2 — Test Your Light Bar 🚨",
        "tip": "Upload your code and verify the flashing pattern works correctly.",
        "tabs": {
          "complete": {
            "label": "🎉 Congratulations",
            "content": """
<h3>You Built a Patrol Light Bar System! 🎉</h3>

<p>
Your light system is ready. Now it's time to test it.
</p>

<p>
🔌 Connect your Arduino<br>
⬆️ Upload your code<br>
🔘 Press the master button<br>
🚨 Watch the light sequence
</p>

<p>
<b>Check your system:</b><br><br>

✔️ Button OFF → All lights stay OFF<br>
✔️ Button ON → Lights begin flashing<br>
✔️ Red → Blue → Clear sequence runs in order<br>
✔️ Each light turns ON and OFF with a delay<br>
✔️ Pattern repeats continuously
</p>

<p>
If all of these work, your patrol light bar is operating correctly!
</p>
"""
          },
          "sim": {
            "label": "🎮 Try It",
            "type": "sim",
            "sim_config": {
              "components": [
                {"type": "button", "id": "btn1",  "pin": 12, "label": "Master Button"},
                {"type": "led",    "id": "led_r",  "color": "red",   "pin": 8, "label": "Red Light"},
                {"type": "led",    "id": "led_b",  "color": "blue",  "pin": 6, "label": "Blue Light"},
                {"type": "led",    "id": "led_w",  "color": "white", "pin": 4, "label": "Clear Strobe"},
              ],
              "behaviors": [
                {
                  "when": {"btn1": "pressed"},
                  "then": {"_sequence": ["led_r", "led_b", "led_w"], "_interval": 150}
                },
                {
                  "when": {"btn1": "released"},
                  "then": {"_stop_sequence": "yes", "led_r": "off", "led_b": "off", "led_w": "off"}
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
//>> Step 1 - Complete the skecth | guided

//?? Define the Switch Pin
int switchPin = 12;
//?? Define The Red LED Pin
int redLED = 8;
//?? Define The Blue LED Pin
int blueLED = 6;
//?? Define The Clear LED Pin
int clearLED = 4;

void setup() {
//?? Set the mode for the switch pin
  pinMode(switchPin, INPUT_PULLUP);
//?? Set the mode for the red LED pin
  pinMode(redLED, OUTPUT);
//?? Set the mode for the blue LED pin
  pinMode(blueLED, OUTPUT);
//?? Set the mode for the clear LED pin
  pinMode(clearLED, OUTPUT);
}

void loop()
{
//##  if (digitalRead(switchPin) == LOW)
//##  {

//##    digitalWrite(redLED, HIGH);
//?? set delay to 150
    delay(150);
//##    digitalWrite(redLED, LOW);

//?? Set the blue LED to high
    digitalWrite(blueLED, HIGH);
//##    delay(150);
//##    digitalWrite(blueLED, LOW);

//##    digitalWrite(clearLED, HIGH);
//##    delay(150);
//?? set the clear LED to low
    digitalWrite(clearLED, LOW);
 //## }
 //## else
 //## {
//?? set the red LED to low
    digitalWrite(redLED, LOW);
//?? set the blue LED to low
    digitalWrite(blueLED, LOW);
//?? set the clear LED to low
    digitalWrite(clearLED, LOW);
  //##}
}

//>> Step 2 - Complete | free
void setup() { }
void loop() { }
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