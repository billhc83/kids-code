"""
Route-level tests for POST /api/help — extends the pytest-flask pattern from
tests/test_admin.py (fake session login via session_transaction) with new
OpenAI-client mocking infrastructure (routes.help._client is monkeypatched
with a fake object exposing .chat.completions.create), since no prior test
mocked an OpenAI call.

Covers all three retrieval tiers (DIRECT / RAG / LEGACY) plus the three bugs
fixed in this rewrite: raw exception text leaking to the chat bubble, the
daily cap being consumed on a failed call, and silent truncation at the
token cap.
"""

import itertools
import json
from types import SimpleNamespace

import httpx
import openai
import pytest

import routes.help as help_route
from utils import help_kb

_uid_counter = itertools.count()


@pytest.fixture(autouse=True)
def _disable_csrf(app):
    # No existing test posts JSON to a CSRF-protected route; /api/help is a
    # same-origin fetch() call in production (auto-injected token via the
    # frontend interceptor, see CLAUDE.md) — irrelevant for these tests.
    app.config["WTF_CSRF_ENABLED"] = False


@pytest.fixture
def logged_in_client(client):
    with client.session_transaction() as sess:
        sess["user_id"] = f"test-user-{next(_uid_counter)}"
    return client


def _fake_request():
    return httpx.Request("POST", "https://api.openai.com/v1/chat/completions")


class _FakeCompletions:
    def __init__(self, outcome):
        self._outcome = outcome  # ("value", response) or ("raise", exception)
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        kind, payload = self._outcome
        if kind == "raise":
            raise payload
        return payload


class _FakeClient:
    def __init__(self, chat_outcome):
        self.chat = SimpleNamespace(completions=_FakeCompletions(chat_outcome))


def _chat_response(content, finish_reason="stop"):
    choice = SimpleNamespace(message=SimpleNamespace(content=content), finish_reason=finish_reason)
    return SimpleNamespace(choices=[choice])


def _set_client(monkeypatch, chat_outcome):
    fake = _FakeClient(chat_outcome)
    monkeypatch.setattr(help_route, "_client", fake)
    return fake


def _force_tier(monkeypatch, tier, chunks=None):
    """Bypass real embedding calls — deterministically drive routes.help's
    tier decision via the same help_kb functions it calls.
    """
    if tier == "unavailable":
        monkeypatch.setattr(help_kb, "is_available", lambda: False)
        return
    monkeypatch.setattr(help_kb, "is_available", lambda: True)
    monkeypatch.setattr(help_route.help_kb, "embed_query", lambda *a, **kw: object())
    monkeypatch.setattr(help_route.help_kb, "retrieve", lambda *a, **kw: chunks or [])


def _chunk(chunk_id, similarity, text="canned answer text", project_key=None):
    return help_kb.RetrievedChunk(
        chunk_id=chunk_id, similarity=similarity, title=chunk_id, text=text,
        project_key=project_key, step_index=None, source="kb_troubleshooting",
    )


def _post_help(client, **body):
    payload = {"project_key": "project_one", "step_index": 0, "symptom": "", "freeform": ""}
    payload.update(body)
    return client.post("/api/help", json=payload)


def _sse_text(response):
    """Reconstruct the delivered chat-bubble content the same way the frontend
    does (utils/block_builder.py's sendHelp): concatenate every `data: "..."`
    JSON-decoded line up to [DONE]. _fake_stream splits a single answer
    across several SSE lines as plain strings (accumulated as text), while
    _error_response sends a single {"html": "..."} object (rendered via
    innerHTML) — raw substring search on the wire format would miss text
    spanning a chunk boundary, or fail to concatenate a dict payload at all.
    """
    text = ""
    for line in response.get_data(as_text=True).splitlines():
        if not line.startswith("data: "):
            continue
        payload = line[len("data: "):]
        if payload == "[DONE]":
            break
        parsed = json.loads(payload)
        if isinstance(parsed, dict):
            text += parsed.get("html", "")
        else:
            text += parsed
    return text


# ── DIRECT tier ──────────────────────────────────────────────────────────────

def test_direct_tier_returns_chunk_text_without_calling_llm(monkeypatch, logged_in_client):
    fake = _set_client(monkeypatch, ("value", _chat_response("should not be used")))
    _force_tier(monkeypatch, "direct", chunks=[
        _chunk("kb_troubleshooting:x", 0.90, text="Unplug it and plug it back in."),
        _chunk("kb_troubleshooting:y", 0.60, text="unrelated runner-up"),
    ])

    resp = _post_help(logged_in_client, freeform="my led wont light up")

    assert resp.status_code == 200
    body = _sse_text(resp)
    assert "Unplug it and plug it back in." in body
    assert fake.chat.completions.calls == [], "DIRECT tier must not call the LLM at all"


def test_direct_tier_increments_daily_cap(monkeypatch, logged_in_client):
    _set_client(monkeypatch, ("value", _chat_response("unused")))
    _force_tier(monkeypatch, "direct", chunks=[
        _chunk("kb_troubleshooting:x", 0.90, text="answer"),
        _chunk("kb_troubleshooting:y", 0.60),
    ])

    _post_help(logged_in_client, freeform="my led wont light up")

    with logged_in_client.session_transaction() as sess:
        assert sess["help_requests"] == 1


# ── RAG tier ─────────────────────────────────────────────────────────────────

def test_rag_tier_calls_llm_with_reference_material(monkeypatch, logged_in_client):
    fake = _set_client(monkeypatch, ("value", _chat_response("Here's a hint!")))
    _force_tier(monkeypatch, "rag", chunks=[
        _chunk("kb_troubleshooting:x", 0.48, text="Some relevant background."),
    ])

    resp = _post_help(logged_in_client, freeform="something about my circuit")

    assert resp.status_code == 200
    assert "Here's a hint!" in _sse_text(resp)
    assert len(fake.chat.completions.calls) == 1
    system_msg = fake.chat.completions.calls[0]["messages"][0]["content"]
    assert "Reference material" in system_msg
    assert "Some relevant background." in system_msg


def test_rag_tier_increments_daily_cap_on_success(monkeypatch, logged_in_client):
    _set_client(monkeypatch, ("value", _chat_response("An answer.")))
    _force_tier(monkeypatch, "rag", chunks=[_chunk("kb_troubleshooting:x", 0.48)])

    _post_help(logged_in_client, freeform="something about my circuit")

    with logged_in_client.session_transaction() as sess:
        assert sess["help_requests"] == 1


# ── LEGACY tier ──────────────────────────────────────────────────────────────

def test_legacy_tier_when_kb_unavailable(monkeypatch, logged_in_client):
    fake = _set_client(monkeypatch, ("value", _chat_response("Legacy answer.")))
    _force_tier(monkeypatch, "unavailable")

    resp = _post_help(logged_in_client, freeform="anything")

    assert resp.status_code == 200
    assert "Legacy answer." in _sse_text(resp)
    system_msg = fake.chat.completions.calls[0]["messages"][0]["content"]
    assert "Reference material" not in system_msg


def test_legacy_tier_when_similarity_below_low_threshold(monkeypatch, logged_in_client):
    fake = _set_client(monkeypatch, ("value", _chat_response("Legacy answer.")))
    _force_tier(monkeypatch, "rag", chunks=[_chunk("kb_troubleshooting:x", 0.10)])

    resp = _post_help(logged_in_client, freeform="vague")

    assert resp.status_code == 200
    system_msg = fake.chat.completions.calls[0]["messages"][0]["content"]
    assert "Reference material" not in system_msg


def test_embedding_failure_falls_back_to_legacy_transparently(monkeypatch, logged_in_client):
    fake = _set_client(monkeypatch, ("value", _chat_response("Legacy answer.")))
    monkeypatch.setattr(help_kb, "is_available", lambda: True)
    monkeypatch.setattr(help_route.help_kb, "embed_query", lambda *a, **kw: None)

    resp = _post_help(logged_in_client, freeform="my led wont light up")

    assert resp.status_code == 200
    assert "Legacy answer." in _sse_text(resp)
    system_msg = fake.chat.completions.calls[0]["messages"][0]["content"]
    assert "Reference material" not in system_msg


# ── Bug fixes: error handling, cap accounting, truncation ───────────────────

def test_quota_exhausted_shows_friendly_message_and_does_not_consume_cap(monkeypatch, logged_in_client):
    exc = openai.RateLimitError("quota", response=httpx.Response(429, request=_fake_request()),
                                 body={"code": "insufficient_quota"})
    _set_client(monkeypatch, ("raise", exc))
    _force_tier(monkeypatch, "unavailable")

    resp = _post_help(logged_in_client, freeform="anything")

    body = _sse_text(resp)
    assert "quota" not in body.lower()
    assert "insufficient_quota" not in body
    assert "taking a quick break" in body
    assert "/feedback" in body and "contact us" in body
    with logged_in_client.session_transaction() as sess:
        assert sess.get("help_requests", 0) == 0


def test_rate_limited_shows_different_friendly_message(monkeypatch, logged_in_client):
    exc = openai.RateLimitError("slow down", response=httpx.Response(429, request=_fake_request()),
                                 body={"code": "rate_limit_exceeded"})
    _set_client(monkeypatch, ("raise", exc))
    _force_tier(monkeypatch, "unavailable")

    resp = _post_help(logged_in_client, freeform="anything")

    body = _sse_text(resp)
    assert "lots of questions" in body
    assert "/feedback" in body and "contact us" in body
    with logged_in_client.session_transaction() as sess:
        assert sess.get("help_requests", 0) == 0


def test_generic_exception_never_leaks_raw_text(monkeypatch, logged_in_client):
    _set_client(monkeypatch, ("raise", RuntimeError("super secret internal detail")))
    _force_tier(monkeypatch, "unavailable")

    resp = _post_help(logged_in_client, freeform="anything")

    body = _sse_text(resp)
    assert "super secret internal detail" not in body
    assert "/feedback" in body and "contact us" in body
    with logged_in_client.session_transaction() as sess:
        assert sess.get("help_requests", 0) == 0


def test_truncated_response_shows_visible_marker(monkeypatch, logged_in_client):
    _set_client(monkeypatch, ("value", _chat_response("this got cut off", finish_reason="length")))
    _force_tier(monkeypatch, "unavailable")

    resp = _post_help(logged_in_client, freeform="anything")

    body = _sse_text(resp)
    assert "this got cut off" in body
    assert "ran out of room" in body
    with logged_in_client.session_transaction() as sess:
        assert sess["help_requests"] == 1


def test_length_truncation_with_empty_content_shows_friendly_message_not_bare_marker(monkeypatch, logged_in_client):
    # Reasoning models (o4-mini) can spend the entire max_completion_tokens
    # budget on internal reasoning, leaving content='' with finish_reason
    # == "length" — confirmed directly against the real API. Must not show
    # a truncation note dangling with no answer in front of it, and must
    # not consume the daily cap for a non-answer.
    _set_client(monkeypatch, ("value", _chat_response("", finish_reason="length")))
    _force_tier(monkeypatch, "unavailable")

    resp = _post_help(logged_in_client, freeform="anything")

    body = _sse_text(resp)
    assert "ran out of room to explain more" not in body
    assert "ran out of room" in body  # the empty-content-specific friendly message
    assert "/feedback" in body and "contact us" in body
    with logged_in_client.session_transaction() as sess:
        assert sess.get("help_requests", 0) == 0


# ── Existing behavior preserved ──────────────────────────────────────────────

def test_daily_cap_returns_429_without_calling_llm(monkeypatch, logged_in_client):
    fake = _set_client(monkeypatch, ("value", _chat_response("unused")))
    _force_tier(monkeypatch, "unavailable")
    with logged_in_client.session_transaction() as sess:
        sess["help_requests"] = help_route.DAILY_CAP

    resp = _post_help(logged_in_client, freeform="anything")

    assert resp.status_code == 429
    assert resp.get_json()["error"] == "daily_cap"
    assert fake.chat.completions.calls == []


def test_no_client_shows_friendly_message_not_blank_bubble(monkeypatch, logged_in_client):
    # Previously a plain jsonify(..., 503) — the frontend only special-cases
    # HTTP 429, so any other status silently left the chat bubble blank
    # forever (confirmed by inspection of utils/block_builder.py). Now
    # routed through the same SSE + contact-link shape as every other
    # failure mode, so it always displays something.
    monkeypatch.setattr(help_route, "_client", None)

    resp = _post_help(logged_in_client, freeform="anything")

    assert resp.status_code == 200
    assert resp.content_type.startswith("text/event-stream")
    body = _sse_text(resp)
    assert "/feedback" in body and "contact us" in body
