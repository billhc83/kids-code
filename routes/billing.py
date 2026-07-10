"""
routes/billing.py — Stripe Checkout entry points + webhook receiver.

See docs/superpowers/specs/2026-07-10-stripe-registration-gate-design.md
for the full flow this implements: pending user row -> Checkout -> webhook
activation -> existing /check-email + /verify/<token> flow (unchanged).
"""

from flask import Blueprint, session, redirect, url_for, render_template, request, jsonify, abort

from extensions import csrf, limiter
from utils.auth import get_user_by_id
from utils.billing import (
    create_checkout_session, verify_webhook_signature,
    handle_checkout_completed, handle_subscription_updated, handle_subscription_deleted,
)

billing_bp = Blueprint('billing', __name__)


@billing_bp.route("/subscribe/checkout")
def subscribe_checkout():
    user_id = session.get("pending_subscription_user_id")
    if not user_id:
        abort(400)
    user = get_user_by_id(user_id)
    if not user:
        abort(400)
    url = create_checkout_session(
        user,
        success_url=url_for("billing.subscribe_success", _external=True),
        cancel_url=url_for("billing.subscribe_cancelled", _external=True),
    )
    return redirect(url)


@billing_bp.route("/subscribe/success")
def subscribe_success():
    user_id = session.get("pending_subscription_user_id")
    user = get_user_by_id(user_id) if user_id else None
    if user:
        session["pending_email"] = user["email"]
        return redirect(url_for("auth.check_email"))
    return render_template("subscribe_success.html")


@billing_bp.route("/subscribe/cancelled")
def subscribe_cancelled():
    return render_template("subscribe_cancelled.html")


@billing_bp.route("/subscribe/pending/<user_id>")
def subscribe_pending(user_id):
    session["pending_subscription_user_id"] = user_id
    return render_template("subscribe_pending.html")


@billing_bp.route("/webhooks/stripe", methods=["POST"])
@csrf.exempt
@limiter.limit("100 per minute")
def stripe_webhook():
    payload = request.get_data()
    sig_header = request.headers.get("Stripe-Signature", "")
    try:
        event = verify_webhook_signature(payload, sig_header)
    except Exception:
        return jsonify(error="invalid signature"), 400

    event_type = event["type"]
    if event_type == "checkout.session.completed":
        handle_checkout_completed(event)
    elif event_type == "customer.subscription.updated":
        handle_subscription_updated(event)
    elif event_type == "customer.subscription.deleted":
        handle_subscription_deleted(event)

    return jsonify(received=True), 200
