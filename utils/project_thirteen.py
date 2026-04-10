
from utils.step_builder import build_step, intro_step, rect, circle, line

META = {
    'title': 'Project 13: The Reaction Timer',
    'circuit_image': 'static/graphics/reaction_timer_circuit.png',
    'banner_image': None,
}

STEPS = [
    intro_step(
        "Let's build our thirteenth project",
        "Press the next button for a step by step guide",
    ),
    build_step(
        "Place the button onto the breadboard.<br>Place the legs into rows 8 and 10, columns E and F.",
        "Touch the button to start the timer. Press it again to stop it!",
        rect(708, 249, 818, 340),
        greyout=True,
    ),
    build_step(
        "Place one end of the wire in Arduino Pin 2.<br>Place the other end in row 8, column D.",
        "This is the signal for our timer button.",
        line((361, 493), (384, 487), (568, 342), (748, 345), width=20),
        greyout=True,
    ),
    build_step(
        "Place one end of the wire in row 10, column G.<br>Place the other end in the negative (-) rail.",
        "This completes our button loop.",
        line((787, 253), (768, 98), width=20),
        greyout=True,
    ),
    build_step(
        "Place one end of the wire in Arduino Pin GND.<br>Place the other end in the negative (-) rail.",
        "This helps complete our circuit loop.",
        # Coordinate for GND to Rail based on standard layout
        line((621, 113), (356, 249), width=20),
        greyout=True,
    ),
]

from utils.image_utils import img_to_b64

timer_circuit_b64 = img_to_b64("static/graphics/reaction_timer_circuit.png")

DRAWER_CONTENT = {
  "project_thirteen": {
    "steps": [
      {
        "title": "Step 1 — Build the Reaction Timer ⏱️",
        "tip": "Understand and assemble the full reaction timer system.",
        "tabs": {
          "story": {
            "label": "🧪 Mission",
            "content": """
<h3>Welcome to the Arduino Reaction Lab! 🧪</h3>

<p>
Today, you will build a <b>reaction timer</b> — just like scientists use to measure reflexes.
</p>

<p><b>Your mission:</b></p>

<p>
🔘 Press the button as fast as you can<br>
⏱️ The Arduino will measure your reaction time<br>
💻 Watch the results on your computer
</p>

<p>
Ready… Set… React!
</p>
""",
            "image_b64": timer_circuit_b64
          },

          "code": {
            "label": "💻 Build & Understand",
            "content": """
<h3>The Reaction Timer Program</h3>

<p>
You are going to build this program step by step. Each part has a specific job that makes the timer work.
</p>

<h4>🧩 Variables — Memory</h4>
<pre>
int button = 2;
int running = 0;

unsigned long startTime = 0;
unsigned long time = 0;
</pre>
<p>
These variables store everything the program needs to remember:
<br>
• Which pin the button is on<br>
• Whether the timer is running<br>
• When the timer started<br>
• How long the reaction took
</p>

<h4>⚙️ Setup — Preparation</h4>
<pre>
void setup() {
  pinMode(button, INPUT_PULLUP);
  Serial.begin(9600);
}
</pre>
<p>
The Arduino prepares itself:
<br>
• Sets up the button input<br>
• Opens communication with the computer
</p>

<h4>🔁 Loop — Continuous Check</h4>
<pre>
void loop() {
</pre>
<p>
The Arduino constantly checks for button presses.
</p>

<h4>🔘 Input — Detect Press</h4>
<pre>
if (digitalRead(button) == LOW) {
</pre>
<p>
When the button is pressed, the program reacts.
</p>

<h4>🟢 Start Timing</h4>
<pre>
if (running == 0) {
  startTime = millis();
  running = 1;
}
</pre>
<p>
First press → start the timer.
</p>

<h4>🔴 Stop Timing</h4>
<pre>
else {
  time = millis() - startTime;
  Serial.println(time);
  running = 0;
}
</pre>
<p>
Second press → stop the timer and display the result.
</p>

<h4>⏱️ Stabilize Input</h4>
<pre>
delay(300);
</pre>
<p>
Prevents accidental multiple readings from one press.
</p>

<pre>
}
</pre>
"""
          },

          "logic": {
            "label": "🧩 Logic",
            "content": """
<h3>How the Timer Thinks</h3>

<p>
The Arduino is constantly running a simple decision loop:
</p>

<p>
🔘 Check the button<br>
🤔 Is this the first press or second press?<br>
⏱️ Start or stop timing<br>
💻 Send result to the computer<br>
🔁 Repeat
</p>

<p>
<b>Flow:</b><br>
First press → Start timer<br>
Second press → Stop timer and record reaction
</p>
"""
          },

          "translation": {
            "label": "🧬 Translation",
            "content": """
<h3>Key Code Meanings</h3>

<p><b>pinMode(button, INPUT_PULLUP)</b><br>
Prepares the button input with a stable signal</p>

<p><b>digitalRead(button)</b><br>
Checks if the button is pressed</p>

<p><b>running</b><br>
Tracks whether the timer is active</p>

<p><b>millis()</b><br>
Gives the current time in milliseconds</p>

<p><b>time = millis() - startTime</b><br>
Calculates reaction time</p>

<p><b>Serial.println(time)</b><br>
Sends the result to the computer</p>

<p><b>delay(300)</b><br>
Prevents multiple accidental presses</p>
"""
          }
        }
      },

      {
        "title": "Step 2 — Test Your Reaction Timer 🚀",
        "tip": "Upload your code and measure your reaction time.",
        "tabs": {
          "complete": {
            "label": "🎉 Congratulations",
            "content": """
<h3>You Built a Reaction Timer! 🎉</h3>

<p>
Your system is ready. Now it's time to test it.
</p>

<p>
🔌 Connect your Arduino<br>
⬆️ Upload your code<br>
💻 Open the Serial Monitor<br>
🔘 Press the button twice to measure your reaction time
</p>

<p>
Try multiple times and see how fast you can react!
</p>
"""
          },
          "sim": {
            "label": "🎮 Try It",
            "type": "sim",
            "sim_config": {
              "components": [
                {"type": "button", "id": "btn1", "pin": 2, "label": "Timer Button"},
                {"type": "timer",  "id": "tmr1",           "label": "Reaction Time"},
              ],
              "behaviors": [
                {"when": {"btn1": "pressed"}, "then": {"tmr1": "toggle"}},
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
//## int button = 2;

//## int running = 0;

//?? Set unsined long variable to 0
unsigned long startTime = 0;
//?? Set unsined long variable to 0
unsigned long time = 0;

void setup() {
  //?? Set the pinmode for the button
  pinMode(button, INPUT_PULLUP);
  //## Serial.begin(9600);
}

void loop() {

  //## if (digitalRead(button) == LOW) {

    //## if (running == 0) {
      //?? Set the start time to equal millis
      startTime = millis();
      //?? Set running to 1
      running = 1;
    //## }
    //## else {
      //?? When was the button pressed?
      time = millis() - startTime;
      //## Serial.println(time);
      //?? Set running to 0
        running = 0;
    //## }

    //## delay(300);
  //## }
//## }
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