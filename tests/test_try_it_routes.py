"""
tests/test_try_it_routes.py — route-level tests for the anonymous /try
blueprint (routes/try_it.py). Follows the pytest-flask pattern from
tests/test_help_route.py: app/client fixtures come from tests/conftest.py.
"""

import pytest


@pytest.fixture(autouse=True)
def _disable_csrf(app):
    app.config["WTF_CSRF_ENABLED"] = False


def test_try_page_loads_without_login(client):
    resp = client.get("/try")
    assert resp.status_code == 200


def test_try_builder_fragment_has_no_login_gate(client):
    resp = client.get("/try/builder")
    assert resp.status_code == 200
    assert b"try_it" in resp.data


def test_try_parse_rejects_oversized_sketch(client):
    huge_code = "x" * 3000
    resp = client.post("/try/parse", json={"code": huge_code})
    assert resp.status_code == 400


def test_try_sim_ignores_client_loop_iterations(client):
    sketch = (
        "void setup() { pinMode(13, OUTPUT); }\n"
        "void loop() { digitalWrite(13, HIGH); delay(500); "
        "digitalWrite(13, LOW); delay(500); }"
    )
    resp = client.post("/try/sim", json={
        "sketch": sketch,
        "sim_config": {"pins": {"13": {"type": "led"}}, "loop_iterations": 999999, "max_ms": 999999999},
    })
    assert resp.status_code == 200
    body = resp.get_json()
    # 4 loop iterations x 1000ms/cycle, clamped server-side regardless of
    # the client's requested 999999999 max_ms.
    assert body["duration"] <= 12000


def test_try_sim_rejects_too_many_pins(client):
    sketch = "void setup() {}\nvoid loop() {}"
    pins = {str(i): {"type": "led"} for i in range(10)}
    resp = client.post("/try/sim", json={"sketch": sketch, "sim_config": {"pins": pins}})
    assert resp.status_code == 400


def test_try_lead_requires_consent(client):
    resp = client.post("/try/lead", json={"email": "a@example.com", "consent": False})
    assert resp.status_code == 400


def test_try_lead_honeypot_returns_ok_without_writing(client, monkeypatch):
    calls = []
    monkeypatch.setattr("routes.try_it.create_lead", lambda *a, **k: calls.append(1))
    resp = client.post("/try/lead", json={
        "email": "bot@example.com", "consent": True, "website": "http://spam.example",
    })
    assert resp.status_code == 200
    assert calls == []


def test_try_lead_success_sets_session(client, monkeypatch):
    monkeypatch.setattr(
        "routes.try_it.create_lead",
        lambda email, source: {"id": "lead-1", "email": email},
    )
    resp = client.post("/try/lead", json={"email": "parent@example.com", "consent": True})
    assert resp.status_code == 200
    with client.session_transaction() as sess:
        assert sess["try_email_captured"] is True
        assert sess["try_lead_email"] == "parent@example.com"
