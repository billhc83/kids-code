"""
Flask version of contents.py
Images are passed as base64 strings, not rendered HTML.
The block builder service handles the hover zoom rendering.
"""
import base64
from pathlib import Path

def img_to_b64(path):
    data = Path(path).read_bytes()
    b64 = base64.b64encode(data).decode()
    ext = Path(path).suffix.lstrip(".")
    return f"data:image/{ext};base64,{b64}"

# Pre-encode circuit images
engine_circuit_b64 = img_to_b64("static/graphics/project_twelve_circuit.png")
patrol_circuit_b64 = img_to_b64("static/graphics/project_thirteen_circuit.png")

DRAWER_CONTENT = {
    "engine_start": {
        "title": "📘 Engine Start Guide",
        "tip": "Build the rules that control when the engine is allowed to run.",
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
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;engine ON<br><br>
IF switch is OFF (else)<br>
&nbsp;&nbsp;&nbsp;&nbsp;everything OFF<br><br>
Remember: The switch is the boss.
"""
            }
        }
    },

    "codebreaker": [

    {
        "title": "Step 1 — The Variables 📦",
        "tip": "Set up your agent’s memory for the mission.",
        "tabs": {
            "explain": {
                "label": "📖 What & Why",
                "content": "<p>Every agent needs memory for the mission. These memory containers are called variables.</p><br><p>We prepare three key pieces of memory for the code-breaking device:</p><ul><li>🔐 <b>answer</b> → the secret 5-letter code trainees must find. This is text, so it must be in quotes.\"SPARK\"<br><br></li><li>🔢 <b>likeness</b> → how many letters match the secret code. Start at 0 because we haven't had any guesses yet.<br><br></li><li>🚪 <b>solved</b> → has the code has been cracked? Start as false because we haven't had any guesses yet.<br><br></li></ul><p>Without these, the system won’t remember anything the trainee does.</p>"
            },
            "howto": {
                "label": "🔧 How To",
                "content": "<p>1. Create a container called <b>answer</b> for the secret word \"SPARK\". Write the word in quotes because it is text.</p><p>2. Create a container called <b>likeness</b> to count correct letters. Start it at 0.</p><p>3. Create a container called <b>solved</b> to track if the code is cracked. Set it to false at the beginning.</p><p>These are the foundations for your agent’s memory. Make sure you name the containers exactly as above so the system can use them later.</p>"
            },
            "logic": {
                "label": "🧠 Logic",
                "content": "<p>Think of these like secret pockets in an agent’s backpack. Each pocket has a purpose: one stores the code, one counts matches, one knows if the mission is complete. Without them, the agent can’t do the mission.</p>"
            }
        }
    },

    {
        "title": "Step 2 — Serial Begin 💻",
        "tip": "Activate communication with HQ (the screen).",
        "tabs": {
            "explain": {
                "label": "📖 What & Why",
                "content": "<p>Your device needs a way to talk to the trainee. This communication line is opened with <b>Serial.begin(9600)</b>.</p><p>Once open, the system can display the coded message grid the trainee will analyze.</p>"
            },
            "howto": {
                "label": "🔧 How To",
                "content": "<p>1. Go to the setup section.</p><p>2. Turn on the communication line with the correct speed: 9600.</p><p>3. We have provided the cipher code so you don't need to enter it. The cipher include lines that show the letters trainees will analyze, the instructions to guess, and a prompt to enter guesses.</p><p>This lets the trainee see the mission briefing clearly.</p>"
            },
            "logic": {
                "label": "🧠 Logic",
                "content": "<p>Without serialbegin(9600), your agent stays silent.  It won't communicate with the termial without starting the connection. The trainee won’t see anything, even if all the other parts are working perfectly.</p>"
            }
        }
    },

    {
        "title": "Step 3 — Listen for Input ⌨️",
        "tip": "Wait for the trainee to send a guess from HQ.",
        "tabs": {
            "explain": {
                "label": "📖 What & Why",
                "content": "<p>The device must wait until a trainee types a guess. We don’t want to read nothing over and over we only want to read when something is entered..</p><p>Checking if new data is available ensures the system only acts when the trainee is ready.</p>"
            },
            "howto": {
                "label": "🔧 How To",
                "content": "<p>1. We need to create and \"if\" statement.</p><p>2. This means only do this \"if\" the conditions are met.<br><br>In our case we are saying \"if\" serial.available is greater than 0, do somehthing.<br>Serial.available checks to see if there is data waiting.<br>If there was no data waiting Serial.available = 0, because there is nothing there.<br>If there is something there it will be greater than 0, we don't care how much is there we just want to make sure something is there.<br>This opens the door for processing the guess.</p><p>This is like checking a secure mailbox: the agent only looks when a message is inside.</p>"
            },
            "logic": {
                "label": "🧠 Logic",
                "content": "<p>\"if\" statements are part of the decicion making tools in coding.<br>In our system here the program must wait for the trainee’s input to continue the mission.</p>"
            }
        }
    },

    {
        "title": "Step 4 — Read the Guess 📓",
        "tip": "Capture the trainee’s guess and clean it for analysis.",
        "tabs": {
            "explain": {
                "label": "📖 What & Why",
                "content": "<p>Once input is detected, we store it in a variable called <b>guess</b>.</p><br><p>guess.trim() trims any blank spaces that might be at the beinning or end of the guess.<br>We dont want a bunch of blank spaces at the beginning and end of the guesses that will throw off the system.<br></p><ul><li>guess.trim(); - ✂️ Remove extra spaces at the start and end.</li><br>🔠 guess.toUpperCase() converts all letters to uppercase so they match the secret code format.<br><br>We don't want confustion between \"Spark\" and \"spark\" and \"SPARK\"<br><br><li>guess.toUpperCase(); - Convert all the letters in guess to capital letters</li></ul>"
            },
            "howto": {
                "label": "🔧 How To",
                "content": "<p>1. Use the block builder to create a variable called <b>guess</b>.<br>String var - A variable that is a string. Strings are words or text. <br>Numbers can be put into string variables as well, lets look at the difference between a number as a string var, and a number as a int var:<br><li>String var = \"1\"</li><br><li>int var = 1</li><br>You need to put the right type of data into the right kind of variable.</p><p>2. Take the trainees typed input and store it in <b>guess</b>.<br>Serial.read allows us to grab what the user enters.</p><p>3. Remove any extra spaces at the beginning or end.</p><p>4. Convert all letters to uppercase so the system can compare fairly with the secret code.</p>"
            },
            "logic": {
                "label": "🧠 Logic",
                "content": "<p>This step prevents small mistakes like typing ' spark ' or 'Spark' from causing the system to fail. Every input is cleaned before checking.</p>"
            }
        }
    },

    {
        "title": "Step 5 — Reset the Score 🔄",
        "tip": "Prepare the device for a fresh comparison.",
        "tabs": {
            "explain": {
                "label": "📖 What & Why",
                "content": "<p>Before checking the new guess, reset the <b>likeness</b> counter to 0.</p><p>This ensures each guess is measured independently.</p>"
            },
            "howto": {
                "label": "🔧 How To",
                "content": "<p>1. Inside the input check, set <b>likeness</b> to 0 before counting matches.</p><p>We do this each time a new guess is read.  This way we start fresh for every new guess.</p>"
            },
            "logic": {
                "label": "🧠 Logic",
                "content": "<p>If we forget this, old scores would add to new ones, giving incorrect results.</p>"
            }
        }
    },

    {
        "title": "Step 6 — The Letter Checker 🔍",
        "tip": "Compare each letter in the guess with the secret code.",
        "tabs": {
            "explain": {
                "label": "📖 What & Why",
                "content": "<p>We compare the guess to the answer letter by letter.</p><p>If a letter is correct and in the right position, it counts as a match. This increases <b>likeness</b>. We have provided this code so when you are ready, continue to the next step.</p>"
            },
            "howto": {
                "label": "🔧 How To",
                "content": "<p>1. Look at each of the 5 letters in the guess.</p><p>2. Compare each letter with the corresponding letter in the secret code.</p><p>3. Every time a letter matches exactly, add 1 to <b>likeness</b>.</p><p>4. This will give a score from 0 to 5 that shows how close the guess is.</p>"
            },
            "logic": {
                "label": "🧠 Logic",
                "content": "<p>Correct letter AND correct position = point earned. This is the core of the training challenge.</p>"
            }
        }
    },

    {
        "title": "Step 7 — Show the Result 💬",
        "tip": "Report how close the guess was to HQ.",
        "tabs": {
            "explain": {
                "label": "📖 What & Why",
                "content": "<p>After counting matches, we must show the trainee the result.<br>We need to print some information to the terminal to let the know how good or bad their guess was.</p><p>This gives feedback so the trainee can adjust their next guess.</p>"
            },
            "howto": {
                "label": "🔧 How To",
                "content": "<p>1. Print a label like \"Likeness = \".<br>This text has to match exactly so if you need to use copy and paste to make sure it is correct.</p><p>2. Print the value of <b>likeness</b> next to the label.</p><p>3. Make sure this happens for every guess so the trainee can learn from the feedback.<br><br>Tip:  We use println if we want to print something on a new line.  We use print if we want to print something else on the same line</p>"
            },
            "logic": {
                "label": "🧠 Logic",
                "content": "<p>Feedback creates a loop: guess → result → adjust → guess again. This helps the trainee improve their code-breaking skills.</p>"
            }
        }
    },

    {
        "title": "Step 8 — Win or Retry 🏁",
        "tip": "Decide if the trainee has cracked the code.",
        "tabs": {
            "explain": {
                "label": "📖 What & Why",
                "content": "<p>Now the system decides if the guess is correct.</p><p>If <b>likeness</b> equals 5, the code is fully correct. Otherwise, the trainee tries again.</p>"
            },
            "howto": {
                "label": "🔧 How To",
                "content": "<p>1. Check if <b>likeness</b> equals 5.</p><p>2. If yes:</p><ul><li>Show a success message: \"CODE CRACKED! ACCESS GRANTED.\"</li><li>Set <b>solved</b> to True.</li></ul><p>3. If no:</p><ul><li>Prompt the trainee: \"Try again:\"</li></ul><p>This step makes the device behave like a real mission control, giving immediate results for the trainee’s action.</p>"
            },
            "logic": {
                "label": "🧠 Logic",
                "content": "<p>This is the mission’s final checkpoint. The previous steps build up to this decision point.</p>"
            }
        }
    },

    {
        "title": "Step 9 — Mission Complete 🏆",
        "tip": "Your agent’s code-breaking system is operational.",
        "tabs": {
            "explain": {
                "label": "📖 Debrief",
                "content": "<p>🟢 Code cracked. Excellent work, Agent!</p><p>You built a fully operational code-breaking device. It can:</p><ul><li>Receive input</li><li>Store and clean data</li><li>Compare and evaluate guesses</li><li>Report results</li><li>Decide if the mission is complete</li></ul><p>This mirrors real training systems used by agents in the field.</p>"
            },
            "howto": {
                "label": "🧠 What You Built",
                "content": "<p>You didn’t just write code… you built a complete loop:</p><p>⌨️ INPUT → 📓 STORE → 🔍 CHECK → 💬 OUTPUT → 🏁 RESULT</p><p>Every future program will follow this same pattern.</p>"
            },
            "logic": {
                "label": "🕵️ Final Message",
                "content": "<p>Copy your code and run it in the Arduino IDE<br>📡 Incoming transmission…</p><p>Agent, your system is now active and ready for the next trainees.</p><p>They will try to break the code you created. Stay sharp — you may need to improve or outsmart your own design in future missions.</p>"
            }
        }
    }
],


    "patrol_alarm": {
        "title": "📘 Light Bar Control Guide",
        "tip": "Build the flashing pattern that controls the patrol light bar.",
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
<p>Each light flash must use a short pause.<br>
At Night Patrol Academy we use: <b>delay(150)</b><br>
Use this delay after each light turns ON and turns OFF.</p>
<p>Your job is to build the flashing pattern using blocks.</p>
""",
                "image_b64": patrol_circuit_b64
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
    }
}