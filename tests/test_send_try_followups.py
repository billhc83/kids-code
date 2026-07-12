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
