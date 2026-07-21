
from utils.step_builder import build_step, intro_step, rect, circle, line
from utils.affiliate_kits import BASIC_KITS

META = {
    'title': 'Project 13: The Reaction Timer',
    'circuit_image': 'static/graphics/reaction_timer_circuit.png',
    'banner_image': 'project_thirteen_banner.png',
    'required_kits': BASIC_KITS,
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

CIRCUIT_SPEC = {
    "meta": {
        "title": "The Reaction Timer",
        "difficulty": "beginner",
    },
    "components": [
        {"id": "BTN", "type": "BUTTON", "properties": {}},
    ],
    "connections": [
        {"from": "arduino.D2", "to": "BTN.TL"},
        {"from": "BTN.BR", "to": "arduino.GND"},
    ],
}

from utils.circuit_engine import generate_circuit

reaction_timer_circuit_definition = generate_circuit(
    CIRCUIT_SPEC["meta"], CIRCUIT_SPEC["components"], CIRCUIT_SPEC["connections"]
)

# age_group: 11-12
DRAWER_CONTENT = {
  "project_thirteen": {
    "steps": [
      {
        "title": "Step 1 — Set Up the Lab's Memory 📦",
        "tip": "Create two memory slots your timer will need: one for the start time, one for the result.",
        "tabs": {
          "explain": {
            "label": "📖 What & Why",
            "content": """
<p>Every stopwatch needs somewhere to keep track of what it is doing before it can time anything at all. Right now your Reaction Lab has the Timer Button wired in, but your program has no place to remember the moment someone pressed it, and no place to hold the final answer once the reaction time is worked out.</p>
<p>This step builds two memory boxes for your program to use. Think of them like two small boxes with labels taped on the front. The first box is labeled "when it started." The second box is labeled "the answer." Both boxes start out empty, so you will fill them with the number zero for now.</p>
<p>If you skipped this step, your program would have no boxes to put anything into later on. It could not remember when the timer started, and it would have nothing new to show on the screen when you pressed the button a second time.</p>
<p>Next, you will turn the Timer Button on and open the connection to your computer screen, so your Reaction Lab can finally start talking to you.</p>
""",
            "circuit_definition": reaction_timer_circuit_definition,
          },
          "howto": {
            "label": "🔧 How To",
            "content": """
<p>Your Reaction Lab needs two places to keep track of time, so the first thing to build here is a pair of memory boxes.</p>
<p>The first box remembers the exact moment the timer starts. You'll place a memory box built for very large numbers, since a running clock can climb into the millions before long. Give it the name <code>startTime</code>, and start it at <b>0</b>, since no round has begun yet.</p>
<p>The second box holds the finished reaction time once it's worked out. It uses that same large-number box. Name this one <code>time</code>, and start it at <b>0</b> too, just like an empty scoreboard before a game begins.</p>
<p>You'll notice a third box already sitting above these two, holding the number 2. That one is already built for you. It simply remembers which pin your Timer Button is wired to, so the rest of your program can call it "button" instead of having to remember the number 2 every time.</p>
""",
          },
          "logic": {
            "label": "🧠 Logic",
            "content": """
<p>Think of a scientist's lab notebook with two blank labels already printed on the page. One says "Start Time," and the other says "The Answer." Nothing is written on either line yet, but the notebook is ready the moment an experiment begins.</p>
<p>Your two memory boxes work exactly the same way. They are empty right now, but they are ready to be filled the instant your timer springs into action.</p>
""",
          },
        }
      },
      {
        "title": "Step 2 — Wire the Button & Open Comms 📡",
        "tip": "Tell the Arduino how to read the button, then open the line to your computer.",
        "tabs": {
          "explain": {
            "label": "📖 What & Why",
            "content": """
<p>Your Reaction Lab now has two memory boxes ready to use, but the Arduino still cannot hear the Timer Button, and it has no way to show you anything on your screen yet.</p>
<p>This step happens once, the very moment your Arduino turns on. It tells the Arduino to listen to the Timer Button, and it turns on the connection to your computer screen, called the Serial Monitor. That screen is where every reaction time will show up later.</p>
<p>Without this step, pressing the button would do nothing at all, even if the rest of your program were perfect. The Arduino simply would not be listening yet, and it would have no screen to talk to even if it were.</p>
<p>Next, you will press the button for the very first time, and prove that your Arduino really is paying attention.</p>
""",
          },
          "howto": {
            "label": "🔧 How To",
            "content": """
<p>A pin can only do one job at a time for the Arduino: either it listens for a signal coming in, or it sends a signal out. Right now, the Arduino has no idea which job the Timer Button's pin is supposed to do, so it can't hear anything yet.</p>
<p>This step tells the Arduino that the Timer Button's pin should listen, not speak. You'll set the pin's mode to INPUT_PULLUP. Your Timer Button is wired straight to the Arduino, with nothing extra there to keep its signal calm when it isn't being pressed. INPUT_PULLUP tells the Arduino to quietly hold that signal steady all by itself, so the button only causes a change the moment you actually press it. The one thing to remember: because of this mode, a real press will actually show up as LOW instead of HIGH, the opposite of what you might expect.</p>
<p>The line below it, <code>Serial.begin(9600)</code>, is already set up for you. It's a standard line that opens the connection to your computer screen at a fixed speed, the same in almost every Arduino project that prints anything.</p>
""",
          },
          "logic": {
            "label": "🧠 Logic",
            "content": """
<p>Think of a mission control room before a launch. Someone has to flip the switch that turns on the radio channel before anyone can hear "all systems go" from the capsule.</p>
<p>This step does the same job for your Reaction Lab. It flips the switches so the button can be heard and the results can be seen, before any real countdown begins.</p>
""",
          },
        }
      },
      {
        "title": "Step 3 — Prove the Signal Works 📶",
        "tip": "Reward-first: print something every single press, no rules yet, just proof it works.",
        "tabs": {
          "explain": {
            "label": "📖 What & Why",
            "content": """
<p>Before you teach your timer any real rules, it is worth proving that the button and the screen actually work together. This is exactly what real scientists do before running an experiment. They test that their tools work before trusting any of the readings.</p>
<p>This step makes your program print a number to the screen every single time you press the Timer Button. There are no rules yet, and no memory of earlier presses. It is simply proof that a press really does reach your screen.</p>
<p>Starting this way matters. If a wire were loose, or a part were wired to the wrong pin, you would want to find that out right now, before building anything more complicated on top of it.</p>
<p>Next, you will start teaching your timer to actually remember the moment it began, and you will watch this simple number turn into something real.</p>
<p>🎮 <b>Try It:</b> Open the sim tab and press the Timer Button a few times. A number appears on the screen every single time. That number only tells you how long the Arduino has been turned on, not a real reaction time yet, but it proves your button and your screen are both working.</p>
""",
          },
          "howto": {
            "label": "🔧 How To",
            "content": """
<p>An "if" check only runs the things inside it when a specific question is true. Here, "if" is asking one exact question: is the Timer Button being pressed down right at this instant?</p>
<p>You need that question answered first, because everything else in this step should only happen at the exact moment of a press, not constantly while the Arduino sits there running. You'll place a check comparing the button's reading to LOW, since you learned last step that INPUT_PULLUP flips things around: a real press actually reads as LOW, not HIGH.</p>
<p>Once that question is true, two more things need to happen so you can actually see proof the press worked. First, your program needs to grab a snapshot of the current moment: place a line that sets your <code>time</code> memory box using millis(), a built-in tool that tells you how many milliseconds have passed since the Arduino turned on. Then it needs to actually show you that number, or the whole test would prove nothing: place a line that prints <code>time</code> using "println" mode, which prints the number and then starts a new line, so the next one appears underneath it instead of running together.</p>
<p>The <code>delay(300)</code> sitting underneath all of this is already built for you. It's a short pause after every press, so one quick tap of the button doesn't accidentally get counted as several presses in a row.</p>
""",
          },
          "logic": {
            "label": "🧠 Logic",
            "content": """
<p>Think of testing a walkie-talkie by just pressing "talk" and saying "testing, testing." You are not having a real conversation yet. You are only proving the signal gets through at all.</p>
<p>That is this whole step. Press the button, see a number appear, and know the connection between your hand and your screen is solid.</p>
""",
          },
          "sim": {
            "label": "🎮 Try It",
            "type": "sim",
            "sim_config": {
              "mode": "interpreted",
              "components": [
                {"type": "button", "id": "btn1", "pin": 2, "label": "Timer Button"},
                {"type": "console", "id": "console1", "label": "Serial Monitor"},
              ]
            }
          }
        }
      },
      {
        "title": "Step 4 — Teach It to Remember 🧠",
        "tip": "Add a memory switch for whether the timer is running yet. There's no second half of the logic yet, so printing stops completely.",
        "tabs": {
          "explain": {
            "label": "📖 What & Why",
            "content": """
<p>Your button and your screen have both proven that they work, but your timer still cannot remember anything. Every press only shows how long the Arduino has been turned on, which is not a real reaction time at all. A real timer needs to remember the moment you first pressed the button, so it can measure how long it takes until you press it again.</p>
<p>This step gives your program a way to remember whether the timer is already running. Think of it like a small flag that starts down and gets raised the moment you press the button. The same moment the flag goes up, your program also remembers exactly when that happened.</p>
<p>Here is the important part, and it is done on purpose. This step only teaches your timer what to do the first time you press the button. It does not yet know what to do the second time. So instead of showing a number like the last step did, pressing the button now shows nothing at all.</p>
<p>Next, you will teach your timer what to do on that second press, and that is when your real reaction time finally appears.</p>
<p>🎮 <b>Try It:</b> Open the sim tab and press the Timer Button. Nothing appears on the screen. Press it again, and again, and still nothing shows up, no matter how many times you press it. That is a big change from the last step, where every single press showed a number. Do not worry, nothing is broken. Your timer is quietly remembering that it has started, it just has not been taught how to react to a second press yet.</p>
""",
          },
          "howto": {
            "label": "🔧 How To",
            "content": """
<p>An "if" check only runs the things inside it when a specific question is true. Ask it something true, and everything inside happens. Ask it something false, and everything inside gets skipped completely, as if it weren't there at all.</p>
<p>Your reaction timer needs exactly this kind of check right now, because it has to treat two different moments completely differently. The very first press of a round should start the clock. Any press after that, until the round finishes, should not start the clock all over again. The only way your program can tell these two moments apart is by remembering whether a round is already underway, which is exactly why you built the <code>running</code> flag in this step.</p>
<p>So you'll place a check that asks: is <code>running</code> still equal to 0? In other words, is this genuinely the first press since the flag was last reset? This check goes right inside the button-press check from Step 3, so it only ever gets asked at the moment of a press, not constantly.</p>
<p>If the answer is yes, meaning no round has started yet, two things need to happen right then. Your program needs to remember exactly what moment it is right now, so place a line that sets <code>startTime</code> using millis(), the same time-reading tool you used back in Step 3. And your program needs to raise the flag, so the next press gets treated differently. Place a line that sets <code>running</code> to 1.</p>
<p>If the answer is no, meaning a round is already underway, neither of those two lines runs this time, because a round is already timing and shouldn't be restarted. What should happen instead on that second press is exactly what the next step teaches.</p>
<p>The outer button check and the <code>delay(300)</code> pause both carry over unchanged from Step 3. You are not rebuilding them. You are only adding this new check inside.</p>
""",
          },
          "logic": {
            "label": "🧠 Logic",
            "content": """
<p>Think of a stopwatch with a single start button that has no stop button wired in yet. Pressing it quietly starts the internal clock, but nothing on the display changes, because nobody has told it what "stop" means.</p>
<p>Your timer is in that exact spot right now. It is secretly keeping time. It just cannot tell you about it yet.</p>
""",
          },
          "sim": {
            "label": "🎮 Try It",
            "type": "sim",
            "sim_config": {
              "mode": "interpreted",
              "components": [
                {"type": "button", "id": "btn1", "pin": 2, "label": "Timer Button"},
                {"type": "console", "id": "console1", "label": "Serial Monitor"},
              ]
            }
          }
        }
      },
      {
        "title": "Step 5 — Clock the Reaction ⏱️",
        "tip": "The big reveal: teach the second press to calculate and print the real reaction time.",
        "tabs": {
          "explain": {
            "label": "📖 What & Why",
            "content": """
<p>This is the step where your Reaction Lab finally comes together. Right now, the first press starts your timer quietly in the background, and every press after that does nothing at all. You built it that way on purpose, so you could focus on one small piece at a time.</p>
<p>This step teaches your timer what to do once it is already running. It works out how much time has passed since the first press, shows that real reaction time on your screen, and then lowers the flag from the last step, so the very next press can start a brand new round.</p>
<p>Without this step, your timer would keep starting new rounds forever, but it would never once tell you the result. That is exactly what you saw happen in the last step.</p>
<p>🎮 <b>Try It:</b> Open the sim tab. Press the Timer Button once, and the screen stays quiet, just like before. Wait a moment, then press it again, and a real number appears. That number is how long you waited between your two presses, not how long the Arduino has been turned on like the very first test showed. Press it a few more times and watch the number change depending on how long you wait. That is a real, working reaction timer.</p>
""",
          },
          "howto": {
            "label": "🔧 How To",
            "content": """
<p>Step 4 only taught your timer what to do when the answer to "has this round already started?" is yes. But every single time you press the button after that, the answer is no, since the flag is already raised, and right now nothing has been built for that case at all. That's exactly the silence you saw in the last step.</p>
<p>This step fills in that missing case, using an "else," which only runs when the check right before it turned out to be false. Everything you place here only happens on the press that follows the very first one.</p>
<p>First, your program needs to know exactly what moment it is right now, so it can figure out how much time has gone by. Place a line that sets a new, temporary memory box called <code>now</code> using millis(), the exact same time-reading tool from before.</p>
<p>Next comes the actual point of this whole project: turning two raw moments into a single, meaningful gap. Place a line that sets <code>time</code> to <code>now</code> minus <code>startTime</code>. Subtracting the moment you started from the moment you finished leaves just the difference between them, which is your real reaction time, in milliseconds.</p>
<p>Then, place a line that prints <code>time</code> to the screen, the same kind of print line you built back in Step 3. This time, though, it's printing a real answer instead of a raw, ever-growing number.</p>
<p>Finally, lower the flag by placing a line that sets <code>running</code> back to 0. Without this, your program would think a round was still underway forever, and the very next press would be treated as if it were the second press of an already-finished round instead of the start of a brand new one.</p>
""",
          },
          "logic": {
            "label": "🧠 Logic",
            "content": """
<p>Think of a real stopwatch at a race. Press once and it starts counting silently in the background. Press again, and it doesn't just make a noise. It shows you the exact time on the display, then resets itself, ready for the next runner.</p>
<p>That is exactly the two-press rhythm you just built. Start silently, then reveal the result, then reset.</p>
""",
          },
          "sim": {
            "label": "🎮 Try It",
            "type": "sim",
            "sim_config": {
              "mode": "interpreted",
              "components": [
                {"type": "button", "id": "btn1", "pin": 2, "label": "Timer Button"},
                {"type": "console", "id": "console1", "label": "Serial Monitor"},
              ]
            }
          }
        }
      },
      {
        "title": "Step 6 — Polish Mission Control's Readout 🖥️",
        "tip": "Your logic is done. This step only adds friendly print messages so the Serial Monitor reads like a real instrument.",
        "tabs": {
          "explain": {
            "label": "📖 What & Why",
            "content": """
<p>Your Reaction Lab's thinking is completely finished. The last step already works out a real, correct reaction time. Right now, though, your screen only ever shows plain numbers, with nothing to explain what they mean.</p>
<p>This step does not change how your timer thinks at all. It only adds a few friendly messages around the exact same thinking you already built, so your screen reads like a real instrument instead of a stream of bare numbers.</p>
<p>Since this step is only about making the screen easier to read, every part of it is already built for you. There is nothing new to place. Read through the How To tab to see exactly what was added and why.</p>
<p>🎮 <b>Try It:</b> Open the sim tab and press the Timer Button once. Instead of silence like before, you will now see the words "Timer started! Press again to stop." Press it again, and instead of a bare number, you will see "Your time was:" followed by the number and the letters "ms." The timing underneath has not changed one bit. Only the screen got easier to read.</p>
""",
          },
          "howto": {
            "label": "🔧 How To",
            "content": """
<p>Every line in this step is already built for you, since nothing here is new logic, just a clearer way of showing the same result.</p>
<p>Right after the timer starts (the same <code>running = 1</code> line from Step 4), a new line now prints <code>"Timer started! Press again to stop."</code> That single message finally gives you visible confirmation the moment a round begins, instead of the silence you sat through back in Step 4.</p>
<p>The single bare number print from Step 5 has also changed. Instead of printing just the number, it now prints three separate pieces in a row: <code>"Your time was: "</code>, then the number itself, then <code>" ms"</code> right after it. Spelling out the units means nobody has to guess whether a result is milliseconds, seconds, or something else entirely.</p>
<p>Everything else, the flag, the subtraction, the reset, is exactly what you built in Steps 4 and 5. This step only ever adds messages around that thinking. It never changes what gets calculated.</p>
""",
          },
          "logic": {
            "label": "🧠 Logic",
            "content": """
<p>Think of the difference between a stopwatch that just flashes a bare number and one with a little screen that says "GO!" and then "Your time: 4.12 seconds." Same internal clock, same accuracy. Just a display that actually talks to you.</p>
""",
          },
          "sim": {
            "label": "🎮 Try It",
            "type": "sim",
            "sim_config": {
              "mode": "interpreted",
              "components": [
                {"type": "button", "id": "btn1", "pin": 2, "label": "Timer Button"},
                {"type": "console", "id": "console1", "label": "Serial Monitor"},
              ]
            }
          }
        }
      },
      {
        "title": "Mission Complete 🎉",
        "tip": "Your Reaction Lab timer is fully operational!",
        "tabs": {
          "explain": {
            "label": "📖 What You Built",
            "content": """
<p>Mission complete! 🧪 You built a real reaction timer from scratch. It starts quietly, works out how long you took to react, and shows you the answer in plain, friendly words.</p>
<p>Your Reaction Lab now:</p>
<ul>
<li>🔘 Reads the Timer Button reliably, every single press</li>
<li>🧠 Remembers whether a round is already running, using a flag inside your program</li>
<li>⏱️ Works out the real gap between two presses, instead of just showing a clock that never stops counting</li>
<li>📟 Shows friendly, labeled messages on the screen instead of bare numbers</li>
<li>🔁 Resets itself automatically after every round, ready for the very next press</li>
</ul>
<p>You proved you can build something that goes from "does this even work?" all the way to "this measures something real," one small, honest step at a time.</p>
""",
          },
          "howto": {
            "label": "🔧 Try This Next",
            "content": """
<p>Now that your system works, here are some ideas to make it even better.</p>
<ul>
<li>⏱️ <b>Change the debounce pause.</b> Try shrinking <code>delay(300)</code> to 100ms and see if extra-fast double-presses start sneaking through.</li>
<li>🎯 <b>Add a "best time" tracker.</b> Create a new memory box that remembers your fastest reaction time so far, and only overwrite it when you beat it.</li>
<li>🔴 <b>Add an LED.</b> Light one up while the timer is running, so you get a visual cue on top of the Serial Monitor's silence in Step 4's stage.</li>
<li>🔢 <b>Count your rounds.</b> Add a counter that increases every time a reaction time is printed, and show it alongside each result.</li>
<li>🎮 <b>Build a reflex game.</b> Combine this with another project's sensor so the timer only starts once a random light or sound goes off, measuring true reflex speed instead of a second deliberate press.</li>
</ul>
<p>Experimenting is how real engineers improve their instruments.</p>
""",
          },
          "logic": {
            "label": "🧠 What You Learned",
            "content": """
<p>This project brought together everything you've been building.</p>
<ul>
<li>📦 <b>Variables.</b> Labeled memory boxes that store a number your program can read and change later.</li>
<li>🎁 <b>Reward-first testing.</b> Proving your button and Serial Monitor work before building any real timing logic on top.</li>
<li>🧠 <b>The running flag.</b> A flag that lets your program remember something between one press and the next, not just react in the moment.</li>
<li>⏱️ <b>millis() and subtraction.</b> Turning two raw time readings into a meaningful gap of time.</li>
<li>🔐 <b>Building in isolated steps.</b> Teaching the "first press" behavior completely, watching it go silent on purpose, then adding the "second press" behavior separately.</li>
<li>📟 <b>Serial output as an instrument.</b> The difference between a bare debug number and a labeled, readable result.</li>
</ul>
<p>You're now thinking like a real lab engineer, proving each piece before trusting the whole system. 🚀</p>
""",
          },
          "sim": {
            "label": "🎮 Try It",
            "type": "sim",
            "sim_config": {
              "mode": "interpreted",
              "components": [
                {"type": "button", "id": "btn1", "pin": 2, "label": "Timer Button"},
                {"type": "console", "id": "console1", "label": "Serial Monitor"},
              ]
            }
          }
        }
      },
    ]
  }
}


SKETCH_PRESET = {
    'sketch': """
//>> Step 1 - Declare Your Variables | guided | blocks

//## int button = 2;
//?? Create a variable to remember when timing started, set to 0
unsigned long startTime = 0;
//?? Create a variable to hold the reaction time, set to 0
unsigned long time = 0;

//>> Step 2 - Set Up Pins and Serial | guided | blocks

void setup() {
  //?? Set the button pin as an input
  pinMode(button, INPUT_PULLUP);
  //## Serial.begin(9600);
}

void loop() {}

//>> Step 3 - Print Every Press | guided | blocks

void setup() {}

void loop() {
  //?? Check if the button is pressed
  if (digitalRead(button) == LOW) {
    //?? Store the current time
    time = millis();
    //?? Print the time to the Serial Monitor
    Serial.println(time);
    //## delay(300);
  }
}

//>> Step 4 - Remember When You Started | guided | blocks

//?? Add a variable to track if the timer is running, starting at 0
int running = 0;

void setup() {}

void loop() {
  //## if (digitalRead(button) == LOW) {
    //?? Check if the timer is not running yet
    if (running == 0) {
      //?? Set the start time to right now
      startTime = millis();
      //?? Set running to 1
      running = 1;
    }
    //## delay(300);
  //## }
}

//>> Step 5 - React to the Second Press | guided | blocks

void setup() {}

void loop() {
  //## if (digitalRead(button) == LOW) {
    //## if (running == 0) {
      //## startTime = millis();
      //## running = 1;
    //## }
    //?? Otherwise, calculate and print the reaction time
    else {
      //?? Get the current time
      long now = millis();
      //?? Calculate the reaction time
      time = now - startTime;
      //?? Print the reaction time
      Serial.println(time);
      //?? Set running back to 0
      running = 0;
    }
    //## delay(300);
  //## }
}

//>> Step 6 - Polish the Serial Monitor | free | blocks

void setup() {}

void loop() {
  //## if (digitalRead(button) == LOW) {
    //## if (running == 0) {
      //## startTime = millis();
      //## running = 1;
      //## Serial.println("Timer started! Press again to stop.");
    //## }
    //## else {
      //## long now = millis();
      //## time = now - startTime;
      //## Serial.print("Your time was: ");
      //## Serial.print(time);
      //## Serial.println(" ms");
      //## running = 0;
    //## }
    //## delay(300);
  //## }
}

//>> Mission Complete | open | blocks
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
CHIPS = [
    "I think my button legs missed row 10",
    "I can't tell if wire is in column D",
    "My Pin 2 wire isn't making contact",
    "My ground wire isn't in the negative rail",
    "I think my wire in column G is misplaced",
]

PROJECT = {
    "meta": META,
    "steps": STEPS,
    "drawer": DRAWER_CONTENT,
    "chips": CHIPS,
    "presets": {
        "default": SKETCH_PRESET,
        "challenge": CHALLENGE_PRESET,
        "progression": PROGRESSION_PRESET,
    },
    "circuit_spec": CIRCUIT_SPEC,
}
