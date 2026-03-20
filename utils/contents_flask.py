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