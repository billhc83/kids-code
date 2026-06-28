from flask import Blueprint, request, session, Response, stream_with_context, jsonify
from flask_limiter.util import get_remote_address
from extensions import limiter
from utils.decorators import login_required
from utils.project_registry import PROJECTS
from config import OPENAI_MODEL
from openai import OpenAI
import json
import re

help_bp = Blueprint("help", __name__)

from config import OPENAI_API_KEY
_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

DAILY_CAP     = 20   # max help requests per session
MAX_TOKENS    = 250  # max tokens per LLM response

def _user_key():
    return str(session.get("user_id") or get_remote_address())


@help_bp.route("/api/help", methods=["POST"])
@login_required
@limiter.limit("5 per minute", key_func=_user_key)
@limiter.limit("30 per hour",  key_func=_user_key)
def help_chat():
    if _client is None:
        return jsonify(error="ai_unavailable"), 503
    used = session.get("help_requests", 0)
    if used >= DAILY_CAP:
        return jsonify(error="daily_cap"), 429
    session["help_requests"] = used + 1
    data         = request.get_json(silent=True) or {}
    project_key  = data.get("project_key", "")
    step_index   = int(data.get("step_index", 0))
    symptom      = data.get("symptom", "")
    student_code = data.get("student_code", "")
    freeform     = data.get("freeform", "")

    project = PROJECTS.get(project_key, {})
    meta    = project.get("meta", {})
    steps   = project.get("steps") or []
    drawer  = project.get("drawer", {})

    title = meta.get("title", "Arduino Project")
    theme = title.split(":", 1)[1].strip() if ":" in title else title

    # Current step instruction text
    current_step     = steps[step_index] if 0 <= step_index < len(steps) else {}
    step_instruction = re.sub(r"<[^>]+>", " ", current_step.get("instruction", "")).strip()

    # Drawer hints for this step (howto tab)
    drawer_hints = ""
    drawer_steps = (drawer.get(project_key) or {}).get("steps", [])
    if 0 <= step_index < len(drawer_steps):
        tabs     = drawer_steps[step_index].get("tabs", {})
        howto    = tabs.get("howto", {})
        raw_hint = re.sub(r"<[^>]+>", " ", howto.get("content", "")).strip()
        if raw_hint:
            drawer_hints = raw_hint

    system  = _build_system(title, theme, step_instruction, drawer_hints, symptom, student_code)
    user_msg = symptom or freeform or "I'm stuck and need help."

    def generate():
        try:
            stream = _client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user",   "content": user_msg},
                ],
                max_completion_tokens=MAX_TOKENS,
                stream=True,
            )
            for chunk in stream:
                token = (chunk.choices[0].delta.content or "")
                if token:
                    yield f"data: {json.dumps(token)}\n\n"
        except Exception as exc:
            yield f"data: {json.dumps(f'Sorry, something went wrong: {exc}')}\n\n"
        yield "data: [DONE]\n\n"

    return Response(
        stream_with_context(generate()),
        content_type="text/event-stream",
        headers={"X-Accel-Buffering": "no", "Cache-Control": "no-cache"},
    )


def _build_system(title, theme, step_instruction, drawer_hints, symptom, student_code):
    lines = [
        f"You are a friendly, encouraging coding helper for kids ages 8–14 working on '{title}'.",
        f"Stay in the spirit of the {theme} theme when you respond — make it fun and relevant.",
        "Keep responses to 3–5 sentences. Be warm and age-appropriate.",
        "Never reveal the full answer — guide the student with a hint or a question.",
        "Use simple language and explain any technical terms briefly.",
    ]
    if step_instruction:
        lines.append(f"\nThe student is on this step: {step_instruction}")
    if drawer_hints:
        lines.append(f"\nHints for this step: {drawer_hints}")
    if student_code:
        lines.append(f"\nStudent's current code:\n```\n{student_code}\n```")
    if symptom:
        lines.append(f"\nThe student tapped: '{symptom}'")
    return "\n".join(lines)
