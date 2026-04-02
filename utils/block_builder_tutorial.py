from utils.step_builder import build_step, intro_step, rect, circle

META = {
    'title': 'How to use the block builder',
    'circuit_image': None,
    'banner_image': None,
}

STEPS = None

DRAWER_CONTENT = {
    "block_builder_tutorial": {
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
    'sketch': """
//>> Step 1 - The Program Structure | free | blocks | nofilter
void setup() {
int i = 0;
}
void loop() {
}

//>> Step 2 - Start Communication | guided 
void setup() {
  //?? Turn on the serial connection
  Serial.begin(9600);
}
void loop() {
}

//>> Step 3 - Send Your First Message | guided
void setup() {
  //## Serial.begin(9600);
  //?? Send a message to the computer
  Serial.println("Hello!");
}
void loop() {
}

//>> Step 4 - Create a Variable | guided
//?? Create a number variable
int myNumber = 5;

void setup() {
  //## Serial.begin(9600);
  //## Serial.println("Hello!");
}
void loop() {
}

//>> Step 5 - Print the Variable | guided
void setup() {
  //## Serial.begin(9600);
  //?? Print the variable value
  Serial.println(myNumber);
}
void loop() {
}

//>> Step 6 - Change the Variable | guided
void setup() {
  //## Serial.begin(9600);
  //?? Change the variable value
  myNumber = 10;
  //## Serial.println(myNumber);
}
void loop() {
}

//>> Step 7 - Move to Loop | guided
void setup() {
  //## Serial.begin(9600);
}

void loop() {
  //?? Print the variable repeatedly
  Serial.println(myNumber);
}

//>> Step 8 - Add a Delay | guided
void setup() {
  //## Serial.begin(9600);
}

void loop() {
  //## Serial.println(myNumber);
  //?? Wait 1 second between prints
  delay(1000);
}

//>> Step 9 - Tutorial Complete | free
void setup() {
  //## Serial.begin(9600);
}

void loop() {
  //## Serial.println(myNumber);
  //## delay(1000);
}
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