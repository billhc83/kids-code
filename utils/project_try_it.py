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
the breadboard circuit tab, only SimEngine (see
docs/superpowers/specs/2026-07-09-try-page-infra-design.md's "SimEngine
only — no circuit renderer" section).
"""

META = {
    'title': 'Try It: Light It Up!',
    'circuit_image': None,
    'banner_image': None,
}

STEPS = []

SKETCH = """//>> Ready! | open | blocks
//## int ledPin = 13;
//>> Turn it ON | guided | editor | readonly:false
void setup() {
  //## pinMode(ledPin, OUTPUT);
}
void loop() {
  //?? Turn the LED on
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

DRAWER_CONTENT = {
    "project_try_it": {
        "steps": [
            {
                # Step 0 — "Ready!" (non-interactive, global-only)
                "title": "Welcome! 👋",
                "tip": "You're about to write one real line of Arduino code — no download, no hardware, just your browser.",
                "tabs": {
                    "explain": {
                        "label": "📖 What's happening",
                        "content": (
                            "<p>Every KidsCode lesson gives you a real circuit to build "
                            "and real Arduino code to write. This trial skips the circuit "
                            "so you can jump straight to the fun part: making a light turn "
                            "on with code you write yourself.</p>"
                            "<p>Hit <b>Next</b> to get started.</p>"
                        ),
                    },
                },
            },
            {
                # Step 1 — "Turn it ON" (view=editor: type real code first)
                "title": "Step 1 — Turn it ON 💡",
                "tip": "Type the highlighted line into the code editor, then tap Switch to Blocks.",
                "tabs": {
                    "pitch": {
                        "label": "✨ Why this matters",
                        "content": (
                            "<p>You're looking at the <b>code editor</b> — the same place "
                            "professional programmers write Arduino code. Inside "
                            "<code>loop()</code> you'll see a highlighted comment, already "
                            "selected for you. Just start typing — it'll replace the "
                            "comment:</p>"
                            "<p><code>digitalWrite(ledPin, HIGH);</code></p>"
                            "<p>That single line means \"send power to the LED pin.\" Once "
                            "you've typed it, tap <b>Switch to Blocks</b> in the top bar — "
                            "watch the line you just typed turn into a block, automatically. "
                            "That's not a trick: blocks and code are always two views of the "
                            "exact same program.</p>"
                        ),
                    },
                    "howto": {
                        "label": "🔧 How To",
                        "content": (
                            "<ol>"
                            "<li>Look inside <code>loop()</code> — a highlighted comment marks the spot, already selected.</li>"
                            "<li>Just start typing: <code>digitalWrite(ledPin, HIGH);</code> (it replaces the comment automatically).</li>"
                            "<li>Tap <b>Switch to Blocks</b> in the top bar.</li>"
                            "<li>Tap <b>Complete Step</b> once your block appears.</li>"
                            "</ol>"
                        ),
                    },
                    "sim": _SIM_TAB,
                },
            },
            {
                # Step 2 — "Make it blink!" (view=blocks: click-to-place)
                "title": "Step 2 — Make it blink! ✨",
                "tip": "This time, click a block instead of typing — notice how much faster it is.",
                "tabs": {
                    "pitch": {
                        "label": "✨ Why this matters",
                        "content": (
                            "<p>Last step, you typed real code by hand. This time you'll "
                            "build with <b>blocks</b> instead: click a block in the palette "
                            "to select it, then click the highlighted spot to place it — no "
                            "typing, no worrying about semicolons or spelling.</p>"
                            "<p>Notice how much faster that is — but you're still building "
                            "the exact same program. Tap <b>Switch to Editor</b> any time to "
                            "see the real code your blocks just wrote. That's the whole idea: "
                            "blocks help you move fast and stay unstuck, while the code is "
                            "always right there when you're ready for it.</p>"
                        ),
                    },
                    "howto": {
                        "label": "🔧 How To",
                        "content": (
                            "<ol>"
                            "<li>Click the highlighted block slot to fill it in.</li>"
                            "<li>Click <b>delay</b> in the palette, then click the first highlighted spot.</li>"
                            "<li>Repeat for the second highlighted spot.</li>"
                            "<li>Tap <b>Complete Step</b> once both blocks are placed.</li>"
                            "</ol>"
                        ),
                    },
                    "sim": _SIM_TAB,
                },
            },
            {
                # Step 3 — "Mission Complete" — the conversion moment
                "title": "You did it! 🎉",
                "tip": "You just wrote and ran two real Arduino programs — with nothing but a browser.",
                "tabs": {
                    "explain": {
                        "label": "🚀 What's next",
                        "content": (
                            "<p>You just controlled real hardware logic, in both code and "
                            "blocks, with zero setup. Every KidsCode lesson builds on "
                            "exactly this — except with a real circuit on your desk and a "
                            "story to guide you through it.</p>"
                            "<p>Ready to keep building?</p>"
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
