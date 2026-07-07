"""Hand-authored glossary knowledge base for the help-chat RAG index.

Each entry explains one Arduino/electronics/programming concept that
recurs across multiple lessons, so a single well-written passage can
serve every project that touches it instead of being re-explained per
lesson. Plain text (no HTML), kid-friendly (ages 8-14).

project_key / step_index / tab_key are intentionally omitted — filled in
as None by the build script, same as utils/kb_troubleshooting.py.

Discovered automatically by utils/kb_build.py via pkgutil, the same way
utils/project_registry.py discovers utils/project_*.py modules.
"""

CHUNKS = [

    {
        "id": "kb_glossary:pinmode",
        "title": "What is pinMode()?",
        "text": (
            "pinMode() tells the Arduino how you want to use one of its pins before you use it — "
            "either as OUTPUT (sending power out, like to light an LED) or INPUT (reading a signal "
            "in, like from a button or sensor). It's like flipping a switch that decides which "
            "direction electricity flows for that pin. You call pinMode() once for each pin you use, "
            "inside setup()."
        ),
        "tags": ["pinmode", "pins", "setup"],
    },
    {
        "id": "kb_glossary:digitalwrite",
        "title": "What is digitalWrite()?",
        "text": (
            "digitalWrite() sends power out of a pin that's been set to OUTPUT — either HIGH (full "
            "power, like turning something on) or LOW (no power, turning it off). It's how your code "
            "turns an LED on and off, or sends a signal to another component that only needs a "
            "simple on/off switch."
        ),
        "tags": ["digitalwrite", "output", "high-low"],
    },
    {
        "id": "kb_glossary:digitalread",
        "title": "What is digitalRead()?",
        "text": (
            "digitalRead() checks whether a pin set to INPUT is currently HIGH or LOW — for example, "
            "reading whether a button is being pressed (HIGH) or not (LOW). Your code uses this to "
            "make decisions, like \"if the button is pressed, turn on the LED.\""
        ),
        "tags": ["digitalread", "input", "button"],
    },
    {
        "id": "kb_glossary:analogread",
        "title": "What is analogRead()?",
        "text": (
            "analogRead() reads a value that isn't just on or off, but somewhere in a range — like "
            "how bright a light sensor detects, or how far a dial has been turned. It gives back a "
            "number from 0 to 1023, letting your code respond to \"how much\" of something instead of "
            "just \"yes or no.\""
        ),
        "tags": ["analogread", "sensor", "input"],
    },
    {
        "id": "kb_glossary:analogwrite_pwm",
        "title": "What is analogWrite() and PWM?",
        "text": (
            "analogWrite() lets you send a value between 0 and 255 to certain pins, which is how you "
            "make an LED glow at half-brightness instead of just fully on or off, or make a motor "
            "spin at a chosen speed. Behind the scenes this uses something called PWM (pulse-width "
            "modulation) — the pin flips on and off very fast, and the ratio of on-time to off-time "
            "controls how strong the effect feels, even though it's technically only ever fully on or "
            "fully off at any instant."
        ),
        "tags": ["analogwrite", "pwm", "brightness", "motor-speed"],
    },
    {
        "id": "kb_glossary:high_low",
        "title": "What do HIGH and LOW mean?",
        "text": (
            "HIGH and LOW are the two states a digital pin can be in — HIGH means full power (on), "
            "LOW means no power (off). Think of them like a light switch: HIGH is flipped up, LOW is "
            "flipped down. Most digital components (LEDs, buzzers, simple sensors) only care about "
            "HIGH or LOW, not values in between."
        ),
        "tags": ["high", "low", "digital", "basics"],
    },
    {
        "id": "kb_glossary:setup_function",
        "title": "What does setup() do?",
        "text": (
            "setup() is a special part of every Arduino sketch that runs exactly once, right when "
            "the board powers on or resets — it's where you tell the Arduino how each pin should be "
            "used (pinMode) and get anything ready before the main program starts. After setup() "
            "finishes, the Arduino moves on to loop() and never runs setup() again until it's "
            "restarted."
        ),
        "tags": ["setup", "structure", "basics"],
    },
    {
        "id": "kb_glossary:loop_function",
        "title": "What does loop() do?",
        "text": (
            "loop() is the part of an Arduino sketch that repeats over and over, forever, as long as "
            "the board has power — it's where the actual ongoing behavior of your project lives, "
            "like continuously checking a sensor or blinking an LED. Every line inside loop() runs "
            "from top to bottom, then starts again from the top, extremely fast."
        ),
        "tags": ["loop", "structure", "basics"],
    },
    {
        "id": "kb_glossary:variable",
        "title": "What is a variable?",
        "text": (
            "A variable is a named container that stores a value your code can use and change later "
            "— like a labeled box. For example, int ledPin = 9; creates a variable called ledPin that "
            "stores the number 9, so if you ever move the LED to a different pin, you only need to "
            "change that one line instead of every place the pin number is used."
        ),
        "tags": ["variable", "programming-basics"],
    },
    {
        "id": "kb_glossary:integer_boolean",
        "title": "What are int and boolean (data types)?",
        "text": (
            "int is a variable type that stores whole numbers, like 9 or -3 or 1023 — used for things "
            "like pin numbers or sensor readings. A boolean stores just one of two values: true or "
            "false — useful for things like \"is the button currently pressed?\" Choosing the right "
            "type helps the Arduino understand what kind of value a variable is supposed to hold."
        ),
        "tags": ["int", "boolean", "data-types"],
    },
    {
        "id": "kb_glossary:if_else",
        "title": "What is an if/else statement?",
        "text": (
            "An if/else statement lets your code make decisions: \"if this condition is true, do "
            "this — otherwise (else), do something different.\" For example: if the button is "
            "pressed, turn the LED on; else, turn it off. Each condition is checked every time loop() "
            "runs, so the decision updates continuously."
        ),
        "tags": ["if-else", "conditionals", "programming-basics"],
    },
    {
        "id": "kb_glossary:comparison_operators",
        "title": "What do ==, >, and < mean in code?",
        "text": (
            "These symbols compare two values inside a condition. == checks if two things are equal "
            "(note: two equals signs, not one — a single = means something different, it assigns a "
            "value). > means \"greater than\" and < means \"less than.\" For example, if "
            "(sensorValue > 500) checks whether a sensor's reading is above 500 before doing "
            "something."
        ),
        "tags": ["comparison-operators", "conditionals", "programming-basics"],
    },
    {
        "id": "kb_glossary:repeat_loops",
        "title": "What are repeat blocks / for and while loops?",
        "text": (
            "A repeat loop runs the same block of code multiple times without you having to write it "
            "out over and over — for example, repeating \"blink the LED\" 5 times, or repeating "
            "\"check the sensor\" forever. In text code these are written as for loops (repeat a set "
            "number of times) or while loops (repeat as long as a condition stays true)."
        ),
        "tags": ["for-loop", "while-loop", "repeat", "programming-basics"],
    },
    {
        "id": "kb_glossary:delay",
        "title": "What does delay() do?",
        "text": (
            "delay() pauses your code for a set number of milliseconds (1000 milliseconds = 1 "
            "second) before moving on to the next line. It's commonly used to make a blink pattern "
            "visible — for example, turning an LED on, delaying, turning it off, delaying again. "
            "While delay() is running, the Arduino can't do anything else, which is important to "
            "know for projects that need to respond quickly to more than one thing at once."
        ),
        "tags": ["delay", "timing", "programming-basics"],
    },
    {
        "id": "kb_glossary:millis",
        "title": "What is millis() and why use it instead of delay()?",
        "text": (
            "millis() tells you how many milliseconds have passed since the Arduino turned on — it "
            "keeps counting in the background without pausing anything. Some projects use millis() "
            "instead of delay() when they need to keep checking sensors or buttons while also timing "
            "something else, since delay() would freeze everything else while it waits."
        ),
        "tags": ["millis", "timing", "advanced"],
    },
    {
        "id": "kb_glossary:serial_print",
        "title": "What is Serial.print / Serial.println?",
        "text": (
            "Serial.print() and Serial.println() send text or numbers from your Arduino back to your "
            "computer, where you can see it in the serial monitor — hugely useful for checking what "
            "a sensor is actually reading, or confirming a part of your code ran. Serial.println adds "
            "a line break after the message so each one appears on its own line; Serial.print does "
            "not."
        ),
        "tags": ["serial-print", "serial-monitor", "debugging"],
    },
    {
        "id": "kb_glossary:baud_rate",
        "title": "What is baud rate?",
        "text": (
            "Baud rate is the speed at which your Arduino and computer agree to send serial messages "
            "back and forth — both sides need to be set to the same number (commonly 9600) or the "
            "serial monitor will show garbled text or nothing at all. If you ever see strange "
            "symbols in the serial monitor instead of readable text, a mismatched baud rate is a "
            "common cause."
        ),
        "tags": ["baud-rate", "serial-monitor", "advanced"],
    },
    {
        "id": "kb_glossary:breadboard",
        "title": "What is a breadboard?",
        "text": (
            "A breadboard is a reusable board full of holes that let you build circuits without any "
            "soldering — you just push wires and component legs into the holes. Holes in the same "
            "short row in the middle section are electrically connected to each other, and the long "
            "rows along the edges (power rails) connect power and ground across the whole board."
        ),
        "tags": ["breadboard", "hardware-basics"],
    },
    {
        "id": "kb_glossary:resistor",
        "title": "What is a resistor?",
        "text": (
            "A resistor is a small component that limits how much electric current can flow through "
            "part of a circuit — think of it like a narrow section of pipe slowing down water flow. "
            "Resistors protect other components (especially LEDs) from getting too much current, "
            "which could otherwise damage or destroy them."
        ),
        "tags": ["resistor", "hardware-basics"],
    },
    {
        "id": "kb_glossary:led",
        "title": "What is an LED?",
        "text": (
            "LED stands for Light Emitting Diode — a small component that lights up when electricity "
            "flows through it in the correct direction. Unlike a regular light bulb, an LED only "
            "works one way around (it has polarity), and it needs a resistor in the circuit to avoid "
            "drawing too much current and burning out."
        ),
        "tags": ["led", "hardware-basics"],
    },
    {
        "id": "kb_glossary:polarity",
        "title": "What does polarity mean?",
        "text": (
            "Polarity means a component only works correctly when connected in one specific "
            "direction — LEDs, some capacitors, servos, and batteries are all polarized. Getting the "
            "direction backwards usually just stops the component from working (an LED simply won't "
            "light), though for some components it can cause damage, so it's always worth "
            "double-checking against the circuit diagram."
        ),
        "tags": ["polarity", "hardware-basics"],
    },
    {
        "id": "kb_glossary:pullup_pulldown",
        "title": "What is a pull-up or pull-down resistor?",
        "text": (
            "A pull-up or pull-down resistor keeps an input pin at a known, steady value (HIGH or "
            "LOW) when a button isn't being pressed, instead of letting it \"float\" and give random, "
            "unpredictable readings. A pull-up resistor keeps the pin HIGH until the button pulls it "
            "LOW when pressed; a pull-down does the opposite. Some Arduino pins have a built-in "
            "pull-up you can turn on in code (INPUT_PULLUP) without needing an extra physical "
            "resistor."
        ),
        "tags": ["pull-up", "pull-down", "button", "advanced"],
    },
    {
        "id": "kb_glossary:debounce",
        "title": "What is debounce (why does my button press register multiple times)?",
        "text": (
            "When you press a physical button, the metal contacts inside can bounce and touch "
            "several times in a tiny fraction of a second before settling — to the Arduino, this can "
            "look like several rapid presses instead of one. Debouncing is a technique (often just a "
            "short delay, or checking the state has been stable for a moment) that ignores this "
            "rapid bouncing so one press is counted as exactly one press."
        ),
        "tags": ["debounce", "button", "advanced"],
    },
    {
        "id": "kb_glossary:servo",
        "title": "What is a servo motor?",
        "text": (
            "A servo is a small motor that can rotate to a specific angle (usually between 0 and 180 "
            "degrees) and hold that position, rather than spinning continuously like a fan motor. "
            "You tell it what angle to move to in your code, and it has three wires: power, ground, "
            "and a signal wire that carries the angle instruction."
        ),
        "tags": ["servo", "motor", "hardware-basics"],
    },
    {
        "id": "kb_glossary:buzzer",
        "title": "What is a buzzer (piezo)?",
        "text": (
            "A buzzer (sometimes called a piezo buzzer) makes sound by vibrating rapidly when "
            "electricity is applied. Simple buzzers just make one tone when powered on; others can "
            "play different pitches using Arduino's tone() function, which is how projects make "
            "beeps, alarms, or simple melodies."
        ),
        "tags": ["buzzer", "piezo", "sound", "hardware-basics"],
    },
    {
        "id": "kb_glossary:sensor_general",
        "title": "What is a sensor?",
        "text": (
            "A sensor is a component that detects something about the world — light, temperature, "
            "motion, distance, sound — and turns it into an electrical signal the Arduino can read, "
            "usually with analogRead() or digitalRead(). Different sensors detect different things, "
            "but they all work the same basic way: real-world change in, readable number out."
        ),
        "tags": ["sensor", "hardware-basics"],
    },
    {
        "id": "kb_glossary:potentiometer",
        "title": "What is a potentiometer (dial/knob)?",
        "text": (
            "A potentiometer is a knob or slider you can turn or move by hand, and it sends back a "
            "changing analog signal depending on its position — read with analogRead(). It's how "
            "projects let you manually control something like volume, brightness, or speed with a "
            "physical dial."
        ),
        "tags": ["potentiometer", "sensor", "hardware-basics"],
    },
    {
        "id": "kb_glossary:ground_gnd",
        "title": "What is ground (GND)?",
        "text": (
            "Ground (GND) is the \"return path\" for electricity in a circuit — power flows out from "
            "a source, through your components, and back to ground to complete the loop. Without a "
            "connection back to ground, a circuit is incomplete and won't work at all, even if "
            "everything else looks correctly wired."
        ),
        "tags": ["ground", "gnd", "circuit-basics"],
    },
    {
        "id": "kb_glossary:voltage_current",
        "title": "What are voltage and current?",
        "text": (
            "Voltage is the \"push\" that makes electricity want to flow — like water pressure in a "
            "pipe. Current is how much electricity is actually flowing — like the amount of water "
            "moving through the pipe. Arduino boards typically work at 5 volts (or 3.3 volts on some "
            "boards), and components are chosen to handle the current that flows at that voltage "
            "safely."
        ),
        "tags": ["voltage", "current", "electronics-basics"],
    },
    {
        "id": "kb_glossary:power_rail",
        "title": "What is a power rail?",
        "text": (
            "The power rails are the long rows of holes running along the edges of a breadboard, "
            "usually marked with a red line (power/+) and a blue or black line (ground/-). Every hole "
            "along one rail is connected together, letting you share power and ground with many "
            "components without wiring each one directly back to the Arduino."
        ),
        "tags": ["power-rail", "breadboard", "hardware-basics"],
    },
    {
        "id": "kb_glossary:usb_serial_port",
        "title": "What is a serial port / COM port?",
        "text": (
            "A serial port (shown as something like COM3 on Windows) is the communication channel "
            "your computer uses to talk to the Arduino over the USB cable — both for uploading code "
            "and for the serial monitor. Each USB device gets assigned its own port, which is why "
            "you need to pick the right one from the dropdown, especially if you have more than one "
            "device plugged in."
        ),
        "tags": ["serial-port", "com-port", "usb"],
    },
    {
        "id": "kb_glossary:function",
        "title": "What is a function (in code)?",
        "text": (
            "A function is a named, reusable chunk of instructions — like pinMode(), digitalWrite(), "
            "or delay() are functions built into Arduino that you can call whenever you need that "
            "behavior, instead of rewriting the steps every time. You can also write your own custom "
            "functions to organize your code and avoid repeating yourself."
        ),
        "tags": ["function", "programming-basics"],
    },
    {
        "id": "kb_glossary:comment",
        "title": "What are comments (//) in code?",
        "text": (
            "A comment is a note written in your code for humans to read — the Arduino ignores "
            "anything after // on a line. Comments are used to explain what a piece of code does, or "
            "to temporarily leave notes and reminders, without affecting how the program runs."
        ),
        "tags": ["comments", "programming-basics"],
    },
    {
        "id": "kb_glossary:constant",
        "title": "What does const mean?",
        "text": (
            "const marks a variable as unchanging — once you set its value, the code won't allow it "
            "to be changed later. It's useful for values that should always stay the same, like a "
            "pin number, and helps catch mistakes where you accidentally try to change something you "
            "didn't mean to."
        ),
        "tags": ["const", "variable", "programming-basics"],
    },
    {
        "id": "kb_glossary:tone_function",
        "title": "What does tone() do?",
        "text": (
            "tone() makes a buzzer or speaker play a specific musical pitch by vibrating at a chosen "
            "frequency — for example tone(buzzerPin, 440) plays the musical note A. It's how simple "
            "melodies and sound effects are made in Arduino projects, and noTone() stops the sound."
        ),
        "tags": ["tone", "buzzer", "sound"],
    },
    {
        "id": "kb_glossary:map_function",
        "title": "What does map() do?",
        "text": (
            "map() takes a number from one range and rescales it into a different range — for "
            "example, converting a sensor's raw 0-1023 reading into a more useful 0-255 value for "
            "controlling brightness with analogWrite(). It's a handy shortcut instead of doing that "
            "math yourself every time."
        ),
        "tags": ["map", "sensor", "advanced"],
    },
    {
        "id": "kb_glossary:random_function",
        "title": "What does random() do?",
        "text": (
            "random() picks an unpredictable number within a range you choose, which is useful for "
            "projects that want variety — like a random blink pattern, a random game outcome, or "
            "picking a random delay time so a project doesn't feel too repetitive."
        ),
        "tags": ["random", "programming-basics"],
    },
    {
        "id": "kb_glossary:fqbn_board",
        "title": "What is a board type / FQBN?",
        "text": (
            "Every kind of Arduino board (UNO, Nano, Mega, and others) has slightly different "
            "hardware, so the tools that compile your code need to know exactly which board you're "
            "using — this is sometimes called the board's FQBN behind the scenes. These lessons are "
            "all set up for the Arduino UNO, so you won't need to choose a board type yourself — it's "
            "handled automatically."
        ),
        "tags": ["fqbn", "board-type", "advanced"],
    },
]
