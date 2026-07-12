"""
utils/billing.py — Stripe Checkout + webhook data access.

Every write here touches only the four subscription columns added by
migrations/add_subscription_columns.sql. See docs/superpowers/specs/
2026-07-10-stripe-registration-gate-design.md for the full state machine
and why each handler is idempotent (webhooks can be redelivered).
"""

import calendar
import datetime
import stripe

from config import (
    STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET, STRIPE_PRICE_ID,
    REFERRAL_REWARD_MONTHS, REFERRER_ANNUAL_CAP_MONTHS,
)
from utils.db_client import supabase
from utils.auth import get_user_by_id, get_user_by_stripe_subscription_id, send_verification_email
from utils.referrals import (
    get_referral_code_by_id, claim_redemption_row, update_redemption_row,
    cas_increment_redemption_count, acquire_redemption_lock_blocking, release_redemption_lock,
    sum_referrer_credited_months, current_annual_window,
    VALID_REDEMPTION_SUBSCRIPTION_STATUSES,
)

stripe.api_key = STRIPE_SECRET_KEY


def _sget(obj, key, default=None):
    """dict/StripeObject-agnostic .get(). stripe-python's StripeObject supports
    `obj[key]` and `key in obj` but has no `.get()` (no Mapping inheritance) —
    calling `.get()` directly on one raises AttributeError."""
    return obj[key] if key in obj else default


def create_checkout_session(user, success_url, cancel_url, referral_code_id=None):
    kwargs = dict(
        mode="subscription",
        line_items=[{"price": STRIPE_PRICE_ID, "quantity": 1}],
        client_reference_id=user["id"],
        customer_email=user["email"],
        success_url=success_url,
        cancel_url=cancel_url,
    )
    if referral_code_id:
        # metadata (not just the Flask session) is what carries this to
        # handle_checkout_completed — that handler runs from a Stripe webhook
        # request, which has no access to this request's Flask session at all.
        kwargs["metadata"] = {"referral_code_id": referral_code_id}
        code_row = get_referral_code_by_id(referral_code_id)
        if code_row and code_row.get("code_type") == "admin_discount" and code_row.get("stripe_coupon_id"):
            kwargs["discounts"] = [{"coupon": code_row["stripe_coupon_id"]}]
    session = stripe.checkout.Session.create(**kwargs)
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

    _redeem_referral_code(session_obj, user, subscription_id)


def _add_months(dt, months):
    month_index = dt.month - 1 + months
    year = dt.year + month_index // 12
    month = month_index % 12 + 1
    day = min(dt.day, calendar.monthrange(year, month)[1])
    return dt.replace(year=year, month=month, day=day)


def _credit_subscription_months(subscription_id, months):
    """Push trial_end out by `months` from the subscription's *current*
    current_period_end. Always re-reads fresh from Stripe right before modify()
    rather than trusting a locally-cached period end — see "Concurrency &
    idempotency" (race B) in the design doc: two redemptions crediting the same
    subscription close together must each see the other's write, not stack
    silently wrong or overwrite each other."""
    sub = stripe.Subscription.retrieve(subscription_id)
    period_end = datetime.datetime.fromtimestamp(_sget(sub, "current_period_end"), tz=datetime.timezone.utc)
    new_trial_end = _add_months(period_end, months)
    stripe.Subscription.modify(
        subscription_id,
        trial_end=int(new_trial_end.timestamp()),
        proration_behavior="none",
    )


def _redeem_referral_code(session_obj, invitee_user, invitee_subscription_id):
    """Only reachable once per invitee, ever — claim_redemption_row's UNIQUE(redeemed_by)
    constraint is the entire dedup mechanism for Stripe webhook redelivery (see
    "Concurrency & idempotency" in the design doc). Refund/chargeback clawback is
    explicitly out of scope for this spec: nothing here reverses a trial_end push
    if the invitee's payment is later refunded or disputed — a conscious omission,
    revisit only if it becomes a real problem."""
    metadata = _sget(session_obj, "metadata", {}) or {}
    referral_code_id = _sget(metadata, "referral_code_id")
    if not referral_code_id:
        return
    code_row = get_referral_code_by_id(referral_code_id)
    if not code_row:
        return

    # Gap #4 (self-referral): a parent can't redeem their own code with a second
    # account they control. Checked here, not at invite-request, because this is
    # the first point a concrete redeemed_by user exists to compare against
    # created_by — it's a cheap, exact check, not an attempt to catch a parent
    # using a *different* email/account they also control.
    if code_row["created_by"] == invitee_user["id"]:
        print(f"[referrals] self-referral blocked: user={invitee_user['id']} code={code_row['id']}")
        return

    redemption_row = claim_redemption_row(code_row["id"], invitee_user["id"])
    if not redemption_row:
        # Already processed (webhook redelivery), or this user already redeemed
        # a different code — same UNIQUE constraint, same "skip everything past
        # this point" response either way.
        return

    ok, code_row = cas_increment_redemption_count(code_row["id"])
    if not ok:
        print(f"[referrals] max_redemptions cap hit at redemption time: code={referral_code_id}")
        return

    if code_row["code_type"] == "admin_discount":
        # Discount already happened at Checkout time via the coupon param —
        # this just records what was applied. One-sided; no month credit.
        update_redemption_row(redemption_row["id"], discount_applied=code_row.get("discount_value"))
        return

    _redeem_parent_referral(code_row, redemption_row, invitee_user, invitee_subscription_id)


def _redeem_parent_referral(code_row, redemption_row, invitee_user, invitee_subscription_id):
    reward_months = code_row.get("reward_months") or REFERRAL_REWARD_MONTHS
    referrer = get_user_by_id(code_row["created_by"])

    # Re-check live: the provisioning check at invite-request time can go stale
    # during Checkout. If it fails now, the code is invalid outright — neither
    # side gets a reward, rather than quietly downgrading to "invitee pays full
    # price" (see "How a month credit is actually applied" in the design doc).
    if not referrer or referrer.get("subscription_status") not in VALID_REDEMPTION_SUBSCRIPTION_STATUSES:
        print(f"[referrals] referrer subscription lapsed at redemption time: code={code_row['id']}")
        return

    months_credited_invitee = None
    if invitee_subscription_id:
        _credit_subscription_months(invitee_subscription_id, reward_months)
        months_credited_invitee = reward_months

    months_credited_referrer = _credit_referrer(code_row, referrer, reward_months)

    update_redemption_row(
        redemption_row["id"],
        months_credited_invitee=months_credited_invitee,
        months_credited_referrer=months_credited_referrer,
    )


def _credit_referrer(code_row, referrer, reward_months):
    referrer_subscription_id = referrer.get("stripe_subscription_id")
    if not referrer_subscription_id:
        return None

    # Guards the referrer-side read-then-modify Stripe sequence against two
    # different invitees redeeming the same popular parent code close together
    # (race B). The invitee's own credit above never needs this: UNIQUE(redeemed_by)
    # already guarantees only one webhook delivery ever processes a given invitee.
    # See migrations/add_referral_redemption_lock_column.sql for why this is a
    # DB-column lock rather than the design doc's suggested pg_advisory_xact_lock,
    # and acquire_redemption_lock_blocking's docstring for why acquiring it retries
    # instead of giving up on the first miss — real contention here is expected
    # under normal load (two redemptions of the same popular code close together),
    # not just a pathological case, and a single try would silently drop the
    # referrer's reward on every occurrence of it.
    if not acquire_redemption_lock_blocking(code_row["id"]):
        print(f"[referrals] referrer lock contention, skipping referrer credit: code={code_row['id']}")
        return None
    try:
        window_start, window_end = current_annual_window(referrer["created_at"])
        already_credited = sum_referrer_credited_months(code_row["id"], window_start, window_end)
        if already_credited + reward_months > REFERRER_ANNUAL_CAP_MONTHS:
            print(f"[referrals] referrer annual cap reached, skipping referrer credit: "
                  f"code={code_row['id']} already_credited={already_credited}")
            return None
        _credit_subscription_months(referrer_subscription_id, reward_months)
        return reward_months
    finally:
        release_redemption_lock(code_row["id"])


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
