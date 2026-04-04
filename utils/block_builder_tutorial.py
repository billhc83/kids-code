from utils.step_builder import build_step, intro_step, rect, circle

META = {
    'title': 'How to use the block builder',
    'circuit_image': None,
    'banner_image': None,
}

STEPS = None

DRAWER_CONTENT = {
    "block_builder_tutorial": {
        "title": "🧭 Getting Started with the Block Builder",
        "tip": "Learn how to use the editor, blocks, and controls before building real programs.",
        "tabs": {

            "mission": {
                "label": "🚀 Mission",
                "content": """
<h3>👋 Welcome to the Block Builder!</h3>

<p>
This is your main tool for creating Arduino programs.
</p>

<p>
You will learn how to:
</p>

<p>
🧱 Build code using blocks<br>
💻 See the same code in the editor<br>
⚡ Send your program to your Arduino
</p>

<p>
💡 Important:
</p>

<p>
The <b>Editor</b> and the <b>Block Builder</b> are the SAME program.<br>
They are just two different ways of building it.
</p>

<p>
Blocks make things easier — no typing required!<br>
The editor shows the real code behind the blocks.
</p>

<p>
Let’s explore the interface so you know what everything does.
</p>
"""
            },

            "controls": {
                "label": "🛠️ Controls",
                "content": """
<h3>🔧 Interface Controls</h3>

<p><b>🔌 Connection</b></p>
<p>
<b>Port Selector</b><br>
Choose where your Arduino is plugged into your computer.
</p>

<p><b>🚀 Running Your Code</b></p>
<p>
<b>Compile</b><br>
Check your code for errors before running it.
</p>

<p>
<b>Upload</b><br>
Send your code to the Arduino so it can run.
</p>

<p>
<b>Serial Monitor</b><br>
Open a window to see messages from your Arduino.
</p>

<p><b>🧰 Tools</b></p>
<p>
<b>Save</b> — Save your progress<br>
<b>Copy</b> — Copy your code<br>
<b>Reset</b> — Restore the starting code<br>
<b>Clear</b> — Remove everything
</p>
"""
            },

            "builder": {
                "label": "🧱 Builder",
                "content": """
<h3>🧱 The Block Builder</h3>

<p>
Look for the blue button 🤖 in the corner of the screen.
</p>

<p>
That button opens your <b>Block Builder</b>.
</p>

<p>
Inside, you will see:
</p>

<p>
🧩 Blocks — the pieces of your program<br>
📐 Workspace — where blocks snap together<br>
💻 Editor — shows the code version
</p>

<p>
💡 When you change blocks, the code updates.<br>
When you change code, the blocks update.
</p>

<p>
It’s all connected!
</p>
"""
            },

            "first_try": {
                "label": "✏️ First Try",
                "content": """
<h3>🎯 Try It Yourself</h3>

<p>
Let’s write your first line of code!
</p>

<p>
Inside the <b>loop()</b> section, type:
</p>

<pre>
Serial.println("Hello world!");
</pre>

<p>
This line tells the Arduino to send a message to your computer.
</p>

<p>
💡 Don’t worry if it doesn’t work yet — this is just practice!
</p>

<p>
In the next step, we’ll make it work for real 🚀
</p>
"""
            }
        }
     }
  }



SKETCH_PRESET = {
    'sketch': """
//>> Step 1 - The Program Structure | free | blocks | nofilter
void setup() {
}
void loop() {
}

//>> Step 2 - Start Communication | free | blocks | nofilter| fill:false
void setup() {
  //?? Turn on the serial connection
  Serial.begin(9600);
}
void loop() {
}

//>> Step 3 - Send Your First Message 
void setup() {
  //## Serial.begin(9600);
  //?? Send a message to the computer
  Serial.println("Hello!");
}
void loop() {
}

//>> Step 4 - Create a Variable | free | blocks | nofilter
//?? Create a number variable
int myNumber = 5;

void setup() {
  //## Serial.begin(9600);
  //## Serial.println("Hello!");
}
void loop() {
}

//>> Step 5 - Print the Variable | free | blocks | nofilter
void setup() {
  //## Serial.begin(9600);
  //?? Print the variable value
  Serial.println(myNumber);
}
void loop() {
}

//>> Step 6 - Change the Variable | guided | blocks | nofilter
void setup() {
  //## Serial.begin(9600);
  //?? Change the variable value
  myNumber = 10;
  //## Serial.println(myNumber);
}
void loop() {
}

//>> Step 7 - Move to Loop | free | blocks | nofilter
void setup() {
  //## Serial.begin(9600);
}

void loop() {
  //?? Print the variable repeatedly
  Serial.println(myNumber);
}

//>> Step 8 - Add a Delay | free | blocks | nofilter
void setup() {
  //## Serial.begin(9600);
}

void loop() {
  //## Serial.println(myNumber);
  //?? Wait 1 second between prints
  delay(1000);
}

//>> Step 9 - Tutorial Complete | free | blocks | nofilter
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