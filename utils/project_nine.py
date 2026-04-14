

from utils.step_builder import build_step, intro_step, rect, circle

META = {
    'title': 'Project 9: The Universal Power Slot',
    'circuit_image': 'static/graphics/project_one_circuit.png',
    'banner_image': None,
}

STEPS = [
    intro_step(
        "Let's build our ninth project",
        "Press the next button for a step by step guide",
    ),
    
    build_step(
        "Place the LED long leg in row 12, column E.<br>"
        "Place the LED short leg in row 11, column E",
        "The long leg is positive — it's called the anode!",
        rect(708, 175, 899, 331),
        greyout=True,
    ),

    build_step(
        "Place one leg of the 220 ohm resistor in row 11, column D.<br>"
        "Place the second leg of the resistor in row 7, column D",
        "The resistor slows down the electricity.",
        rect(693, 324, 825, 363),
        circle(492, 154, radius=60),
        greyout=True,
    ),

    build_step(
        "Place one end of the wire in the Arduino GND Pin.<br>"
        "Place the other end in row 7, column E",
        "Wires are like roads for electricity.",
        rect(375, 231, 740, 339),
        greyout=True,
    ),

    build_step(
        "Place one end of the wire in the Arduino Pin 8.<br>"
        "Place the other end in row 12, column A",
        "This wire powers the LED when energy is available.",
        rect(346, 350, 844, 453),
        greyout=True,
    ),
]

DRAWER_CONTENT = {

    "project_nine": {
    "title": "🛠️ Universal Power Slot",
    "tip": "Learn how variables store information and control what your system does.",
    "tabs": {
        "story": {
            "label": "👷 Mission",
            "content": """
<h3>Welcome, Senior Systems Engineer! 🛠️</h3>

<p>
You’ve been promoted 👷‍♂️👷‍♀️
</p>

<p>
Today, you're working in the <b>Design Lab</b>, building a machine powered by different energy sources.
</p>

<p>
But there's a problem...
</p>

<p>
Not every item can power the system!
</p>

<p>
Available "power sources":
</p>

<p>
🥒⚡ Zappy-Zucchini Juice<br>
🐿️💥 Sparky-Squirrel Static<br>
🥛🌙 Mega-Glow Lightening-Milk<br>
🥪 The Crusty Club Sandwich
</p>

<p>
Your job:
</p>

<p>
🔌 Insert a power source into the slot<br>
⚡ See how much energy it provides<br>
💡 Decide if the system should turn ON
</p>

<p>
What happens if you try to power a machine… with a sandwich? 🤔
</p>
"""
        },
        "code": {
            "label": "💻 Code",
            "content": """
<h3>The Power System</h3>

<pre>
String powerSlot = "Crusty Club Sandwich"; 

int currentEnergy = 0;

void setup() {
  pinMode(8, OUTPUT);
  Serial.begin(9600);
}

void loop() {

  if (powerSlot == "Mega-Glow Lightening-Milk") {
    currentEnergy = 100;
  } 
  else if (powerSlot == "Sparky-Squirrel Static") {
    currentEnergy = 50;
  }
  else if (powerSlot == "Zappy-Zucchini Juice") {
    currentEnergy = 10;
  }
  else {
    currentEnergy = 0;
  }

  if (currentEnergy > 0) {
    digitalWrite(8, HIGH);
  } else {
    digitalWrite(8, LOW);
  }

  delay(3000);
}
</pre>

<p>
This system checks what power source is inserted and reacts accordingly.
</p>
"""
        },
        "logic": {
            "label": "🧩 Logic",
            "content": """
<h3>How the System Thinks</h3>

<p>
The machine follows this process:
</p>

<p>
📦 Read what is in the power slot<br>
🔍 Compare it to known power sources<br>
⚡ Assign energy value<br>
💡 Turn system ON or OFF<br>
🔁 Repeat
</p>

<p>
If valid power → System ON 💡<br>
If invalid → System OFF 📴
</p>
"""
        },
        "translation": {
            "label": "🧠 Translation",
            "content": """
<h3>Engineering Breakdown</h3>

<p>
<b>String powerSlot</b><br>
This is a variable — it stores text 📝<br>
It represents what is plugged into the system.
</p>

<p>
<b>int currentEnergy</b><br>
Stores how much power is available 🔢
</p>

<p>
<b>if (powerSlot == "...")</b><br>
Checks if the correct power source is inserted 🔍
</p>

<p>
<b>currentEnergy = value</b><br>
Assigns energy based on the match ⚡
</p>

<p>
<b>else</b><br>
If nothing matches → no power 🚫
</p>

<p>
<b>if (currentEnergy &gt; 0)</b><br>
If energy exists → turn system ON 💡
</p>

<p>
<b>Key Idea</b><br>
Variables store information.<br>
Matching values controls behavior.
</p>

<p>
Wrong input → nothing happens 😴
</p>
"""
        }
    }
    }
}
SKETCH_PRESET = {
    'sketch': """String powerSlot = "Crusty Club Sandwich"; 

int currentEnergy = 0;

void setup() {
  pinMode(8, OUTPUT);
  Serial.begin(9600);
}

void loop() {

  if (powerSlot == "Mega-Glow Lightening-Milk") {
    currentEnergy = 100;
  } 
  else if (powerSlot == "Sparky-Squirrel Static") {
    currentEnergy = 50;
  }
  else if (powerSlot == "Zappy-Zucchini Juice") {
    currentEnergy = 10;
  }
  else {
    currentEnergy = 0;
  }

  if (currentEnergy > 0) {
    digitalWrite(8, HIGH);
  } else {
    digitalWrite(8, LOW);
  }

  delay(3000);
}""",
    'default_view': 'editor',
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