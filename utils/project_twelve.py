
from utils.step_builder import build_step, intro_step, rect, circle, line
from utils.affiliate_kits import BASIC_KITS

META = {
    'title': 'Project 12: Night Patrol Alarm',
    'circuit_image': 'static/graphics/project_twelve_circuit.png',
    'banner_image': 'patrol_alarm.png',
    'required_kits': BASIC_KITS,
}

STEPS = [
    intro_step(
        "Let's build our twelfth project",
        "Press the next button for a step by step guide",
    ),
    build_step(
        "Place the long leg of the LED in row 18, column E.<br>Place the short leg in row 17, column E",
        "Make sure your lights are in the right order.",
        rect(876, 175, 971, 344),
    ),
    build_step(
        "Place the long leg of the LED in row 24, column E.<br>Place the short leg in row 23, column E.",
        "Red, then Blue!",
        rect(994, 181, 1083, 347),
    ),
    build_step(
        "Place the long leg of the LED in row 30, column E.<br>Place the short leg in row 29, column E",
        "The Clear Strobe goes last.",
        rect(1093, 168, 1203, 343),
    ),
    build_step(
        "Add the 220 ohm resistors for each LED to protect them.",
        "Resistors slow down the electricity.",
        rect(805, 318, 940, 376),
        rect(929, 305, 1056, 376),
        rect(1047, 300, 1171, 370),
    ),
    build_step(
        "Place the button onto the breadboard across the center gap.",
        "This is the Master Power Button.",
        rect(719, 244, 812, 347),
    ),
    build_step(
        "Wire the LEDs to Pins 8, 6, and 4.",
        "Red = Pin 8, Blue = Pin 6, Clear = Pin 4.",
        line((366, 358), (933, 364)),
        line((1048, 401), (364, 411)),
        line((1165, 399), (370, 449)),
    ),
    build_step(
        "Wire the Button to Pin 12.",
        "This wire sends the signal to the Arduino.",
        line((749, 347), (366, 284)),
    ),
    build_step(
        "Complete the Ground (GND) connections.",
        "Finish the circuit loop to the negative rail.",
        line((621, 113), (356, 249)),
        line((788, 263), (766, 106)),
        line((844, 337), (806, 106)),
        line((956, 333), (962, 111)),
        line((1075, 336), (1078, 103)),
    ),
]

CIRCUIT_SPEC = {
    "meta": {
        "title": "Night Patrol Alarm",
        "difficulty": "intermediate",
    },
    "components": [
        {"id": "BTN", "type": "BUTTON", "properties": {}},
        {"id": "RED_LED", "type": "LED", "properties": {"color": "red"}},
        {"id": "BLUE_LED", "type": "LED", "properties": {"color": "blue"}},
        {"id": "CLEAR_LED", "type": "LED", "properties": {"color": "white"}},
    ],
    "connections": [
        {"from": "arduino.D12", "to": "BTN.TL"},
        {"from": "BTN.BR", "to": "arduino.GND"},
        {"from": "arduino.D8", "to": "RED_LED.anode"},
        {"from": "R_RED_LED.pin2", "to": "arduino.GND"},
        {"from": "arduino.D6", "to": "BLUE_LED.anode"},
        {"from": "R_BLUE_LED.pin2", "to": "arduino.GND"},
        {"from": "arduino.D4", "to": "CLEAR_LED.anode"},
        {"from": "R_CLEAR_LED.pin2", "to": "arduino.GND"},
    ],
}

from utils.circuit_engine import generate_circuit

patrol_alarm_circuit_definition = generate_circuit(
    CIRCUIT_SPEC["meta"], CIRCUIT_SPEC["components"], CIRCUIT_SPEC["connections"]
)

# --- Drawer content ---------------------------------------------------------
# age_group: 11-12
DRAWER_CONTENT = {
  "project_twelve": {
    "steps": [
      {
        "title": "Step 1 — Wire Up the Dashboard 🔌",
        "tip": "Tell the Arduino which pin is the button and which pins are the lights.",
        "tabs": {
          "explain": {
            "label": "📖 What & Why",
            "content": """
<p>Welcome back to the Emergency Systems Lab, trainee. 🚓 Tonight's cruiser has a Master Power Button and three lights on its light bar — Red, Blue, and a Clear Strobe. Before any of it can work, the Arduino needs a map of the dashboard.</p>
<p>This step gives every part a name and tells the Arduino how to treat it: the button is something the Arduino <b>listens</b> to, and the three lights are things the Arduino <b>controls</b>.</p>
<p>Skip this step and none of it works later — <code>digitalRead</code> and <code>digitalWrite</code> would have no pin numbers to act on, and the whole light bar stays dark no matter what code you write after this.</p>
<p>Next up: your first win. You'll turn all three lights on and prove the wiring works before writing a single rule.</p>
""",
            "circuit_definition": patrol_alarm_circuit_definition,
          },
          "howto": {
            "label": "🔧 How To",
            "content": """
<p><b>First, name each part.</b> You'll place four variable blocks — one per part on the dashboard:</p>
<ol>
<li><b>Intent:</b> give each pin a plain-English name instead of a bare number, so later blocks read like "redLED" instead of "8."</li>
<li><b>Block:</b> a variable block that stores a whole number.</li>
<li><b>Values:</b> <code>buttonPin = 12</code>, <code>redLED = 8</code>, <code>blueLED = 6</code>, <code>clearLED = 4</code> — these match exactly where you wired each part on the breadboard.</li>
<li><b>Result:</b> nothing happens yet — this only introduces the names the rest of the project will use.</li>
</ol>
<p><b>Then, set each pin's mode inside Setup.</b> Four more blocks, same pattern:</p>
<ol>
<li><b>Intent:</b> tell the Arduino whether each pin should listen for a signal or send one out.</li>
<li><b>Block:</b> a pinMode block, placed inside <code>setup()</code>.</li>
<li><b>Values:</b> <code>buttonPin</code> → <b>INPUT_PULLUP</b> (it listens; because of this wiring style, "pressed" will actually read as LOW, not HIGH). <code>redLED</code>, <code>blueLED</code>, and <code>clearLED</code> → <b>OUTPUT</b> (the Arduino sends power to each one).</li>
<li><b>Result:</b> Setup finishes quietly — still no visible change, but the Arduino now fully understands the dashboard.</li>
</ol>
""",
          },
          "logic": {
            "label": "🧠 Logic",
            "content": """
<p>Think of a new officer's first night learning the dashboard of a patrol car. Before they can flip anything, they have to know which switch is the siren, which is the light bar, and which pedal does what.</p>
<p>That's exactly what this step does for the Arduino — it's memorizing the dashboard before the shift starts.</p>
""",
          },
        }
      },
      {
        "title": "Step 2 — Lights On 💡",
        "tip": "Reward-first: all three lights turn on and stay on, no button needed yet.",
        "tabs": {
          "explain": {
            "label": "📖 What & Why",
            "content": """
<p>Time for your first win, trainee! Before you teach the light bar any rules, prove the wiring actually works.</p>
<p>This step turns the Red, Blue, and Clear lights <b>ON</b> — no button, no conditions, just on. If a wire is loose or a pin number is wrong, you want to catch it right now, not after burying it inside a bunch of rules.</p>
<p>Next, you'll wrap these same three blocks in a timer so each light flashes instead of staying lit.</p>
<p>🎮 <b>Try It:</b> Open the sim tab. All three lights should switch on immediately, with no button press needed. That's your proof the wiring is good.</p>
""",
          },
          "howto": {
            "label": "🔧 How To",
            "content": """
<p>You'll place three blocks — one per light:</p>
<ol>
<li><b>Turn on the Red light.</b> Intent: prove Pin 8 is wired correctly. Block: an output block. Values: <code>redLED</code>, set to <b>HIGH</b> — full power. Result: the red light glows immediately.</li>
<li><b>Turn on the Blue light.</b> Same block, values: <code>blueLED</code>, <b>HIGH</b>. Result: blue glows too.</li>
<li><b>Turn on the Clear Strobe.</b> Same block, values: <code>clearLED</code>, <b>HIGH</b>. Result: all three lights are now lit at once.</li>
</ol>
""",
          },
          "logic": {
            "label": "🧠 Logic",
            "content": """
<p>Think of an electrician testing a new room by flipping the master breaker and checking every bulb lights up — before wiring in any switches or dimmers.</p>
<p>That's this step exactly: prove the raw connections work before adding any behavior on top.</p>
""",
          },
          "sim": {
            "label": "🎮 Try It",
            "type": "sim",
            "sim_config": {
              "mode": "interpreted",
              "components": [
                {"type": "led", "id": "led_r", "color": "red",   "pin": 8, "label": "Red Light"},
                {"type": "led", "id": "led_b", "color": "blue",  "pin": 6, "label": "Blue Light"},
                {"type": "led", "id": "led_w", "color": "white", "pin": 4, "label": "Clear Strobe"},
              ],
            }
          }
        }
      },
      {
        "title": "Step 3 — Add the Delay ⏱️",
        "tip": "Turn the steady lights into a chase: on, wait, off — one at a time.",
        "tabs": {
          "explain": {
            "label": "📖 What & Why",
            "content": """
<p>Good work — the lights are wired correctly. But right now all three just sit there lit up together, which isn't a patrol pattern, it's just a nightlight.</p>
<p>This step makes each light turn back off after a brief flash, one after another — Red flashes, then Blue, then Clear. That's the real timed "chase" a patrol light bar is known for.</p>
<p>Without this, there's no way to tell the difference between "the wiring works" and "an actual signal pattern" — every light would just stay stuck on forever.</p>
<p>Next: you'll wrap this whole chase in a rule so it only runs while the Master Button is held.</p>
<p>🎮 <b>Try It:</b> Open the sim tab. Instead of Step 2's "all on and stay on," watch each light flash once, in order, then go dark before the next one lights up.</p>
""",
          },
          "howto": {
            "label": "🔧 How To",
            "content": """
<p>Your Step 2 blocks (each light turning HIGH) are already locked in place. For each light, you'll add two new blocks:</p>
<ol>
<li><b>Red:</b> Intent — make red turn back off after a moment. Block — a delay block, then an output block. Values — <code>delay(150)</code> (the Academy's official flash timing, in milliseconds), then <code>redLED</code> set to <b>LOW</b> (no power). Result — red flashes once, then goes dark.</li>
<li><b>Blue:</b> same pair of blocks. Values — <code>delay(150)</code>, then <code>blueLED</code> set to <b>LOW</b>. Result — blue flashes right after red goes dark.</li>
<li><b>Clear:</b> same pair again. Values — <code>delay(150)</code>, then <code>clearLED</code> set to <b>LOW</b>. Result — the full chase completes: red, then blue, then clear, each on its own beat.</li>
</ol>
""",
          },
          "logic": {
            "label": "🧠 Logic",
            "content": """
<p>Picture a lighthouse: the beam flashes for a set moment, then rests in the dark before the next flash — never staying lit the whole time.</p>
<p>Your light bar now works the same way, one light at a time, on its own timed beat.</p>
""",
          },
          "sim": {
            "label": "🎮 Try It",
            "type": "sim",
            "sim_config": {
              "mode": "interpreted",
              "components": [
                {"type": "led", "id": "led_r", "color": "red",   "pin": 8, "label": "Red Light"},
                {"type": "led", "id": "led_b", "color": "blue",  "pin": 6, "label": "Blue Light"},
                {"type": "led", "id": "led_w", "color": "white", "pin": 4, "label": "Clear Strobe"},
              ],
            }
          }
        }
      },
      {
        "title": "Step 4 — Gate with the Master Button 🔘",
        "tip": "Wrap the chase in a rule: only run it while the Master Button is held.",
        "tabs": {
          "explain": {
            "label": "📖 What & Why",
            "content": """
<p>Right now the light bar chases nonstop, the moment the Arduino powers on — no officer has to touch anything. A real patrol cruiser doesn't work that way; someone has to hold the Master Power Button for the light bar to run at all.</p>
<p>This step doesn't rewrite your chase — it takes the exact three-light pattern you already built in Steps 2 and 3 and moves it inside a rule that checks the button first.</p>
<p>Without this, the light bar can't ever be turned off, which isn't just annoying — a real patrol light bar left running all the time would drain the battery and give away the cruiser's position when it should be dark.</p>
<p>Next: you'll try tuning the chase's speed.</p>
<p>🎮 <b>Try It:</b> Open the sim tab. Nothing happens until you press and hold the Master Button — then the same chase from Step 3 runs. Release the button and the whole bar snaps dark immediately. That's a big change from Step 3, where the chase ran on its own with no button at all.</p>
""",
          },
          "howto": {
            "label": "🔧 How To",
            "content": """
<p>Everything from Steps 2–3 is already locked in place. You'll place two new pieces:</p>
<ol>
<li><b>Check if the button is pressed.</b> Intent — only run the chase while the Master Button is actually held down. Block — an "if" block. Values — <code>digitalRead(buttonPin) == LOW</code>. Because of the INPUT_PULLUP wiring from Step 1, "pressed" reads backwards, as LOW instead of HIGH. Result — your whole Step 2/3 chase now sits inside this if, unchanged, and only runs while it's true.</li>
<li><b>Turn everything off when it's not pressed.</b> Intent — make sure the light bar goes fully dark the instant the button is released, instead of freezing mid-blink. Block — an "else" block attached to the if above. Values — no new values; it turns Red, Blue, and Clear to <b>LOW</b> all at once. Result — release the button and the bar goes dark immediately, every time.</li>
</ol>
""",
          },
          "logic": {
            "label": "🧠 Logic",
            "content": """
<p>A real patrol light bar doesn't run itself — an officer has to hold the master switch for it to do anything at all, and letting go stops it instantly, no delay.</p>
<p>That's exactly the rule you just built: the button is the boss, and the chase only exists while it says so.</p>
""",
          },
          "sim": {
            "label": "🎮 Try It",
            "type": "sim",
            "sim_config": {
              "mode": "interpreted",
              "components": [
                {"type": "button", "id": "btn1", "pin": 12, "label": "Master Button"},
                {"type": "led", "id": "led_r", "color": "red",   "pin": 8, "label": "Red Light"},
                {"type": "led", "id": "led_b", "color": "blue",  "pin": 6, "label": "Blue Light"},
                {"type": "led", "id": "led_w", "color": "white", "pin": 4, "label": "Clear Strobe"},
              ],
            }
          }
        }
      },
      {
        "title": "Step 5 — Change the Delay ⚡",
        "tip": "Try a faster pace — swap all three delays to 60ms.",
        "tabs": {
          "explain": {
            "label": "📖 What & Why",
            "content": """
<p>Your gated chase works — now Patrol Command wants to see it run faster. This step proves something important: the timing numbers you used in Step 3 aren't fixed rules, they're just settings you can tune.</p>
<p>You're not adding any new blocks here — you're changing one number, three times, inside the chase you already built and gated behind the button.</p>
<p>If you couldn't change this, every project would be stuck at whatever speed it was first built at — real patrol equipment gets tuned constantly for different situations.</p>
<p>Next: you'll rearrange the order the lights fire in.</p>
<p>🎮 <b>Try It:</b> Hold the Master Button and compare this to Step 4 — the same red-blue-clear pattern now snaps by noticeably faster.</p>
""",
          },
          "howto": {
            "label": "🔧 How To",
            "content": """
<p>The whole chase is already locked in place from Steps 2–4. You're only swapping the value inside three existing delay blocks:</p>
<ol>
<li><b>Intent:</b> make the whole chase noticeably snappier.</li>
<li><b>Block:</b> the same delay block from Step 3 — you're not adding a new one.</li>
<li><b>Values:</b> change all three from <code>150</code> down to <code>60</code> milliseconds.</li>
<li><b>Result:</b> the fully-gated chase from Step 4 now runs at a faster tempo — same order, same button, just quicker.</li>
</ol>
""",
          },
          "logic": {
            "label": "🧠 Logic",
            "content": """
<p>Think of turning the speed dial on a strobe light at a concert — same bulb, same wiring, just a different number telling it how long to wait between flashes.</p>
<p>That's all a delay value ever is: a dial you're allowed to turn.</p>
""",
          },
          "sim": {
            "label": "🎮 Try It",
            "type": "sim",
            "sim_config": {
              "mode": "interpreted",
              "components": [
                {"type": "button", "id": "btn1", "pin": 12, "label": "Master Button"},
                {"type": "led", "id": "led_r", "color": "red",   "pin": 8, "label": "Red Light"},
                {"type": "led", "id": "led_b", "color": "blue",  "pin": 6, "label": "Blue Light"},
                {"type": "led", "id": "led_w", "color": "white", "pin": 4, "label": "Clear Strobe"},
              ],
            }
          }
        }
      },
      {
        "title": "Step 6 — Rearrange the Sequence 🔄",
        "tip": "Reorder the chase — blue first, then red, then clear.",
        "tabs": {
          "explain": {
            "label": "📖 What & Why",
            "content": """
<p>Patrol Command has a new request: lead with Blue instead of Red. This step proves that the <i>order</i> you place blocks in is what defines the pattern — not some hidden rule about which light has to go first.</p>
<p>You're reusing the exact same three on-wait-off block groups from Steps 2, 3, and 5 — just placing them in a new order: Blue, then Red, then Clear.</p>
<p>Without this flexibility, every lesson's pattern would be locked to whatever order it was first written in — real patrol light bars support multiple sequences for exactly this reason.</p>
<p>Next: you'll add a counter so the pattern can start making decisions, not just repeat.</p>
<p>🎮 <b>Try It:</b> Hold the Master Button. Step 5's order was red, blue, clear — now watch it fire blue, red, clear instead. Same three blocks, same 60ms pace, new order.</p>
""",
          },
          "howto": {
            "label": "🔧 How To",
            "content": """
<p>You already know these blocks — they're the same on/wait/off trio you've built twice now, just placed for a different light each time and in a new order:</p>
<ol>
<li><b>Blue first.</b> Intent — move blue to the front of the chase. Block — the same on/delay/off trio. Values — <code>blueLED</code> HIGH, <code>delay(60)</code>, <code>blueLED</code> LOW. Result — blue fires first now.</li>
<li><b>Red second.</b> Same trio. Values — <code>redLED</code> HIGH, <code>delay(60)</code>, <code>redLED</code> LOW. Result — red fires right after blue.</li>
<li><b>Clear third.</b> Same trio. Values — <code>clearLED</code> HIGH, <code>delay(60)</code>, <code>clearLED</code> LOW. Result — clear finishes the pattern, same as before, just last in this new order.</li>
</ol>
<p>The button check and the "everything off" else from Step 4 stay exactly where they were — only the order of the three light groups changed.</p>
""",
          },
          "logic": {
            "label": "🧠 Logic",
            "content": """
<p>Think of a drill sergeant swapping the order of moves in a routine — same three moves, same timing between them, but the sequence itself is what changes the whole feel of the drill.</p>
<p>The blocks don't know or care what order they're in — the order is entirely up to you.</p>
""",
          },
          "sim": {
            "label": "🎮 Try It",
            "type": "sim",
            "sim_config": {
              "mode": "interpreted",
              "components": [
                {"type": "button", "id": "btn1", "pin": 12, "label": "Master Button"},
                {"type": "led", "id": "led_r", "color": "red",   "pin": 8, "label": "Red Light"},
                {"type": "led", "id": "led_b", "color": "blue",  "pin": 6, "label": "Blue Light"},
                {"type": "led", "id": "led_w", "color": "white", "pin": 4, "label": "Clear Strobe"},
              ],
            }
          }
        }
      },
      {
        "title": "Step 7 — Count the Blinks 🔢",
        "tip": "Add a new global — a counter that will track blue blinks. Nothing visible changes yet.",
        "tabs": {
          "explain": {
            "label": "📖 What & Why",
            "content": """
<p>New mission upgrade, trainee: Command wants Red to join the pattern only once every two Blue blinks — a real backup-request signal, not just another light in the rotation.</p>
<p>Before the Arduino can make that decision, it needs somewhere to keep count. This step creates exactly one thing: a memory slot named <code>blueCount</code>, starting at zero.</p>
<p>Without a place to store the tally, there's nothing for a later rule to check — "has blue blinked twice yet?" is meaningless if the Arduino has no memory of past blinks at all.</p>
<p>Next: you'll wrap Red's existing blink in a check against this counter.</p>
""",
          },
          "howto": {
            "label": "🔧 How To",
            "content": """
<ol>
<li><b>Intent:</b> reserve a memory slot that remembers how many times blue has blinked so far.</li>
<li><b>Block:</b> a variable block, storing a whole number, placed above <code>setup()</code> so it's global — it will carry its value forward across every pass of the loop.</li>
<li><b>Values:</b> <code>blueCount</code>, starting value <code>0</code> — zero blinks counted yet.</li>
<li><b>Result:</b> nothing visible happens. This step only reserves the slot; nothing reads or changes it until Step 8.</li>
</ol>
""",
          },
          "logic": {
            "label": "🧠 Logic",
            "content": """
<p>Think of a dispatcher keeping a tally on a notepad every time a certain type of call comes in. The tally by itself doesn't do anything — but it's what lets a later rule say "once we hit 3 of these, call for backup."</p>
<p><code>blueCount</code> is that notepad. This step just hands the Arduino the pad and the pencil.</p>
""",
          },
        }
      },
      {
        "title": "Step 8 — Guard the Red Light 🚦",
        "tip": "Wrap red's existing blink in a counter check — it won't fire yet, and that's the point.",
        "tabs": {
          "explain": {
            "label": "📖 What & Why",
            "content": """
<p>Time to put that counter to work. This step wraps Red's blink — already built back in Step 6 — inside a check: only run it once <code>blueCount</code> has reached <b>2</b>. Once red fires, the counter resets to zero so the cycle can start over.</p>
<p>Here's the deliberate catch: nothing increases <code>blueCount</code> yet. Blue and Clear will keep chasing exactly like before, but Red will stay dark no matter how long you hold the button — because the counter never moves off zero. That's not a bug. It's proof the guard itself is working correctly before you connect the piece that feeds it.</p>
<p>Command also bumped every delay in this chase up to <b>1,500 milliseconds</b> for this test — that's slow on purpose, so you have time to actually count the blue blinks out loud while you watch for red to join in. Those timing blocks are locked in for you.</p>
<p>Next: one line connects blue's blink to the counter, and the full pattern clicks into place.</p>
<p>🎮 <b>Try It:</b> Hold the Master Button and watch closely. Blue and Clear keep chasing, just like Step 6 — but Red never lights up, no matter how long you hold it. That's exactly the point: the guard is in place, but nothing is feeding the counter yet.</p>
""",
          },
          "howto": {
            "label": "🔧 How To",
            "content": """
<p>The button check, the full blue/clear chase, and Red's on/wait/off blocks are all already locked in place from earlier steps. You'll place three new pieces:</p>
<ol>
<li><b>Check the counter before letting Red fire.</b> Intent — only let Red join the pattern once two blue blinks have actually been counted. Block — an "if" block, nested inside the button's if. Values — <code>blueCount == 2</code>, checking the memory slot from Step 7. Result — Red's existing blink blocks now only run when this is true.</li>
<li><b>Reset the count after Red fires.</b> Intent — start the tally over so the pattern can repeat. Block — an assignment block (sets a variable to a new value). Values — <code>blueCount = 0</code>. Result — right after Red flashes, the counter is back at zero, ready to count the next two blue blinks.</li>
<li><b>Run the normal chase otherwise.</b> Intent — everything that used to run every single pass (blue then clear) now only runs when the counter <i>hasn't</i> reached 2 yet. Block — an "else" block attached to the counter check. Values — none new; it's the same blue-then-clear chase from Steps 2, 3, and 6, just moved inside this else. Result — for now, blue and clear fire every pass since nothing increases <code>blueCount</code> — exactly what Step 9 fixes.</li>
</ol>
""",
          },
          "logic": {
            "label": "🧠 Logic",
            "content": """
<p>Think of a security guard who only radios "all clear" once they've completed exactly two full rounds of the building — one round by itself doesn't earn the report.</p>
<p>Red is that report. The guard (your counter check) is standing by, but nothing has told it a round finished yet.</p>
""",
          },
          "sim": {
            "label": "🎮 Try It",
            "type": "sim",
            "sim_config": {
              "mode": "interpreted",
              "polling": True,
              "components": [
                {"type": "button", "id": "btn1", "pin": 12, "label": "Master Button"},
                {"type": "led", "id": "led_r", "color": "red",   "pin": 8, "label": "Red Light"},
                {"type": "led", "id": "led_b", "color": "blue",  "pin": 6, "label": "Blue Light"},
                {"type": "led", "id": "led_w", "color": "white", "pin": 4, "label": "Clear Strobe"},
              ],
            }
          }
        }
      },
      {
        "title": "Step 9 — Make Blue Count Itself 🎯",
        "tip": "One new line: increase the counter every time blue blinks. Now red joins in every 3rd beat.",
        "tabs": {
          "explain": {
            "label": "📖 What & Why",
            "content": """
<p>One line left, trainee — the piece Step 8 was missing. Right now blue blinks but never tells the counter about it. This step adds exactly that: every time blue blinks, <code>blueCount</code> goes up by one.</p>
<p>With this in place, your Night Patrol Alarm is complete: blue, clear, blue, clear — and once that's happened twice, red joins in, then the counter resets and the whole pattern starts again.</p>
<p>Without this line, <code>blueCount</code> would sit at zero forever, and Red would never fire — exactly the frozen behavior you saw in Step 8.</p>
""",
          },
          "howto": {
            "label": "🔧 How To",
            "content": """
<p>Everything else is already locked in place. You'll place one block, right after blue's existing on/wait/off blocks:</p>
<ol>
<li><b>Intent:</b> make the counter actually go up every time blue blinks.</li>
<li><b>Block:</b> an assignment block that sets a variable using its own current value.</li>
<li><b>Values:</b> <code>blueCount = blueCount + 1</code> — take whatever the tally currently holds and add one.</li>
<li><b>Result:</b> after two blue blinks, <code>blueCount</code> reaches 2, Step 8's guard opens, and Red joins the pattern — then the reset sends it back to zero and the whole cycle repeats.</li>
</ol>
""",
          },
          "logic": {
            "label": "🧠 Logic",
            "content": """
<p>Think of a guard's hand-clicker — each completed round clicks the count up by one. Once it reads 2, that's the guard's own cue to radio in, without anyone else telling them to.</p>
<p>That single click is all blue was missing — it just needed to report its own progress.</p>
""",
          },
          "sim": {
            "label": "🎮 Try It",
            "type": "sim",
            "sim_config": {
              "mode": "interpreted",
              "polling": True,
              "components": [
                {"type": "button", "id": "btn1", "pin": 12, "label": "Master Button"},
                {"type": "led", "id": "led_r", "color": "red",   "pin": 8, "label": "Red Light"},
                {"type": "led", "id": "led_b", "color": "blue",  "pin": 6, "label": "Blue Light"},
                {"type": "led", "id": "led_w", "color": "white", "pin": 4, "label": "Clear Strobe"},
              ],
            }
          }
        }
      },
      {
        "title": "Mission Complete 🎉",
        "tip": "Your Night Patrol Alarm is fully operational!",
        "tabs": {
          "explain": {
            "label": "📖 What You Built",
            "content": """
<p>Mission complete, trainee! 🚓 You built a real patrol light bar with a working counting rule — the kind of system a real cruiser depends on every night.</p>
<p>Your light bar now:</p>
<ul>
<li>🔘 Stays completely dark until the Master Button is actually held</li>
<li>💡 Chases Blue, then Clear, in a tuned, timed pattern</li>
<li>🔢 Keeps a running count of every blue blink, using memory that persists across the whole patrol</li>
<li>🔴 Brings Red into the pattern only once two blue blinks have been counted</li>
<li>🔁 Resets the count automatically so the pattern repeats on its own</li>
<li>🛑 Shuts every light off instantly the moment the button is released</li>
</ul>
<p>You proved you can build a system that doesn't just react — it remembers. That's real patrol-tech thinking.</p>
""",
          },
          "howto": {
            "label": "🔧 Try This Next",
            "content": """
<p>Now that your system works, here are some ideas to make it even better.</p>
<ul>
<li>⏱️ <b>Change the delay again</b> — try 800ms or 2,000ms and see how it changes the feel of the countdown to red.</li>
<li>🔄 <b>Reorder the chase again</b> — try Clear first, then Blue, then see where Red should slot in.</li>
<li>🔢 <b>Change the count</b> — make Red wait for 3 blue blinks instead of 2, or fire after just 1.</li>
<li>🚨 <b>Add a second counter</b> — track how many times Red has fired total, and do something special on the 5th time.</li>
<li>🔘 <b>Add a second button</b> — a siren toggle that runs independently of the light bar's button.</li>
<li>🎮 <b>Combine with another project</b> — pair this counting pattern with a sensor from another mission to trigger the alarm automatically instead of by button press.</li>
</ul>
<p>Experimenting is how real patrol engineers improve their equipment.</p>
""",
          },
          "logic": {
            "label": "🧠 What You Learned",
            "content": """
<p>This project brought together everything you've been building.</p>
<ul>
<li>🎁 <b>Reward-first testing</b> — proving your lights work before wrapping them in any rules.</li>
<li>🔐 <b>Capture</b> — taking code you already built and wrapping it inside a new condition, without rewriting it.</li>
<li>🔘 <b>INPUT_PULLUP</b> — a wiring style where "pressed" actually reads as LOW.</li>
<li>🎛️ <b>Tunable parameters</b> — delay values and block order aren't fixed rules, they're settings you control.</li>
<li>🔢 <b>Global counters</b> — a variable that remembers a running tally across every pass of the loop, not just the current one.</li>
<li>🧩 <b>Nested conditions</b> — a rule inside another rule, so Red depends on both the button <i>and</i> the counter.</li>
</ul>
<p>You're now thinking like a real systems engineer — building equipment that remembers, not just reacts. 🚨</p>
""",
          },
          "sim": {
            "label": "🎮 Try It",
            "type": "sim",
            "sim_config": {
              "mode": "interpreted",
              "polling": True,
              "components": [
                {"type": "button", "id": "btn1", "pin": 12, "label": "Master Button"},
                {"type": "led", "id": "led_r", "color": "red",   "pin": 8, "label": "Red Light"},
                {"type": "led", "id": "led_b", "color": "blue",  "pin": 6, "label": "Blue Light"},
                {"type": "led", "id": "led_w", "color": "white", "pin": 4, "label": "Clear Strobe"},
              ],
            }
          }
        }
      },
    ]
  }
}

SKETCH_PRESET = {
    'sketch': """
//>> Step 1 - Setup Pins | guided | blocks | fill:true

//?? Define the Master Button Pin
int buttonPin = 12;
//?? Define the Red LED Pin
int redLED = 8;
//?? Define the Blue LED Pin
int blueLED = 6;
//?? Define the Clear LED Pin
int clearLED = 4;

void setup() {
  //?? Set the button pin as an input
  pinMode(buttonPin, INPUT_PULLUP);
  //?? Set the red LED pin as an output
  pinMode(redLED, OUTPUT);
  //?? Set the blue LED pin as an output
  pinMode(blueLED, OUTPUT);
  //?? Set the clear LED pin as an output
  pinMode(clearLED, OUTPUT);
}

void loop() {}

//>> Step 2 - Lights On | guided | blocks | fill:true

void setup() {}

void loop() {
  //?? Turn the red light on
  digitalWrite(redLED, HIGH);
  //?? Turn the blue light on
  digitalWrite(blueLED, HIGH);
  //?? Turn the clear light on
  digitalWrite(clearLED, HIGH);
}

//>> Step 3 - Add the Delay | guided | blocks | fill:true

void setup() {}

void loop() {
  //## digitalWrite(redLED, HIGH);
  //?? Wait 150 milliseconds
  delay(150);
  //?? Turn the red light off
  digitalWrite(redLED, LOW);

  //## digitalWrite(blueLED, HIGH);
  //?? Wait 150 milliseconds
  delay(150);
  //?? Turn the blue light off
  digitalWrite(blueLED, LOW);

  //## digitalWrite(clearLED, HIGH);
  //?? Wait 150 milliseconds
  delay(150);
  //?? Turn the clear light off
  digitalWrite(clearLED, LOW);
}

//>> Step 4 - Gate with the Button | guided | blocks | fill:true

void setup() {}

void loop() {
  //?? Check if the button is pressed
  if (digitalRead(buttonPin) == LOW) {
    //## digitalWrite(redLED, HIGH);
    //## delay(150);
    //## digitalWrite(redLED, LOW);

    //## digitalWrite(blueLED, HIGH);
    //## delay(150);
    //## digitalWrite(blueLED, LOW);

    //## digitalWrite(clearLED, HIGH);
    //## delay(150);
    //## digitalWrite(clearLED, LOW);
  }
  //?? Otherwise, turn every light off
  else {
    digitalWrite(redLED, LOW);
    digitalWrite(blueLED, LOW);
    digitalWrite(clearLED, LOW);
  }
}

//>> Step 5 - Change the Delay | guided | blocks | fill:true

void setup() {}

void loop() {
  //## if (digitalRead(buttonPin) == LOW) {
    //## digitalWrite(redLED, HIGH);
    //?? Try a faster delay - 60 milliseconds
    delay(60);
    //## digitalWrite(redLED, LOW);

    //## digitalWrite(blueLED, HIGH);
    //?? Try a faster delay - 60 milliseconds
    delay(60);
    //## digitalWrite(blueLED, LOW);

    //## digitalWrite(clearLED, HIGH);
    //?? Try a faster delay - 60 milliseconds
    delay(60);
    //## digitalWrite(clearLED, LOW);
  //## }
  //## else {
    //## digitalWrite(redLED, LOW);
    //## digitalWrite(blueLED, LOW);
    //## digitalWrite(clearLED, LOW);
  //## }
}

//>> Step 6 - Rearrange the Sequence | guided | blocks | fill:true

void setup() {}

void loop() {
  //## if (digitalRead(buttonPin) == LOW) {
    //?? This time, start with the blue light
    digitalWrite(blueLED, HIGH);
    //?? Wait 60 milliseconds
    delay(60);
    //?? Turn the blue light off
    digitalWrite(blueLED, LOW);

    //?? Now the red light
    digitalWrite(redLED, HIGH);
    //?? Wait 60 milliseconds
    delay(60);
    //?? Turn the red light off
    digitalWrite(redLED, LOW);

    //?? Clear light goes last
    digitalWrite(clearLED, HIGH);
    //?? Wait 60 milliseconds
    delay(60);
    //?? Turn the clear light off
    digitalWrite(clearLED, LOW);
  //## }
  //## else {
    //## digitalWrite(redLED, LOW);
    //## digitalWrite(blueLED, LOW);
    //## digitalWrite(clearLED, LOW);
  //## }
}

//>> Step 7 - Count the Blinks | guided | blocks | fill:true

//?? Define a counter to count blue blinks
int blueCount = 0;

//>> Step 8 - Guard the Red Light | guided | blocks | fill:true

void setup() {}

void loop() {
  //## if (digitalRead(buttonPin) == LOW) {
    //?? Only blink red once we've counted 2 blue blinks
    if (blueCount == 2) {
      //## digitalWrite(redLED, HIGH);
      //## delay(1500);
      //## digitalWrite(redLED, LOW);
      //?? Reset the counter back to 0
      blueCount = 0;
    }
    //?? Otherwise, run the normal blue and clear chase
    else {
      //## digitalWrite(blueLED, HIGH);
      //## delay(1500);
      //## digitalWrite(blueLED, LOW);

      //## digitalWrite(clearLED, HIGH);
      //## delay(1500);
      //## digitalWrite(clearLED, LOW);
    }
  //## }
  //## else {
    //## digitalWrite(redLED, LOW);
    //## digitalWrite(blueLED, LOW);
    //## digitalWrite(clearLED, LOW);
  //## }
}

//>> Step 9 - Make Blue Count Itself | guided | blocks | fill:true

void setup() {}

void loop() {
  //## if (digitalRead(buttonPin) == LOW) {
    //## if (blueCount == 2) {
      //## digitalWrite(redLED, HIGH);
      //## delay(1500);
      //## digitalWrite(redLED, LOW);
      //## blueCount = 0;
    //## }
    //## else {
      //## digitalWrite(blueLED, HIGH);
      //## delay(1500);
      //## digitalWrite(blueLED, LOW);
      //?? Add one to the blue counter
      blueCount = blueCount + 1;

      //## digitalWrite(clearLED, HIGH);
      //## delay(1500);
      //## digitalWrite(clearLED, LOW);
    //## }
  //## }
  //## else {
    //## digitalWrite(redLED, LOW);
    //## digitalWrite(blueLED, LOW);
    //## digitalWrite(clearLED, LOW);
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
    "I can't light my LED on pin 8",
    "My LED on pin 6 won't turn on",
    "My LED on pin 4 stays dark",
    "Pressing my button on pin 12 does nothing",
    "My 220 ohm resistor feels hot",
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
