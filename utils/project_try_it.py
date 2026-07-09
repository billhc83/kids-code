"""
utils/project_try_it.py — content for the anonymous /try trial page.

SCAFFOLD CONTENT: this is a real, working sketch (not a placeholder) used to
build and test the /try infrastructure end-to-end. The fully curated
try-it experience (copy, theming, step count) is an explicit follow-up
spec — see "Explicitly out of scope" in
docs/superpowers/specs/2026-07-09-try-page-infra-design.md.

No circuit_image / STEPS / wiring content on purpose: /try never renders
the breadboard circuit tab, only SimEngine (see the spec's "SimEngine
only — no circuit renderer" section).
"""

META = {
    'title': 'Try It: Light It Up!',
    'circuit_image': None,
    'banner_image': None,
}

STEPS = []

SKETCH = """void setup() {
}

void loop() {
}
//>> Ready! | open | blocks
//## int ledPin = 13;
//>> Turn it ON | guided | blocks
void setup() {
  //## pinMode(ledPin, OUTPUT);
}
void loop() {
  //?? Turn the LED on
}
//>> Make it blink! | guided | blocks
void setup() {
  //## pinMode(ledPin, OUTPUT);
}
void loop() {
  //## digitalWrite(ledPin, HIGH);
  //?? Wait half a second
  //## digitalWrite(ledPin, LOW);
  //?? Wait half a second again
}
//>> Mission Complete | open | blocks
"""

DRAWER_CONTENT = {
    "project_try_it": {
        "title": "Try It — Light It Up! 💡",
        "tip": "Place the blocks, hit Run, and watch the light react to your code.",
        "tabs": {
            "explain": {
                "label": "📖 What & Why",
                "content": (
                    "<p>Every Arduino project starts the same way: tell a pin what "
                    "it's for (<code>pinMode</code>), then turn it on or off "
                    "(<code>digitalWrite</code>). That's it — that's the whole "
                    "trick behind a blinking light.</p>"
                ),
            },
            "sim": {
                "label": "🎮 Try It",
                "type": "sim",
                "sim_config": {
                    "mode": "code_driven",
                    "endpoint": "/try/sim",
                    "pins": {
                        "13": {"type": "led", "color": "red", "label": "Try-It Light"}
                    },
                },
            },
        },
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
