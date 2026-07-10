"""
utils/billing.py — Stripe Checkout + webhook data access.

Every write here touches only the four subscription columns added by
migrations/add_subscription_columns.sql. See docs/superpowers/specs/
2026-07-10-stripe-registration-gate-design.md for the full state machine
and why each handler is idempotent (webhooks can be redelivered).
"""

import datetime
import stripe

from config import STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET, STRIPE_PRICE_ID
from utils.db_client import supabase
from utils.auth import get_user_by_id, get_user_by_stripe_subscription_id, send_verification_email

stripe.api_key = STRIPE_SECRET_KEY


def _sget(obj, key, default=None):
    """dict/StripeObject-agnostic .get(). stripe-python's StripeObject supports
    `obj[key]` and `key in obj` but has no `.get()` (no Mapping inheritance) —
    calling `.get()` directly on one raises AttributeError."""
    return obj[key] if key in obj else default


def create_checkout_session(user, success_url, cancel_url):
    session = stripe.checkout.Session.create(
        mode="subscription",
        line_items=[{"price": STRIPE_PRICE_ID, "quantity": 1}],
        client_reference_id=user["id"],
        customer_email=user["email"],
        success_url=success_url,
        cancel_url=cancel_url,
    )
    return session.url


def verify_webhook_signature(payload, sig_header):
    return stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)


def _period_end_iso(subscription_obj):
    ts = _sget(subscription_obj, "current_period_end")
    if not ts:
        return None
    return datetime.datetime.fromtimestamp(ts, tz=datetime.timezone.utc).isoformat()


def handle_checkout_completed(event):
    session_obj = event["data"]["object"]
    user_id = _sget(session_obj, "client_reference_id")
    if not user_id:
        return
    user = get_user_by_id(user_id)
    if not user:
        return

    subscription_id = _sget(session_obj, "subscription")
    subscription_obj = stripe.Subscription.retrieve(subscription_id) if subscription_id else {}

    supabase.table("users").update({
        "stripe_customer_id": _sget(session_obj, "customer"),
        "stripe_subscription_id": subscription_id,
        "subscription_status": "active",
        "subscription_period_end": _period_end_iso(subscription_obj),
    }).eq("id", user_id).execute()

    send_verification_email(user["email"], user["verification_token"])


_STRIPE_STATUS_MAP = {
    "active": "active",
    "trialing": "active",
    "past_due": "past_due",
    "unpaid": "past_due",
    "canceled": "canceled",
    "incomplete_expired": "canceled",
}


def handle_subscription_updated(event):
    subscription_obj = event["data"]["object"]
    user = get_user_by_stripe_subscription_id(subscription_obj["id"])
    if not user:
        return
    mapped_status = _STRIPE_STATUS_MAP.get(_sget(subscription_obj, "status"), "canceled")
    supabase.table("users").update({
        "subscription_status": mapped_status,
        "subscription_period_end": _period_end_iso(subscription_obj),
    }).eq("id", user["id"]).execute()


def handle_subscription_deleted(event):
    subscription_obj = event["data"]["object"]
    user = get_user_by_stripe_subscription_id(subscription_obj["id"])
    if not user:
        return
    supabase.table("users").update({
        "subscription_status": "canceled",
    }).eq("id", user["id"]).execute()
