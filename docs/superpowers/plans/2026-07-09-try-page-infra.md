# /try Page Infrastructure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the anonymous `/try` trial experience — a curated, no-login block-builder page with a Monaco toggle and simulated hardware feedback, gated by a one-time email capture after step 1, plus the supporting `leads` table and a weekly (not instant) follow-up cron script.

**Architecture:** A new anonymous Flask blueprint (`routes/try_it.py`) serves a trimmed copy of the existing hardware IDE template (with all compile/upload/serial-agent chrome removed) sourced from a new bespoke project module (`utils/project_try_it.py`). The sim endpoint reuses the existing regex-based `utils/sim_engine.py` (no code execution, so no sandbox-escape risk) behind IP rate limits and clamped inputs. Email capture writes to a new `leads` table, kept separate from `users` so the paid-customer-only invariant holds; a standalone cron script (mirroring the existing `utils/purge_deleted_accounts.py` pattern) sends one batched weekly reminder.

**Tech Stack:** Flask, Supabase (Postgres via `supabase-py`), Flask-Limiter, vanilla JS (existing `block_builder.js`/`sim-engine.js`/Monaco), pytest + `responses`/`respx` for Supabase mocking (see `tests/conftest.py`).

## Global Constraints

- Spec of record: `docs/superpowers/specs/2026-07-09-try-page-infra-design.md` — every task below implements a section of it.
- No `@login_required` on anything under `/try*` — this is the anonymous surface.
- No arbitrary code execution risk to guard against on `/try/sim` — `utils.sim_engine.run()` is regex extraction only, confirmed by reading it; the real abuse surface is input volume, handled by length caps + clamped `sim_config` + IP rate limiting via the existing `extensions.limiter`.
- Anonymous endpoints never leak `str(exception)` in error responses (existing `/sim/run` does this — do not copy that pattern).
- `leads` table is separate from `users` — never insert a lead as a `users` row.
- Email-gate persistence uses Flask's default (non-permanent) session — dies on browser close. Do not set `session.permanent = True` for this flag.
- `utils/project_try_it.py` ships with a real, working 2-step LED-blink sketch as functional scaffold content (not a placeholder) — the fully curated version is an explicit follow-up spec, noted as such in the module's module-docstring, not built here.

---

### Task 1: `leads` table migration + `utils/leads.py` data helpers

**Files:**
- Create: `migrations/add_leads_table.sql`
- Create: `utils/leads.py`
- Test: `tests/test_leads.py`

**Interfaces:**
- Produces: `utils.leads.create_lead(email: str, source: str) -> dict` (raises nothing; returns the inserted row or `None` on failure), `utils.leads.get_unfollowed_leads() -> list[dict]`, `utils.leads.mark_followed_up(lead_id: str) -> None`, `utils.leads.email_exists_in_users(email: str) -> bool`.

- [ ] **Step 1: Write the migration SQL**

```sql
-- Migration: add leads table
-- Run in the Supabase SQL editor before deploying the /try page.
-- Leads are deliberately NOT rows in `users` — every `users` row must stay
-- either a paying or admin-provisioned account (see docs/superpowers/specs/
-- 2026-07-09-try-page-infra-design.md).

CREATE TABLE IF NOT EXISTS leads (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email             TEXT NOT NULL,
    consent_given_at  TIMESTAMPTZ NOT NULL,
    source            TEXT NOT NULL DEFAULT 'try_page',
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    followed_up_at    TIMESTAMPTZ DEFAULT NULL
);

CREATE INDEX IF NOT EXISTS idx_leads_followed_up_at ON leads (followed_up_at);
```

- [ ] **Step 2: Write `utils/leads.py`**

```python
"""
utils/leads.py — data access for the `leads` table.

Leads come from the anonymous /try page's email-capture gate (see
routes/try_it.py). Deliberately not part of utils/auth.py: leads are never
`users` rows, and this module has no session/password concerns.
"""

import datetime
from utils.db_client import supabase


def create_lead(email, source="try_page"):
    """Insert a lead row. Returns the inserted row, or None on failure."""
    resp = supabase.table("leads").insert({
        "email": email,
        "consent_given_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "source": source,
    }).execute()
    return resp.data[0] if resp.data else None


def get_unfollowed_leads():
    """Return all leads where followed_up_at IS NULL."""
    resp = supabase.table("leads").select("*").is_("followed_up_at", "null").execute()
    return resp.data or []


def mark_followed_up(lead_id):
    supabase.table("leads").update({
        "followed_up_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }).eq("id", lead_id).execute()


def email_exists_in_users(email):
    resp = supabase.table("users").select("id").eq("email", email).execute()
    return len(resp.data or []) > 0
```

- [ ] **Step 3: Write the test**

```python
"""
tests/test_leads.py — unit tests for utils/leads.py against a mocked
Supabase REST API (see tests/conftest.py's `mock_supabase` fixture, same
pattern used by tests/test_help_kb.py).
"""

from utils import leads


def test_create_lead_inserts_and_returns_row(mock_supabase):
    mock_supabase.add(
        "POST",
        "https://mock-project.supabase.co/rest/v1/leads",
        json=[{"id": "lead-1", "email": "parent@example.com", "source": "try_page"}],
        status=201,
    )
    row = leads.create_lead("parent@example.com")
    assert row["id"] == "lead-1"
    assert row["email"] == "parent@example.com"


def test_get_unfollowed_leads_returns_rows(mock_supabase):
    mock_supabase.add(
        "GET",
        "https://mock-project.supabase.co/rest/v1/leads?select=%2A&followed_up_at=is.null",
        json=[{"id": "lead-1", "email": "a@example.com", "followed_up_at": None}],
        status=200,
    )
    rows = leads.get_unfollowed_leads()
    assert len(rows) == 1
    assert rows[0]["email"] == "a@example.com"


def test_email_exists_in_users_true(mock_supabase):
    mock_supabase.add(
        "GET",
        "https://mock-project.supabase.co/rest/v1/users?select=id&email=eq.parent%40example.com",
        json=[{"id": "user-1"}],
        status=200,
    )
    assert leads.email_exists_in_users("parent@example.com") is True


def test_email_exists_in_users_false(mock_supabase):
    mock_supabase.add(
        "GET",
        "https://mock-project.supabase.co/rest/v1/users?select=id&email=eq.nobody%40example.com",
        json=[],
        status=200,
    )
    assert leads.email_exists_in_users("nobody@example.com") is False
```

- [ ] **Step 4: Run the tests**

Run: `pytest tests/test_leads.py -v`
Expected: 4 passed. (If URL query-string matching is finicky against `responses`, loosen the mocked URL to the base path — follow the existing loose-matching pattern already built into the `mock_supabase` fixture in `tests/conftest.py`, which matches on `url__startswith` when a `?` is present.)

- [ ] **Step 5: Commit**

```bash
git add migrations/add_leads_table.sql utils/leads.py tests/test_leads.py
git commit -m "Add leads table migration and data-access helpers"
```

---

### Task 2: `utils/project_try_it.py` — scaffold sketch content

**Files:**
- Create: `utils/project_try_it.py`

**Interfaces:**
- Produces: a `PROJECT` dict picked up automatically by `utils/project_registry.py`'s auto-discovery (any `utils/project_*.py` module exposing `PROJECT`) under the key `"project_try_it"`. Consumed by Task 4's routes via `from utils.project_registry import PROJECTS; PROJECTS["project_try_it"]`.

- [ ] **Step 1: Write the module**

```python
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
```

- [ ] **Step 2: Verify auto-discovery picks it up**

Run: `python -c "from utils.project_registry import PROJECTS; assert 'project_try_it' in PROJECTS; print('OK', list(PROJECTS['project_try_it']['presets']['default'].keys()))"`
Expected: `OK ['sketch', 'default_view', 'read_only', 'lock_view', 'fill_values', 'fill_conditions']` with no traceback.

- [ ] **Step 3: Verify the sketch parses into 4 steps**

Run: `python -c "from utils.block_parser import parse_steps; from utils.project_try_it import SKETCH; steps = parse_steps(SKETCH); print(len(steps), [s['label'] for s in steps])"`
Expected: `4 ['Ready!', 'Turn it ON', 'Make it blink!', 'Mission Complete']` with no traceback.

- [ ] **Step 4: Commit**

```bash
git add utils/project_try_it.py
git commit -m "Add scaffold sketch content for the /try trial page"
```

---

### Task 3: Make the sim-engine endpoint configurable

**Files:**
- Modify: `static/js/sim-engine.js:656-696` (the `initCodeDriven` function)

**Interfaces:**
- Consumes: `simConfig.endpoint` (new, optional key on the existing `sim_config` shape documented at the top of the file) — when absent, behavior is byte-for-byte identical to today (defaults to `/sim/run`), so all 19 existing lesson drawer sim tabs are unaffected.
- Produces: nothing new consumed elsewhere; this is a pure internal change.

- [ ] **Step 1: Update the docstring comment above `SimEngine`**

Find the comment block at the top of `static/js/sim-engine.js` (lines 1-21) and add one line to the `simConfig shape` section:

```
 *   endpoint    (code-driven only) — sim-run URL to POST to. Defaults to
 *               '/sim/run' when absent.
```
Insert it directly below the `behaviors:` line (currently line 7).

- [ ] **Step 2: Change the hardcoded fetch URL**

Find this in `initCodeDriven` (around line 674):

```javascript
    fetch('/sim/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ sketch: sketch, sim_config: simConfig }),
    })
```

Replace with:

```javascript
    fetch(simConfig.endpoint || '/sim/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ sketch: sketch, sim_config: simConfig }),
    })
```

- [ ] **Step 3: Manual smoke check**

Run: `grep -n "fetch(simConfig.endpoint" static/js/sim-engine.js`
Expected: one match, the line just edited.

Run: `grep -rn "sim_config" utils/project_*.py | grep -v project_try_it`
Expected: none of these existing projects' `sim_config` dicts contain an `endpoint` key (confirms the default-to-`/sim/run` fallback keeps them working unchanged).

- [ ] **Step 4: Commit**

```bash
git add static/js/sim-engine.js
git commit -m "Make SimEngine.initCodeDriven's sim-run endpoint configurable"
```

---

### Task 4: `routes/try_it.py` — anonymous blueprint (page, builder fragment, parse, sim, lead)

**Files:**
- Create: `routes/try_it.py`
- Modify: `app.py` (register the new blueprint)
- Test: `tests/test_try_it_routes.py`

**Interfaces:**
- Consumes: `utils.project_registry.PROJECTS["project_try_it"]` (Task 2), `utils.sim_engine.run(sketch, sim_config)` (existing), `utils.block_parser.parse_steps`/`parse_sketch` (existing), `utils.leads.create_lead(email, source)` (Task 1), `extensions.limiter`/`extensions.csrf` (existing).
- Produces: Flask blueprint `try_it_bp` registered at no prefix, exposing `GET /try`, `GET /try/builder`, `POST /try/parse`, `POST /try/sim`, `POST /try/lead`.

- [ ] **Step 1: Write `routes/try_it.py`**

```python
"""
routes/try_it.py — anonymous /try trial page.

Every route here is deliberately unauthenticated (no @login_required
anywhere in this file — that is the point of this blueprint). See
docs/superpowers/specs/2026-07-09-try-page-infra-design.md for the full
design rationale, in particular:

- Why /try/sim can safely accept client-submitted sketch code (sim_engine.run
  is regex extraction, not code execution — no sandbox to escape).
- Why the abuse boundary here is input-size caps + a clamped sim_config +
  IP rate limiting, not a bespoke abuse-prevention system.
- Why leads are a separate table, never a `users` row.
"""

import json

from flask import Blueprint, request, jsonify, render_template, session

from extensions import limiter, csrf
from utils.leads import create_lead

try_it_bp = Blueprint('try_it', __name__)

_MAX_SKETCH_CHARS = 2000
_MAX_EMAIL_CHARS = 254
_FIXED_SIM_LOOP_ITERATIONS = 4
_FIXED_SIM_MAX_MS = 12000
_MAX_SIM_PINS = 6


def _project_try_it():
    from utils.project_registry import PROJECTS
    return PROJECTS["project_try_it"]


@try_it_bp.route("/try")
def try_page():
    return render_template(
        "try_it_builder.html",
        email_captured=bool(session.get("try_email_captured")),
    )


@try_it_bp.route("/try/builder")
def try_builder_fragment():
    from utils.block_parser import parse_steps
    proj = _project_try_it()
    sketch = proj["presets"]["default"]["sketch"]
    steps = parse_steps(sketch)
    drawer = proj.get("drawer", {})
    config = {
        "mode": "progression",
        "steps": steps,
        "palette": None,
        "master": None,
        "username": None,
        "page": "try_it",
        "drawer": drawer,
        "lock_mode": False,
        "is_overlay": False,
        "default_view": "blocks",
        "lock_view": False,
        "readonly_mode": False,
        "force_preset": True,
        "supabase_url": "",
        "supabase_key": "",
    }
    config_json = json.dumps(config).replace('</', '<\\/')
    return render_template("block_builder_fragment.html", config=config_json)


def _generic_error(status=400):
    return jsonify(error="Something went wrong. Please try again."), status


@try_it_bp.route("/try/parse", methods=["POST"])
@csrf.exempt
@limiter.limit("10 per minute")
@limiter.limit("100 per hour")
def try_parse():
    from utils.block_parser import parse_sketch
    data = request.get_json(silent=True) or {}
    code = data.get("code", "")
    if not isinstance(code, str) or len(code) > _MAX_SKETCH_CHARS:
        return _generic_error()
    try:
        return parse_sketch(code, fill_conditions=True, fill_values=True)
    except Exception:
        return _generic_error()


@try_it_bp.route("/try/sim", methods=["POST"])
@csrf.exempt
@limiter.limit("10 per minute")
@limiter.limit("100 per hour")
def try_sim():
    from utils.sim_engine import run as engine_run
    data = request.get_json(silent=True) or {}
    sketch = data.get('sketch', '')
    client_sim_config = data.get('sim_config', {})

    if not isinstance(sketch, str) or len(sketch) > _MAX_SKETCH_CHARS:
        return _generic_error()
    if not isinstance(client_sim_config, dict):
        return _generic_error()

    pins = client_sim_config.get('pins', {})
    if not isinstance(pins, dict) or len(pins) > _MAX_SIM_PINS:
        return _generic_error()

    # Everything except `pins` is forced server-side — loop_iterations/max_ms
    # control response size and compute, not correctness, so the client's
    # values are never trusted here.
    safe_sim_config = {
        'pins': pins,
        'loop_iterations': _FIXED_SIM_LOOP_ITERATIONS,
        'max_ms': _FIXED_SIM_MAX_MS,
    }

    try:
        return engine_run(sketch, safe_sim_config)
    except Exception:
        return _generic_error()


@try_it_bp.route("/try/lead", methods=["POST"])
@csrf.exempt
@limiter.limit("5 per minute")
@limiter.limit("20 per hour")
def try_lead():
    data = request.get_json(silent=True) or {}

    # Honeypot: a bot that fills this hidden field is told it "succeeded"
    # so it doesn't learn it was caught (see spec's Abuse boundary section).
    if data.get("website"):
        return jsonify(ok=True)

    email = (data.get("email") or "").strip()
    consent = bool(data.get("consent"))

    if not email or len(email) > _MAX_EMAIL_CHARS or "@" not in email or not consent:
        return _generic_error()

    row = create_lead(email, source="try_page")
    if not row:
        return _generic_error(500)

    session["try_email_captured"] = True
    session["try_lead_email"] = email
    return jsonify(ok=True)
```

- [ ] **Step 2: Register the blueprint in `app.py`**

In `app.py`, add the import next to the other route imports (after `from routes.account import account_bp`):

```python
from routes.try_it import try_it_bp
```

And add the registration next to the other `app.register_blueprint(...)` calls (after `app.register_blueprint(account_bp)`):

```python
app.register_blueprint(try_it_bp)
```

- [ ] **Step 3: Write the route tests**

```python
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
```

- [ ] **Step 4: Run the tests**

Run: `pytest tests/test_try_it_routes.py -v`
Expected: 8 passed.

- [ ] **Step 5: Commit**

```bash
git add routes/try_it.py app.py tests/test_try_it_routes.py
git commit -m "Add anonymous /try blueprint: page, builder fragment, parse, sim, lead capture"
```

---

### Task 5: `templates/try_it_builder.html` — trimmed IDE template

**Files:**
- Create: `templates/try_it_builder.html` (start from a copy of `templates/components/arduino_interface.html`)

**Interfaces:**
- Consumes: `email_captured` (bool, passed by `GET /try` in Task 4), fetches `GET /try/builder` (Task 4) to populate `#blocks-view` (same pattern as the existing `loadBlockBuilder()` in `arduino_interface.html`, which fetches `/builder?preset=...`), posts to `/try/parse` (Task 4) instead of `/parse`.
- Produces: the page rendered at `GET /try`.

This task is a **copy-and-trim**, not a from-scratch build — the source file already contains the Monaco/blocks toggle, drawer rendering, and sim-tab wiring this page needs; only the hardware-specific chrome needs to come out.

- [ ] **Step 1: Copy the source file**

```bash
cp templates/components/arduino_interface.html templates/try_it_builder.html
```

- [ ] **Step 2: Remove the hardware-chrome HTML elements**

In `templates/try_it_builder.html`, delete these elements entirely (identify by the `id` attributes found in the copied file — exact line numbers will shift slightly from the ones below since this is a fresh copy, search for the `id=` string to relocate them):

- The `<select id="port-select">`, `<button id="connect-btn">`, `<button id="compile-btn">`, `<button id="upload-btn">` elements inside `#top-bar` (originally around line 387-392 of `arduino_interface.html`). Keep the rest of `#top-bar` (title, `#mode-toggle-btn`, `#agent-status` — remove `#agent-status` too, see below).
- The `<div id="agent-status">...</div>` element (originally line 406) — this shows Arduino-agent connection status, irrelevant with no hardware.
- The entire `<div id="serial-monitor-overlay">...</div>` block (originally lines ~426-435).
- The entire `<div id="kclink-overlay">...</div>` block and its modal content (originally lines ~436-450) — this is the "install KidsCode Link" prompt, irrelevant with no hardware.

Keep: `#drawer-panel`/`#drawer-tab`, `#workspace`, `#blocks-view`, `#editor-view`, `#mode-toggle-btn`.

- [ ] **Step 3: Remove the hardware-chrome CSS**

Delete the `<style>` rules that only style elements removed in Step 2: `#upload-btn`, `#compile-btn`, `.orange-btn`, `#serial-monitor-overlay` and its children (`#serial-monitor-toolbar`, `#serial-monitor`), `#agent-status`, `.status-online`, `.status-offline`, `#kclink-overlay` and its children (`#kclink-modal`, `#kclink-modal-header`, `#kclink-modal-body`, and any other `#kclink-*` selectors present).

Keep: everything under `/* WORKSPACE */`, `/* BLOCKS VIEW */`, `/* EDITOR VIEW */`, and the base `body`/`button`/`select` rules.

- [ ] **Step 4: Remove the hardware-chrome JavaScript**

Delete these functions/blocks and every call site that references them:

- Any function that calls `http://127.0.0.1:52010/...` (status polling, `/ports`, `/serial/start`, `/serial/stop`, `/compile`, `/upload`) — these were found at (pre-edit) lines 757, 854, 887, 892, 967, 1007, 1097 of `arduino_interface.html`. Delete the enclosing functions (`compileSketch`, `uploadSketch`, `connectSerial`, `fetchPorts`, agent status polling, and similar) in full, not just the fetch calls.
- `openSerialMonitor()` / `closeSerialMonitor()` and the `serialMonitorOpen` variable.
- `openKCLinkModal()` / `closeKCLinkModal()` and the click-outside-to-close handler for `#kclink-overlay`.
- The event wiring block that attaches `.onclick` to the now-deleted `#refresh-ports-btn`, `#connect-btn`, `#compile-btn`, `#upload-btn` (originally lines 1224-1230).
- The `{% if preset == 'open_coding' %} ... {% endif %}` block (originally lines 1237-1286) — this is the download/load-to-PC feature, tied to a `preset` template variable `/try` doesn't pass. Delete the whole Jinja conditional block including its contents.

- [ ] **Step 5: Rewire the two remaining fetch calls**

In `loadBlockBuilder()` (kept from Step 2-4, originally around line 1123-1205), find:

```javascript
    const urlParams = new URLSearchParams(window.location.search);
    const pathParts = window.location.pathname.split('/');
    const preset = urlParams.get('preset') || pathParts[pathParts.length - 1] || 'codebreaker';
    const page = urlParams.get('page') || '';

    const response = await fetch('/builder?preset=' + preset + '&page=' + page);
```

Replace with:

```javascript
    const response = await fetch('/try/builder');
```

Find the remaining `/parse` fetch call (the one inside the Monaco→blocks conversion, not the one deleted in Step 4's `open_coding` block):

```javascript
    const res = await fetch('/parse', {
```

Replace with:

```javascript
    const res = await fetch('/try/parse', {
```

Run `grep -n "fetch('/parse'" templates/try_it_builder.html` afterward to confirm zero remaining matches, and `grep -n "fetch('/try/parse'" templates/try_it_builder.html` to confirm exactly one.

- [ ] **Step 6: Add the email-gate modal markup**

Add this just before the closing `</body>` tag:

```html
<div id="try-email-gate-overlay" style="display:none;position:fixed;inset:0;background:rgba(13,17,23,0.85);z-index:9999;align-items:center;justify-content:center;padding:20px;">
  <div id="try-email-gate-modal" style="background:#fff;border-radius:16px;max-width:420px;width:100%;padding:24px;box-shadow:0 24px 64px rgba(0,0,0,0.4);">
    <h2 style="margin:0 0 8px;font-size:18px;">Thanks for trying it out!</h2>
    <p style="margin:0 0 16px;font-size:13px;color:#475569;">Want a reminder about KidsCode? Leave your email and we'll send you one note — that's it.</p>
    <form id="try-email-gate-form">
      <input type="text" name="website" id="try-gate-honeypot" style="position:absolute;left:-9999px;" tabindex="-1" autocomplete="off">
      <input type="email" id="try-gate-email" placeholder="parent@example.com" required style="width:100%;padding:8px;margin-bottom:10px;border:1px solid #e2e8f0;border-radius:6px;">
      <label style="display:flex;gap:8px;align-items:flex-start;font-size:12px;color:#475569;margin-bottom:16px;">
        <input type="checkbox" id="try-gate-consent" required style="margin-top:2px;">
        I'd like to receive one follow-up email about KidsCode.
      </label>
      <div id="try-gate-error" style="display:none;color:#ef4444;font-size:12px;margin-bottom:10px;"></div>
      <button type="submit" style="width:100%;padding:10px;background:#22c55e;color:#020617;font-weight:600;border:none;border-radius:6px;">Continue</button>
    </form>
    <div id="try-email-gate-thanks" style="display:none;text-align:center;">
      <p style="font-size:16px;">Thanks for your interest! 🎉</p>
    </div>
  </div>
</div>

<script>
(function () {
  // BB.STEPS index whose completion should trigger the gate — index 1 is
  // "Turn it ON" in utils/project_try_it.py's SKETCH (index 0 "Ready!" is a
  // non-interactive global-only step). Verified via the parse_steps check
  // in Task 2 Step 3 of the implementation plan.
  var GATE_AFTER_STEP_INDEX = 1;
  var emailCaptured = {{ 'true' if email_captured else 'false' }};
  var overlay = document.getElementById('try-email-gate-overlay');
  var form = document.getElementById('try-email-gate-form');
  var thanks = document.getElementById('try-email-gate-thanks');
  var errorEl = document.getElementById('try-gate-error');

  function showGate(proceedFn) {
    form.style.display = '';
    thanks.style.display = 'none';
    errorEl.style.display = 'none';
    overlay.style.display = 'flex';
    form.onsubmit = function (e) {
      e.preventDefault();
      var email = document.getElementById('try-gate-email').value.trim();
      var consent = document.getElementById('try-gate-consent').checked;
      var honeypot = document.getElementById('try-gate-honeypot').value;
      fetch('/try/lead', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: email, consent: consent, website: honeypot }),
      })
        .then(function (r) { if (!r.ok) throw new Error('failed'); return r.json(); })
        .then(function () {
          emailCaptured = true;
          form.style.display = 'none';
          thanks.style.display = '';
          setTimeout(function () {
            overlay.style.display = 'none';
            proceedFn();
          }, 1200);
        })
        .catch(function () {
          errorEl.textContent = 'Something went wrong — please try again.';
          errorEl.style.display = '';
        });
    };
  }

  // window.bbNext (static/js/bb-validation.js) is the actual step-advance
  // handler wired to the Next-step button's onclick — bb_next_state is only
  // an informational event for the button's label/enabled state, it cannot
  // be used to intercept or cancel an advance. bbNext is defined inside the
  // block-builder scripts that loadBlockBuilder() injects asynchronously
  // (see /try/builder), so poll until it exists before wrapping it — same
  // defensive pattern the copied template already uses for window._bbCheckInterval.
  var installPoll = setInterval(function () {
    if (typeof window.bbNext !== 'function') return;
    clearInterval(installPoll);
    var originalBbNext = window.bbNext;
    window.bbNext = function () {
      var atGateStep = window.BB && BB.CURRENT_STEP === GATE_AFTER_STEP_INDEX;
      var isAdvanceClick = window.BB && BB.nextBtnState && BB.nextBtnState.mode === 'next-mode';
      if (!emailCaptured && atGateStep && isAdvanceClick) {
        showGate(originalBbNext);
        return;
      }
      originalBbNext();
    };
  }, 100);
})();
</script>
```

- [ ] **Step 7: Smoke-test the trimmed template**

Run: `python -c "from app import app; c = app.test_client(); r = c.get('/try'); print(r.status_code); body = r.data.decode(); print('compile-btn' in body, 'kclink-overlay' in body, '127.0.0.1:52010' in body, '/try/builder' in body)"`

Expected: `200` then `False False False True` — confirms hardware chrome is gone and the fragment fetch points at the new endpoint. (This requires Task 4 to already be merged since `/try` depends on `routes/try_it.py`.)

- [ ] **Step 8: Commit**

```bash
git add templates/try_it_builder.html
git commit -m "Add trimmed try_it_builder.html: Monaco/blocks toggle, sim tab, email gate, no hardware chrome"
```

---

### Task 6: Weekly follow-up cron script

**Files:**
- Create: `utils/send_try_followups.py`
- Test: `tests/test_send_try_followups.py`

**Interfaces:**
- Consumes: `utils.leads.get_unfollowed_leads()`, `utils.leads.email_exists_in_users(email)`, `utils.leads.mark_followed_up(lead_id)` (all Task 1).
- Produces: a `main()` function and a `send_followup_email(to_email)` function, standalone-invocable via `python utils/send_try_followups.py`.

- [ ] **Step 1: Write the script**

```python
#!/usr/bin/env python3
"""
Standalone weekly follow-up script — run manually or via cron.

One reminder per lead, ever (not a drip sequence). Leads who converted on
their own before this ran are stamped followed_up_at without an email being
sent, so they're never picked up again either.

Usage:
    python utils/send_try_followups.py

Cron example (Monday mornings at 9am), same convention as
utils/purge_deleted_accounts.py:
    0 9 * * 1 cd /path/to/project && venv/bin/python utils/send_try_followups.py >> logs/try_followups.log 2>&1
"""

import sys
import os
import datetime
import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from config import RESEND_API_KEY
from utils.leads import get_unfollowed_leads, email_exists_in_users, mark_followed_up


def send_followup_email(to_email):
    resp = requests.post(
        "https://api.resend.com/emails",
        headers={
            "Authorization": f"Bearer {RESEND_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "from": "KidsCode <no-reply@kidscode.ca>",
            "to": to_email,
            "subject": "Still thinking about KidsCode?",
            "html": """
                <h2>Hey there!</h2>
                <p>You tried out a KidsCode project a little while ago — thanks for
                giving it a shot!</p>
                <p>If you're ready to keep building, head back to
                <a href="https://app.kidscode.ca/try">app.kidscode.ca/try</a> any time.</p>
            """
        }
    )
    if not resp.ok:
        print(f"[send_followup_email] Resend error {resp.status_code}: {resp.text}")
    return resp.ok


def main():
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    print(f"[{now}] Starting weekly try-page follow-up run")

    unfollowed = get_unfollowed_leads()
    if not unfollowed:
        print(f"[{now}] No unfollowed leads.")
        return

    sent = 0
    skipped_converted = 0
    errors = 0
    for lead in unfollowed:
        try:
            if email_exists_in_users(lead["email"]):
                mark_followed_up(lead["id"])
                skipped_converted += 1
                continue
            ok = send_followup_email(lead["email"])
            mark_followed_up(lead["id"])
            if ok:
                sent += 1
            else:
                errors += 1
        except Exception as e:
            print(f"  ERROR processing lead {lead.get('id')}: {e}")
            errors += 1

    print(f"[{now}] Done. Sent: {sent}, Skipped (already converted): {skipped_converted}, Errors: {errors}")
    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Write the test**

```python
"""
tests/test_send_try_followups.py — unit tests for utils/send_try_followups.py.
Mocks utils.leads directly (unit-level, not the Supabase REST layer) and
mocks the Resend HTTP call via the `responses` library already used
throughout this test suite.
"""

import responses

from utils import send_try_followups


def test_main_skips_lead_that_already_converted(monkeypatch):
    monkeypatch.setattr(
        send_try_followups, "get_unfollowed_leads",
        lambda: [{"id": "lead-1", "email": "converted@example.com"}],
    )
    monkeypatch.setattr(send_try_followups, "email_exists_in_users", lambda email: True)
    marked = []
    monkeypatch.setattr(send_try_followups, "mark_followed_up", lambda lead_id: marked.append(lead_id))

    sent_calls = []
    monkeypatch.setattr(send_try_followups, "send_followup_email", lambda email: sent_calls.append(email) or True)

    send_try_followups.main()

    assert marked == ["lead-1"]
    assert sent_calls == []  # never emailed a lead who already converted


@responses.activate
def test_send_followup_email_posts_to_resend(monkeypatch):
    monkeypatch.setattr(send_try_followups, "RESEND_API_KEY", "mock-resend-key")
    responses.add(
        responses.POST, "https://api.resend.com/emails",
        json={"id": "email-1"}, status=200,
    )
    ok = send_try_followups.send_followup_email("parent@example.com")
    assert ok is True
    assert len(responses.calls) == 1


def test_main_sends_and_marks_new_lead(monkeypatch):
    monkeypatch.setattr(
        send_try_followups, "get_unfollowed_leads",
        lambda: [{"id": "lead-2", "email": "new@example.com"}],
    )
    monkeypatch.setattr(send_try_followups, "email_exists_in_users", lambda email: False)
    marked = []
    monkeypatch.setattr(send_try_followups, "mark_followed_up", lambda lead_id: marked.append(lead_id))
    sent_calls = []
    monkeypatch.setattr(send_try_followups, "send_followup_email", lambda email: sent_calls.append(email) or True)

    send_try_followups.main()

    assert sent_calls == ["new@example.com"]
    assert marked == ["lead-2"]
```

- [ ] **Step 3: Run the tests**

Run: `pytest tests/test_send_try_followups.py -v`
Expected: 3 passed.

- [ ] **Step 4: Commit**

```bash
git add utils/send_try_followups.py tests/test_send_try_followups.py
git commit -m "Add weekly try-page lead follow-up cron script"
```

---

## Handing off to you (Bill)

None of these tasks execute the SQL migration — that's explicitly your call per your request. Once Task 1 is merged, run `migrations/add_leads_table.sql` in the Supabase SQL editor before Task 4 is deployed (Task 4's `/try/lead` route will 500 on every request until the table exists).

## Explicitly out of scope for this plan (unchanged from the spec)

- The fully curated `/try` project content — Task 2 ships working scaffold content, not final copy.
- Wiring the existing splash-page widget to `utils/project_try_it.py`.
- Stripe Checkout / registration / webhook flow, and any payment logging/reporting-API work.
- Teacher/cohort license payment flow.
- Unifying `circuit_renderer.js` and `SimEngine`.
