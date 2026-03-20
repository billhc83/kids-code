# ── Preset sketches ───────────────────────────────────────────────────
from utils.codebreaker_presets import CODEBREAKER_PRESETS

PRESETS = {
    'engine_start': {
        'sketch': """
void setup() {
  pinMode(9, INPUT);   // Arm switch
  pinMode(7, INPUT);   // Engage button
  pinMode(2, OUTPUT);  // Engine light
  pinMode(5, OUTPUT); // Engine buzzer
}

void loop() {

  if (digitalRead(9) == LOW) {   // Switch ON

    //## digitalWrite(2, HIGH);        // Light ON (armed)

    if (digitalRead(7) == LOW) {
      digitalWrite(5, HIGH);     // Start engine
    }

  } else {                        // Switch OFF

    digitalWrite(2, LOW);         // Light OFF
    digitalWrite(5, LOW);        // Engine OFF (reset)

  }
}
""",
    },
    'patrol_alarm': {
        'sketch': """
int switchPin = 12;

int redLED = 8;
int blueLED = 6;
int clearLED = 4;

void setup()
{
  pinMode(switchPin, INPUT_PULLUP);

  pinMode(redLED, OUTPUT);
  pinMode(blueLED, OUTPUT);
  pinMode(clearLED, OUTPUT);
}

void loop()
{

  // Check if the switch is ON
  if (digitalRead(switchPin) == LOW)
  {

    // Red flash
    digitalWrite(redLED, HIGH);
    delay(150);
    digitalWrite(redLED, LOW);

    // Blue flash
    digitalWrite(blueLED, HIGH);
    delay(150);
    digitalWrite(blueLED, LOW);

    // Clear flash
    digitalWrite(clearLED, HIGH);
    delay(150);
    digitalWrite(clearLED, LOW);

  }

  else
  {

    // Switch OFF → everything OFF
    digitalWrite(redLED, LOW);
    digitalWrite(blueLED, LOW);
    digitalWrite(clearLED, LOW);

  }

}
""",
    },
    'reaction_timer': {
        'sketch': """
int button = 2;

int running = 0;

unsigned long startTime = 0;
unsigned long time = 0;

void setup() {
  pinMode(button, INPUT_PULLUP);
  Serial.begin(9600);
}

void loop() {

  if (digitalRead(button) == LOW) {

    if (running == 0) {
      startTime = millis();
      running = 1;
    }
    else {
      time = millis() - startTime;
      Serial.println(time);
      running = 0;
    }

    delay(300);
  }

}
""",
        'fill_conditions': True,
        'fill_values': False,
    },
}

PRESETS.update(CODEBREAKER_PRESETS)

# ── Pin reference lists ───────────────────────────────────────────────
# Add your own project keys and component lists here.
# These appear as a reference-only dropdown on every pinMode block.
# The user can pick an item as a label hint or ignore it entirely.

PIN_REFS = {
    "engine_start": ["Switch", "Button", "LED", "Buzzer"],
    "serial_hello": ["TX LED", "RX LED"],
    "button_read":  ["button", "LED"],
}