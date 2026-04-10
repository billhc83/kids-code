"""
Flask version of contents.py
Images are passed as base64 strings, not rendered HTML.
The block builder service handles the hover zoom rendering.
"""
import base64
from pathlib import Path
from utils.image_utils import img_to_b64  # Assuming a new utility file

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
                "content": "<p>1. Use println to print \"Likeness = \" for the user to see..<br>This text has to match exactly so if you need to use copy and paste to make sure it is correct.</p><p>2. Print the value of <b>likeness</b> next to the label.<br>We need to print <b>likeness</b> to tell the user how many letters they had correct.  For example if the user guessed \"SPARE\" likeness would equal 4 so we want to print Likeness = likeness which would show the user Likeness = 4</p><p>3. Make sure this happens for every guess so the trainee can learn from the feedback.<br><br>Tip:  We use println if we want to print something on a new line.  We use print if we want to print something else on the same line</p>"
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

"backup_alarm": [

{
    "title": "Step 1 — System Memory 📦",
    "tip": "Set up your system’s memory so it knows what everything is.",
    "tabs": {
        "explain": {
            "label": "📖 What & Why",
            "content": "<p>Before your backup alarm can work, it needs to know what parts it is using. We store this information in <b>variables</b>.</p><br><p>Each variable acts like a label for a part of your system:</p><ul><li>📡 <b>trigPin</b> → sends out a signal to measure distance<br><br></li><li>👂 <b>echoPin</b> → listens for the signal bouncing back<br><br></li><li>🔊 <b>buzzerPin</b> → makes sound when objects are close<br><br></li><li>💡 <b>greenLED</b>, <b>yellowLED</b>, <b>redLED</b> → show safe, warning, and danger zones<br><br></li><li>⏱ <b>duration</b> → stores how long the signal takes to return<br><br></li><li>📏 <b>distance</b> → stores how far away an object is</li></ul><p>Without these, your system wouldn’t know what anything is!</p>"
        },
        "howto": {
            "label": "🔧 How To",
            "content": "<p>1. Create containers (variables) for each part of your system.</p><p>2. Give each one the exact name shown in the instructions.</p><p>3. Assign each pin a number so your board knows where things are connected.</p><p>4. Create containers for <b>duration</b> and <b>distance</b> to store sensor data.</p><p>These variables will be used in almost every step, so they must be correct!</p>"
        },
        "logic": {
            "label": "🧠 Logic",
            "content": "<p>Think of this like labeling wires in a car. If everything is labeled clearly, the system can react quickly and correctly. If not, things get confusing fast!</p>"
        }
    }
},

{
    "title": "Step 2 — Activate the System ⚙️",
    "tip": "Tell your system what each part is supposed to do.",
    "tabs": {
        "explain": {
            "label": "📖 What & Why",
            "content": "<p>Now that your system knows the parts, you need to tell it how each one behaves using <b>pin modes</b>.</p><br><p>There are two main types:</p><ul><li>📤 <b>OUTPUT</b> → sends signals (LEDs, buzzer, trigger pin)<br><br></li><li>📥 <b>INPUT</b> → receives signals (echo pin)</li></ul><p>This step prepares your system so it can send and receive information properly.</p>"
        },
        "howto": {
            "label": "🔧 How To",
            "content": "<p>1. Go into the <b>setup</b> section.</p><p>2. Set each pin to the correct mode:</p><ul><li>Trigger, buzzer, and LEDs → OUTPUT</li><li>Echo pin → INPUT</li></ul><p>3. Turn on communication with the screen so you can see information later.</p><p>This step only runs once when the system starts.</p>"
        },
        "logic": {
            "label": "🧠 Logic",
            "content": "<p>Imagine plugging in devices at home. Some devices send signals (like a remote), while others receive them (like a TV). If you mix them up, nothing works correctly!</p>"
        }
    }
},

{
    "title": "Step 3 — Prepare the Sensor 📡",
    "tip": "Reset the sensor before sending a signal.",
    "tabs": {
        "explain": {
            "label": "📖 What & Why",
            "content": "<p>The ultrasonic sensor works by sending out a sound wave and listening for it to return.</p><br><p>Before sending a new signal, we must make sure the trigger is turned <b>OFF</b> first.</p><p>This clears any leftover signal so the next reading is accurate.</p><br><p>We also wait a very tiny amount of time to let the sensor settle.</p>"
        },
        "howto": {
            "label": "🔧 How To",
            "content": "<p>1. Inside the loop, turn the trigger pin OFF.</p><p>2. Add a very short delay so the sensor resets properly.</p><p>This prepares the sensor for a clean measurement.</p>"
        },
        "logic": {
            "label": "🧠 Logic",
            "content": "<p>Think of this like taking a deep breath before speaking. You reset first, then send a clear signal. Without resetting, your readings can get messy and unreliable.</p>"
        }
    }
},

{
    "title": "Step 4 — Send the Signal 🚀",
    "tip": "Send out a quick signal to measure distance.",
    "tabs": {
        "explain": {
            "label": "📖 What & Why",
            "content": "<p>Now it's time for your sensor to send out a signal!</p><br><p>The ultrasonic sensor works by sending a tiny burst of sound that travels through the air.</p><p>To do this, we briefly turn the <b>trigger pin ON</b>, then turn it OFF again.</p><br><p>This creates a short pulse — like a quick clap — that starts the measurement.</p><p>The timing of this pulse is very important, so we only leave it on for a very tiny amount of time.</p>"
        },
        "howto": {
            "label": "🔧 How To",
            "content": "<p>1. Turn the trigger pin ON.</p><p>2. Wait a very short time (just enough for the signal to send).</p><p>3. Turn the trigger pin OFF again.</p><p>This creates the pulse that tells the sensor to begin measuring distance.</p>"
        },
        "logic": {
            "label": "🧠 Logic",
            "content": "<p>Think of this like shouting \"Hello!\" into a canyon. The shout is quick, but it travels far. If you shout too long or too short, the echo won’t be clear.</p>"
        }
    }
},

{
    "title": "Step 5 — Listen for the Echo 👂",
    "tip": "Measure how long it takes for the signal to return.",
    "tabs": {
        "explain": {
            "label": "📖 What & Why",
            "content": "<p>After sending the signal, your sensor listens for it to come back.</p><br><p>The sound wave travels forward, hits an object, and bounces back to the sensor.</p><p>We measure how long this takes using a special function.</p><br><p>This time is stored in a variable called <b>duration</b>.</p><p>The longer the time, the farther away the object is.</p>"
        },
        "howto": {
            "label": "🔧 How To",
            "content": "<p>1. Use the echo pin to listen for the returning signal.</p><p>2. Store the time it takes in the <b>duration</b> variable.</p><p>This value will be used to calculate distance in the next step.</p>"
        },
        "logic": {
            "label": "🧠 Logic",
            "content": "<p>This is like yelling and waiting for your echo. If it comes back quickly, the wall is close. If it takes longer, the wall is farther away.</p>"
        }
    }
},

{
    "title": "Step 6 — Calculate Distance 📏",
    "tip": "Turn time into a real-world distance.",
    "tabs": {
        "explain": {
            "label": "📖 What & Why",
            "content": "<p>Now we turn the time measurement into distance!</p><br><p>Sound travels at a known speed through the air. By using this speed, we can convert the time into how far away something is.</p><br><p>We divide the result by 2 because the sound travels to the object <b>and back</b>.</p><p>This final value is stored in the <b>distance</b> variable.</p>"
        },
        "howto": {
            "label": "🔧 How To",
            "content": "<p>1. Take the duration value you measured.</p><p>2. Convert it into distance using the correct formula.</p><p>3. Store the result in the <b>distance</b> variable.</p><p>This gives your system real-world information it can react to.</p>"
        },
        "logic": {
            "label": "🧠 Logic",
            "content": "<p>Imagine timing how long it takes for a ball to bounce off a wall and come back. If you know how fast it moves, you can figure out how far away the wall is.</p>"
        }
    }
},

{
    "title": "Step 7 — Safe Zone Check 🟢",
    "tip": "Decide when everything is safe.",
    "tabs": {
        "explain": {
            "label": "📖 What & Why",
            "content": "<p>Your system now knows the distance — but it needs to decide what that means.</p><br><p>We use an <b>if statement</b> to check conditions.</p><p>This lets the system ask a question like:</p><p><b>“Is the object far enough away to be safe?”</b></p><br><p>If the answer is YES, the system will enter the safe zone.</p><p>This is the first decision your system makes.</p>"
        },
        "howto": {
            "label": "🔧 How To",
            "content": "<p>1. Create an <b>if</b> condition.</p><p>2. Check if the distance is greater than the safe value.</p><p>3. Open the block where your safe actions will go.</p><p>This tells your system when everything is safe.</p>"
        },
        "logic": {
            "label": "🧠 Logic",
            "content": "<p>This is like checking your surroundings before stepping back. If nothing is close, you’re safe to move.</p>"
        }
    }
},

{
    "title": "Step 8 — Safe Zone Response 🟢",
    "tip": "Show that everything is safe.",
    "tabs": {
        "explain": {
            "label": "📖 What & Why",
            "content": "<p>When the system detects a safe distance, it should clearly show that everything is okay.</p><br><p>We do this by:</p><ul><li>💡 Turning the <b>green LED ON</b></li><li>⚫ Turning the other LEDs OFF</li><li>🔇 Keeping the buzzer silent</li></ul><p>This gives clear feedback to the driver: no danger detected.</p>"
        },
        "howto": {
            "label": "🔧 How To",
            "content": "<p>1. Turn the buzzer OFF so there is no sound.</p><p>2. Turn the green LED ON.</p><p>3. Turn the yellow and red LEDs OFF.</p><p>Make sure every light is controlled so there is no confusion.</p>"
        },
        "logic": {
            "label": "🧠 Logic",
            "content": "<p>Think of a traffic light. Green means go — everything is clear. No sound, no warning, just safe movement.</p>"
        }
    }
},

{
    "title": "Step 9 — Warning Zone Check 🟡",
    "tip": "Detect when things are getting closer.",
    "tabs": {
        "explain": {
            "label": "📖 What & Why",
            "content": "<p>Not everything is either safe or dangerous — sometimes you're getting close.</p><br><p>We use an <b>else if</b> statement to check a second condition.</p><p>This only runs if the first condition (safe zone) was NOT true.</p><br><p>Now the system asks:</p><p><b>“Is the object getting close, but not too close?”</b></p><p>This creates a middle warning zone.</p>"
        },
        "howto": {
            "label": "🔧 How To",
            "content": "<p>1. Add an <b>else if</b> after your first condition.</p><p>2. Check if the distance is greater than the warning threshold.</p><p>3. Open the block where your warning actions will go.</p><p>This creates a second level of awareness in your system.</p>"
        },
        "logic": {
            "label": "🧠 Logic",
            "content": "<p>This is like a yellow traffic light. You’re not in danger yet, but you need to pay attention and slow down.</p>"
        }
    }
},

{
    "title": "Step 10 — Warning Response 🟡",
    "tip": "Alert the driver with a repeating beep.",
    "tabs": {
        "explain": {
            "label": "📖 What & Why",
            "content": "<p>When an object is getting close, the system should warn the driver — but not panic yet.</p><br><p>We do this using a <b>buzzer</b> that turns ON and OFF repeatedly.</p><p>This creates a beeping sound.</p><br><p>The pattern works like this:</p><ul><li>🔊 Turn sound ON</li><li>⏳ Wait</li><li>🔇 Turn sound OFF</li><li>⏳ Wait again</li></ul><p>This repeating pattern creates the familiar \"beep... beep...\" warning sound.</p><br><p>We also turn on the yellow LED to show caution.</p>"
        },
        "howto": {
            "label": "🔧 How To",
            "content": "<p>1. Turn the buzzer ON using a tone.</p><p>2. Wait for a short amount of time.</p><p>3. Turn the buzzer OFF.</p><p>4. Wait again.</p><p>5. Set the LEDs so only the yellow light is ON.</p><p>This creates a repeating warning signal.</p>"
        },
        "logic": {
            "label": "🧠 Logic",
            "content": "<p>This is like a car slowly getting closer to something. The system says: \"Be careful… something is getting close.\" The repeating sound grabs attention without causing panic.</p>"
        }
    }
},

{
    "title": "Step 11 — Danger Zone 🚨",
    "tip": "Trigger a constant alert when too close.",
    "tabs": {
        "explain": {
            "label": "📖 What & Why",
            "content": "<p>If the object is very close, the system must react immediately.</p><br><p>This is the <b>danger zone</b>.</p><p>Instead of beeping, the buzzer stays ON continuously to create urgency.</p><br><p>We also turn on the red LED to clearly show danger.</p><p>This tells the driver: <b>STOP NOW!</b></p>"
        },
        "howto": {
            "label": "🔧 How To",
            "content": "<p>1. Add an <b>else</b> block for when no other conditions are true.</p><p>2. Turn the buzzer ON and keep it ON.</p><p>3. Turn the red LED ON.</p><p>4. Turn the other LEDs OFF.</p><p>This creates a strong, clear danger signal.</p>"
        },
        "logic": {
            "label": "🧠 Logic",
            "content": "<p>This is like a loud alarm going off when you're about to hit something. No more warnings — it’s time to stop immediately!</p>"
        }
    }
},

{
    "title": "Step 12 — System Loop 🔁",
    "tip": "Keep the system running smoothly.",
    "tabs": {
        "explain": {
            "label": "📖 What & Why",
            "content": "<p>Your system runs over and over again inside a loop.</p><br><p>Without a small pause, it would run too fast and could cause unstable readings.</p><p>We add a short delay to give the system time to reset before the next measurement.</p><br><p>This makes the sensor more stable and reliable.</p>"
        },
        "howto": {
            "label": "🔧 How To",
            "content": "<p>1. At the end of the loop, add a small delay.</p><p>2. This delay should be short — just enough to stabilize the system.</p><p>3. The loop will then repeat automatically.</p><p>This keeps your system running smoothly.</p>"
        },
        "logic": {
            "label": "🧠 Logic",
            "content": "<p>Think of this like blinking your eyes. You don’t constantly stare without pause — small breaks help everything stay clear and stable.</p>"
        }
    }
},
{
    "title": "Step 13 — Mission Complete 🎉",
    "tip": "Your backup alarm system is fully operational!",
    "tabs": {
        "explain": {
            "label": "📖 What You Built",
            "content": "<p>🚗 Congratulations, Engineer!</p><br><p>You successfully designed and built a <b>smart backup alarm system</b> — just like the ones used in real cars.</p><br><p>Your system can:</p><ul><li>📡 Measure distance using an ultrasonic sensor</li><li>🧠 Make decisions based on that distance</li><li>💡 Show safe, warning, and danger zones using LEDs</li><li>🔊 Alert the driver using sound patterns</li></ul><p>You didn’t just write code — you built a real-world system that senses, thinks, and reacts.</p>"
        },
        "howto": {
            "label": "🔧 Try This Next",
            "content": "<p>Now that your system works, try improving it!</p><br><p>Here are some ideas:</p><ul><li>⚡ Change the distance values to make the system more or less sensitive</li><li>🔊 Make the beeping faster as objects get closer</li><li>🌈 Add more LEDs for smoother distance levels</li><li>📺 Display the distance on a screen</li><li>🎮 Turn it into a game or challenge system</li></ul><p>Experimenting is how real engineers improve their designs!</p>"
        },
        "logic": {
            "label": "🧠 What You Learned",
            "content": "<p>This project brought together everything you’ve been learning:</p><ul><li>📦 Variables to store important information</li><li>⚙️ Setup to prepare your system</li><li>📡 Sensors to collect real-world data</li><li>🧠 Logic to make decisions (if / else if / else)</li><li>💡 Outputs to respond with lights and sound</li><li>🔁 Loops to keep everything running continuously</li></ul><br><p>This is how real systems work — input → thinking → output.</p><p>You are now thinking like an engineer. 🚀</p>"
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