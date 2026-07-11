"""
tests/test_sim_run_route.py — route-level tests for the /sim/run dispatch
added in SIM_ENGINE_ROLLOUT_SPEC.md step 1b: sim_config.mode == "interpreted"
should route to utils.sim_engine.interpret() (the real Phase 0 interpreter)
instead of the regex-replay run(), and should thread the request's
input_state through untouched.

Follows the pytest-flask pattern from tests/test_try_it_routes.py — app/client
fixtures come from tests/conftest.py. /sim/run additionally requires a
logged-in session (login_required) and calls award_simulator_badge, which
hits Supabase — both handled per-test below.
"""

import pytest

import utils.project_three as project_three


@pytest.fixture(autouse=True)
def _disable_csrf(app):
    app.config["WTF_CSRF_ENABLED"] = False


@pytest.fixture(autouse=True)
def _no_badge_write(monkeypatch):
    # sim_run() does `from utils.badges import award_simulator_badge` inline,
    # so the patch target is the source module, not routes.builder's namespace.
    # It hits Supabase; irrelevant to routing behavior under test here.
    monkeypatch.setattr("utils.badges.award_simulator_badge", lambda user_id: None)


@pytest.fixture
def logged_in_client(client):
    with client.session_transaction() as sess:
        sess["user_id"] = "student-123"
    return client


def test_interpreted_mode_button_not_pressed_led_off(logged_in_client):
    sketch = project_three.SKETCH_PRESET['sketch']
    resp = logged_in_client.post("/sim/run", json={
        "sketch": sketch,
        "sim_config": {"mode": "interpreted"},
        "input_state": {},
    })
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["pin_states"]["8"] == "LOW"
    assert body["pin_modes"]["2"] == "INPUT_PULLUP"


def test_interpreted_mode_button_pressed_led_on(logged_in_client):
    sketch = project_three.SKETCH_PRESET['sketch']
    resp = logged_in_client.post("/sim/run", json={
        "sketch": sketch,
        "sim_config": {"mode": "interpreted"},
        "input_state": {"2": 0},
    })
    assert resp.status_code == 200
    assert resp.get_json()["pin_states"]["8"] == "HIGH"


def test_interpreted_mode_missing_input_state_defaults_to_idle(logged_in_client):
    # No input_state key at all — server must not crash, should fall back
    # to interpret()'s own idle defaults (pullup idle = HIGH = not pressed).
    sketch = project_three.SKETCH_PRESET['sketch']
    resp = logged_in_client.post("/sim/run", json={
        "sketch": sketch,
        "sim_config": {"mode": "interpreted"},
    })
    assert resp.status_code == 200
    assert resp.get_json()["pin_states"]["8"] == "LOW"


def test_interpreted_mode_bad_sketch_returns_400(logged_in_client):
    resp = logged_in_client.post("/sim/run", json={
        "sketch": "void loop() { for (int i = 0; i < 5; i++) {} }",
        "sim_config": {"mode": "interpreted"},
    })
    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_interpreted_mode_delay_paced_write_returns_pin_sequences(logged_in_client):
    # SIM_ENGINE_ROLLOUT_SPEC.md item 2a: a branch with its own delay()-paced
    # writes should round-trip pin_sequences/sequence_duration through the
    # route untouched, alongside the usual pin_states/pin_modes.
    sketch = (
        "void setup() { pinMode(8, OUTPUT); }\n"
        "void loop() { digitalWrite(8, HIGH); delay(150); digitalWrite(8, LOW); }"
    )
    resp = logged_in_client.post("/sim/run", json={
        "sketch": sketch,
        "sim_config": {"mode": "interpreted"},
        "input_state": {},
    })
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["pin_sequences"]["8"] == [
        {"t": 0, "state": "HIGH"}, {"t": 150, "state": "LOW"},
    ]
    assert body["sequence_duration"] == 150


def test_missing_mode_still_uses_regex_replay_run(logged_in_client):
    # Regression guard: sim_config without mode (or mode != "interpreted")
    # must keep going through the old timeline-producing run(), not
    # interpret() — existing code_driven tabs must be unaffected by 1b.
    sketch = (
        "void setup() { pinMode(13, OUTPUT); }\n"
        "void loop() { digitalWrite(13, HIGH); delay(500); }"
    )
    resp = logged_in_client.post("/sim/run", json={
        "sketch": sketch,
        "sim_config": {"pins": {"13": {"type": "led"}}},
    })
    assert resp.status_code == 200
    body = resp.get_json()
    assert "duration" in body and "components" in body
    assert "pin_states" not in body


def test_interpreted_mode_round_trips_persistent_state(logged_in_client):
    # SIM_ENGINE_ROLLOUT_SPEC.md item 4 (Phase 1): a `state` blob returned
    # from one call should be accepted back on the next and change the
    # result — proof the route actually threads it into interpret() rather
    # than dropping it. A `counter` global only reaches 2 if state persisted;
    # otherwise `setup()`/globals re-run every time and it'd be stuck at 1.
    sketch = (
        "int counter = 0;\n"
        "void setup() { pinMode(8, OUTPUT); }\n"
        "void loop() {\n"
        "  counter = counter + 1;\n"
        "  if (counter == 2) { digitalWrite(8, HIGH); } else { digitalWrite(8, LOW); }\n"
        "}\n"
    )
    resp1 = logged_in_client.post("/sim/run", json={
        "sketch": sketch,
        "sim_config": {"mode": "interpreted"},
        "input_state": {},
    })
    body1 = resp1.get_json()
    assert body1["pin_states"]["8"] == "LOW"  # counter == 1
    assert "_state" in body1

    resp2 = logged_in_client.post("/sim/run", json={
        "sketch": sketch,
        "sim_config": {"mode": "interpreted"},
        "input_state": {},
        "state": body1["_state"],
    })
    assert resp2.get_json()["pin_states"]["8"] == "HIGH"  # counter == 2, state carried over


def test_interpreted_mode_returns_pin_frequencies_for_tone_with_pitch(logged_in_client):
    # SIM_ENGINE_ROLLOUT_SPEC.md item 5 (Phase 2): a map()'d tone() pitch
    # should round-trip as pin_frequencies through the route untouched,
    # alongside the usual pin_states/pin_modes.
    sketch = (
        "void setup() { pinMode(3, OUTPUT); }\n"
        "void loop() { int pitch = map(25, 5, 50, 200, 1000); tone(3, pitch); }"
    )
    resp = logged_in_client.post("/sim/run", json={
        "sketch": sketch,
        "sim_config": {"mode": "interpreted"},
        "input_state": {},
    })
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["pin_frequencies"]["3"] == 555
    assert body["pin_states"]["3"] == "HIGH"


def test_interpreted_mode_returns_servo_sequences_for_delay_paced_gate(logged_in_client):
    # SIM_ENGINE_ROLLOUT_SPEC.md item 6 (Phase 3): a servo swept, held via
    # delay(), then swept back should round-trip servo_sequences/
    # servo_angles/sequence_duration through the route untouched, alongside
    # the usual pin_states/pin_modes — same shape 2a proved for pin_sequences.
    sketch = (
        "#include <Servo.h>\n"
        "Servo gate;\n"
        "void setup() { gate.attach(9); }\n"
        "void loop() { gate.write(90); delay(2000); gate.write(0); }\n"
    )
    resp = logged_in_client.post("/sim/run", json={
        "sketch": sketch,
        "sim_config": {"mode": "interpreted"},
        "input_state": {},
    })
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["servo_sequences"]["9"] == [
        {"t": 0, "angle": 90}, {"t": 2000, "angle": 0},
    ]
    assert body["sequence_duration"] == 2000


def test_interpreted_mode_servo_write_before_attach_returns_400(logged_in_client):
    sketch = (
        "Servo gate;\n"
        "void setup() {}\n"
        "void loop() { gate.write(90); }\n"
    )
    resp = logged_in_client.post("/sim/run", json={
        "sketch": sketch,
        "sim_config": {"mode": "interpreted"},
        "input_state": {},
    })
    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_sim_run_requires_login(client):
    resp = client.post("/sim/run", json={
        "sketch": "void setup(){} void loop(){}",
        "sim_config": {"mode": "interpreted"},
    })
    assert resp.status_code in (302, 401, 403)
