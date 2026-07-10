"""
tests/test_billing.py — unit tests for utils/billing.py.
Mocks the stripe SDK directly via monkeypatch (no real network call), and
mocks Supabase via the mock_supabase fixture (tests/conftest.py), same
pattern as tests/test_leads.py.
"""

import stripe
import pytest

from utils import billing


class FakeCheckoutSession:
    def __init__(self, url):
        self.url = url


def test_create_checkout_session_returns_url(monkeypatch):
    captured = {}

    def fake_create(**kwargs):
        captured.update(kwargs)
        return FakeCheckoutSession("https://checkout.stripe.com/fake")

    monkeypatch.setattr(stripe.checkout.Session, "create", fake_create)
    url = billing.create_checkout_session(
        {"id": "user-1", "email": "parent@example.com"},
        success_url="https://app/subscribe/success",
        cancel_url="https://app/subscribe/cancelled",
    )
    assert url == "https://checkout.stripe.com/fake"
    assert captured["client_reference_id"] == "user-1"
    assert captured["customer_email"] == "parent@example.com"
    assert captured["mode"] == "subscription"


def test_verify_webhook_signature_raises_on_bad_signature(monkeypatch):
    def fake_construct_event(payload, sig_header, secret):
        raise stripe.error.SignatureVerificationError("bad sig", sig_header)

    monkeypatch.setattr(stripe.Webhook, "construct_event", fake_construct_event)
    with pytest.raises(stripe.error.SignatureVerificationError):
        billing.verify_webhook_signature(b"{}", "bad-sig")


def test_handle_checkout_completed_activates_user(monkeypatch, mock_supabase):
    monkeypatch.setattr(billing, "get_user_by_id", lambda uid: {
        "id": "user-1", "email": "parent@example.com", "verification_token": "tok-1",
    })
    sent = []
    monkeypatch.setattr(billing, "send_verification_email", lambda email, token: sent.append((email, token)))
    monkeypatch.setattr(stripe.Subscription, "retrieve", lambda sub_id: {"current_period_end": 1893456000})

    mock_supabase.add(
        "PATCH", "https://mock-project.supabase.co/rest/v1/users",
        json=[{"id": "user-1"}], status=200,
    )

    event = {"data": {"object": {
        "client_reference_id": "user-1", "customer": "cus_1", "subscription": "sub_1",
    }}}
    billing.handle_checkout_completed(event)
    assert sent == [("parent@example.com", "tok-1")]


def test_handle_subscription_updated_maps_past_due(monkeypatch, mock_supabase):
    monkeypatch.setattr(billing, "get_user_by_stripe_subscription_id", lambda sub_id: {"id": "user-1"})
    mock_supabase.add(
        "PATCH", "https://mock-project.supabase.co/rest/v1/users",
        json=[{"id": "user-1"}], status=200,
    )
    event = {"data": {"object": {"id": "sub_1", "status": "past_due", "current_period_end": None}}}
    billing.handle_subscription_updated(event)  # no assertion beyond "does not raise" — status mapping covered by unit test below


def test_status_map_covers_expected_stripe_statuses():
    assert billing._STRIPE_STATUS_MAP["active"] == "active"
    assert billing._STRIPE_STATUS_MAP["past_due"] == "past_due"
    assert billing._STRIPE_STATUS_MAP["canceled"] == "canceled"
