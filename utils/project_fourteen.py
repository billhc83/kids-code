
from utils.step_builder import build_step, intro_step, rect, circle, line

META = {
    'title': 'Project 14: Codebreaker',
    'circuit_image': None,
    'banner_image': 'project_fourteen_banner.png',
}

STEPS = None

DRAWER_CONTENT = {

 "project_fourteen": [

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
}

SKETCH_PRESET = {   
    'sketch': """
//>> Step 1 - The Variables | guided
//?? Declare the secret word
String answer = "SPARK";
//?? Declare the score tracker
int likeness = 0;
//?? Declare the solved flag
bool solved = false;

void setup() {
}
void loop() {
}

//>> Step 2 - Serial Begin | guided
void setup() {
  //?? Start serial communication
  Serial.begin(9600);
  //## Serial.println("================================");
  //## Serial.println("     C O D E  B R E A K E R    ");
  //## Serial.println("================================");
  //## Serial.println("Find the hidden 5-letter word.");
  //## Serial.println("");
  //## Serial.println("X K Q S P A R K M Z");
  //## Serial.println("B R T F L A M E Q X");
  //## Serial.println("P Q S P A R K T Z R");
  //## Serial.println("W Z X B R A N D T P");
  //## Serial.println("S P A R K X Q Z B M");
  //## Serial.println("T R X N G L O W K B");
  //## Serial.println("Q Z B S P A R K X T");
  //## Serial.println("M X T R B L A Z E P");
  //## Serial.println("B T Z X Q M R N V K");
  //## Serial.println("P N V Q Z B X T M R");
  //## Serial.println("");
  //## Serial.println("Enter your guess:");
}
void loop() {
}

//>> Step 3 - Listen for Input | guided
void setup() {
}
void loop() {
  //?? Listen for player input
  if (Serial.available() > 0) {
  }
}

//>> Step 4 - Read the Guess | guided
void setup() {
}
void loop() {
  //## if (Serial.available() > 0) {
  //?? Read the player's guess
  String guess = Serial.readString(); // includes .trim() and .toUpperCase()
  //##   guess.trim();
  //##   guess.toUpperCase();
  //## }
}

//>> Step 5 - Reset the Score | guided
void loop() {
  //## if (Serial.available() > 0) {
  //##   String guess = Serial.readString();
  //##   guess.trim();
  //##   guess.toUpperCase();
  //?? Reset the score before counting
  likeness = 0;
  //## }
}

//>> Step 6 - The Letter Checker | free
void loop() {
  //## if (Serial.available() > 0) {
  //##   String guess = Serial.readString();
  //##   guess.trim();
  //##   guess.toUpperCase();
  //##   likeness = 0;
  //##   for (int i = 0; i < 5; i++) { if (guess[i] == answer[i]) { likeness++; } }
  //## }
}

//>> Step 7 - Print the Result | guided
void loop() {
  //## if (Serial.available() > 0) {
  //##   String guess = Serial.readString();
  //##   guess.trim();
  //##   guess.toUpperCase();
  //##   likeness = 0;
  //##   for (int i = 0; i < 5; i++) { if (guess[i] == answer[i]) { likeness++; } }
  //?? Print the score label
  Serial.println("Likeness = ");
  //?? Print the score value
  Serial.print(likeness);
  //## }
}

//>> Step 8 - Win or Try Again | guided
void loop() {
  //## if (Serial.available() > 0) {
  //##   String guess = Serial.readString();
  //##   guess.trim();
  //##   guess.toUpperCase();
  //##   likeness = 0;
  //##   for (int i = 0; i < 5; i++) { if (guess[i] == answer[i]) { likeness++; } }
  //##   Serial.print("Likeness = ");
  //##   Serial.println(likeness);
  //?? Print the win message
  if (likeness == 5) {
    //?? Show success
    Serial.println("CODE CRACKED! ACCESS GRANTED.");
    //?? Unlock the game
    solved = true;
  } else {
    //?? Prompt to retry
    Serial.println("Try again:");
  }
  //## }
}

//>> Step 9 - Code Cracker Complete | guided
void loop() {
  //## if (Serial.available() > 0) {
  //##   String guess = Serial.readString();
  //##   guess.trim();
  //##   guess.toUpperCase();
  //##   likeness = 0;
  //##   for (int i = 0; i < 5; i++) { if (guess[i] == answer[i]) { likeness++; } }
  //##   Serial.print("Likeness = ");
  //##   Serial.println(likeness);
  //##   if (likeness == 5) {
  //##     Serial.println("CODE CRACKED! ACCESS GRANTED.");
  //##     solved = true;
  //##   } else {
  //##     Serial.println("Try again:");
  //##   }
  //## }
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