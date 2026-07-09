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
