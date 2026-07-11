"""
Tests for the Phase 0 sim interpreter (utils/sim_engine.py::interpret).

Strategy: feed each project's real SKETCH_PRESET['sketch'] through the
interpreter with different input_state snapshots and assert the resulting
output pin states match what a human reading the sketch would expect —
not against any hand-authored `behaviors` dict, which the rollout spec
(SIM_ENGINE_ROLLOUT_SPEC.md) explicitly says can't be trusted.
"""

import pytest

from utils.sim_engine import interpret
import utils.project_three as project_three
import utils.project_seventeen as project_seventeen
import utils.project_nineteen as project_nineteen


# ── project_three: single if/else, one INPUT_PULLUP button ─────────────────

def test_project_three_button_not_pressed_led_off():
    sketch = project_three.SKETCH_PRESET['sketch']
    result = interpret(sketch, input_state={})  # pin 2 defaults HIGH (idle, pullup)

    assert result['pin_modes'][2] == 'INPUT_PULLUP'
    assert result['pin_modes'][8] == 'OUTPUT'
    assert result['pin_states'][8] == 'LOW'


def test_project_three_button_pressed_led_on():
    sketch = project_three.SKETCH_PRESET['sketch']
    result = interpret(sketch, input_state={2: 0})  # pressed pulls pin LOW

    assert result['pin_states'][8] == 'HIGH'


# ── project_eleven-shaped sketch: nested if/else, two INPUT_PULLUP inputs ──
# Hand-resolved (directives removed / `//##` lines uncommented) equivalent of
# utils/project_eleven.py's SKETCH_PRESET, since the interpreter is only
# ever handed fully-resolved code (see BLOCK_BUILDER_SYNC.md) — the raw
# multi-step //>>-annotated preset is a block-builder concern, not this
# interpreter's.

ELEVEN_RESOLVED_SKETCH = """
void setup() {
  pinMode(9, INPUT_PULLUP);   // Arm switch
  pinMode(7, INPUT_PULLUP);   // Engage button
  pinMode(2, OUTPUT);         // Engine light
  pinMode(5, OUTPUT);         // Engine buzzer
}

void loop() {
  if (digitalRead(9) == LOW) {   // Switch ON
    digitalWrite(2, HIGH);       // Light ON (armed)
    if (digitalRead(7) == LOW) {
      digitalWrite(5, HIGH);     // Start engine
    } else {
      digitalWrite(5, LOW);
    }
  } else {                        // Switch OFF
    digitalWrite(2, LOW);         // Light OFF
    digitalWrite(5, LOW);         // Engine OFF
  }
}
"""


def test_eleven_switch_off_light_and_buzzer_off():
    result = interpret(ELEVEN_RESOLVED_SKETCH, input_state={9: 1, 7: 1})
    assert result['pin_states'][2] == 'LOW'
    assert result['pin_states'][5] == 'LOW'


def test_eleven_switch_on_button_released_light_on_buzzer_off():
    result = interpret(ELEVEN_RESOLVED_SKETCH, input_state={9: 0, 7: 1})
    assert result['pin_states'][2] == 'HIGH'
    assert result['pin_states'][5] == 'LOW'


def test_eleven_switch_on_button_pressed_both_on():
    result = interpret(ELEVEN_RESOLVED_SKETCH, input_state={9: 0, 7: 0})
    assert result['pin_states'][2] == 'HIGH'
    assert result['pin_states'][5] == 'HIGH'


def test_eleven_button_pressed_but_switch_off_stays_off():
    # Regression target: this is exactly the case the old regex-replay
    # engine (run()) gets wrong — it has no conditional awareness at all.
    result = interpret(ELEVEN_RESOLVED_SKETCH, input_state={9: 1, 7: 0})
    assert result['pin_states'][2] == 'LOW'
    assert result['pin_states'][5] == 'LOW'


# ── Language coverage: globals, statement sequencing, comparisons, bool ────

def test_global_int_carries_into_loop():
    sketch = """
    int threshold = 3;
    void setup() { pinMode(8, OUTPUT); }
    void loop() {
      if (threshold == 3) { digitalWrite(8, HIGH); } else { digitalWrite(8, LOW); }
    }
    """
    result = interpret(sketch, input_state={})
    assert result['pin_states'][8] == 'HIGH'


def test_statement_sequencing_assign_then_use():
    # Same shape as project `ten`: read into locals first, compare after.
    sketch = """
    void setup() {
      pinMode(2, INPUT_PULLUP);
      pinMode(3, INPUT_PULLUP);
      pinMode(8, OUTPUT);
    }
    void loop() {
      int lockA = digitalRead(2);
      int lockB = digitalRead(3);
      if (lockA == 0 && lockB == 0) {
        digitalWrite(8, HIGH);
      } else {
        digitalWrite(8, LOW);
      }
    }
    """
    assert interpret(sketch, {2: 0, 3: 0})['pin_states'][8] == 'HIGH'
    assert interpret(sketch, {2: 0, 3: 1})['pin_states'][8] == 'LOW'


def test_string_equality_branch():
    # Same shape as project `nine`: String equality driving a branch.
    sketch = """
    String powerSlot = "solar";
    void setup() { pinMode(8, OUTPUT); }
    void loop() {
      if (powerSlot == "solar") { digitalWrite(8, HIGH); } else { digitalWrite(8, LOW); }
    }
    """
    assert interpret(sketch, {})['pin_states'][8] == 'HIGH'


def test_else_if_chain():
    sketch = """
    void setup() { pinMode(8, OUTPUT); pinMode(9, OUTPUT); }
    void loop() {
      int level = 2;
      if (level == 1) { digitalWrite(8, HIGH); }
      else if (level == 2) { digitalWrite(9, HIGH); }
      else { digitalWrite(8, LOW); digitalWrite(9, LOW); }
    }
    """
    result = interpret(sketch, {})
    assert result['pin_states'][9] == 'HIGH'
    assert 8 not in result['pin_states']  # branch never taken, never written


def test_delay_is_inert_and_does_not_crash():
    sketch = """
    void setup() { pinMode(8, OUTPUT); }
    void loop() { digitalWrite(8, HIGH); delay(500); }
    """
    assert interpret(sketch, {})['pin_states'][8] == 'HIGH'


def test_input_pin_cannot_be_driven():
    # Guard mirrored from the old run(): writes to a non-OUTPUT pin are dropped.
    sketch = """
    void setup() { pinMode(8, INPUT); }
    void loop() { digitalWrite(8, HIGH); }
    """
    assert 8 not in interpret(sketch, {})['pin_states']


def test_unsupported_construct_raises_value_error():
    sketch = """
    void setup() {}
    void loop() { for (int i = 0; i < 5; i++) {} }
    """
    with pytest.raises(ValueError):
        interpret(sketch, {})


# ── Timed sequences (SIM_ENGINE_ROLLOUT_SPEC.md item 2a) ────────────────────
# A branch containing its own delay()-paced writes should produce a
# `pin_sequences` timeline instead of collapsing to a single instantaneous
# pin_states value.

def test_single_write_no_delay_has_no_sequence():
    sketch = """
    void setup() { pinMode(8, OUTPUT); }
    void loop() { digitalWrite(8, HIGH); }
    """
    result = interpret(sketch, {})
    assert result['pin_states'][8] == 'HIGH'
    assert 'pin_sequences' not in result
    assert 'sequence_duration' not in result


def test_two_writes_same_timestamp_collapse_to_no_sequence():
    # No delay() between the writes — both land at t=0, so there's only one
    # distinct timestamp once collapsed, i.e. no real timed transition.
    sketch = """
    void setup() { pinMode(8, OUTPUT); }
    void loop() { digitalWrite(8, HIGH); digitalWrite(8, LOW); }
    """
    result = interpret(sketch, {})
    assert result['pin_states'][8] == 'LOW'
    assert 'pin_sequences' not in result


def test_delay_paced_write_produces_pin_sequence():
    sketch = """
    void setup() { pinMode(8, OUTPUT); }
    void loop() {
      digitalWrite(8, HIGH);
      delay(150);
      digitalWrite(8, LOW);
    }
    """
    result = interpret(sketch, {})
    assert result['pin_sequences'][8] == [
        {'t': 0, 'state': 'HIGH'},
        {'t': 150, 'state': 'LOW'},
    ]
    assert result['sequence_duration'] == 150
    assert result['pin_states'][8] == 'LOW'  # final value stays correct too


def test_delay_with_global_variable_argument_advances_clock():
    sketch = """
    int pulseMs = 200;
    void setup() { pinMode(8, OUTPUT); }
    void loop() {
      digitalWrite(8, HIGH);
      delay(pulseMs);
      digitalWrite(8, LOW);
    }
    """
    result = interpret(sketch, {})
    assert result['sequence_duration'] == 200
    assert result['pin_sequences'][8][1]['t'] == 200


# ── project_twelve-shaped sketch: button-held 3-LED delay chase ────────────
# Hand-resolved (directives stripped) equivalent of utils/project_twelve.py's
# SKETCH_PRESET Step 1 — same pins (12 button, 8/6/4 LEDs) and delay values
# (150ms) as the real project. This is the sketch item 2 exists to unblock:
# the old hand-authored `behaviors` `_sequence`/`_interval` macro is exactly
# the code-independent authoring this interpreter replaces.

TWELVE_RESOLVED_SKETCH = """
int switchPin = 12;
int redLED = 8;
int blueLED = 6;
int clearLED = 4;

void setup() {
  pinMode(switchPin, INPUT_PULLUP);
  pinMode(redLED, OUTPUT);
  pinMode(blueLED, OUTPUT);
  pinMode(clearLED, OUTPUT);
}

void loop()
{
  if (digitalRead(switchPin) == LOW)
  {
    digitalWrite(redLED, HIGH);
    delay(150);
    digitalWrite(redLED, LOW);

    digitalWrite(blueLED, HIGH);
    delay(150);
    digitalWrite(blueLED, LOW);

    digitalWrite(clearLED, HIGH);
    delay(150);
    digitalWrite(clearLED, LOW);
  }
  else
  {
    digitalWrite(redLED, LOW);
    digitalWrite(blueLED, LOW);
    digitalWrite(clearLED, LOW);
  }
}
"""


def test_twelve_button_pressed_produces_staggered_chase_sequence():
    result = interpret(TWELVE_RESOLVED_SKETCH, input_state={12: 0})  # pressed

    assert result['pin_sequences'][8] == [
        {'t': 0, 'state': 'HIGH'}, {'t': 150, 'state': 'LOW'},
    ]
    assert result['pin_sequences'][6] == [
        {'t': 150, 'state': 'HIGH'}, {'t': 300, 'state': 'LOW'},
    ]
    assert result['pin_sequences'][4] == [
        {'t': 300, 'state': 'HIGH'}, {'t': 450, 'state': 'LOW'},
    ]
    assert result['sequence_duration'] == 450


def test_twelve_button_released_all_off_no_sequence():
    result = interpret(TWELVE_RESOLVED_SKETCH, input_state={12: 1})  # not pressed

    assert result['pin_states'][8] == 'LOW'
    assert result['pin_states'][6] == 'LOW'
    assert result['pin_states'][4] == 'LOW'
    assert 'pin_sequences' not in result


# ── eight-shaped sketch: re-triggerable blink-while-true branch ────────────
# Same shape as utils/project_eight.py's dark-branch (if/else, one branch
# with a delay-paced blink+tone that repeats every pass, the other a steady
# state) but using digitalRead instead of analogRead/A0 — the real sketch
# can't be interpret()-ed yet because A0 isn't in _CONSTANTS (unrelated
# pre-existing gap, not this test's concern).

EIGHT_SHAPED_SKETCH = """
void setup() {
  pinMode(9, INPUT_PULLUP);
  pinMode(13, OUTPUT);
  pinMode(8, OUTPUT);
}

void loop() {
  if (digitalRead(9) == LOW) {
    digitalWrite(13, HIGH);
    tone(8, 800);
    delay(150);
    digitalWrite(13, LOW);
    noTone(8);
    delay(150);
  } else {
    digitalWrite(13, LOW);
    noTone(8);
    delay(100);
  }
}
"""


def test_eight_shaped_dark_branch_produces_blink_sequence():
    result = interpret(EIGHT_SHAPED_SKETCH, input_state={9: 0})  # condition true

    assert result['pin_sequences'][13] == [
        {'t': 0, 'state': 'HIGH'}, {'t': 150, 'state': 'LOW'},
    ]
    assert result['pin_sequences'][8] == [
        {'t': 0, 'state': 'HIGH'}, {'t': 150, 'state': 'LOW'},
    ]
    assert result['sequence_duration'] == 300


def test_eight_shaped_bright_branch_has_no_sequence():
    result = interpret(EIGHT_SHAPED_SKETCH, input_state={9: 1})  # condition false

    assert result['pin_states'][13] == 'LOW'
    assert result['pin_states'][8] == 'LOW'
    assert 'pin_sequences' not in result


# ── Phase 1 (SIM_ENGINE_ROLLOUT_SPEC.md item 4): arithmetic, new types,
#    millis()/micros(), pulseIn, and persistent state across interpret() calls
# ─────────────────────────────────────────────────────────────────────────

def test_arithmetic_operators():
    sketch = """
    void setup() { pinMode(8, OUTPUT); }
    void loop() {
      int a = 10;
      int b = 3;
      int sum = a + b;
      int diff = a - b;
      int prod = a * b;
      int quot = a / b;
      int rem = a % b;
      if (sum == 13 && diff == 7 && prod == 30 && quot == 3 && rem == 1) {
        digitalWrite(8, HIGH);
      } else {
        digitalWrite(8, LOW);
      }
    }
    """
    assert interpret(sketch, {})['pin_states'][8] == 'HIGH'


def test_unary_minus():
    sketch = """
    void setup() { pinMode(8, OUTPUT); }
    void loop() {
      int x = 5;
      int y = -x + 10;
      if (y == 5) { digitalWrite(8, HIGH); } else { digitalWrite(8, LOW); }
    }
    """
    assert interpret(sketch, {})['pin_states'][8] == 'HIGH'


def test_float_literal_and_division():
    sketch = """
    void setup() { pinMode(8, OUTPUT); }
    void loop() {
      float distance = 0.20;
      float half = distance / 2;
      if (half == 0.1) { digitalWrite(8, HIGH); } else { digitalWrite(8, LOW); }
    }
    """
    assert interpret(sketch, {})['pin_states'][8] == 'HIGH'


def test_unsigned_long_and_long_types_parse():
    sketch = """
    unsigned long a = 0;
    long b = -5;
    void setup() { pinMode(8, OUTPUT); }
    void loop() {
      if (a == 0 && b == -5) { digitalWrite(8, HIGH); } else { digitalWrite(8, LOW); }
    }
    """
    assert interpret(sketch, {})['pin_states'][8] == 'HIGH'


def test_pulse_in_reads_duration_from_input_state():
    # Same shape as project `eighteen`'s sonar reads: pulseIn's "duration" is
    # supplied directly by the (future) sonar component via input_state,
    # keyed by the echo pin — same pattern as digitalRead/analogRead.
    sketch = """
    int echoPin = 3;
    void setup() { pinMode(echoPin, INPUT); pinMode(8, OUTPUT); }
    void loop() {
      long duration = pulseIn(echoPin, HIGH);
      long distance = duration * 0.034 / 2;
      if (distance < 30) { digitalWrite(8, HIGH); } else { digitalWrite(8, LOW); }
    }
    """
    assert interpret(sketch, {3: 1000})['pin_states'][8] == 'HIGH'  # distance=17
    assert interpret(sketch, {3: 3000})['pin_states'][8] == 'LOW'   # distance=51


def test_delay_microseconds_and_serial_begin_are_inert():
    sketch = """
    void setup() { Serial.begin(9600); pinMode(8, OUTPUT); }
    void loop() { digitalWrite(8, HIGH); delayMicroseconds(10); digitalWrite(8, LOW); }
    """
    result = interpret(sketch, {})
    assert result['pin_states'][8] == 'LOW'
    assert 'console_lines' not in result


def test_serial_println_appends_console_lines():
    sketch = """
    void setup() {}
    void loop() { Serial.println(42); Serial.println("done"); }
    """
    result = interpret(sketch, {})
    assert result['console_lines'] == ['42', 'done']


def test_stateless_call_still_reruns_globals_and_setup_every_time():
    # Regression guard: existing callers that never pass `state` (every test
    # above this section) must keep getting the pre-Phase-1 behaviour —
    # globals + setup() re-run fresh on every single call.
    sketch = """
    int counter = 0;
    void setup() { pinMode(8, OUTPUT); }
    void loop() {
      counter = counter + 1;
      if (counter == 1) { digitalWrite(8, HIGH); } else { digitalWrite(8, LOW); }
    }
    """
    assert interpret(sketch, {})['pin_states'][8] == 'HIGH'
    assert interpret(sketch, {})['pin_states'][8] == 'HIGH'  # still 1st iter, not 2nd


# ── project_thirteen's real reaction-timer sketch — persistent `running`/
#    `startTime` state and millis() across two discrete button presses ─────
# Hand-resolved (directives stripped) equivalent of
# utils/project_thirteen.py's SKETCH_PRESET Step 1.

THIRTEEN_RESOLVED_SKETCH = """
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
"""


def test_thirteen_reaction_timer_persists_state_across_press_and_release():
    # Call 1 — power-on + first press: starts the clock.
    r1 = interpret(THIRTEEN_RESOLVED_SKETCH, input_state={2: 0}, now_ms=1000.0)
    assert 'console_lines' not in r1  # nothing printed yet, just armed

    # Call 2 — release: outer `if` is false (idle/HIGH), nothing happens,
    # but `running`/`startTime` must survive into call 3.
    r2 = interpret(THIRTEEN_RESOLVED_SKETCH, input_state={2: 1}, state=r1['_state'], now_ms=1200.0)
    assert 'console_lines' not in r2

    # Call 3 — second press, 500ms after the first: stops the clock and
    # prints the reaction time. This is the exact case the old regex-replay
    # engine (and the pre-Phase-1 interpreter) can't represent at all —
    # neither has any notion of "time elapsed since an earlier call".
    r3 = interpret(THIRTEEN_RESOLVED_SKETCH, input_state={2: 0}, state=r2['_state'], now_ms=1500.0)
    assert r3['console_lines'] == ['500']


def test_thirteen_reaction_timer_state_is_json_safe():
    r1 = interpret(THIRTEEN_RESOLVED_SKETCH, input_state={2: 0}, now_ms=1000.0)
    import json
    json.dumps(r1['_state'])  # must not raise


# ── project_eighteen's real dual-sonar speed trap — verifies the
#    interpreter alone (no sim_config/frontend wiring; see rollout spec item
#    4's "not done yet" note) correctly evaluates persistent sawA/sawB flags,
#    micros()-based timing, and the float speed calculation against the
#    project's actual, unmodified Step 10 sketch. ─────────────────────────

EIGHTEEN_RESOLVED_SKETCH = """
int trigA = 2;
int echoA = 3;
int trigB = 4;
int echoB = 5;

float distance = 0.20;
unsigned long timeA = 0;
bool sawA = false;
unsigned long timeB = 0;
bool sawB = false;

void setup() {
  Serial.begin(9600);
  pinMode(trigA, OUTPUT);
  pinMode(echoA, INPUT);
  pinMode(trigB, OUTPUT);
  pinMode(echoB, INPUT);
  Serial.println("Ready!");
}

void loop() {
  digitalWrite(trigA, LOW);
  delayMicroseconds(2);
  digitalWrite(trigA, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigA, LOW);
  long durationA = pulseIn(echoA, HIGH);
  long distanceA = durationA * 0.034 / 2;
  digitalWrite(trigB, LOW);
  delayMicroseconds(2);
  digitalWrite(trigB, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigB, LOW);
  long durationB = pulseIn(echoB, HIGH);
  long distanceB = durationB * 0.034 / 2;
  if (distanceA < 30 && sawA == false) {
    timeA = micros();
    sawA = true;
    Serial.println("Saw A");
  }
  if (distanceB < 30 && sawA == true && sawB == false) {
    timeB = micros();
    sawB = true;
    Serial.println("Saw B");
  }
  if (sawA == true && sawB == true) {
    float timeDiff = (timeB - timeA) / 1000000.0;
    float speed = distance / timeDiff;
    Serial.print("Speed m/s: ");
    Serial.println(speed);
    sawA = false;
    sawB = false;
    delay(1000);
  }
}
"""


def test_eighteen_speed_trap_persists_sawA_across_calls_and_computes_speed():
    # Pass 1: object is near Sensor A (echoA=pin 3, duration 1000us -> 17cm),
    # far from Sensor B (echoB=pin 5, duration 3000us -> 51cm). Sensor A fires.
    r1 = interpret(
        EIGHTEEN_RESOLVED_SKETCH, input_state={3: 1000, 5: 3000}, now_ms=1_000_000.0,
    )
    assert r1['console_lines'] == ['Ready!', 'Saw A']  # setup() ran once, then Sensor A

    # Pass 2, 500ms later: object has moved on — now near Sensor B, clear of
    # A. sawA must have survived from pass 1 (restored from `_state`) for the
    # `sawA == true` half of Sensor B's guard to pass; the speed calc uses
    # `timeB - timeA`, which only works if timeA also survived.
    r2 = interpret(
        EIGHTEEN_RESOLVED_SKETCH, input_state={3: 3000, 5: 1000},
        state=r1['_state'], now_ms=1_000_500.0,
    )
    assert r2['console_lines'] == ['Saw B', 'Speed m/s: ', '0.4']
    # distance (0.20m) / timeDiff (0.5s) = 0.4 m/s

    # Pass 3: sawA/sawB were reset by the speed-calc branch — Sensor A must
    # be able to fire again for the next run without a stale flag blocking it.
    r3 = interpret(
        EIGHTEEN_RESOLVED_SKETCH, input_state={3: 1000, 5: 3000},
        state=r2['_state'], now_ms=1_002_000.0,
    )
    assert r3['console_lines'] == ['Saw A']


# ── Phase 2 (SIM_ENGINE_ROLLOUT_SPEC.md item 5): map() + continuous
#    tone() pitch capture, instead of collapsing to on/off ─────────────────

def test_map_basic_range_remap():
    sketch = """
    void setup() { pinMode(8, OUTPUT); }
    void loop() {
      int pitch = map(25, 5, 50, 200, 1000);
      if (pitch == 555) { digitalWrite(8, HIGH); } else { digitalWrite(8, LOW); }
    }
    """
    assert interpret(sketch, {})['pin_states'][8] == 'HIGH'


def test_map_truncates_float_input_toward_zero_like_arduinos_long_cast():
    # Arduino's map() takes `long` params — a float x narrows the same way an
    # implicit cast would (truncate toward zero: 25.9 -> 25, not rounded to
    # 26), so map(25.9, 5, 50, 200, 1000) == map(25, 5, 50, 200, 1000) == 555.
    sketch = """
    void setup() { pinMode(8, OUTPUT); }
    void loop() {
      float x = 25.9;
      int pitch = map(x, 5, 50, 200, 1000);
      if (pitch == 555) { digitalWrite(8, HIGH); } else { digitalWrite(8, LOW); }
    }
    """
    assert interpret(sketch, {})['pin_states'][8] == 'HIGH'


def test_map_endpoints():
    sketch = """
    void setup() { pinMode(8, OUTPUT); pinMode(9, OUTPUT); }
    void loop() {
      int lo = map(5, 5, 50, 200, 1000);
      int hi = map(50, 5, 50, 200, 1000);
      if (lo == 200) { digitalWrite(8, HIGH); }
      if (hi == 1000) { digitalWrite(9, HIGH); }
    }
    """
    result = interpret(sketch, {})
    assert result['pin_states'][8] == 'HIGH'
    assert result['pin_states'][9] == 'HIGH'


def test_map_zero_span_input_raises_value_error():
    sketch = """
    void setup() {}
    void loop() { int pitch = map(10, 5, 5, 200, 1000); }
    """
    with pytest.raises(ValueError):
        interpret(sketch, {})


def test_tone_with_frequency_populates_pin_frequencies():
    sketch = """
    void setup() { pinMode(3, OUTPUT); }
    void loop() { tone(3, 620); }
    """
    result = interpret(sketch, {})
    assert result['pin_states'][3] == 'HIGH'
    assert result['pin_frequencies'] == {3: 620}


def test_no_tone_clears_pin_frequencies():
    # A pin that's been noTone()'d ends the pass LOW — its stale last
    # frequency shouldn't be reported, since nothing is actually sounding.
    sketch = """
    void setup() { pinMode(3, OUTPUT); }
    void loop() { tone(3, 620); noTone(3); }
    """
    result = interpret(sketch, {})
    assert result['pin_states'][3] == 'LOW'
    assert 'pin_frequencies' not in result


def test_tone_without_frequency_arg_has_no_pin_frequencies():
    # Real Arduino also supports tone(pin) taking a previously-set frequency,
    # but no project here calls it that way — this just guards that omitting
    # the arg doesn't crash and doesn't fabricate a frequency.
    sketch = """
    void setup() { pinMode(3, OUTPUT); }
    void loop() { tone(3); }
    """
    result = interpret(sketch, {})
    assert result['pin_states'][3] == 'HIGH'
    assert 'pin_frequencies' not in result


# ── project_seventeen's real Mission Complete sketch — sonar distance
#    mapped through map() into a continuous buzzer pitch, no discrete zones.
#    This is exactly the sketch `interpret()` couldn't run at all before
#    Phase 2 (map() raised "not supported by the sim interpreter yet"), and
#    the case the shipped `behaviors` config got wrong (SIM_ENGINE_ROLLOUT_
#    SPEC.md's "Bug found during this audit" — 3 hand-authored zones copied
#    from project fifteen, onto a sketch that has none). ─────────────────

def _duration_for_cm(distance_cm):
    # Inverse of the sketch's own distance = duration * 0.034 / 2.
    return distance_cm * 2 / 0.034


def test_seventeen_near_hand_produces_low_pitch():
    sketch = project_seventeen.SKETCH_PRESET['sketch']
    result = interpret(sketch, input_state={10: _duration_for_cm(5)})
    assert result['pin_frequencies'][3] == 200


def test_seventeen_far_hand_produces_high_pitch():
    sketch = project_seventeen.SKETCH_PRESET['sketch']
    result = interpret(sketch, input_state={10: _duration_for_cm(50)})
    assert result['pin_frequencies'][3] == 1000


def test_seventeen_pitch_varies_continuously_not_in_three_zones():
    # The old `behaviors` config only ever produced one of 3 fixed states
    # (safe/warning/danger). The real sketch has no zones at all — distinct
    # distances anywhere in range must produce distinct pitches.
    sketch = project_seventeen.SKETCH_PRESET['sketch']
    pitches = [
        interpret(sketch, input_state={10: _duration_for_cm(d)})['pin_frequencies'][3]
        for d in (5, 15, 27, 38, 50)
    ]
    assert pitches == sorted(pitches)
    assert len(set(pitches)) == len(pitches)  # every distance gives a distinct pitch


# ── Phase 3 (SIM_ENGINE_ROLLOUT_SPEC.md item 6): Servo actuator ────────────
# `Servo <name>;` + `#include <Servo.h>`, `.attach(pin)`, `.write(angle)`.
# Mechanism tests first, then project_nineteen's real, unmodified gate
# sketch end-to-end (hand-resolved — directives stripped — same convention
# as eleven/twelve/thirteen/eighteen above, since the raw //>>-annotated
# SKETCH_PRESET has //## lines whose *code* is still comment-prefixed, per
# BLOCK_BUILDER_SYNC.md; only project_seventeen's single-step preset happens
# to have no such directives left to strip).

def test_servo_include_is_stripped_and_attach_write_produce_angle():
    sketch = """
    #include <Servo.h>
    Servo gate;
    void setup() {
      gate.attach(9);
      gate.write(45);
    }
    void loop() {}
    """
    result = interpret(sketch, {})
    assert result['servo_angles'] == {9: 45}
    assert 'servo_sequences' not in result


def test_servo_single_write_no_delay_has_no_sequence():
    sketch = """
    Servo gate;
    void setup() { gate.attach(9); }
    void loop() { gate.write(90); }
    """
    result = interpret(sketch, {})
    assert result['servo_angles'] == {9: 90}
    assert 'servo_sequences' not in result


def test_servo_delay_paced_writes_produce_sequence():
    sketch = """
    Servo gate;
    void setup() { gate.attach(9); }
    void loop() {
      gate.write(90);
      delay(2000);
      gate.write(0);
    }
    """
    result = interpret(sketch, {})
    assert result['servo_sequences'] == {9: [{'t': 0, 'angle': 90}, {'t': 2000, 'angle': 0}]}
    assert result['sequence_duration'] == 2000


def test_servo_write_before_attach_raises_value_error():
    sketch = """
    Servo gate;
    void setup() {}
    void loop() { gate.write(90); }
    """
    with pytest.raises(ValueError):
        interpret(sketch, {})


def test_servo_declared_but_never_written_has_no_servo_angles():
    sketch = """
    Servo gate;
    void setup() { gate.attach(9); }
    void loop() {}
    """
    result = interpret(sketch, {})
    assert 'servo_angles' not in result
    assert 'servo_sequences' not in result


def test_servo_attach_persists_across_calls_via_state():
    # attach() runs once in setup(); a later call with `state` provided
    # skips globals/setup() entirely (Phase 1 semantics) — write() must
    # still resolve the servo's pin from the *restored* servo_pins, not
    # re-run attach() itself.
    sketch = """
    Servo gate;
    int p = 9;
    void setup() { gate.attach(p); }
    void loop() { gate.write(45); }
    """
    r1 = interpret(sketch, {})
    assert r1['servo_angles'] == {9: 45}
    r2 = interpret(sketch, {}, state=r1['_state'])
    assert r2['servo_angles'] == {9: 45}


def test_servo_state_is_json_safe():
    sketch = """
    Servo gate;
    void setup() { gate.attach(9); }
    void loop() { gate.write(45); }
    """
    result = interpret(sketch, {})
    import json
    json.dumps(result['_state'])  # must not raise


# ── project_nineteen's real gate sketch — button press swings the servo to
#    90°, lights the LED, holds 2 seconds via delay(), then closes both.
#    Hand-resolved equivalent of the Mission Complete state (all //##/
#    //?? directives stripped, matching what the block builder would
#    actually send). ──────────────────────────────────────────────────────

NINETEEN_RESOLVED_SKETCH = """
#include <Servo.h>
Servo gateServo;
int servoPin = 9;
int buttonPin = 4;
int ledPin = 7;

void setup() {
  gateServo.attach(servoPin);
  pinMode(buttonPin, INPUT_PULLUP);
  pinMode(ledPin, OUTPUT);
  gateServo.write(0);
}

void loop() {
  int buttonState = digitalRead(buttonPin);
  if (buttonState == LOW) {
    gateServo.write(90);
    digitalWrite(ledPin, HIGH);
    delay(2000);
    gateServo.write(0);
    digitalWrite(ledPin, LOW);
  }
}
"""


def test_nineteen_idle_gate_closed():
    result = interpret(NINETEEN_RESOLVED_SKETCH, input_state={})  # pin 4 idle HIGH (pullup)
    assert result['servo_angles'] == {9: 0}
    assert 'servo_sequences' not in result


def test_nineteen_button_press_sweeps_gate_open_then_closed_with_led():
    result = interpret(NINETEEN_RESOLVED_SKETCH, input_state={4: 0})  # pressed pulls pin LOW
    assert result['servo_sequences'] == {9: [{'t': 0, 'angle': 90}, {'t': 2000, 'angle': 0}]}
    assert result['pin_sequences'] == {7: [{'t': 0, 'state': 'HIGH'}, {'t': 2000, 'state': 'LOW'}]}
    assert result['sequence_duration'] == 2000


def test_nineteen_button_release_after_press_does_nothing_this_pass():
    # The sketch has no `else` — a released-button pass, after the previous
    # press's sequence already played out client-side, writes nothing new.
    r1 = interpret(NINETEEN_RESOLVED_SKETCH, input_state={4: 0})
    r2 = interpret(NINETEEN_RESOLVED_SKETCH, input_state={4: 1}, state=r1['_state'])
    assert r2['pin_states'] == {}
    assert 'servo_angles' not in r2
    assert 'servo_sequences' not in r2


def test_nineteen_servo_pin_attach_learned_from_real_sketch():
    result = interpret(NINETEEN_RESOLVED_SKETCH, input_state={})
    assert result['_state']['servo_pins'] == {'gateServo': 9}
