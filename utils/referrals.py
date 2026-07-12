"""
utils/referrals.py — data-access layer for referral_codes / referral_code_redemptions.

See docs/superpowers/specs/2026-07-12-referral-codes-design.md for the full design.
This module owns code generation and the read-side validity checks used by
/register/invite. Redemption (the write side — self-referral check, the
concurrency-safe conditional update, the trial_end month credit, and the
referrer's annual cap) is deliberately NOT here; it lives in
handle_checkout_completed (utils/billing.py) where it can be done atomically
against a live Stripe subscription — see "Concurrency & idempotency" in the spec.
"""

import datetime
import secrets
import time

from utils.db_client import supabase
from utils.auth import get_user_by_id

# Unambiguous charset: no 0/O, 1/I/l — a parent needs to be able to read this
# over the phone. ~12 chars is long enough that brute-forcing a live code
# against the rate-limited /register/invite endpoint isn't practical.
_CODE_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
_CODE_LENGTH = 12

VALID_REDEMPTION_SUBSCRIPTION_STATUSES = ("active", "past_due")


def _parse_ts(value):
    if not value:
        return None
    dt = datetime.datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.timezone.utc)
    return dt


def generate_code():
    """Random unique code, uppercase, from the unambiguous charset. Retries
    on the (astronomically unlikely) chance of a collision with an existing code."""
    while True:
        code = "".join(secrets.choice(_CODE_ALPHABET) for _ in range(_CODE_LENGTH))
        if not get_referral_code_by_code(code):
            return code


def get_referral_code_by_code(code):
    if not code:
        return None
    resp = supabase.table("referral_codes").select("*").eq("code", code.strip().upper()).execute()
    return resp.data[0] if resp.data else None


def get_referral_code_by_id(code_id):
    if not code_id:
        return None
    resp = supabase.table("referral_codes").select("*").eq("id", code_id).execute()
    return resp.data[0] if resp.data else None


def create_admin_discount_code(created_by, discount_type, discount_value, stripe_coupon_id,
                                max_redemptions=None, valid_till=None):
    """Insert the row side of an admin discount code. Caller (the admin route,
    piece 6) is responsible for creating the Stripe Coupon first and passing its
    id in as stripe_coupon_id — the Stripe object is what Checkout actually
    enforces; this row is the lifecycle wrapper around it."""
    row = {
        "code": generate_code(),
        "code_type": "admin_discount",
        "created_by": created_by,
        "discount_type": discount_type,
        "discount_value": discount_value,
        "stripe_coupon_id": stripe_coupon_id,
        "max_redemptions": max_redemptions,
        "valid_till": valid_till,
    }
    resp = supabase.table("referral_codes").insert(row).execute()
    return resp.data[0] if resp.data else None


def get_or_create_parent_referral_code(parent_id, reward_months):
    """Lazily provision the one parent_referral code for this parent. Does NOT
    check the parent's subscription status — that's a live check applied at
    validation/redemption time (resolve_valid_referral_code), not a gate on the
    row existing. Effectively unlimited max_redemptions (None)."""
    resp = supabase.table("referral_codes").select("*") \
        .eq("created_by", parent_id).eq("code_type", "parent_referral").execute()
    if resp.data:
        return resp.data[0]
    row = {
        "code": generate_code(),
        "code_type": "parent_referral",
        "created_by": parent_id,
        "reward_months": reward_months,
        "max_redemptions": None,
    }
    insert_resp = supabase.table("referral_codes").insert(row).execute()
    return insert_resp.data[0] if insert_resp.data else None


def _is_active_now(code_row):
    """Pure check of the code row's own fields — status, expiry, redemption cap.
    Does not check a parent_referral creator's live subscription status; see
    resolve_valid_referral_code for the full check."""
    if code_row.get("status") != "active":
        return False
    valid_till = _parse_ts(code_row.get("valid_till"))
    if valid_till and datetime.datetime.now(datetime.timezone.utc) > valid_till:
        return False
    max_redemptions = code_row.get("max_redemptions")
    if max_redemptions is not None and code_row.get("redemption_count", 0) >= max_redemptions:
        return False
    return True


def claim_redemption_row(code_id, redeemed_by):
    """Attempt to insert the one redemption row this user will ever get,
    relying on referral_code_redemptions.redeemed_by's UNIQUE constraint for
    dedup. Returns the inserted row if this call created it, or None if a row
    already existed (webhook redelivery, or the user already redeemed a
    different code — same UNIQUE constraint, same check either way). Callers
    must not do any further work (crediting, Stripe calls) when this returns
    None — see "Concurrency & idempotency" in the design doc: this insert is
    the entire dedup mechanism, nothing past it should ever re-run."""
    resp = supabase.table("referral_code_redemptions").upsert(
        {"code_id": code_id, "redeemed_by": redeemed_by},
        on_conflict="redeemed_by",
        ignore_duplicates=True,
    ).execute()
    return resp.data[0] if resp.data else None


def update_redemption_row(redemption_id, **fields):
    supabase.table("referral_code_redemptions").update(fields).eq("id", redemption_id).execute()


def cas_increment_redemption_count(code_id, max_attempts=5):
    """Atomically increment redemption_count, respecting max_redemptions, using
    optimistic concurrency (compare-and-swap on the previously-read count)
    instead of a `redemption_count < max_redemptions` filter — PostgREST can't
    express a column-vs-column comparison, so this reads the current value and
    retries the UPDATE if a concurrent redemption changed it first. This is
    the same "let two concurrent redemptions both slip past the cap" gap the
    design doc's conditional-UPDATE pattern is meant to close, just phrased as
    a CAS loop. Returns (True, updated_row) on success, (False, code_row) if
    the cap is reached or contention couldn't be resolved within max_attempts."""
    for _ in range(max_attempts):
        code_row = get_referral_code_by_id(code_id)
        if not code_row:
            return False, None
        max_redemptions = code_row.get("max_redemptions")
        current = code_row.get("redemption_count", 0)
        if max_redemptions is not None and current >= max_redemptions:
            return False, code_row
        new_count = current + 1
        update = {"redemption_count": new_count}
        if max_redemptions is not None and new_count >= max_redemptions:
            update["status"] = "expired"
        resp = supabase.table("referral_codes").update(update) \
            .eq("id", code_id).eq("redemption_count", current).execute()
        if resp.data:
            return True, resp.data[0]
        # Lost the race to a concurrent redemption — loop and re-read.
    return False, get_referral_code_by_id(code_id)


_REDEMPTION_LOCK_TTL_SECONDS = 30


def try_acquire_redemption_lock(code_id):
    """Hand-rolled substitute for the design doc's pg_advisory_xact_lock — see
    migrations/add_referral_redemption_lock_column.sql for why. Claims
    referral_codes.redemption_locked_at via the same atomic-conditional-update
    pattern as cas_increment_redemption_count. A stale lock (crashed process)
    self-clears after _REDEMPTION_LOCK_TTL_SECONDS so it can't wedge a code
    forever. Only guards the referrer-side Stripe read-then-modify sequence
    (potentially shared across many concurrent invitees of one popular parent
    code) — an invitee's own credit never needs this, since UNIQUE(redeemed_by)
    already guarantees only one webhook ever processes a given invitee."""
    now = datetime.datetime.now(datetime.timezone.utc)
    stale_before = (now - datetime.timedelta(seconds=_REDEMPTION_LOCK_TTL_SECONDS)).isoformat()
    resp = supabase.table("referral_codes").update({"redemption_locked_at": now.isoformat()}) \
        .eq("id", code_id).or_(f"redemption_locked_at.is.null,redemption_locked_at.lt.{stale_before}").execute()
    return bool(resp.data)


def release_redemption_lock(code_id):
    supabase.table("referral_codes").update({"redemption_locked_at": None}).eq("id", code_id).execute()


_REDEMPTION_LOCK_RETRY_ATTEMPTS = 6
_REDEMPTION_LOCK_RETRY_DELAY_SECONDS = 0.4


def acquire_redemption_lock_blocking(code_id, max_attempts=_REDEMPTION_LOCK_RETRY_ATTEMPTS,
                                      delay_seconds=_REDEMPTION_LOCK_RETRY_DELAY_SECONDS):
    """try_acquire_redemption_lock, retried with a short delay between attempts.
    A single non-retried attempt isn't an equivalent substitute for the design
    doc's blocking pg_advisory_xact_lock: real contention here only lasts as
    long as whoever holds the lock's Stripe read+modify round trip (sub-second),
    so two redemptions of the same popular parent code landing close together —
    an expected case under normal load, not a pathological one — would
    otherwise have the second one give up and silently drop the referrer's
    reward forever. Retrying a handful of times covers that. max_attempts still
    caps the wait so a genuinely wedged/stale-but-not-yet-TTL-expired lock
    can't hang the webhook handler indefinitely; giving up after that remains
    the documented "skip this redemption's referrer credit, log it" behavior."""
    for attempt in range(max_attempts):
        if try_acquire_redemption_lock(code_id):
            return True
        if attempt < max_attempts - 1:
            time.sleep(delay_seconds)
    return False


def sum_referrer_credited_months(code_id, window_start, window_end):
    """SUM(months_credited_referrer) already granted to this parent's code
    within [window_start, window_end) — the referrer's rolling-12-month
    annual-cap check reads this before crediting another redemption."""
    resp = supabase.table("referral_code_redemptions").select("months_credited_referrer") \
        .eq("code_id", code_id) \
        .gte("redeemed_at", window_start.isoformat()) \
        .lt("redeemed_at", window_end.isoformat()) \
        .execute()
    return sum((row.get("months_credited_referrer") or 0) for row in (resp.data or []))


def current_annual_window(created_at, now=None):
    """The referrer's current rolling-12-month window: the most recent
    anniversary of `created_at` that is <= now, through one year later.
    created_at/now are ISO strings or datetimes; returns (start, end) as
    timezone-aware datetimes. See "Referrer reward cap" in the design doc for
    why users.created_at (not the ever-shifting subscription_period_end) is
    the anchor."""
    created_dt = created_at if isinstance(created_at, datetime.datetime) else _parse_ts(created_at)
    now = now or datetime.datetime.now(datetime.timezone.utc)

    def _in_year(dt, year):
        try:
            return dt.replace(year=year)
        except ValueError:
            return dt.replace(year=year, day=28)  # Feb 29 anchor, non-leap target year

    anniversary = _in_year(created_dt, now.year)
    if anniversary > now:
        anniversary = _in_year(created_dt, now.year - 1)
    return anniversary, _in_year(anniversary, anniversary.year + 1)


def list_referral_codes():
    """All codes, newest first — backs the admin listing view. Deliberately
    unfiltered (both code_types, every status): the admin view is meant to
    show the full lifecycle, not just currently-usable codes."""
    resp = supabase.table("referral_codes").select("*").order("created_at", desc=True).execute()
    return resp.data or []


def disable_referral_code(code_id):
    """Admin-only kill switch (abuse case) — see 'Lifecycle states' in the
    design doc: disabled is reserved for admin action, distinct from a code
    reaching expired naturally via valid_till/max_redemptions."""
    resp = supabase.table("referral_codes").update({"status": "disabled"}).eq("id", code_id).execute()
    return resp.data[0] if resp.data else None


def resolve_valid_referral_code(code):
    """Full validity check for a submitted code string: exists, active, not
    expired, under its redemption cap, and — for parent_referral codes only —
    the referring parent currently has access (subscription_status in
    active/past_due, same definition the login gate uses). Returns the code
    row if usable, None otherwise. Callers must not distinguish *why* it
    failed in any user-visible way — see the enumeration-prevention note in
    the design doc's "Validation at request time" section."""
    code_row = get_referral_code_by_code(code)
    if not code_row:
        return None
    if not _is_active_now(code_row):
        return None
    if code_row["code_type"] == "parent_referral":
        creator = get_user_by_id(code_row["created_by"])
        if not creator or creator.get("subscription_status") not in VALID_REDEMPTION_SUBSCRIPTION_STATUSES:
            return None
    return code_row
