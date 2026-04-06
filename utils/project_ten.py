
from utils.step_builder import build_step, intro_step, rect, circle

META = {
    'title': 'Project 10: The Spy Vault Security Console',
    'circuit_image': 'static/graphics/project_ten_circuit.png',
    'banner_image': None,
}

STEPS = [
    intro_step(
        "Let's build our tenth project",
        "Press the next button for a step by step guide",
    ),
    
    build_step(
        "Place the LED long leg in row 12, column E.<br>Place the LED short leg in row 11, column E",
        "The long leg is positive — it's called the anode!",
        rect(766, 231, 934, 390),
        greyout=True,
    ),
    build_step(
        "Place one leg of the 220 Ohm resistor in row 11, column D.<br>Place the second leg of the resistor in row 7, column D",
        "The resistor slows down the electricity",
        rect(733, 361, 879, 423),
        circle(540, 208, radius=60),
        greyout=True,
    ),
    build_step(
        "Place Switch 1 on the breadboard.<br>The centre pin goes in row 24 column E<br>The side pin goes in row 25 column E",
        "The switch acts like a key card",
        rect(1034, 280, 1150, 398),
        greyout=True,
    ),
    build_step(
        "Place Switch 2 on the breadboard.<br>The centre pin goes in row 17 column E<br>The side pin goes in row 18 column E",
        "The security locks turn on and off with the switches",
        rect(902, 290, 1013, 396),
        greyout=True,
    ),
    build_step(
        "Place one end of the wire in the Arduino Pin GND.<br>Place the other end in row 7 column E",
        "Ground wires help complete our circuit loop",
        rect(382, 282, 790, 385),
        greyout=True,
    ),
    build_step(
        "Connect Arduino GND to the negative rail.",
        "Ground wires help complete our circuit loop",
        rect(8, 0, 645, 50),
        rect(0, 12, 84, 415),
        rect(424, 0, 668, 184),
        greyout=True,
    ),
    build_step(
        "Place one end of the wire in Arduino Pin 8.<br>Place the other end in row 12 column A",
        "This wire powers our LED. Light On = Access Granted",
        rect(390, 392, 881, 502),
        greyout=True,
    ),
    build_step(
        "Place one end of the wire in Arduino Pin 3.<br>Place the other end in row 17 column A",
        "This is the signal wire for Switch 2",
        rect(924, 437, 979, 564),
        rect(410, 519, 975, 566),
        greyout=True,
    ),
    build_step(
        "Place one end of the wire in Arduino Pin 2.<br>Place the other end in row 24 column A",
        "This is the signal wire for Switch 1",
        rect(1062, 429, 1115, 590),
        rect(410, 542, 1115, 600),
        greyout=True,
    ),
    build_step(
        "Complete the switch loops to the negative rail.",
        "This wire completes our loop for the switches",
        rect(953, 135, 1046, 411),
        rect(1095, 141, 1174, 406),
        greyout=True,
    ),
]

DRAWER_CONTENT = {

    "project_ten": {
    "title": "🕵️‍♂️ Spy Vault Security Console",
    "tip": "Use multiple inputs and logic conditions to control a secure system.",
    "tabs": {
        "story": {
            "label": "🕶️ Mission",
            "content": """
<h3>Welcome back, Agent Engineer! 🕵️‍♂️💼</h3>

<p>
The Agency needs your help!
</p>

<p>
You are building the high-security lock for the <b>Top Secret Spy Vault</b>.
</p>

<p>
To open the vault:
</p>

<p>
🔑 Two key cards must be activated<br>
⏱️ At the same time!
</p>

<p>
Each switch controls a locking bolt:
</p>

<p>
🔒 Locked = 0<br>
🔓 Unlocked = 1
</p>

<p>
Only when <b>both locks are open</b> will the vault unlock!
</p>

<p>
Can you secure the base? ⚔️🛡️
</p>
"""
        },
        "code": {
            "label": "💻 Code",
            "content": """
<h3>The Security System</h3>

<pre>
// 🔐 Our Security Lock Variables
int LockA = 0; 
int LockB = 0;

void setup() {
  pinMode(2, INPUT_PULLUP);
  pinMode(3, INPUT_PULLUP);
  pinMode(8, OUTPUT);
  Serial.begin(9600);
  Serial.println("--- VAULT SYSTEM ARMED ---");
}

void loop() {
  LockA = digitalRead(2);
  LockB = digitalRead(3);

  if (LockA == 1 && LockB == 1) {
    digitalWrite(8, HIGH);
    Serial.println("🔓 ACCESS GRANTED: Vault Open!");
  } 
  else {
    digitalWrite(8, LOW);
    Serial.println("🔒 ACCESS DENIED: Locks Engaged.");
  }

  delay(500); 
}
</pre>

<p>
This system checks two inputs before allowing access.
</p>
"""
        },
        "logic": {
            "label": "🧩 Logic",
            "content": """
<h3>How the Vault Thinks</h3>

<p>
The system constantly:
</p>

<p>
🔘 Reads Switch A<br>
🔘 Reads Switch B<br>
🤔 Checks if BOTH are active<br>
🚨 Grants or denies access<br>
🔁 Repeats
</p>

<p>
If BOTH are ON → Access Granted 🔓<br>
If ONE or NONE → Access Denied 🔒
</p>
"""
        },
        "translation": {
            "label": "🧬 Translation",
            "content": """
<h3>Spy Logic Breakdown</h3>

<p>
<b>int LockA / LockB</b><br>
Variables that store each lock's state 🔐
</p>

<p>
<b>digitalRead(2 / 3)</b><br>
Reads each switch position 🔘
</p>

<p>
<b>LockA == 1</b><br>
Checks if Lock A is unlocked 🔓
</p>

<p>
<b>&& (AND)</b><br>
Both conditions must be true 🤝<br>
Lock A AND Lock B must be unlocked
</p>

<p>
<b>if (LockA == 1 && LockB == 1)</b><br>
Only then → Open the vault 🚨
</p>

<p>
<b>else</b><br>
Any other case → Stay locked 🔒
</p>

<p>
<b>Key Idea</b><br>
Variables store state.<br>
Logic combines conditions to make decisions.
</p>
"""
        }
    }
    }
}
SKETCH_PRESET = {
    'sketch': """// 🔐 Our Security Lock Variables
int LockA = 0; 
int LockB = 0;

void setup() {
  pinMode(2, INPUT_PULLUP);
  pinMode(3, INPUT_PULLUP);
  pinMode(8, OUTPUT);
  Serial.begin(9600);
  Serial.println("--- VAULT SYSTEM ARMED ---");
}

void loop() {
  LockA = digitalRead(2);
  LockB = digitalRead(3);

  if (LockA == 1 && LockB == 1) {
    digitalWrite(8, HIGH);
    Serial.println("🔓 ACCESS GRANTED: Vault Open!");
  } 
  else {
    digitalWrite(8, LOW);
    Serial.println("🔒 ACCESS DENIED: Locks Engaged.");
  }
  delay(500); 
}""",
    'default_view': 'builder',
    'read_only': True,
    'lock_view': True,
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