"""
utils/project_try_it.py — content for the anonymous /try trial page.

This is the curated trial experience, not a placeholder: one LED, two
interactive steps, deliberately designed to demonstrate (not just teach)
the platform:

  Step "Turn it ON"    (opens in the CODE EDITOR) — type one real line of
                       Arduino C++ by hand, then tap "Switch to Blocks" and
                       watch it become a block. This is the editor->blocks
                       direction.
  Step "Make it blink" (opens in BLOCKS)          — click-to-place a block
                       instead of typing (this platform uses click-to-select,
                       click-to-place — never drag-and-drop). Tap "Switch to
                       Editor" any time to see the exact code the block just
                       wrote. This is the blocks->editor direction, and the
                       explicit contrast with step 1 ("look how much faster
                       this was").

Each interactive step's drawer sim tab also invites active experimentation
("try changing HIGH to LOW and hit Run again") so a visitor can see wrong
code fail before they self-correct it, without any special comparison
widget — the sim already re-runs on whatever code currently exists.

No circuit_image / STEPS / wiring content on purpose: /try never renders
the interactive per-step breadboard build tab (see
docs/superpowers/specs/2026-07-09-try-page-infra-design.md's "SimEngine
only — no circuit renderer" section). The Welcome step does show a static
illustrative diagram of the same LED-on-pin-13 circuit via CircuitRenderer
(utils/demo_circuit.LED_DEMO_CIRCUIT) — that's a teaser graphic with no
STEPS/walkthrough behind it, same pattern splash.html already uses; it's
not the thing that spec section rules out.
"""

from utils.demo_circuit import LED_DEMO_CIRCUIT

META = {
    'title': 'Try It: Light It Up!',
    'circuit_image': None,
    'banner_image': None,
}

STEPS = []

SKETCH = """//>> Ready! | open | blocks
//## int ledPin = 13;
//>> Turn it ON | verify | editor | readonly:false | active:loop
void setup() {
  //## pinMode(ledPin, OUTPUT);
}
void loop() {
}
//==
//## int ledPin = 13;
void setup() {
  //## pinMode(ledPin, OUTPUT);
}
void loop() {
  digitalWrite(ledPin, HIGH);
}
//>> Make it blink! | guided | blocks
void setup() {
  //## pinMode(ledPin, OUTPUT);
}
void loop() {
  //## digitalWrite(ledPin, HIGH);
  //?? Wait half a second
  delay(500);
  //## digitalWrite(ledPin, LOW);
  //?? Wait half a second again
  delay(500);
}
//>> Mission Complete | open | blocks
"""

_SIM_TAB = {
    "label": "🎮 Try It",
    "type": "sim",
    "sim_config": {
        "mode": "code_driven",
        "endpoint": "/try/sim",
        "pins": {
            "13": {"type": "led", "color": "red", "label": "Try-It Light"}
        },
    },
}

# Static illustrative diagram of the LED-on-pin-13 circuit — the same
# physical circuit SimEngine is standing in for. Not tied to STEPS/wiring;
# just shows a visitor what a real KidsCode circuit looks like.
_CIRCUIT_TAB = {
    "label": "🔌 The Circuit",
    "type": "circuit",
    "content": (
        "<p>Here's the circuit behind this trial: one LED, one resistor, wired into pin 13.</p>"
        "<p>Every real KidsCode project comes with a diagram just like this one to follow — "
        "so once you're ready, you can build it for real on your own Arduino, with your own hands.</p>"
    ),
    "circuit_def": LED_DEMO_CIRCUIT,
}

DRAWER_CONTENT = {
    "project_try_it": {
        "steps": [
            {
                # Step 0 — "Ready!" (non-interactive, global-only)
                "title": "Welcome! 👋",
                "tip": "🚀 One real line of Arduino code. No download. No hardware. Just your browser.",
                "tabs": {
                    "explain": {
                        "label": "📖 What's happening",
                        "content": (
                            "<p>👋 Every KidsCode lesson gives you a real circuit and real Arduino code.</p>"
                            "<p>This trial skips building the circuit — no hardware needed right now. "
                            "Curious what it looks like? Switch to the 🔌 <b>The Circuit</b> tab above.</p>"
                            "<p>You'll jump straight to the fun part: making a program run. In under 5 minutes.</p>"
                            "<p>🔁 You'll do it twice, two different ways:</p>"
                            "<ul>"
                            "<li>⌨️ First, type one line of code by hand — like a real programmer.</li>"
                            "<li>🧩 Then, build the same idea again with blocks — click instead of type.</li>"
                            "</ul>"
                            "<p>By the end, you'll see code become blocks, and blocks become code. That's the whole idea behind KidsCode.</p>"
                            "<p>👉 Hit <b>Next</b> to get started.</p>"
                        ),
                    },
                    "circuit": _CIRCUIT_TAB,
                },
            },
            {
                # Step 1 — "Turn it ON" (view=editor: type real code first)
                "title": "Step 1 — Turn it ON 💡",
                "tip": "💡 Type one line into the code editor. Then switch to Blocks.",
                "tabs": {
                    "pitch": {
                        "label": "✨ Why this matters",
                        "content": (
                            "<p>You're in the <b>code editor</b> 👨‍💻 — the same place real Arduino programmers write code.</p>"
                            "<p>Look inside <code>loop()</code>. Find the blank line under the comment.</p>"
                            "<p>Type this:</p>"
                            "<p><code>digitalWrite(ledPin, HIGH);</code></p>"
                            "<p>That line means: \"send power to the LED pin.\" 💡</p>"
                            "<p>Tap <b>Switch to Blocks</b>. Watch your line turn into a block — automatically!</p>"
                            "<p>Blocks and code are always the same program. Just two different views.</p>"
                            "<p>🧭 Blocks view has 3 panels:</p>"
                            "<ul>"
                            "<li>🌐 <b>Global</b> — set up once, before anything runs.</li>"
                            "<li>⚙️ <b>setup()</b> — runs one time, right at the start.</li>"
                            "<li>🔁 <b>loop()</b> — runs forever. This is where your code just landed!</li>"
                            "</ul>"
                            "<p>Don't see your block? Click the <b>loop()</b> panel to open it.</p>"
                            "<p>🎮 Now open the <b>Try It</b> tab and press <b>RUN YOUR CODE</b>. Watch the light turn on!</p>"
                            "<p>Now try flipping <code>HIGH</code> to <code>LOW</code>:</p>"
                            "<ul>"
                            "<li>✏️ In the editor: edit the word directly.</li>"
                            "<li>🧩 In Blocks: click the dropdown on your block.</li>"
                            "</ul>"
                            "<p>Press <b>RUN YOUR CODE</b> again. One word changed. The result flipped!</p>"
                            "<p>That's the core loop of programming: change something small → run it → see what happens.</p>"
                            "<p>⚠️ Flip it back to <code>HIGH</code> before you tap <b>Complete Step</b>. The mission is to turn the light <i>on</i>.</p>"
                        ),
                    },
                    "howto": {
                        "label": "🔧 How To",
                        "content": (
                            "<ol>"
                            "<li>🔍 Find the blank line inside <code>loop()</code>, under the comment.</li>"
                            "<li>⌨️ Type: <code>digitalWrite(ledPin, HIGH);</code></li>"
                            "<li>🧩 Tap <b>Switch to Blocks</b>. Watch your line become a block.</li>"
                            "<li>🔁 Don't see it? Click the <b>loop()</b> panel — that's where your code lives.</li>"
                            "<li>🎮 Open <b>Try It</b> and press <b>RUN YOUR CODE</b>. The light turns on!</li>"
                            "<li>🔀 Try LOW instead: flip the block's dropdown (Blocks), or edit the word (editor). Run again — the light turns off.</li>"
                            "<li>✅ Set it back to <code>HIGH</code>. Tap <b>Complete Step</b>.</li>"
                            "</ol>"
                        ),
                    },
                    "sim": _SIM_TAB,
                },
            },
            {
                # Step 2 — "Make it blink!" (view=blocks: click-to-place)
                "title": "Step 2 — Make it blink! ✨",
                "tip": "🧩 Click blocks instead of typing. Watch how fast it is.",
                "tabs": {
                    "pitch": {
                        "label": "✨ Why this matters",
                        "content": (
                            "<p>Last step, you typed code by hand. This time: <b>blocks</b>. 🧩</p>"
                            "<p>Every block follows the same move:</p>"
                            "<ol>"
                            "<li>🔵 Click a blue box in the workspace.</li>"
                            "<li>🟣 It turns purple — selected!</li>"
                            "<li>🪣 Click the block you want in the bucket.</li>"
                            "<li>✨ It drops right in.</li>"
                            "</ol>"
                            "<p>No typing. No semicolons. No spelling.</p>"
                            "<p>⏱️ This step is different: <code>delay()</code> has a blank <i>inside</i> it.</p>"
                            "<p><code>delay()</code> pauses your program. But for how long? You have to say — in milliseconds. (1000 ms = 1 second.)</p>"
                            "<p>So <code>delay</code> needs that move done <b>twice</b>:</p>"
                            "<ol>"
                            "<li>🔵🟣🪣 Place the <code>delay</code> block the usual way.</li>"
                            "<li>🔎 Look inside it — there's a smaller empty box.</li>"
                            "<li>Click that box, then click <b>value</b> in the bucket's Expressions section.</li>"
                            "<li>⌨️ A number field appears. Type <code>500</code>.</li>"
                            "</ol>"
                            "<p>That empty box is called a <b>value</b>. Almost every useful block has one hiding inside it. Spotting them is a real programming skill!</p>"
                            "<p>🎮 Once both delays are placed and filled in, open <b>Try It</b> and press <b>RUN YOUR CODE</b>. Watch it blink!</p>"
                            "<p>🔬 Now experiment:</p>"
                            "<ul>"
                            "<li>Click a number field. Change <code>500</code>.</li>"
                            "<li>Try <code>100</code> — a fast, nervous blink. ⚡</li>"
                            "<li>Try <code>2000</code> — a slow, lazy blink. 🐢</li>"
                            "<li>Press <b>RUN YOUR CODE</b> again each time.</li>"
                            "</ul>"
                            "<p>Same blocks. Different number. Totally different rhythm.</p>"
                            "<p>✅ Set both numbers back to <code>500</code>. Then tap <b>Complete Step</b>.</p>"
                            "<p>Tip: tap <b>Switch to Editor</b> anytime to see the real code your blocks wrote.</p>"
                        ),
                    },
                    "howto": {
                        "label": "🔧 How To",
                        "content": (
                            "<ol>"
                            "<li>🔵 Click the highlighted blue box — it turns 🟣 purple.</li>"
                            "<li>🪣 Click <b>delay</b> in the bucket. It drops right in.</li>"
                            "<li>🔎 Click the empty box inside it.</li>"
                            "<li>🪣 Click <b>value</b> in the bucket's Expressions section.</li>"
                            "<li>⌨️ Type <code>500</code> into the number field.</li>"
                            "<li>🔁 Repeat steps 1–5 for the second highlighted box.</li>"
                            "<li>🎮 Open <b>Try It</b> and press <b>RUN YOUR CODE</b>. Watch it blink!</li>"
                            "<li>🔬 Change a number (try <code>100</code> or <code>2000</code>). Run again — hear the difference in speed.</li>"
                            "<li>✅ Set both numbers back to <code>500</code>. Tap <b>Complete Step</b>.</li>"
                            "</ol>"
                        ),
                    },
                    "sim": _SIM_TAB,
                },
            },
            {
                # Step 3 — "Mission Complete" — the conversion moment
                "title": "You did it! 🎉",
                "tip": "🎉 You just wrote and ran two real Arduino programs. With nothing but a browser.",
                "tabs": {
                    "explain": {
                        "label": "🚀 What's next",
                        "content": (
                            "<p>Look what you just did:</p>"
                            "<ul>"
                            "<li>💻 Controlled real hardware logic — in code <i>and</i> blocks.</li>"
                            "<li>⌨️ Typed a real line of C++.</li>"
                            "<li>🧩 Placed real blocks, including filling in a real value. (Plenty of adults trip on that one!)</li>"
                            "<li>🔬 Used a live simulator to test your own idea.</li>"
                            "</ul>"
                            "<p>That's the actual practice of programming. Not a preview of it. 🎯</p>"
                            "<p>Every KidsCode lesson builds on exactly this:</p>"
                            "<ul>"
                            "<li>🔌 A real circuit on your desk — real LED, real wires, real Arduino.</li>"
                            "<li>📖 A story to guide you.</li>"
                            "<li>🚀 Code that grows: buttons, sensors, sound, motors — even multi-part builds.</li>"
                            "</ul>"
                            "<p>More projects keep unlocking as you go.</p>"
                            "<p>🎮 Keep playing with the <b>Try It</b> tab below — it's still yours.</p>"
                            "<p>Ready to build for real? Sign up below. Or reach out with questions first. 👇</p>"
                        ),
                    },
                    "sim": _SIM_TAB,
                },
            },
        ]
    }
}

SKETCH_PRESET = {
    'sketch': SKETCH,
    'default_view': 'blocks',
    'read_only': False,
    'lock_view': False,
    'fill_values': True,
    'fill_conditions': True,
}

PROJECT = {
    "meta": META,
    "steps": STEPS,
    "drawer": DRAWER_CONTENT,
    "presets": {
        "default": SKETCH_PRESET,
    }
}
