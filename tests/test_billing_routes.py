"""
tests/test_billing_routes.py — route-level tests for routes/billing.py.
"""

import stripe


def test_subscribe_checkout_requires_pending_session(client):
    resp = client.get("/subscribe/checkout")
    assert resp.status_code == 400


def test_subscribe_checkout_redirects_to_stripe(client, monkeypatch):
    monkeypatch.setattr("routes.billing.get_user_by_id", lambda uid: {"id": "user-1", "email": "a@example.com"})
    monkeypatch.setattr("routes.billing.create_checkout_session", lambda user, success_url, cancel_url, referral_code_id=None: "https://checkout.stripe.com/fake")
    with client.session_transaction() as sess:
        sess["pending_subscription_user_id"] = "user-1"
    resp = client.get("/subscribe/checkout")
    assert resp.status_code == 302
    assert resp.location == "https://checkout.stripe.com/fake"


def test_subscribe_pending_requires_session(client):
    resp = client.get("/subscribe/pending")
    assert resp.status_code == 400


def test_subscribe_pending_renders_when_session_set(client):
    with client.session_transaction() as sess:
        sess["pending_subscription_user_id"] = "user-1"
    resp = client.get("/subscribe/pending")
    assert resp.status_code == 200


def test_subscribe_success_redirects_to_check_email(client, monkeypatch):
    monkeypatch.setattr("routes.billing.get_user_by_id", lambda uid: {"id": "user-1", "email": "a@example.com"})
    with client.session_transaction() as sess:
        sess["pending_subscription_user_id"] = "user-1"
    resp = client.get("/subscribe/success")
    assert resp.status_code == 302
    assert "/check-email" in resp.location


def test_webhook_rejects_bad_signature(client, monkeypatch):
    def raise_sig_error(payload, sig_header):
        raise stripe.error.SignatureVerificationError("bad", sig_header)
    monkeypatch.setattr("routes.billing.verify_webhook_signature", raise_sig_error)
    resp = client.post("/webhooks/stripe", data=b"{}", headers={"Stripe-Signature": "bad"})
    assert resp.status_code == 400


def test_webhook_dispatches_checkout_completed(client, monkeypatch):
    monkeypatch.setattr("routes.billing.verify_webhook_signature", lambda payload, sig: {"type": "checkout.session.completed", "data": {"object": {}}})
    calls = []
    monkeypatch.setattr("routes.billing.handle_checkout_completed", lambda event: calls.append(event))
    resp = client.post("/webhooks/stripe", data=b"{}", headers={"Stripe-Signature": "ok"})
    assert resp.status_code == 200
    assert len(calls) == 1
