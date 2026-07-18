from flask import Blueprint, request, session, Response, stream_with_context, jsonify
from flask_limiter.util import get_remote_address
from extensions import limiter
from utils.decorators import login_required
from utils.project_registry import PROJECTS
from utils import help_kb
from config import OPENAI_MODEL, OPENAI_API_KEY
import openai
from openai import OpenAI
import json
import re
import time

help_bp = Blueprint("help", __name__)

_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

DAILY_CAP      = 20    # max help requests per session
MAX_TOKENS     = 250   # max tokens per LLM response
EMBED_TIMEOUT  = 4.0   # seconds — separate, short timeout for the retrieval embedding call
RETRIEVAL_K    = 5

# Calibrated against real embedded query/chunk pairs over the actual corpus
# (see utils/kb_troubleshooting.py / utils/kb_glossary.py) — text-embedding-3-small
# cosine similarities for short prose in this domain compress into a narrow band
# (noise floor ~0.25-0.30, ceiling ~0.65-0.79 for excellent matches).
HIGH_THRESHOLD = 0.55  # DIRECT tier: confident enough to answer without the LLM
DIRECT_MARGIN  = 0.08  # top match must clearly beat the runner-up, not just clear the threshold
LOW_THRESHOLD  = 0.40  # RAG tier: inject as reference context, still let the LLM phrase the answer
RAG_CHUNK_MARGIN = 0.10  # in RAG tier, only pass chunks within this of top1 — don't hand the LLM the full overfetched top-k


def _user_key():
    return str(session.get("user_id") or get_remote_address())


def _strip_html(html):
    return re.sub(r"<[^>]+>", " ", html or "").strip()


def _sse(text):
    return f"data: {json.dumps(text)}\n\n"


def _fake_stream(text, chunk_words=3, delay=0.03):
    """Chunk an already-fully-known answer back over SSE so it still visually
    'types out' for the student, even though — unlike the old implementation —
    the OpenAI call itself is no longer streamed token-by-token.

    This trade-off exists because Flask's signed-cookie session writes the
    Set-Cookie header before a streamed generator body ever starts executing
    (verified directly), so the "only count this request against the daily
    cap if it actually produced an answer" rule can only work if the call's
    success/failure is known BEFORE the response — and therefore the stream —
    is constructed.
    """
    words = (text or "").split(" ")
    for i in range(0, len(words), chunk_words):
        chunk = " ".join(words[i:i + chunk_words])
        if i + chunk_words < len(words):
            chunk += " "
        yield _sse(chunk)
        if delay:
            time.sleep(delay)
    yield "data: [DONE]\n\n"


def _stream_response(generator):
    return Response(
        stream_with_context(generator),
        content_type="text/event-stream",
        headers={"X-Accel-Buffering": "no", "Cache-Control": "no-cache"},
    )


_CONTACT_LINK = "<a href='/feedback' style='color:#7c3aed;font-weight:600;'>contact us</a>"


def _error_response(message):
    """Terminal error/fallback messages — sent as a single {"html": ...} SSE
    payload (not the plain-string token shape _fake_stream uses), so the
    frontend can safely render the contact-page link as a real <a> tag via
    innerHTML instead of it showing up as literal escaped text under the
    normal textContent-based streaming path. Matches the existing daily_cap
    429 handling's own innerHTML + <a href='/feedback'> pattern in
    utils/block_builder.py — this brings every other failure mode up to the
    same "friendly message + a real way to escalate" standard, not just the
    daily cap.
    """
    html = f"{message} If it keeps happening, {_CONTACT_LINK} and we’ll help out."

    def generate():
        yield f"data: {json.dumps({'html': html})}\n\n"
        yield "data: [DONE]\n\n"

    return _stream_response(generate())


@help_bp.route("/api/help", methods=["POST"])
@login_required
@limiter.limit("5 per minute", key_func=_user_key)
@limiter.limit("30 per hour",  key_func=_user_key)
def help_chat():
    if _client is None:
        # Not a 503 jsonify response on purpose: the frontend's fetch handler
        # (utils/block_builder.py) only special-cases HTTP 429, and otherwise
        # always tries to read the body as an SSE stream — a plain JSON 503
        # here left the chat bubble blank forever (confirmed by inspection).
        # Routing through _error_response gives it the same friendly-message
        # + contact-link treatment as every other failure mode, with zero
        # additional frontend branching needed.
        return _error_response("I can't reach the AI helper right now — try again later! 🤖")
    used = session.get("help_requests", 0)
    if used >= DAILY_CAP:
        return jsonify(error="daily_cap"), 429

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
    step_instruction = _strip_html(current_step.get("instruction", ""))

    # Drawer hints for this step (howto tab) — today's exact-key grounding,
    # kept as the LEGACY-tier fallback when retrieval doesn't clear either
    # threshold below.
    drawer_hints = ""
    drawer_steps = (drawer.get(project_key) or {}).get("steps", [])
    if 0 <= step_index < len(drawer_steps):
        tabs     = drawer_steps[step_index].get("tabs", {})
        howto    = tabs.get("howto", {})
        raw_hint = _strip_html(howto.get("content", ""))
        if raw_hint:
            drawer_hints = raw_hint

    # ---- Retrieval: decide DIRECT / RAG / LEGACY -------------------------
    query_text   = symptom or freeform
    tier         = "legacy"
    direct_chunk = None
    rag_chunks   = []

    if help_kb.is_available() and query_text:
        qvec = help_kb.embed_query(query_text, _client, timeout=EMBED_TIMEOUT)
        if qvec is not None:
            retrieved = help_kb.retrieve(
                qvec, project_key=project_key, step_index=step_index, k=RETRIEVAL_K,
            )
            if retrieved:
                by_sim = sorted(retrieved, key=lambda r: -r.similarity)
                top1 = by_sim[0].similarity
                top2 = by_sim[1].similarity if len(by_sim) > 1 else 0.0
                if top1 >= HIGH_THRESHOLD and (top1 - top2) >= DIRECT_MARGIN:
                    tier = "direct"
                    direct_chunk = by_sim[0]
                elif top1 >= LOW_THRESHOLD:
                    tier = "rag"
                    rag_chunks = [r for r in by_sim if (top1 - r.similarity) <= RAG_CHUNK_MARGIN]
        # else: embedding call failed/timed out — fall through to LEGACY silently.

    # ---- DIRECT: no LLM call at all, guaranteed success ------------------
    if tier == "direct":
        session["help_requests"] = used + 1
        return _stream_response(_fake_stream(direct_chunk.text))

    # ---- RAG / LEGACY: call the LLM synchronously first ------------------
    # (Not streamed from OpenAI directly — see _fake_stream's docstring for
    # why: the cap can only be conditionally incremented before the response,
    # and the response can't be built before we know the call succeeded.)
    system   = _build_system(title, theme, step_instruction, drawer_hints, symptom, student_code, rag_chunks)
    user_msg = symptom or freeform or "I'm stuck and need help."

    try:
        response = _client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": user_msg},
            ],
            max_completion_tokens=MAX_TOKENS,
        )
    except openai.RateLimitError as exc:
        code = (getattr(exc, "body", None) or {}).get("code")
        if code == "insufficient_quota":
            message = "I'm taking a quick break — try again in a little while! 🛠️"
        else:
            message = "Whoa, lots of questions right now — give it a few seconds and try again! ⏱️"
        return _error_response(message)
    except (openai.APITimeoutError, openai.APIConnectionError):
        return _error_response("Having trouble connecting — try again in a moment! 🔌")
    except openai.APIError:
        return _error_response("Something went wrong on my end — try again! 🤖")
    except Exception:
        return _error_response("Sorry, something went wrong — try again!")

    choice      = response.choices[0]
    answer_text = (choice.message.content or "").strip()

    # o4-mini is a reasoning model — its reasoning tokens count against
    # max_completion_tokens, and can consume the entire budget before any
    # visible answer is produced (finish_reason == "length" with empty
    # content). Confirmed directly: a real call reasoning_tokens=250 of a
    # 250-token cap, content=''. That's a "didn't get an answer" case, not
    # a "got cut off mid-sentence" case, so it needs its own message rather
    # than a truncation note dangling with nothing in front of it.
    if not answer_text:
        return _error_response(
            "Hmm, that one made me think too hard and I ran out of room! Try asking again, "
            "maybe a bit more specifically. 🤔"
        )

    if choice.finish_reason == "length":
        answer_text += "\n\n(...I ran out of room to explain more — ask again if you want more detail!)"

    session["help_requests"] = used + 1
    return _stream_response(_fake_stream(answer_text))


def _build_system(title, theme, step_instruction, drawer_hints, symptom, student_code, rag_chunks=None):
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
    if rag_chunks:
        lines.append(
            "\nReference material (for your background only — do not paste it verbatim, "
            "and still follow the guidance rules above):"
        )
        for chunk in rag_chunks:
            lines.append(f"- {chunk.title}: {chunk.text}")
    return "\n".join(lines)
