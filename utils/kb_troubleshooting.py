"""Hand-authored troubleshooting knowledge base for the help-chat RAG index.

Each entry in CHUNKS is a self-contained passage covering one specific
problem a student might hit — connecting/using KidsCode Link, common
compiler/upload errors, or physical circuit mistakes. Written in plain
text (no HTML) for direct embedding.

project_key / step_index / tab_key are intentionally omitted here — the
build script (utils/kb_build.py) fills them in as None for every entry
in this module, since none of this content is tied to a specific lesson.

Discovered automatically by utils/kb_build.py via pkgutil (any utils/kb_*.py
module exporting a module-level CHUNKS list is picked up the same way
utils/project_registry.py discovers utils/project_*.py modules).
"""

CHUNKS = [

    # ---- KidsCode Link: install / connect / run --------------------------

    {
        "id": "kb_troubleshooting:kclink_not_installed",
        "title": "KidsCode Link Offline — not installed yet",
        "text": (
            "If the status indicator at the top of the page says \"KidsCode Link Offline\", "
            "you probably haven't installed KidsCode Link yet. KidsCode Link is a small free "
            "helper app that lets this website talk to your Arduino board. Click the red status "
            "indicator, then click \"Download KidsCode Link\" and run the installer. It only takes "
            "about a minute, and you only need to do it once on this computer. Ask a parent for "
            "help if you're not sure about installing new programs."
        ),
        "tags": ["kclink", "connection", "install", "offline"],
    },
    {
        "id": "kb_troubleshooting:kclink_sleeping",
        "title": "KidsCode Link is sleeping",
        "text": (
            "If a pop-up says \"KidsCode Link is sleeping\", that means it's already installed on "
            "your computer but isn't running right now. Click \"Open KidsCode Link\" to wake it up, "
            "or look for its icon in your system tray (usually near the clock, bottom-right of the "
            "screen on Windows) and click it. Give it a few seconds to start, then come back and "
            "check the status indicator — it should turn green."
        ),
        "tags": ["kclink", "connection", "sleeping", "tray"],
    },
    {
        "id": "kb_troubleshooting:kclink_windows_only",
        "title": "KidsCode Link only works on Windows right now",
        "text": (
            "KidsCode Link currently only works on Windows computers — Mac support is coming soon "
            "but isn't ready yet. If you're on a Mac (or Linux), you won't be able to install "
            "KidsCode Link right now. The good news: you can still upload your code using the free "
            "Arduino IDE app instead, which works on both Windows and Mac. Ask a parent to help you "
            "download the Arduino IDE from the official Arduino website if you need this option."
        ),
        "tags": ["kclink", "mac", "windows", "compatibility"],
    },
    {
        "id": "kb_troubleshooting:kclink_chrome_required",
        "title": "Chrome or Edge required for KidsCode Link",
        "text": (
            "KidsCode Link can't connect through Firefox or Safari — those browsers block the kind "
            "of local connection KidsCode Link needs for safety reasons. If you see a message about "
            "needing Chrome or Edge, close this tab and reopen the website in Google Chrome or "
            "Microsoft Edge instead. Everything else about the site works the same, you just need "
            "one of those two browsers to upload code to your Arduino."
        ),
        "tags": ["kclink", "browser", "chrome", "firefox", "safari"],
    },
    {
        "id": "kb_troubleshooting:kclink_first_run_needs_internet",
        "title": "KidsCode Link setup needs the internet the first time",
        "text": (
            "The very first time you open KidsCode Link, it downloads a small set of tools it needs "
            "to talk to Arduino boards. This only happens once, but it needs an internet connection "
            "to finish. If KidsCode Link's tray icon says \"Setup failed\" or seems stuck, check that "
            "your computer is connected to Wi-Fi or a network cable, then quit and reopen KidsCode "
            "Link so it can try the setup again."
        ),
        "tags": ["kclink", "setup", "internet", "first-run"],
    },
    {
        "id": "kb_troubleshooting:kclink_port_conflict",
        "title": "\"Port already in use\" when starting KidsCode Link",
        "text": (
            "If KidsCode Link's tray icon shows a warning about a port already being in use, it "
            "usually means another copy of KidsCode Link is already running — maybe from before you "
            "restarted your computer, or you accidentally opened it twice. Right-click the KidsCode "
            "Link icon in your system tray and choose Quit, then open it again fresh. If that doesn't "
            "fix it, restarting your computer will clear it up."
        ),
        "tags": ["kclink", "port-conflict", "tray"],
    },
    {
        "id": "kb_troubleshooting:kclink_board_not_in_list",
        "title": "My Arduino isn't showing up in the port dropdown",
        "text": (
            "If your Arduino isn't in the port dropdown list, first try unplugging the USB cable "
            "and plugging it back in firmly, then click the Refresh button next to the dropdown. "
            "Make sure KidsCode Link's status shows green (connected), not the offline warning. If "
            "it still doesn't appear, try a different USB port on your computer, and double-check "
            "you're using a USB-A to USB-B cable — that's the one with a rectangular plug on the "
            "Arduino end, not a round or oval one."
        ),
        "tags": ["port", "dropdown", "usb", "not-detected"],
    },
    {
        "id": "kb_troubleshooting:kclink_wrong_cable",
        "title": "Which USB cable does my Arduino need?",
        "text": (
            "Arduino UNO boards use a USB-A to USB-B cable — a rectangular \"printer-style\" plug on "
            "the Arduino end and a regular flat USB plug on the computer end. Phone charging cables "
            "usually won't work because many of them are \"charge only\" and can't send data, or "
            "they have the wrong shape of connector. If your Arduino lights up but the port never "
            "appears in the dropdown, trying a different cable is one of the most common fixes."
        ),
        "tags": ["usb", "cable", "hardware"],
    },
    {
        "id": "kb_troubleshooting:kclink_driver_missing_ch340",
        "title": "My Arduino plugs in but Windows doesn't recognize it (driver issue)",
        "text": (
            "Some cheaper Arduino-compatible boards use a chip called the CH340 to talk over USB, "
            "and Windows doesn't always install the right driver for it automatically. If your board "
            "never shows up as a port no matter what you try, but it powers on (a light turns on), "
            "this is a likely cause. A parent can search online for \"CH340 driver windows\" from the "
            "board's official manufacturer to download and install it — after installing, unplug and "
            "replug the board and it should appear in the port list."
        ),
        "tags": ["driver", "ch340", "windows", "not-detected"],
    },
    {
        "id": "kb_troubleshooting:kclink_operation_in_progress",
        "title": "\"Another operation is already in progress\"",
        "text": (
            "This message means KidsCode Link is still busy finishing a previous compile or upload. "
            "Wait a few seconds for it to finish, then try again. If it seems stuck for more than a "
            "minute, quit KidsCode Link from the system tray and reopen it, then try uploading again."
        ),
        "tags": ["upload", "compile", "busy", "error"],
    },
    {
        "id": "kb_troubleshooting:kclink_serial_monitor_blank",
        "title": "The serial monitor isn't showing anything",
        "text": (
            "If you opened the serial monitor but nothing is appearing, first check that your code "
            "actually uses Serial.print or Serial.println to send messages — if the code never "
            "prints anything, the monitor will stay empty even though everything is working fine. "
            "Also make sure you started the serial monitor before uploading finished, since it needs "
            "to be connected fresh after any new upload. If you just uploaded new code, try closing "
            "the serial monitor and reopening it."
        ),
        "tags": ["serial-monitor", "blank", "no-output"],
    },
    {
        "id": "kb_troubleshooting:kclink_serial_disconnect",
        "title": "\"Serial connection closed\" or \"Serial connection failed\"",
        "text": (
            "This shows up if the connection between your browser and your Arduino's serial monitor "
            "got interrupted — often because KidsCode Link restarted, the USB cable got bumped, or "
            "another program is using the same port (like the Arduino IDE open in the background). "
            "Close any other Arduino programs, make sure the cable is snug, then click to reconnect "
            "the serial monitor."
        ),
        "tags": ["serial-monitor", "disconnect", "connection"],
    },
    {
        "id": "kb_troubleshooting:kclink_arduino_ide_alternative",
        "title": "Using the Arduino IDE instead of KidsCode Link",
        "text": (
            "If KidsCode Link isn't working for you — for example you're on a Mac, or your browser "
            "isn't supported — you can still complete projects using the free Arduino IDE app "
            "instead. It works on both Windows and Mac and doesn't need KidsCode Link at all. You'll "
            "need to copy your code into the Arduino IDE and upload it from there, following the same "
            "wiring steps shown on this website."
        ),
        "tags": ["arduino-ide", "alternative", "mac"],
    },
    {
        "id": "kb_troubleshooting:kclink_auto_shutdown",
        "title": "KidsCode Link closed itself after I stepped away",
        "text": (
            "KidsCode Link automatically shuts down after sitting idle for a while (30 minutes by "
            "default) to save your computer's resources, as long as nothing is actively connected. "
            "If you come back to a project and the status shows offline even though you installed "
            "it earlier, this is probably why — just reopen KidsCode Link from your system tray or "
            "desktop shortcut and it'll reconnect right away."
        ),
        "tags": ["kclink", "shutdown", "idle", "dormancy"],
    },
    {
        "id": "kb_troubleshooting:kclink_reinstall",
        "title": "Reinstalling KidsCode Link",
        "text": (
            "If KidsCode Link seems broken and reopening it doesn't help, you can reinstall it fresh: "
            "click the status indicator to open the help popup, then choose \"Reinstall KidsCode "
            "Link\" to download a new copy of the installer. Run it the same way you did the first "
            "time. This won't affect any of your saved projects on the website, since your code is "
            "stored online, not inside KidsCode Link."
        ),
        "tags": ["kclink", "reinstall", "download"],
    },

    # ---- Compile errors ----------------------------------------------------

    {
        "id": "kb_troubleshooting:compile_missing_semicolon",
        "title": "Compile error about a missing semicolon",
        "text": (
            "In Arduino code, almost every instruction line needs to end with a semicolon ( ; ) — "
            "it tells the computer \"that's the end of this instruction.\" If the error message "
            "points near a line and mentions \"expected ';'\", check the end of the previous line for "
            "a missing semicolon — that's almost always the real spot to fix, even if the error "
            "points slightly further down."
        ),
        "tags": ["compile-error", "semicolon", "syntax"],
    },
    {
        "id": "kb_troubleshooting:compile_undeclared_variable",
        "title": "Compile error: \"was not declared in this scope\"",
        "text": (
            "This error means the code is trying to use a variable or name that was never created, "
            "or was spelled differently somewhere. Check for typos — Arduino code is case-sensitive, "
            "so ledPin and LEDPin are treated as two completely different names. Make sure every "
            "variable you use was declared earlier in the code with a type, like int ledPin = 9;"
        ),
        "tags": ["compile-error", "variable", "scope", "typo"],
    },
    {
        "id": "kb_troubleshooting:compile_mismatched_braces",
        "title": "Compile error about mismatched braces or unexpected end of file",
        "text": (
            "Arduino code uses curly braces { } to group blocks of code together, like everything "
            "inside setup() or loop(). If you get an error about an unexpected end of file or "
            "mismatched braces, count your opening { and closing } braces — there's likely one "
            "missing or one extra somewhere in the code. In block-based mode this is handled for "
            "you automatically, so this mostly comes up in the text editor view."
        ),
        "tags": ["compile-error", "braces", "syntax"],
    },
    {
        "id": "kb_troubleshooting:compile_case_sensitivity",
        "title": "My code looks right but still won't compile — check capitalization",
        "text": (
            "Arduino code cares a lot about uppercase and lowercase letters. Function names like "
            "pinMode, digitalWrite, and HIGH/LOW must be typed exactly right — pinmode or digitalwrite "
            "(all lowercase) will cause an error even though it looks almost the same to us. If "
            "you're stuck on an error you can't explain, carefully check the capital letters in "
            "built-in Arduino commands first."
        ),
        "tags": ["compile-error", "case-sensitive", "syntax"],
    },
    {
        "id": "kb_troubleshooting:compile_missing_pinmode",
        "title": "Code compiles but the pin doesn't behave as expected",
        "text": (
            "Every pin you use for input or output needs to be set up first in setup() using "
            "pinMode(pin, OUTPUT) or pinMode(pin, INPUT) before you can read from it or write to it "
            "in loop(). If a pin isn't doing what you expect (an LED not lighting, a button never "
            "registering), double check that pinMode was called for that exact pin number earlier "
            "in setup()."
        ),
        "tags": ["pinmode", "setup", "pin-config"],
    },
    {
        "id": "kb_troubleshooting:compile_quotes_and_strings",
        "title": "Compile error involving quotes or text in Serial.print",
        "text": (
            "Text you want to print or display needs to be wrapped in double quotes, like "
            "Serial.println(\"Hello!\"); — if a quote mark is missing, or you used a curly/smart "
            "quote from a word processor instead of a straight one, the code won't compile. Try "
            "retyping the quotes directly in the block builder or editor rather than pasting from "
            "another app."
        ),
        "tags": ["compile-error", "strings", "quotes", "serial-print"],
    },
    {
        "id": "kb_troubleshooting:compile_setup_loop_typo",
        "title": "\"void setup\" or \"void loop\" errors",
        "text": (
            "Every Arduino sketch needs exactly one void setup() { } block and one void loop() { } "
            "block — these are special names the Arduino looks for, and they must be spelled and "
            "capitalized exactly that way. If you see an error mentioning setup or loop, check "
            "there isn't an extra space, missing parenthesis, or typo in either of those two lines."
        ),
        "tags": ["setup", "loop", "compile-error", "structure"],
    },

    # ---- Upload errors -------------------------------------------------------

    {
        "id": "kb_troubleshooting:upload_failed_generic",
        "title": "Upload failed — general first steps",
        "text": (
            "If uploading fails, first make sure the correct port is selected in the dropdown and "
            "that KidsCode Link's status shows green, not offline. Then check that no other program "
            "— like the Arduino IDE, a serial monitor tool, or another browser tab — is also "
            "connected to the same port, since only one program can talk to the Arduino at a time. "
            "Closing other Arduino-related programs and trying the upload again fixes most cases."
        ),
        "tags": ["upload", "error", "port"],
    },
    {
        "id": "kb_troubleshooting:upload_port_busy",
        "title": "Upload fails because the port is busy",
        "text": (
            "\"Port busy\" or similar upload failures usually mean another program has the Arduino's "
            "port open at the same time, like the Arduino IDE's serial monitor running in the "
            "background. Close any other Arduino software or serial monitor windows, then try "
            "uploading again from this website."
        ),
        "tags": ["upload", "port-busy", "error"],
    },
    {
        "id": "kb_troubleshooting:upload_no_port_selected",
        "title": "Nothing happens when I click Upload",
        "text": (
            "If clicking Upload doesn't seem to do anything, check that a port is actually selected "
            "in the dropdown menu first — if it's empty, click Refresh to look for your board again, "
            "and make sure it's plugged in and KidsCode Link shows as connected."
        ),
        "tags": ["upload", "no-port", "dropdown"],
    },
    {
        "id": "kb_troubleshooting:upload_blocks_need_attention",
        "title": "\"Some blocks need attention\" message before uploading",
        "text": (
            "This message means one or more of your code blocks are incomplete or set up "
            "incorrectly — maybe an empty slot where a value should go, or a block that's missing a "
            "piece it needs. Look for any blocks highlighted or marked on the screen and fix those "
            "before trying to upload again."
        ),
        "tags": ["blocks", "validation", "upload-blocked"],
    },

    # ---- Hardware / wiring troubleshooting -----------------------------------

    {
        "id": "kb_troubleshooting:hw_led_not_lighting",
        "title": "My LED won't light up at all",
        "text": (
            "If an LED isn't lighting up, check these in order: is it plugged in backwards? LEDs "
            "only work in one direction — look for the longer leg (positive) and the flat edge on "
            "the LED's plastic case (negative side). Next, check the wire from the Arduino pin all "
            "the way to the breadboard is snug in both ends. Finally, make sure your code is actually "
            "turning that exact pin HIGH — a wrong pin number in the code is one of the most common "
            "reasons an LED stays dark."
        ),
        "tags": ["led", "not-lighting", "hardware", "wiring"],
    },
    {
        "id": "kb_troubleshooting:hw_led_backwards",
        "title": "How to tell if an LED is plugged in backwards",
        "text": (
            "LEDs are polarized, meaning electricity can only flow through them one way. Look at the "
            "two legs: the longer leg is positive and should connect toward power (or the Arduino "
            "pin, depending on your circuit), and the shorter leg is negative and connects toward "
            "ground. You can also look at the plastic dome — there's usually a flat side near the "
            "negative (shorter) leg. If an LED that should be lighting up stays dark, try flipping "
            "it around in the breadboard."
        ),
        "tags": ["led", "polarity", "backwards", "wiring"],
    },
    {
        "id": "kb_troubleshooting:hw_led_no_resistor",
        "title": "Why does my LED need a resistor?",
        "text": (
            "LEDs need a resistor in the circuit to limit how much electricity flows through them — "
            "without one, too much current can flow and burn the LED out permanently (it'll stop "
            "working, sometimes after a puff of smoke or a burning smell). If a project's instructions "
            "show a resistor next to an LED, make sure it's actually in the circuit before powering "
            "it on, especially if you're building the circuit from memory rather than following the "
            "diagram exactly."
        ),
        "tags": ["led", "resistor", "hardware", "safety"],
    },
    {
        "id": "kb_troubleshooting:hw_loose_wire",
        "title": "My circuit worked before but stopped working",
        "text": (
            "If a circuit was working and then suddenly stopped, a loose wire is the most common "
            "cause — breadboard wires can wiggle out of place if the board gets bumped or moved. Go "
            "through each wire in your circuit and press it firmly back into its breadboard hole. "
            "It also helps to compare your circuit side-by-side with the circuit diagram to spot any "
            "wire that's ended up in the wrong row or column."
        ),
        "tags": ["loose-wire", "stopped-working", "hardware"],
    },
    {
        "id": "kb_troubleshooting:hw_breadboard_rows",
        "title": "How breadboard rows and power rails work",
        "text": (
            "A breadboard's middle section is split into short rows of 5 holes, and every hole in "
            "one of those rows is electrically connected to the others in that same row (but not to "
            "the row next to it). The long rows running along the top and bottom edges are power "
            "rails — usually marked with a red line (+ / power) and a blue or black line (- / "
            "ground) — and those run the full length of the board. Plugging a component into the "
            "wrong row, or into a power rail by mistake, is a very common wiring mistake."
        ),
        "tags": ["breadboard", "rows", "power-rail", "basics"],
    },
    {
        "id": "kb_troubleshooting:hw_button_not_responding",
        "title": "My button isn't doing anything when I press it",
        "text": (
            "If a pushbutton doesn't seem to register presses, first check it's straddling the gap "
            "in the middle of the breadboard correctly — pushbuttons have 4 legs, and it's easy to "
            "accidentally plug it in rotated 90 degrees so two legs that should be separate end up "
            "connected. Also check that a pull-up or pull-down resistor is wired in if your project's "
            "diagram shows one — without it, the button's pin can float between HIGH and LOW "
            "randomly instead of giving a clear reading."
        ),
        "tags": ["button", "not-working", "hardware", "pull-up"],
    },
    {
        "id": "kb_troubleshooting:hw_short_circuit_wrong_row",
        "title": "Something got warm or a component stopped working suddenly",
        "text": (
            "If a component (or the Arduino itself) got warm to the touch, or something stopped "
            "working right after you changed the wiring, unplug the USB cable immediately and "
            "recheck your circuit for a short circuit — usually caused by a wire accidentally "
            "connecting the power rail directly to the ground rail, or two wires touching in the "
            "same breadboard row that shouldn't be connected. Compare carefully against the circuit "
            "diagram before plugging power back in."
        ),
        "tags": ["short-circuit", "warm", "safety", "hardware"],
    },
    {
        "id": "kb_troubleshooting:hw_resistor_bands",
        "title": "How do I know which resistor to use?",
        "text": (
            "Resistors are marked with colored stripes that tell you their value in ohms, but for "
            "these projects you don't need to memorize the color code — just match the resistor "
            "shown in the circuit diagram or parts list for that project. If you're unsure which "
            "resistor you're holding, ask a parent to help look up the color-code stripes online, or "
            "check if your kit sorts resistors by value in labeled bags."
        ),
        "tags": ["resistor", "color-code", "hardware"],
    },
    {
        "id": "kb_troubleshooting:hw_servo_not_moving",
        "title": "My servo motor isn't moving",
        "text": (
            "If a servo isn't moving at all, check that its three wires are connected correctly: "
            "power, ground, and signal — plugging power and ground backwards can prevent it from "
            "working (and can damage it, so double-check against the diagram first). Also confirm "
            "the signal wire is connected to a pin capable of the kind of output your code expects, "
            "and that your code is actually sending a new position value in loop() or setup()."
        ),
        "tags": ["servo", "motor", "not-moving", "hardware"],
    },
    {
        "id": "kb_troubleshooting:hw_buzzer_no_sound",
        "title": "My buzzer isn't making any sound",
        "text": (
            "If a buzzer stays silent, check it's plugged in the correct way around if it's a "
            "polarized buzzer (look for a + marking or a longer leg), confirm the wire from the "
            "Arduino signal pin is snug, and make sure your code is actually calling tone() or "
            "digitalWrite HIGH/LOW on that exact pin. Some buzzers are very quiet — try holding your "
            "ear close before assuming it isn't working at all."
        ),
        "tags": ["buzzer", "sound", "not-working", "hardware"],
    },
    {
        "id": "kb_troubleshooting:hw_sensor_reads_zero",
        "title": "My sensor always reads 0 (or always reads the same number)",
        "text": (
            "A sensor that always returns the same reading, especially 0, is often a wiring issue "
            "rather than a code issue — check the sensor's power and ground legs are in the power "
            "rails (not swapped), and that the signal wire goes to the exact analog or digital pin "
            "your code is reading from. If you're using Serial.println to check the sensor's raw "
            "value while testing, that's a great way to confirm whether the problem is the wiring or "
            "the code."
        ),
        "tags": ["sensor", "reads-zero", "hardware", "debugging"],
    },
    {
        "id": "kb_troubleshooting:hw_ground_not_connected",
        "title": "My circuit has power but nothing works right",
        "text": (
            "Every circuit needs a complete loop — power has to be able to flow out from the "
            "Arduino, through your components, and back to a ground (GND) pin. A very common mistake "
            "is wiring the power side of a component but forgetting to connect its ground leg back "
            "to the Arduino's GND pin or the breadboard's ground rail. If nothing in your circuit "
            "works even though everything looks plugged in, check every component has a path back to "
            "ground."
        ),
        "tags": ["ground", "gnd", "circuit-basics", "hardware"],
    },
    {
        "id": "kb_troubleshooting:hw_multiple_grounds",
        "title": "Do I need more than one ground wire?",
        "text": (
            "Yes — if you have several components in one circuit, each of them generally needs its "
            "own path back to ground, but they can all share the breadboard's ground rail rather than "
            "needing separate wires straight to the Arduino. Make sure the Arduino's own GND pin is "
            "connected to that shared ground rail with at least one wire, and every component's "
            "ground leg is plugged into that same rail."
        ),
        "tags": ["ground", "multiple-components", "hardware"],
    },

    # ---- General debugging strategy ------------------------------------------

    {
        "id": "kb_troubleshooting:debug_first_steps",
        "title": "I don't know where to start when something's wrong",
        "text": (
            "When something isn't working and you're not sure why, it helps to check things in this "
            "order: 1) Is everything plugged in firmly — cable, wires, breadboard connections? 2) Does "
            "KidsCode Link show as connected? 3) Did the upload actually succeed (look for a success "
            "message)? 4) Does your code match what the step is asking for? Working through these one "
            "at a time, instead of guessing, finds most problems quickly."
        ),
        "tags": ["debugging", "getting-started", "strategy"],
    },
    {
        "id": "kb_troubleshooting:debug_isolate_the_problem",
        "title": "How to figure out if it's the code or the wiring",
        "text": (
            "A great trick for figuring out if a problem is in your code or your wiring: try a very "
            "simple test, like blinking the built-in LED on the Arduino board itself (no extra wiring "
            "needed) to confirm uploads are working at all. If that works, the problem is likely in "
            "your circuit wiring. If even that doesn't work, the problem is probably with the "
            "connection or upload, not your circuit."
        ),
        "tags": ["debugging", "isolate", "strategy"],
    },
    {
        "id": "kb_troubleshooting:debug_use_serial_monitor",
        "title": "Using the serial monitor to find bugs",
        "text": (
            "Adding Serial.println() statements in your code to print out variable values while it "
            "runs is one of the best ways to figure out what's actually happening inside your "
            "program, instead of guessing. For example, printing a sensor's raw reading can tell you "
            "instantly whether the problem is in the wiring (reading never changes) or in how your "
            "code responds to that reading."
        ),
        "tags": ["serial-monitor", "debugging", "strategy"],
    },
    {
        "id": "kb_troubleshooting:debug_compare_diagram",
        "title": "Comparing your circuit to the diagram carefully",
        "text": (
            "When a circuit doesn't work and you can't spot why, it helps to go wire by wire against "
            "the circuit diagram, rather than glancing at the whole thing at once. Pick one wire, "
            "check both of its ends match the diagram exactly, then move to the next wire. Small "
            "differences — one row off, or a wire in the wrong rail — are easy to miss when looking "
            "at everything together."
        ),
        "tags": ["debugging", "circuit-diagram", "strategy"],
    },
    {
        "id": "kb_troubleshooting:debug_ask_for_help",
        "title": "When to ask a parent or teacher for help",
        "text": (
            "Some problems — like installing drivers, dealing with a computer's security settings, "
            "or a component that might be damaged — are good moments to bring in a parent or teacher, "
            "especially anything involving downloading and installing new software. It's not giving "
            "up to ask for help; even experienced makers ask each other for help with tricky hardware "
            "problems all the time."
        ),
        "tags": ["ask-for-help", "parent", "teacher", "strategy"],
    },
]
