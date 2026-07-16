
from utils.step_builder import build_step, intro_step, rect, circle, line, lbl
from utils.affiliate_kits import SONAR_KIT
from utils.image_utils import img_to_b64

META = {
    'title': 'Project 15: Backup Alarm',
    'circuit_image': "static/graphics/project_fifteen_circuit.png",
    'banner_image': 'backup_alarm_banner.png',
    'required_kits': SONAR_KIT,
}

STEPS = [
    intro_step(
        "Let's build our fifteenth project",
        "Press the next button for a step by step guide",
    ),

    build_step(
        "Place one leg of the 220 Ohm resistor in row 1, column D.<br>Place the other leg in row 5, column D.",
        "",
        rect(760, 490, 942, 587),
        greyout=True,
    ),

    build_step(
        "Place one leg of the 220 Ohm resistor in row 7, column D.<br>Place the other leg in row 11, column D.",
        "",
        rect(918, 495, 1111, 575),
        greyout=True,
    ),

    build_step(
        "Place one leg of the 220 Ohm resistor in row 13, column D.<br>Place the other leg in row 17, column D.",
        "",
        rect(1099, 502, 1255, 575),
        greyout=True,
    ),

    build_step(
        "Place the long leg of the LED in row 6, column E.<br>Place the short leg of the LED in row 5, column E.",
        "",
        rect(834, 267, 1019, 565),
        labels=[lbl("Long Leg", pos=(964, 462), font_size=16)],
        greyout=True,
    ),

    build_step(
        "Place the long leg of the LED in row 12, column E.<br>Place the short leg of the LED in row 11, column E.",
        "",
        rect(971, 262, 1183, 567),
        labels=[lbl("Long", pos=(1137, 493), font_size=16)],
        greyout=True,
    ),

    build_step(
        "Place the long leg of the LED in row 18, column E.<br>Place the short leg of the LED in row 17, column E.",
        "",
        rect(1120, 284, 1375, 558),
        labels=[lbl("Long", pos=(1265, 507), font_size=16)],
        greyout=True,
    ),

    build_step(
        "We have shown the wires in column G for clarity. Please place the wires in column J<br>It is important to not put wires in front of the sonar sensor.<br>Place the Vcc pin in row 23 column J. <br>Place the trig pin in row 24 column J.<br>Place the echo pin in row 25 column J.<br>Place the GND pin in row 26 column J.",
        "This is our sonar sensor",
        rect(1171, 87, 1676, 385),
        greyout=True,
    ),

    build_step(
        "Place the long leg of the buzzer in row 1, column J.<br>Place the short leg of the buzzer in row 4, column J.",
        "",
        rect(651, 204, 880, 397),
        labels=[lbl("Long", pos=(656, 320), font_size=16)],
        greyout=True,
    ),

    build_step(
        "Place one end of the wire in Arduino Pin 6.<br>Place the other end in row 6, column A.",
        "",
        line((495, 582), (935, 577), (935, 632), width=25),
        greyout=True,
    ),

    build_step(
        "Place one end of the wire in Arduino Pin 5.<br>Place the other end in row 12, column A.",
        "",
        line((502, 601), (654, 606), (654, 750), (1096, 745), (1094, 615), width=25),
        greyout=True,
    ),

    build_step(
        "Place one end of the wire in Arduino Pin 4.<br>Place the other end in row 18, column A.",
        "",
        line((498, 632), (625, 632), (625, 779), (1265, 779), (1260, 611), width=25),
        greyout=True,
    ),

    build_step(
        "Place one end of the wire in Arduino Pin 3.<br>Place the other end in row 1, column F.",
        "",
        line((575, 659), (380, 666), (375, 404), (803, 401), width=25),
        greyout=True,
    ),

    build_step(
        "Place one end of the wire in Arduino Pin GND.<br>Place the other end in row 4, column A.",
        "",
        line((10, 500), (125, 495), (127, 375), (853, 368), (853, 416), width=25),
        greyout=True,
    ),

    build_step(
        "Place one end of the wire in Arduino Pin 9.<br>Place the other end in row 24, column F.",
        "",
        line((481, 483), (1421, 481), (1421, 409), width=25),
        greyout=True,
    ),

    build_step(
        "Place one end of the wire in Arduino Pin 10.<br>Place the other end in row 25, column F.",
        "",
        line((493, 457), (1450, 457), (1447, 401), width=25),
        greyout=True,
    ),

    build_step(
        "Place one end of the wire in Arduino Pin 5V.<br>Place the other end in row 23, column F.",
        "",
        line((2, 474), (649, 426), (1394, 428), width=25),
        greyout=True,
    ),

    build_step(
        "Place one end of the wire in Arduino Pin GND.<br>Place the other end in row 26, column F.",
        "",
        line((522, 356), (685, 250), (1584, 250), (1584, 428), (1476, 430), width=25),
        greyout=True,
    ),

    build_step(
        "Place one end of the wire in Arduino Pin GND.<br>Place the other end in the negative / - rail.",
        "",
        line((14, 522), (356, 700), (815, 700), width=25),
        greyout=True,
    ),

    build_step(
        "Place one end of the wire in row 1, column A.<br>Place the other end in the negative / - rail.",
        "",
        line((791, 611), (841, 716), width=25),
        greyout=True,
    ),

    build_step(
        "Place one end of the wire in row 7, column A.<br>Place the other end in the negative / - rail.",
        "",
        line((954, 606), (1010, 712), width=25),
        greyout=True,
    ),

    build_step(
        "Place one end of the wire in row 13, column A.<br>Place the other end in the negative / - rail.",
        "",
        line((1111, 615), (1173, 709), width=25),
        greyout=True,
    ),

]

backup_circuit_b64 = img_to_b64("static/graphics/project_fifteen_circuit.png")

SIM_LIGHTS_ONLY = {
    "mode": "interpreted",
    "components": [
        {"type": "led",    "id": "greenLED",  "color": "green",  "pin": 4, "label": "Green"},
        {"type": "led",    "id": "yellowLED", "color": "yellow", "pin": 5, "label": "Yellow"},
        {"type": "led",    "id": "redLED",    "color": "red",    "pin": 6, "label": "Red"},
        {"type": "buzzer", "id": "buz1",                          "pin": 3, "label": "Buzzer"},
    ],
}

SIM_FULL = {
    "mode": "interpreted",
    "components": [
        {"type": "sonar",  "id": "sonar1",    "label": "Distance Sensor", "pin_trig": 9, "pin_echo": 10},
        {"type": "led",    "id": "greenLED",  "color": "green",  "pin": 4, "label": "Safe"},
        {"type": "led",    "id": "yellowLED", "color": "yellow", "pin": 5, "label": "Warning"},
        {"type": "led",    "id": "redLED",    "color": "red",    "pin": 6, "label": "Danger"},
        {"type": "buzzer", "id": "buz1",                         "pin": 3, "label": "Buzzer"},
    ],
}

DRAWER_CONTENT = {

 "project_fifteen": {
  "steps": [

{
    "title": "Step 1 — System Memory 📦",
    "tip": "Set up your system's memory so it knows what everything is.",
    "tabs": {
        "explain": {
            "label": "📖 What & Why",
            "content": "<p>Every build starts with a parts list. Before your backup alarm can measure anything or light anything up, your program needs its own list — a set of <strong>variables</strong> (labels that hold a piece of information your program can look up and change later, similar to a labeled fuse box in a car).</p><p>This step creates eight labels: one for each pin your sensor, buzzer, and LEDs are wired to, plus two more to store the readings your sensor will take later.</p><p>Skip this step and every later step breaks — your code has no way to say \"turn on the buzzer\" without a label pointing at the right pin.</p>",
            "image_b64": backup_circuit_b64
        },
        "howto": {
            "label": "🔧 How To",
            "content": "<p>Each variable needs a name, a type (what kind of value it holds), and a starting value. Here's all eight:</p><ol><li><strong>trigPin</strong> — Sends the sensor's measuring pulse out. It's an integer (whole-number) variable, set to <strong>9</strong> to match Arduino pin 9 from your wiring.</li><li><strong>echoPin</strong> — Listens for the pulse bouncing back. Integer, set to <strong>10</strong>, matching pin 10.</li><li><strong>buzzerPin</strong> — Controls your alarm's sound. Integer, set to <strong>3</strong>, matching pin 3.</li><li><strong>greenLED</strong> — Your safe-zone light. Integer, set to <strong>4</strong>.</li><li><strong>yellowLED</strong> — Your warning light. Integer, set to <strong>5</strong>.</li><li><strong>redLED</strong> — Your danger light. Integer, set to <strong>6</strong>.</li><li><strong>duration</strong> — Will store how long the sensor's pulse takes to bounce back, in microseconds. It's a <em>long</em> variable (like an integer, but built for bigger numbers) since timing values can get large. Starts at <strong>0</strong> since no reading has happened yet.</li><li><strong>distance</strong> — Will store the calculated distance in centimeters once you do the math in a later step. Integer, starts at <strong>0</strong>.</li></ol>"
        },
        "logic": {
            "label": "🧠 Logic",
            "content": "<p>Think of this like a pit crew labeling every gauge on a race car's dashboard before the race starts. A crew that knows exactly which gauge shows fuel and which shows temperature can react instantly — your program needs the same clear labels before it can react to anything.</p>"
        }
    }
},

{
    "title": "Step 2 — Activate the System ⚙️",
    "tip": "Tell your system what each part is supposed to do.",
    "tabs": {
        "explain": {
            "label": "📖 What & Why",
            "content": "<p>Your variables are labeled, but Arduino still doesn't know whether each pin should be sending signals out or listening for them. This step configures every pin's <strong>mode</strong> — OUTPUT for parts that send power (the buzzer, the LEDs, the sensor's trigger pin) and INPUT for the one part that receives a signal (the sensor's echo pin).</p><p>This all happens inside <strong>setup()</strong>, a block of code that runs exactly once when your Arduino powers on — like a car's dashboard doing a quick systems check the moment you turn the key.</p><p>Get a pin mode backwards here and that part simply won't work later, even if the rest of your code is perfect.</p>"
        },
        "howto": {
            "label": "🔧 How To",
            "content": "<ol><li><strong>trigPin</strong> — Set its mode to <strong>OUTPUT</strong>, since your Arduino needs to send a pulse out through it.</li><li><strong>echoPin</strong> — Set its mode to <strong>INPUT</strong>, since this pin only ever receives the sensor's returning pulse.</li><li><strong>buzzerPin</strong> — <strong>OUTPUT</strong>, since Arduino sends power to it to make sound.</li><li><strong>greenLED</strong> — <strong>OUTPUT</strong>.</li><li><strong>yellowLED</strong> — <strong>OUTPUT</strong>.</li><li><strong>redLED</strong> — <strong>OUTPUT</strong>.</li></ol><p>You'll also see <code>Serial.begin(9600)</code> already in place — this turns on a communication channel between your Arduino and your computer, which some later steps use to double-check readings.</p>"
        },
        "logic": {
            "label": "🧠 Logic",
            "content": "<p>This is like a stage manager checking every microphone and speaker before a concert — deciding which ones will pick up sound (INPUT) and which ones will play sound (OUTPUT). Mix that up and the whole show falls apart.</p>"
        }
    }
},

{
    "title": "Step 3 — Light It Up ✨",
    "tip": "Prove your circuit works before you make it smart.",
    "tabs": {
        "explain": {
            "label": "📖 What & Why",
            "content": "<p>Before your alarm can react to anything, let's prove the wiring itself is solid. Real engineers do this too — before adding any decision-making logic, they run a basic test to confirm every part responds when powered.</p><p>This step turns all three LEDs and the buzzer on at the same time, with no conditions attached. If your circuit is wired correctly, you'll see every light and hear the buzzer the moment this code runs.</p><p>Don't worry that this isn't \"smart\" yet — you're about to spend the next several steps teaching your sensor to measure distance, and a few steps after that, you'll come back and turn this into a real reacting alarm.</p><p>🎮 <strong>Try It:</strong> Open the Try It tab now. You should see all three LEDs lit and the buzzer playing a steady 1000 Hz tone — no sensor involved yet, because you haven't wired one into the logic. If everything's lit, your circuit and this step's code both check out.</p>"
        },
        "howto": {
            "label": "🔧 How To",
            "content": "<ol><li><strong>Green LED ON</strong> — Turn greenLED to HIGH (this block sends full power to a pin, the opposite of LOW). You'll see the green light switch on.</li><li><strong>Yellow LED ON</strong> — Same block, applied to yellowLED.</li><li><strong>Red LED ON</strong> — Same block, applied to redLED.</li><li><strong>Buzzer ON</strong> — Use the tone block, which needs two values: the pin (buzzerPin) and a frequency in Hz (how fast the sound wave vibrates — higher numbers sound higher-pitched). Use <strong>1000</strong> Hz.</li></ol>"
        },
        "logic": {
            "label": "🧠 Logic",
            "content": "<p>This is exactly what a pit crew does before a race — floor every gauge and light to make sure the electrics are good, before worrying about how the car should react on track. Confirm the parts work, then teach them when to work.</p>"
        },
        "sim": {"label": "🎮 Try It", "type": "sim", "sim_config": SIM_LIGHTS_ONLY}
    }
},

{
    "title": "Step 4 — Prepare the Sensor 📡",
    "tip": "Reset the sensor before sending a signal.",
    "tabs": {
        "explain": {
            "label": "📖 What & Why",
            "content": "<p>Your lights and buzzer are proven to work — now it's time to teach the system how to actually measure distance. Your ultrasonic sensor (a device that measures distance using sound waves too high-pitched for humans to hear) works by sending a burst of sound and timing how long it takes to bounce back.</p><p>Before sending a fresh pulse, we need the trigger pin to start from a clean OFF state and give the sensor a tiny pause to settle. Skip this reset and leftover signal from a previous reading can throw off the next measurement.</p><p>Your lights are still on in the background from the last step — we're not touching them again until the sensor's measurements are ready to control them.</p>"
        },
        "howto": {
            "label": "🔧 How To",
            "content": "<ol><li><strong>Set trigPin LOW</strong> — Use digitalWrite (a block that sets a pin's power level) with the value LOW, which means \"no power.\" This clears any leftover signal from the trigger pin.</li><li><strong>Small delay</strong> — Use delayMicroseconds (a pause measured in millionths of a second — much shorter than the delay block you may have used before, which pauses in milliseconds). Set it to <strong>2</strong> microseconds, just enough for the sensor to settle.</li></ol>"
        },
        "logic": {
            "label": "🧠 Logic",
            "content": "<p>Think of this like a swimmer shaking out their arms right before diving in — a tiny reset that clears tension so the next move is clean. Your sensor needs the same brief pause before it can send an accurate signal.</p>"
        }
    }
},

{
    "title": "Step 5 — Send the Signal 🚀",
    "tip": "Send out a quick signal to measure distance.",
    "tabs": {
        "explain": {
            "label": "📖 What & Why",
            "content": "<p>With the trigger pin reset, it's time to actually send the measuring pulse. Your sensor sends a burst of sound by briefly switching the trigger pin ON, then quickly back OFF — a signal so short it's measured in millionths of a second.</p><p>This tiny pulse is what starts the whole measurement: the moment it fires, the sensor begins listening for the sound to bounce off something and return.</p>"
        },
        "howto": {
            "label": "🔧 How To",
            "content": "<ol><li><strong>Set trigPin HIGH</strong> — digitalWrite, value HIGH. This fires the pulse.</li><li><strong>Wait 10 microseconds</strong> — delayMicroseconds, value <strong>10</strong>. This is the exact pulse width the HC-SR04 sensor (the sensor model wired into your circuit) needs to register a clean signal.</li><li><strong>Set trigPin LOW</strong> — digitalWrite, value LOW. This ends the pulse.</li></ol>"
        },
        "logic": {
            "label": "🧠 Logic",
            "content": "<p>This is like a coach's short, sharp whistle blast to start a race — not a long note, just a quick, clear signal that kicks things off. Hold the whistle too long and you'd miss timing the runners; your sensor's pulse works the same way.</p>"
        }
    }
},

{
    "title": "Step 6 — Listen for the Echo 👂",
    "tip": "Measure how long it takes for the signal to return.",
    "tabs": {
        "explain": {
            "label": "📖 What & Why",
            "content": "<p>Your sensor sent its signal in the last step — now it needs to listen for that signal to return. The time between sending and receiving is the raw ingredient every distance sensor depends on: sound travels at a known, steady speed, so timing its round trip tells you how far it traveled.</p><p>This measurement is precise enough that it's handled automatically rather than block-by-block — check the How To tab to see exactly what's happening.</p>"
        },
        "howto": {
            "label": "🔧 How To",
            "content": "<p>This step is handled automatically, because timing a returning sound wave to the microsecond isn't something you'd build block-by-block — Arduino has a purpose-built tool for exactly this.</p><p>The locked code uses <strong>pulseIn</strong>, a block built specifically for this kind of ultrasonic sensor. It watches echoPin (the pin your sensor sends its return signal on) and waits for it to go HIGH — the moment the sound wave arrives back. It then measures exactly how long that HIGH signal lasted, in microseconds, and stores that number in <strong>duration</strong>, the variable you created back in Step 1.</p><p>If nothing is close enough to bounce the sound back, pulseIn eventually gives up and returns <strong>0</strong> — you'll use that exact detail in the very next step.</p><p>You now have a real, live measurement stored in duration. The next step turns that raw timing number into an actual distance in centimeters.</p>"
        },
        "logic": {
            "label": "🧠 Logic",
            "content": "<p>This is like timing an echo in a canyon — shout, count the seconds until it returns, and you can work out how far away the canyon wall is. Your sensor \"shouts\" with sound waves instead of a voice, but the idea is identical.</p>"
        }
    }
},

{
    "title": "Step 7 — Calculate Distance 📏",
    "tip": "Turn time into a real-world distance.",
    "tabs": {
        "explain": {
            "label": "📖 What & Why",
            "content": "<p>You now have a raw timing number in duration — but \"4,706 microseconds\" doesn't mean much to a driver. This step converts that timing into an actual distance in centimeters, using the fact that sound travels through air at a known, steady speed.</p><p>There's one edge case to handle first: if nothing was close enough to bounce the signal back, pulseIn returns exactly 0 (as you saw in the last step) — and 0 microseconds obviously doesn't mean \"the object is 0cm away.\" It means the opposite: nothing detected, so treat the object as very far away.</p>"
        },
        "howto": {
            "label": "🔧 How To",
            "content": "<ol><li><strong>If no echo received</strong> — Use an if block (checks a condition, and only runs the code inside it when that condition is true) checking whether duration equals 0.</li><li><strong>Set distance to a far value</strong> — Inside that if, set distance to <strong>999</strong> — a placeholder far outside any real reading, so \"nothing detected\" always counts as safe.</li></ol><p>The locked else branch handles the normal case: <code>distance = duration * 0.034 / 2</code>. 0.034 is the speed of sound in centimeters per microsecond, and dividing by 2 accounts for the sound traveling to the object <em>and back</em> — you only want the one-way distance.</p>"
        },
        "logic": {
            "label": "🧠 Logic",
            "content": "<p>This is like a rally co-driver converting \"it took 3 seconds to hear the echo off that cliff\" into an actual distance in meters — same raw timing, just translated into units a driver can actually act on.</p>"
        }
    }
},

{
    "title": "Step 8 — Safe Zone Check 🟢",
    "tip": "Decide when everything is safe.",
    "tabs": {
        "explain": {
            "label": "📖 What & Why",
            "content": "<p>Your system now knows the real distance to whatever's behind the car — but knowing a number isn't the same as reacting to it. This step adds your first real decision: an if block that asks \"is the object far enough away to be safe?\"</p><p>Right now this decision doesn't do anything yet — the block's body is empty. In the very next step, you'll reconnect it to your lights and buzzer from Step 3, so hang on for that.</p>"
        },
        "howto": {
            "label": "🔧 How To",
            "content": "<ol><li><strong>If distance greater than 50</strong> — Use an if block checking whether distance is greater than <strong>50</strong> (centimeters). 50cm is roughly arm's length — close enough to react to, far enough that there's no rush yet.</li></ol><p>Nothing goes inside it yet — you're just building the question. The answer comes next.</p>"
        },
        "logic": {
            "label": "🧠 Logic",
            "content": "<p>This is like a driver's mirror check before reversing — glancing back and asking \"is anything close?\" before deciding whether to worry. Right now your system is only asking the question; it hasn't decided how to react yet.</p>"
        }
    }
},

{
    "title": "Step 9 — Reconnect the Lights 🟢",
    "tip": "Turn your always-on lights into a real reaction.",
    "tabs": {
        "explain": {
            "label": "📖 What & Why",
            "content": "<p>Remember Step 3, where you turned all three LEDs and the buzzer on permanently, just to prove the wiring worked? Those lines of code are still sitting in your program, running every single time through the loop — they just haven't been touched since.</p><p>This step moves them inside the \"is it safe?\" question you built in Step 8. Once they're inside, they'll only run when the condition is actually true — which means your lights finally start reacting to something instead of just sitting on forever.</p><p>There's a change to make while you move them: \"safe\" shouldn't mean all three lights on — it should mean <strong>only</strong> the green light on. So the yellow and red lights, and the buzzer, need to flip from ON to OFF inside this block.</p><p>🎮 <strong>Try It:</strong> Slide the distance sensor to somewhere past 50cm — you should see only the green light on, buzzer silent. That's a big change from Step 3's \"everything on\" test! Now slide it in close, under 50cm — notice everything goes dark. That's not a bug: you haven't taught your alarm what \"close\" or \"very close\" means yet. That's exactly what the next few steps build.</p>"
        },
        "howto": {
            "label": "🔧 How To",
            "content": "<ol><li><strong>Turn buzzer OFF</strong> — Use the noTone block (the opposite of tone) on buzzerPin. When it's safe, there's nothing to warn about.</li><li><strong>Green LED stays ON</strong> — This line carries over unchanged from Step 3 — green already meant \"good,\" so it doesn't need to flip.</li><li><strong>Turn yellow LED OFF</strong> — digitalWrite, value LOW. In Step 3 this was HIGH; now that it's inside the safe-zone condition, it needs to flip to LOW so only green shows.</li><li><strong>Turn red LED OFF</strong> — digitalWrite, value LOW, same reasoning as yellow.</li></ol>"
        },
        "logic": {
            "label": "🧠 Logic",
            "content": "<p>This is like a race car's pit board — the crew doesn't hold up every signal at once, they show the driver exactly one message that matches the current situation. Your lights are learning the same lesson: show one true answer, not everything at once.</p>"
        },
        "sim": {"label": "🎮 Try It", "type": "sim", "sim_config": SIM_FULL}
    }
},

{
    "title": "Step 10 — Warning Zone Check 🟡",
    "tip": "Detect when things are getting closer.",
    "tabs": {
        "explain": {
            "label": "📖 What & Why",
            "content": "<p>Not every distance is either perfectly safe or full-blown danger — there's a middle zone where a driver should start paying attention. This step adds a second question using <strong>else if</strong> (a block that only gets checked when the first if's condition was false), asking \"is the object getting close, but not too close yet?\"</p><p>Just like Step 8, this step only builds the question — the reaction comes in the next step.</p>"
        },
        "howto": {
            "label": "🔧 How To",
            "content": "<ol><li><strong>Else if distance greater than 20</strong> — Use an else if block checking whether distance is greater than <strong>20</strong> centimeters. Since this only gets checked when the safe-zone condition was false, it effectively means \"between 20 and 50cm.\"</li></ol>"
        },
        "logic": {
            "label": "🧠 Logic",
            "content": "<p>This is like a video game giving you a warning beep when your health drops below a threshold, but before it's actually critical — a heads-up zone between \"fine\" and \"danger,\" giving you a chance to react early.</p>"
        }
    }
},

{
    "title": "Step 11 — Warning Zone Response 🟡",
    "tip": "Alert the driver with a repeating beep.",
    "tabs": {
        "explain": {
            "label": "📖 What & Why",
            "content": "<p>Now let's give the warning zone an actual reaction. Unlike the danger zone (which you'll build soon), a warning shouldn't be a constant, urgent sound — it should be a noticeable but calmer repeating beep, paired with the yellow light.</p><p>You'll build this beep using tone, a short pause, noTone, another short pause — on, off, on, off — which is exactly how a real \"beep… beep… beep…\" warning sound is built.</p><p>🎮 <strong>Try It:</strong> Head back to Try It and slide the sensor into the 20–50cm range — you'll hear a repeating beep and see the yellow light, right alongside the green-only behavior you already built for anything past 50cm. Notice the safe zone still works exactly like it did last time — you've added a whole new zone without breaking the one before it.</p>"
        },
        "howto": {
            "label": "🔧 How To",
            "content": "<ol><li><strong>Turn buzzer ON (1000 Hz)</strong> — tone block, buzzerPin, frequency <strong>1000</strong> Hz.</li><li><strong>Delay 300ms</strong> — delay (a pause measured in milliseconds — a thousand times longer than the microsecond delays from your sensor steps), value <strong>300</strong>.</li><li><strong>Turn buzzer OFF</strong> — noTone, buzzerPin.</li><li><strong>Delay 300ms</strong> — delay, value <strong>300</strong> again, completing the \"on, pause, off, pause\" beep cycle.</li><li><strong>Turn green LED OFF</strong> — digitalWrite, value LOW.</li><li><strong>Turn yellow LED ON</strong> — digitalWrite, value HIGH.</li><li><strong>Turn red LED OFF</strong> — digitalWrite, value LOW.</li></ol>"
        },
        "logic": {
            "label": "🧠 Logic",
            "content": "<p>This is like a car's turn signal — not a constant sound, but a steady, repeating pulse designed to catch your attention without being alarming. A warning should feel different from an emergency, and the repeating beep does exactly that.</p>"
        },
        "sim": {"label": "🎮 Try It", "type": "sim", "sim_config": SIM_FULL}
    }
},

{
    "title": "Step 12 — Danger Zone 🚨",
    "tip": "Trigger a constant alert when too close.",
    "tabs": {
        "explain": {
            "label": "📖 What & Why",
            "content": "<p>This is the final zone — and the moment your alarm becomes a complete, working system. Anything not caught by the safe or warning conditions falls into this last case, using <strong>else</strong> (the block that runs when every earlier if/else if condition was false) — meaning you don't even need to check a number here, since anything this close has already failed both earlier tests.</p><p>Unlike the warning beep, danger needs urgency: a constant tone instead of a repeating one, and the red light instead of yellow.</p><p>🎮 <strong>Try It:</strong> This is the big one — slide the sensor through the full range. Past 50cm: green only. Between 20–50cm: yellow, beeping. Under 20cm: red, with a steady higher-pitched tone. All three zones, working together for the first time, exactly like a real car's backup sensor.</p>"
        },
        "howto": {
            "label": "🔧 How To",
            "content": "<ol><li><strong>Turn buzzer ON (1500 Hz)</strong> — tone block, buzzerPin, frequency <strong>1500</strong> Hz — higher-pitched than the warning zone's 1000 Hz, so it's instantly distinguishable by ear.</li><li><strong>Turn green LED OFF</strong> — digitalWrite, LOW.</li><li><strong>Turn yellow LED OFF</strong> — digitalWrite, LOW.</li><li><strong>Turn red LED ON</strong> — digitalWrite, HIGH.</li></ol><p>Notice there's no delay/noTone pattern here like the warning zone had — the tone just stays on continuously, which is exactly what makes it read as more urgent.</p>"
        },
        "logic": {
            "label": "🧠 Logic",
            "content": "<p>This is like the difference between a car's turn signal and its collision-warning alarm — one is a calm, repeating pulse, the other is a constant, impossible-to-ignore tone. Same buzzer, same LEDs, but the pattern itself communicates how serious the situation is.</p>"
        },
        "sim": {"label": "🎮 Try It", "type": "sim", "sim_config": SIM_FULL}
    }
},

{
    "title": "Step 13 — System Loop 🔁",
    "tip": "Keep the system running smoothly.",
    "tabs": {
        "explain": {
            "label": "📖 What & Why",
            "content": "<p>Your alarm's logic is complete — this last step just makes it run smoothly. Right now your loop repeats as fast as Arduino can possibly execute it, which can make sensor readings jittery and unstable.</p><p>A short pause at the end of each loop gives the sensor time to settle before the next measurement, the same way you gave it a tiny pause back in Step 4.</p>"
        },
        "howto": {
            "label": "🔧 How To",
            "content": "<ol><li><strong>Small delay for stability</strong> — delay block, value <strong>50</strong> milliseconds, added at the very end of loop(). Short enough that the alarm still feels instant to a driver, long enough to steady the readings.</li></ol>"
        },
        "logic": {
            "label": "🧠 Logic",
            "content": "<p>This is like a car's suspension smoothing out small bumps in the road — the system underneath is already working, this step just takes the jitter out of it.</p>"
        }
    }
},

{
    "title": "Step 14 — Mission Complete 🎉",
    "tip": "Your backup alarm system is fully operational!",
    "tabs": {
        "explain": {
            "label": "📖 What You Built",
            "content": "<p>🚗 Congratulations, Engineer! You designed and built a complete smart backup alarm — sensing distance, making decisions, and reacting with lights and sound, just like a real car's system.</p><p>Your system can now:</p><ul><li>📡 Measure real-world distance using an ultrasonic sensor</li><li>🧠 Make three-way decisions using if / else if / else</li><li>💡 Show safe, warning, and danger zones using LEDs</li><li>🔊 Alert the driver with two different sound patterns</li><li>✨ Start from a proven-working circuit and build logic on top of it, one working piece at a time</li></ul><p>You didn't just copy code — you tested your wiring first, then taught your system to think.</p>"
        },
        "howto": {
            "label": "🔧 Try This Next",
            "content": "<p>Now that your system works, here are some ideas to make it even better:</p><ul><li>⚡ <strong>Change the zone distances</strong> — try 40cm and 15cm instead of 50 and 20, and see how it changes the feel.</li><li>🔊 <strong>Speed up the warning beep</strong> — shrink the 300ms delays as distance decreases, so the beep gets faster the closer you get.</li><li>🌈 <strong>Add a fourth LED</strong> — split the warning zone into \"getting close\" and \"really close\" with an extra color.</li><li>📟 <strong>Print the distance to Serial</strong> — use Serial.println(distance) so you can watch the exact numbers as you test.</li><li>🎮 <strong>Turn it into a game</strong> — build a \"don't get caught\" challenge where a player tries to stay in the safe zone as long as possible.</li></ul><p>Experimenting is how real engineers improve their designs.</p>"
        },
        "logic": {
            "label": "🧠 What You Learned",
            "content": "<p>This project brought together everything you've been building toward:</p><ul><li>📦 <strong>Variables</strong> — labels that store and update information your program needs.</li><li>⚙️ <strong>Setup</strong> — configuring your hardware once, before the real logic runs.</li><li>📡 <strong>Sensors</strong> — turning a real-world signal (sound timing) into a usable number.</li><li>🧠 <strong>Conditional logic</strong> — if / else if / else, letting your program choose between multiple reactions.</li><li>💡 <strong>Outputs</strong> — controlling LEDs and a buzzer to communicate a decision.</li><li>🔁 <strong>Loops</strong> — running the same logic continuously, the way a real system never really \"finishes.\"</li></ul><p>You built something that senses, thinks, and reacts — you're thinking like an engineer now. 🚀</p>"
        },
        "sim": {"label": "🎮 Try It", "type": "sim", "sim_config": SIM_FULL}
    }
}

    ]
  }
}

SKETCH_PRESET = {
    'sketch': """
//>> Step 1 - Define Global Variables | guided | blocks | filter:true

//?? Define trigPin
int trigPin = 9;

//?? Define echoPin
int echoPin = 10;

//?? Define buzzerPin
int buzzerPin = 3;

//?? Define greenLED
int greenLED = 4;

//?? Define yellowLED
int yellowLED = 5;

//?? Define redLED
int redLED = 6;

//?? Define duration
long duration = 0;

//?? Define distance
int distance = 0;

void setup() {
    }
void loop() {
    }

//>> Step 2 - Setup the System | guided

void setup() {
  //?? Set trigPin as OUTPUT
  pinMode(trigPin, OUTPUT);

  //?? Set echoPin as INPUT
  pinMode(echoPin, INPUT);

  //?? Set buzzerPin as OUTPUT
  pinMode(buzzerPin, OUTPUT);

  //?? Set greenLED as OUTPUT
  pinMode(greenLED, OUTPUT);

  //?? Set yellowLED as OUTPUT
  pinMode(yellowLED, OUTPUT);

  //?? Set redLED as OUTPUT
  pinMode(redLED, OUTPUT);

  Serial.begin(9600);
}

void loop() {
}

//>> Step 3 - Light It Up | guided

void loop() {
  //?? Turn green LED ON
  digitalWrite(greenLED, HIGH);

  //?? Turn yellow LED ON
  digitalWrite(yellowLED, HIGH);

  //?? Turn red LED ON
  digitalWrite(redLED, HIGH);

  //?? Turn buzzer ON (1000 Hz)
  tone(buzzerPin, 1000);
}

//>> Step 4 - Prepare Sensor | guided

void loop() {
  //?? Set trigPin LOW
  digitalWrite(trigPin, LOW);

  //?? Small delay
  delayMicroseconds(2);

  //## digitalWrite(greenLED, HIGH);
  //## digitalWrite(yellowLED, HIGH);
  //## digitalWrite(redLED, HIGH);
  //## tone(buzzerPin, 1000);
}

//>> Step 5 - Send Pulse | guided

void loop() {
  //## digitalWrite(trigPin, LOW);
  //## delayMicroseconds(2);

  //?? Set trigPin HIGH
  digitalWrite(trigPin, HIGH);

  //?? Wait 10 microseconds
  delayMicroseconds(10);

  //?? Set trigPin LOW
  digitalWrite(trigPin, LOW);

  //## digitalWrite(greenLED, HIGH);
  //## digitalWrite(yellowLED, HIGH);
  //## digitalWrite(redLED, HIGH);
  //## tone(buzzerPin, 1000);
}

//>> Step 6 - Read Echo | free

void loop() {
  //## digitalWrite(trigPin, LOW);
  //## delayMicroseconds(2);
  //## digitalWrite(trigPin, HIGH);
  //## delayMicroseconds(10);
  //## digitalWrite(trigPin, LOW);

  //## Read duration from echoPin
  duration = pulseIn(echoPin, HIGH);

  //## digitalWrite(greenLED, HIGH);
  //## digitalWrite(yellowLED, HIGH);
  //## digitalWrite(redLED, HIGH);
  //## tone(buzzerPin, 1000);
}

//>> Step 7 - Calculate Distance | guided | blocks | filter:true

void loop() {
  //## digitalWrite(trigPin, LOW);
  //## delayMicroseconds(2);
  //## digitalWrite(trigPin, HIGH);
  //## delayMicroseconds(10);
  //## digitalWrite(trigPin, LOW);
  //## duration = pulseIn(echoPin, HIGH);

  //?? If no echo received
  if (duration == 0) {
    //?? Set distance to a far value
    distance = 999;
  }
  else {
    //## distance = duration * 0.034 / 2;
  }

  //## digitalWrite(greenLED, HIGH);
  //## digitalWrite(yellowLED, HIGH);
  //## digitalWrite(redLED, HIGH);
  //## tone(buzzerPin, 1000);
}

//>> Step 8 - Safe Zone Check | guided | blocks | filter:true

void loop() {
  //## digitalWrite(trigPin, LOW);
  //## delayMicroseconds(2);
  //## digitalWrite(trigPin, HIGH);
  //## delayMicroseconds(10);
  //## digitalWrite(trigPin, LOW);
  //## duration = pulseIn(echoPin, HIGH);
  //## if (duration == 0) {
  //##   distance = 999;
  //## }
  //## else {
  //##   distance = duration * 0.034 / 2;
  //## }

  //?? If distance > 50
  if (distance > 50) {
  }

  //## digitalWrite(greenLED, HIGH);
  //## digitalWrite(yellowLED, HIGH);
  //## digitalWrite(redLED, HIGH);
  //## tone(buzzerPin, 1000);
}

//>> Step 9 - Make Safe Mean Only Green | guided

void loop() {
  //## digitalWrite(trigPin, LOW);
  //## delayMicroseconds(2);
  //## digitalWrite(trigPin, HIGH);
  //## delayMicroseconds(10);
  //## digitalWrite(trigPin, LOW);
  //## duration = pulseIn(echoPin, HIGH);
  //## if (duration == 0) {
  //##   distance = 999;
  //## }
  //## else {
  //##   distance = duration * 0.034 / 2;
  //## }
  //## if (distance > 50) {

  //?? Turn buzzer OFF
  noTone(buzzerPin);

  //## digitalWrite(greenLED, HIGH);

  //?? Turn yellow LED OFF
  digitalWrite(yellowLED, LOW);

  //?? Turn red LED OFF
  digitalWrite(redLED, LOW);

  //## }
}

//>> Step 10 - Warning Zone Check | guided | blocks | filter:true

void loop() {
  //## digitalWrite(trigPin, LOW);
  //## delayMicroseconds(2);
  //## digitalWrite(trigPin, HIGH);
  //## delayMicroseconds(10);
  //## digitalWrite(trigPin, LOW);
  //## duration = pulseIn(echoPin, HIGH);
  //## if (duration == 0) {
  //##   distance = 999;
  //## }
  //## else {
  //##   distance = duration * 0.034 / 2;
  //## }
  //## if (distance > 50) {
  //##   noTone(buzzerPin);
  //##   digitalWrite(greenLED, HIGH);
  //##   digitalWrite(yellowLED, LOW);
  //##   digitalWrite(redLED, LOW);
  //## }

  //?? Else if distance > 20
  else if (distance > 20) {
  }
}

//>> Step 11 - Warning Zone Output | guided | filter:true

void loop() {
  //## digitalWrite(trigPin, LOW);
  //## delayMicroseconds(2);
  //## digitalWrite(trigPin, HIGH);
  //## delayMicroseconds(10);
  //## digitalWrite(trigPin, LOW);
  //## duration = pulseIn(echoPin, HIGH);
  //## if (duration == 0) {
  //##   distance = 999;
  //## }
  //## else {
  //##   distance = duration * 0.034 / 2;
  //## }
  //## if (distance > 50) {
  //##   noTone(buzzerPin);
  //##   digitalWrite(greenLED, HIGH);
  //##   digitalWrite(yellowLED, LOW);
  //##   digitalWrite(redLED, LOW);
  //## }
  //## else if (distance > 20) {

  //?? Turn buzzer ON (1000 Hz)
  tone(buzzerPin, 1000);

  //?? Delay 300 ms
  delay(300);

  //?? Turn buzzer OFF
  noTone(buzzerPin);

  //?? Delay 300 ms
  delay(300);

  //?? Turn green LED OFF
  digitalWrite(greenLED, LOW);

  //?? Turn yellow LED ON
  digitalWrite(yellowLED, HIGH);

  //?? Turn red LED OFF
  digitalWrite(redLED, LOW);

  //## }
}

//>> Step 12 - Danger Zone | guided | blocks | filter:true

void loop() {
  //## digitalWrite(trigPin, LOW);
  //## delayMicroseconds(2);
  //## digitalWrite(trigPin, HIGH);
  //## delayMicroseconds(10);
  //## digitalWrite(trigPin, LOW);
  //## duration = pulseIn(echoPin, HIGH);
  //## if (duration == 0) {
  //##   distance = 999;
  //## }
  //## else {
  //##   distance = duration * 0.034 / 2;
  //## }
  //## if (distance > 50) {
  //##   noTone(buzzerPin);
  //##   digitalWrite(greenLED, HIGH);
  //##   digitalWrite(yellowLED, LOW);
  //##   digitalWrite(redLED, LOW);
  //## }
  //## else if (distance > 20) {
  //##   tone(buzzerPin, 1000);
  //##   delay(300);
  //##   noTone(buzzerPin);
  //##   delay(300);
  //##   digitalWrite(greenLED, LOW);
  //##   digitalWrite(yellowLED, HIGH);
  //##   digitalWrite(redLED, LOW);
  //## }

  //?? Else (very close)
  else {

    //?? Turn buzzer ON (1500 Hz)
    tone(buzzerPin, 1500);

    //?? Turn green LED OFF
    digitalWrite(greenLED, LOW);

    //?? Turn yellow LED OFF
    digitalWrite(yellowLED, LOW);

    //?? Turn red LED ON
    digitalWrite(redLED, HIGH);
  }
}

//>> Step 13 - Loop Delay | guided

void loop() {
  //## digitalWrite(trigPin, LOW);
  //## delayMicroseconds(2);
  //## digitalWrite(trigPin, HIGH);
  //## delayMicroseconds(10);
  //## digitalWrite(trigPin, LOW);
  //## duration = pulseIn(echoPin, HIGH);
  //## if (duration == 0) {
  //##   distance = 999;
  //## }
  //## else {
  //##   distance = duration * 0.034 / 2;
  //## }
  //## if (distance > 50) {
  //##   noTone(buzzerPin);
  //##   digitalWrite(greenLED, HIGH);
  //##   digitalWrite(yellowLED, LOW);
  //##   digitalWrite(redLED, LOW);
  //## }
  //## else if (distance > 20) {
  //##   tone(buzzerPin, 1000);
  //##   delay(300);
  //##   noTone(buzzerPin);
  //##   delay(300);
  //##   digitalWrite(greenLED, LOW);
  //##   digitalWrite(yellowLED, HIGH);
  //##   digitalWrite(redLED, LOW);
  //## }
  //## else {
  //##   tone(buzzerPin, 1500);
  //##   digitalWrite(greenLED, LOW);
  //##   digitalWrite(yellowLED, LOW);
  //##   digitalWrite(redLED, HIGH);
  //## }

  //?? Small delay for stability
  delay(50);
}

//>> Step 14 - Mission Complete | open

void loop() {
  //## digitalWrite(trigPin, LOW);
  //## delayMicroseconds(2);
  //## digitalWrite(trigPin, HIGH);
  //## delayMicroseconds(10);
  //## digitalWrite(trigPin, LOW);
  //## duration = pulseIn(echoPin, HIGH);
  //## if (duration == 0) {
  //##   distance = 999;
  //## }
  //## else {
  //##   distance = duration * 0.034 / 2;
  //## }
  //## if (distance > 50) {
  //##   noTone(buzzerPin);
  //##   digitalWrite(greenLED, HIGH);
  //##   digitalWrite(yellowLED, LOW);
  //##   digitalWrite(redLED, LOW);
  //## }
  //## else if (distance > 20) {
  //##   tone(buzzerPin, 1000);
  //##   delay(300);
  //##   noTone(buzzerPin);
  //##   delay(300);
  //##   digitalWrite(greenLED, LOW);
  //##   digitalWrite(yellowLED, HIGH);
  //##   digitalWrite(redLED, LOW);
  //## }
  //## else {
  //##   tone(buzzerPin, 1500);
  //##   digitalWrite(greenLED, LOW);
  //##   digitalWrite(yellowLED, LOW);
  //##   digitalWrite(redLED, HIGH);
  //## }
  //## delay(50);
//##}
"""
    }



CHALLENGE_PRESET = {
    'sketch': '...',
    'default_view': 'blocks',
}

# Optional — progression sketch for guided block builder projects
PROGRESSION_PRESET = {
    'sketch': '...',  # contains //>> markers
}
CHIPS = [
    "I don't hear the buzzer",
    "My LEDs are not lighting up",
    "One resistor leg is in the wrong row",
    "I think a wire is blocking the sonar",
    "My trig and echo pins aren’t working",
]

CIRCUIT_SPEC = {
    "meta": {
        "title": "Backup Alarm",
        "difficulty": "intermediate",
    },
    "components": [
        # Order matters here: HC_SR04 and BUZZER both claim extra-wide
        # footprints (full-width / cross-gap), so they must be placed
        # before the LEDs or the LEDs box them out and placement fails.
        {"id": "SONAR", "type": "HC_SR04", "properties": {}},
        {"id": "BUZZ", "type": "BUZZER", "properties": {}},
        {"id": "GREEN_LED", "type": "LED", "properties": {"color": "green"}},
        {"id": "YELLOW_LED", "type": "LED", "properties": {"color": "yellow"}},
        {"id": "RED_LED", "type": "LED", "properties": {"color": "red"}},
    ],
    "connections": [
        {"from": "arduino.D4", "to": "GREEN_LED.anode"},
        {"from": "R_GREEN_LED.pin2", "to": "arduino.GND"},
        {"from": "arduino.D5", "to": "YELLOW_LED.anode"},
        {"from": "R_YELLOW_LED.pin2", "to": "arduino.GND"},
        {"from": "arduino.D6", "to": "RED_LED.anode"},
        {"from": "R_RED_LED.pin2", "to": "arduino.GND"},
        {"from": "arduino.D3", "to": "BUZZ.positive"},
        {"from": "BUZZ.negative", "to": "arduino.GND"},
        {"from": "arduino.5V", "to": "SONAR.vcc"},
        {"from": "arduino.GND", "to": "SONAR.gnd"},
        {"from": "arduino.D9", "to": "SONAR.trig"},
        {"from": "SONAR.echo", "to": "arduino.D10"},
    ],
}

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
