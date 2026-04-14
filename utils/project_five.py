
from utils.step_builder import build_step, intro_step, rect, circle

META = {
    'title': 'Project 4: Space Station Launch Button',
    'circuit_image': None,
    'banner_image': None,
}

STEPS = None

DRAWER_CONTENT = {

    "project_five": {
    "title": "🕵️ Secret Spy Data Beam",
    "tip": "Learn how your Arduino sends messages to your computer using serial communication.",
    "tabs": {
        "story": {
            "label": "🕶️ Mission",
            "content": """
<h3>🚀 Top Secret Mission! 🤫</h3>

<p>
🕵️‍♂️ Welcome, Agent.
</p>

<p>
Did you know your Arduino can <b>talk to your computer</b>? 🤯<br>
It sends messages using a secret digital signal called a <b>data beam</b>!
</p>

<p>
Your mission:
</p>

<p>
📡 Build a device that sends secret messages<br>
💻 Watch them appear on your screen<br>
🔐 No sound — just data!
</p>

<p>
Engineers and spies use systems like this to share information.
</p>

<p>
Get ready…<br>
<b>Build the beam. Watch the screen. Crack the code!</b> 🔐✨
</p>
"""
        },
        "code": {
            "label": "💻 Code",
            "content": """
<h3>The Spy Program</h3>

<pre>
void setup() {
  // Start the secret chat!
  Serial.begin(9600);
  Serial.println("--- SPY PHONE ON ---");
}

void loop() {
  // Send a secret message
  Serial.println("I am a hacker! 💻");
  delay(1000);

  Serial.println("Mission: Success! ✅");
  delay(1000);
}
</pre>

<p>
This code sends messages from your Arduino to your computer screen.
</p>
"""
        },
        "logic": {
            "label": "🧩 Logic",
            "content": """
<h3>How the Data Beam Works</h3>

<p>
The Arduino follows this pattern:
</p>

<p>
📡 Turn on communication<br>
💬 Send a message<br>
⏱️ Wait<br>
💬 Send another message<br>
⏱️ Wait<br>
🔁 Repeat forever
</p>

<p>
Your computer listens and displays everything it receives!
</p>
"""
        },
        "translation": {
            "label": "🧬 Translation",
            "content": """
<h3>Spy Code Translation</h3>

<p>
<b>Serial.begin(9600)</b><br>
Turns on the "Spy Phone" 📞<br>
This connects your Arduino to the computer.
</p>

<p>
<b>Serial.println()</b><br>
Sends a message 💬<br>
Whatever is inside shows up on your screen!
</p>

<p>
<b>delay(1000)</b><br>
Wait 1 second ⏱️ before sending the next message
</p>

<p>
<b>The loop</b><br>
Runs forever 🔁<br>
Send → Wait → Send → Wait
</p>
"""
        }
    }
},
}
SKETCH_PRESET = {
    'sketch': """void setup() {
  // Start the secret chat!
  Serial.begin(9600);
  Serial.println("--- SPY PHONE ON ---");
}

void loop() {
  // Send a secret message
  Serial.println("I am a hacker!");
  delay(1000);

  Serial.println("Mission: Success!");
  delay(1000);
}""",
    'default_view': 'editor',
    'read_only': True,
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