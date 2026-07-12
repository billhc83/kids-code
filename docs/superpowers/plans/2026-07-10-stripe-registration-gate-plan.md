# Stripe-Gated Registration + `/try` Funnel Integration — Implementation Plan

**Spec of record:** [`2026-07-10-stripe-registration-gate-design.md`](../specs/2026-07-10-stripe-registration-gate-design.md) — every task below implements a section of it. Read it first.

**Goal:** No `users` row exists without an active Stripe subscription behind it (self-serve
accounts only — provisioned `class`/`beta`/`test` accounts untouched). Every splash-page CTA
offers a subscribe-or-try choice. `/try` prompts to subscribe on trial completion.

**Do not execute this plan yet.** It is presented for review per the user's request, matching
how `2026-07-09-try-page-infra.md` was staged before execution. Waiting for explicit go-ahead
task-by-task, same as that plan's own handoff note.

## Global constraints

- No code in this plan is executed until the user approves it.
- Never insert a `leads`-table row into `users`, and never touch admin-provisioned
  (`class`/`beta`/`test`) accounts' gate logic — `user_type == 'standard'` is the only branch
  the new checks apply to.
- Webhook signature verification (`STRIPE_WEBHOOK_SECRET`) is the actual security boundary on
  `/webhooks/stripe` — never trust the payload without it.
- No `str(exception)` leaking in any new anonymous/public response (same rule the try-page-infra
  plan already established for `/try/*`).
- All new Stripe SDK calls in tests are mocked via `monkeypatch` — no real network call to
  Stripe from the test suite, ever.

---

### Task 1: `users` subscription columns migration

**Files:**
- Create: `migrations/add_subscription_columns.sql`

- [ ] **Step 1: Write the migration**

```sql
-- Migration: add subscription columns
-- Run in the Supabase SQL editor before deploying the Stripe-gated registration flow.
-- See docs/superpowers/specs/2026-07-10-stripe-registration-gate-design.md for the
-- subscription_status state machine (none | pending | active | past_due | canceled).

ALTER TABLE users ADD COLUMN IF NOT EXISTS stripe_customer_id      TEXT DEFAULT NULL;
ALTER TABLE users ADD COLUMN IF NOT EXISTS stripe_subscription_id  TEXT DEFAULT NULL;
ALTER TABLE users ADD COLUMN IF NOT EXISTS subscription_status     TEXT NOT NULL DEFAULT 'none';
ALTER TABLE users ADD COLUMN IF NOT EXISTS subscription_period_end TIMESTAMPTZ DEFAULT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS idx_users_stripe_subscription_id
  ON users (stripe_subscription_id) WHERE stripe_subscription_id IS NOT NULL;

-- subscription_status values: 'none' (provisioned accounts) | 'pending' (row created,
-- Checkout not yet confirmed) | 'active' | 'past_due' | 'canceled'
```

- [ ] **Step 2: Hand off to Bill**

Same convention as `add_leads_table.sql`/`add_provisioning_columns.sql` — this plan does not
execute the SQL. Note in the handoff section at the bottom of this doc.

- [ ] **Step 3: Commit**

```bash
git add migrations/add_subscription_columns.sql
git commit -m "Add users subscription-status columns migration"
```

---

### Task 2: Config + dependency

**Files:**
- Modify: `config.py`
- Modify: `requirements.txt`

- [ ] **Step 1: Add Stripe env vars to `config.py`**

Append after the existing `OPENAI_EMBEDDING_MODEL` line:

```python
STRIPE_SECRET_KEY      = os.getenv("STRIPE_SECRET_KEY")
STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY")
STRIPE_WEBHOOK_SECRET  = os.getenv("STRIPE_WEBHOOK_SECRET")
STRIPE_PRICE_ID        = os.getenv("STRIPE_PRICE_ID")
```

- [ ] **Step 2: Add the `stripe` package**

Add a line to `requirements.txt` (alphabetical-ish placement isn't enforced in this file
today, append near `supabase`):

```
stripe
```

Run: `pip install stripe` locally to unblock the rest of this plan's steps.

- [ ] **Step 3: Commit**

```bash
git add config.py requirements.txt
git commit -m "Add Stripe config vars and SDK dependency"
```

---

### Task 3: `utils/billing.py` — Stripe data-access helpers

**Files:**
- Create: `utils/billing.py`
- Test: `tests/test_billing.py`

**Interfaces:**
- Produces: `create_checkout_session(user) -> str` (returns the Checkout Session URL),
  `handle_checkout_completed(event) -> None`, `handle_subscription_updated(event) -> None`,
  `handle_subscription_deleted(event) -> None`, `verify_webhook_signature(payload, sig_header) -> dict`
  (raises `stripe.error.SignatureVerificationError` on failure — let the route catch it).
- Consumes: `utils.auth.get_user_by_username`/equivalent user lookups (add
  `get_user_by_id`/`get_user_by_stripe_subscription_id` to `utils/auth.py` if not already
  present — check first), `utils.auth.send_verification_email` (existing).

- [ ] **Step 1: Add missing lookup helpers to `utils/auth.py` if absent**

Run: `grep -n "def get_user_by_id\|def get_user_by_stripe_subscription_id" utils/auth.py`

If `get_user_by_id` is missing, add it next to `get_user_by_email` (`utils/auth.py:41-43`):

```python
def get_user_by_id(user_id):
    resp = supabase.table("users").select("*").eq("id", user_id).execute()
    return resp.data[0] if resp.data else None

def get_user_by_stripe_subscription_id(subscription_id):
    resp = supabase.table("users").select("*").eq("stripe_subscription_id", subscription_id).execute()
    return resp.data[0] if resp.data else None
```

- [ ] **Step 2: Update `create_user` to accept `subscription_status`**

In `utils/auth.py:45-60`, add a parameter and field:

```python
def create_user(email, username, password_hash, is_parent=False, agreed_at=None, subscription_status="none"):
    ...
    resp = supabase.table("users").insert({
        ...
        "agreed_at": agreed_at,
        "subscription_status": subscription_status,
    }).execute()
```

Every existing caller (admin provisioning in `routes/admin.py`, if it calls `create_user`
directly — check first) keeps the default `"none"` unless it's the self-serve path.

Run: `grep -rn "create_user(" routes/ utils/` to confirm every call site and whether any
non-`routes/auth.py` caller needs updating (admin-provisioned accounts should end up with
`subscription_status='none'`, which is already the default, so those call sites likely need
no change — verify, don't assume).

- [ ] **Step 3: Write `utils/billing.py`**

```python
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
    ts = subscription_obj.get("current_period_end")
    if not ts:
        return None
    return datetime.datetime.fromtimestamp(ts, tz=datetime.timezone.utc).isoformat()


def handle_checkout_completed(event):
    session_obj = event["data"]["object"]
    user_id = session_obj.get("client_reference_id")
    if not user_id:
        return
    user = get_user_by_id(user_id)
    if not user:
        return

    subscription_id = session_obj.get("subscription")
    subscription_obj = stripe.Subscription.retrieve(subscription_id) if subscription_id else {}

    supabase.table("users").update({
        "stripe_customer_id": session_obj.get("customer"),
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
    mapped_status = _STRIPE_STATUS_MAP.get(subscription_obj.get("status"), "canceled")
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
```

- [ ] **Step 4: Write the tests**

```python
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
```

- [ ] **Step 5: Run the tests**

Run: `pytest tests/test_billing.py -v`
Expected: 5 passed. (If `mock_supabase`'s PATCH matching is finicky, loosen the mocked URL to
the base path per the existing loose-matching note in `tests/conftest.py`.)

- [ ] **Step 6: Commit**

```bash
git add utils/billing.py utils/auth.py tests/test_billing.py
git commit -m "Add Stripe Checkout + webhook data-access helpers"
```

---

### Task 4: `routes/billing.py` — checkout, success/cancelled/pending pages, webhook

**Files:**
- Create: `routes/billing.py`
- Create: `templates/subscribe_success.html`, `templates/subscribe_cancelled.html`, `templates/subscribe_pending.html`
- Modify: `app.py` (register blueprint)
- Test: `tests/test_billing_routes.py`

- [ ] **Step 1: Write `routes/billing.py`**

```python
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
```

- [ ] **Step 2: Write the three small templates**

`templates/subscribe_success.html` (fallback for when `pending_subscription_user_id` is
somehow missing — the normal path redirects to `/check-email` and never renders this):

```html
{% extends "base.html" %}
{% block content %}
<div class="auth-card">
  <h2>Payment received! 🎉</h2>
  <p>We're finishing setting up your account. Check your email in a moment for a verification link, or <a href="{{ url_for('auth.login') }}">log in</a> once you've verified.</p>
</div>
{% endblock %}
```

`templates/subscribe_cancelled.html`:

```html
{% extends "base.html" %}
{% block content %}
<div class="auth-card">
  <h2>No worries!</h2>
  <p>You can finish subscribing any time.</p>
  <p><a href="{{ url_for('billing.subscribe_checkout') }}">Resume Checkout</a> — or <a href="{{ url_for('try_it.try_page') }}">try it free first</a>.</p>
</div>
{% endblock %}
```

`templates/subscribe_pending.html`:

```html
{% extends "base.html" %}
{% block content %}
<div class="auth-card">
  <h2>Your subscription isn't active yet</h2>
  <p>If you just paid, give it a moment and <a href="{{ url_for('auth.login') }}">try logging in again</a>.</p>
  <form method="GET" action="{{ url_for('billing.subscribe_checkout') }}">
    <button type="submit">Resume Checkout</button>
  </form>
</div>
{% endblock %}
```

(Check `templates/base.html`'s actual block name — `content` is a guess; grep the existing
`templates/check_email.html` for the block name it extends and match it exactly.)

- [ ] **Step 3: Register the blueprint in `app.py`**

After `from routes.try_it import try_it_bp`:

```python
from routes.billing import billing_bp
```

After `app.register_blueprint(try_it_bp)`:

```python
app.register_blueprint(billing_bp)
```

- [ ] **Step 4: Write route tests**

```python
"""
tests/test_billing_routes.py — route-level tests for routes/billing.py.
"""

import stripe


def test_subscribe_checkout_requires_pending_session(client):
    resp = client.get("/subscribe/checkout")
    assert resp.status_code == 400


def test_subscribe_checkout_redirects_to_stripe(client, monkeypatch):
    monkeypatch.setattr("routes.billing.get_user_by_id", lambda uid: {"id": "user-1", "email": "a@example.com"})
    monkeypatch.setattr("routes.billing.create_checkout_session", lambda user, success_url, cancel_url: "https://checkout.stripe.com/fake")
    with client.session_transaction() as sess:
        sess["pending_subscription_user_id"] = "user-1"
    resp = client.get("/subscribe/checkout")
    assert resp.status_code == 302
    assert resp.location == "https://checkout.stripe.com/fake"


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
```

- [ ] **Step 5: Run the tests**

Run: `pytest tests/test_billing_routes.py -v`
Expected: 5 passed.

- [ ] **Step 6: Commit**

```bash
git add routes/billing.py templates/subscribe_success.html templates/subscribe_cancelled.html templates/subscribe_pending.html app.py tests/test_billing_routes.py
git commit -m "Add Stripe checkout/success/cancelled/pending routes and webhook receiver"
```

---

### Task 5: Wire registration + login to the gate

**Files:**
- Modify: `routes/auth.py`

- [ ] **Step 1: Update `register()` (`routes/auth.py:58-95`)**

Replace the block from `agreed_at = ...` through the redirect:

```python
        agreed_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
        password_hash = hash_password(password)
        user = create_user(email, username, password_hash, is_parent, agreed_at=agreed_at, subscription_status="pending")
        if not user:
            flash("Registration failed, please try again")
            return render_template("register.html")

        session["pending_subscription_user_id"] = user["id"]
        return redirect(url_for("billing.subscribe_checkout"))
```

Note: `send_verification_email(email, user["verification_token"])` and
`session["pending_email"] = email` are **removed** from this function — they now happen in
`utils.billing.handle_checkout_completed` and `routes.billing.subscribe_success`
respectively.

- [ ] **Step 2: Update `login()` (`routes/auth.py:15-56`)**

Insert after the existing `is_verified` check (after line 33's `return redirect(...)`), before
the `session["user_id"] = ...` block:

```python
        if user["user_type"] == "standard" and user.get("subscription_status") not in ("active", "past_due"):
            flash("Your subscription isn't active yet.")
            return redirect(url_for("billing.subscribe_pending", user_id=user["id"]))
```

- [ ] **Step 3: Run the existing auth test suite**

Run: `pytest tests/test_auth.py -v`
Expected: existing tests updated as needed — `test_register_success` (currently asserting a
302 to check-email, per the diff already committed to `dev1` before this branch existed) now
needs to assert a 302 to `billing.subscribe_checkout` instead. Update that assertion.

- [ ] **Step 4: Add new gate-specific tests to `tests/test_auth.py`**

```python
def test_register_redirects_to_checkout(client, mock_supabase):
    # ... existing mock_supabase setup for create_user, mirroring test_register_success ...
    response = client.post("/register", data={
        "email": "test2@example.com", "username": "newuser2", "password": "password123",
        "is_parent": "false", "agree_tos": "true",
    })
    assert response.status_code == 302
    assert "/subscribe/checkout" in response.location


def test_login_blocks_standard_user_without_active_subscription(client, mock_supabase, monkeypatch):
    # mock get_user_by_username to return a standard user with subscription_status='pending'
    ...
    response = client.post("/login", data={"username": "pendinguser", "password": "password123"})
    assert response.status_code == 302
    assert "/subscribe/pending" in response.location


def test_login_allows_provisioned_user_regardless_of_subscription_status(client, mock_supabase, monkeypatch):
    # mock a user_type='class' user with subscription_status='none'
    ...
    response = client.post("/login", data={"username": "classuser", "password": "password123"})
    assert response.status_code == 302
    assert "/subscribe" not in response.location
```

(Fill in the `mock_supabase`/`monkeypatch` bodies following the existing pattern already used
elsewhere in `tests/test_auth.py` — check that file's existing fixtures before writing these
literally, since the exact mock shape depends on what's already set up there.)

- [ ] **Step 5: Run the full auth test suite**

Run: `pytest tests/test_auth.py -v`
Expected: all passed.

- [ ] **Step 6: Commit**

```bash
git add routes/auth.py tests/test_auth.py
git commit -m "Gate registration behind Stripe Checkout and login behind active subscription"
```

---

### Task 6: Splash page subscribe-or-try modal

**Files:**
- Modify: `templates/splash.html`

- [ ] **Step 1: Add the modal markup**

Add just before `</body>` in `templates/splash.html`:

```html
<div id="subscribe-modal-overlay" style="display:none;position:fixed;inset:0;background:rgba(13,17,23,0.85);z-index:9999;align-items:center;justify-content:center;padding:20px;">
  <div id="subscribe-modal" style="background:#fff;border-radius:16px;max-width:420px;width:100%;padding:24px;box-shadow:0 24px 64px rgba(0,0,0,0.4);text-align:center;">
    <h2 style="margin:0 0 8px;font-size:18px;">Ready to start building? 🚀</h2>
    <a href="{{ url_for('auth.register') }}" class="cta-primary" style="display:block;margin-bottom:12px;">Subscribe & Start →</a>
    <a href="{{ url_for('try_it.try_page') }}" class="cta-secondary" style="display:block;">Try it free first →</a>
  </div>
</div>
<script>
(function () {
  var overlay = document.getElementById('subscribe-modal-overlay');
  document.querySelectorAll('[data-action="open-subscribe-modal"]').forEach(function (el) {
    el.addEventListener('click', function (e) {
      e.preventDefault();
      overlay.style.display = 'flex';
    });
  });
  overlay.addEventListener('click', function (e) {
    if (e.target === overlay) overlay.style.display = 'none';
  });
})();
</script>
```

- [ ] **Step 2: Convert the three existing CTAs to modal triggers**

Change each of these three `<a href="{{ url_for('auth.register') }}">` elements (lines 345,
356, 778 per the current file — search by content since exact line numbers may have shifted):

Before (nav, line 345):
```html
<a href="{{ url_for('auth.register') }}" class="nav-link primary">Get Started →</a>
```
After:
```html
<a href="#" data-action="open-subscribe-modal" class="nav-link primary">Get Started →</a>
```

Before (hero, line 356):
```html
<a href="{{ url_for('auth.register') }}" class="cta-primary">Start Your First Mission →</a>
```
After:
```html
<a href="#" data-action="open-subscribe-modal" class="cta-primary">Start Your First Mission →</a>
```

Before (demo section, line 778, inside a JS string):
```javascript
'<a href="/register" style="color:#0969da;font-weight:700;">Sign up to try the full platform →</a>' +
```
After:
```javascript
'<a href="#" data-action="open-subscribe-modal" style="color:#0969da;font-weight:700;">Sign up to try the full platform →</a>' +
```

Note: since this third one is injected via JS string concatenation, confirm the click
listener in Step 1 is attached with event delegation or re-queried after injection — if the
existing code path injects this HTML after page load, `document.querySelectorAll(...)` in
Step 1's `DOMContentLoaded`-time script will miss it. Check how/when that string is inserted
into the DOM (`grep -n "Sign up to try the full platform" templates/splash.html` for the
surrounding function) and either move the modal-open listener to event delegation on
`document` (`e.target.closest('[data-action="open-subscribe-modal"]')`) or attach it at
injection time — delegation is simpler and covers all three CTAs uniformly regardless of
when they're added to the DOM.

- [ ] **Step 3: Manual smoke check**

Run: `python -c "from app import app; c = app.test_client(); r = c.get('/'); body = r.data.decode(); print(body.count('data-action=\"open-subscribe-modal\"'))"`
Expected: `3` (adjust route in the test if `splash.html` isn't served at `/` — check
`routes/main.py` for the actual route).

- [ ] **Step 4: Commit**

```bash
git add templates/splash.html
git commit -m "Route splash page CTAs through a subscribe-or-try-it-free modal"
```

---

### Task 7: `/try` trial-completion subscribe prompt

**Files:**
- Modify: `templates/try_it_builder.html`

- [ ] **Step 1: Add the overlay markup**

Add alongside the existing `#try-email-gate-overlay` and `#try-welcome-overlay` elements
(same structural pattern — see `2026-07-09-try-page-infra-design.md`'s Email gate section
and the try-welcome-splash spec for the established look):

```html
<div id="try-subscribe-prompt-overlay" style="display:none;position:fixed;inset:0;background:rgba(13,17,23,0.85);z-index:9999;align-items:center;justify-content:center;padding:20px;">
  <div style="background:#fff;border-radius:16px;max-width:420px;width:100%;padding:24px;box-shadow:0 24px 64px rgba(0,0,0,0.4);text-align:center;">
    <h2 style="margin:0 0 8px;font-size:18px;">You completed the free trial! 🎉</h2>
    <p style="margin:0 0 16px;font-size:13px;color:#475569;">Ready to build 18 more real projects?</p>
    <a href="{{ url_for('auth.register') }}" style="display:block;padding:10px;background:#22c55e;color:#020617;font-weight:600;border-radius:6px;text-decoration:none;margin-bottom:10px;">Subscribe →</a>
    <button id="try-subscribe-dismiss" style="background:none;border:none;color:#475569;font-size:12px;">Keep exploring</button>
  </div>
</div>
```

- [ ] **Step 2: Add the trigger script**

Add near the existing email-gate script (same `window.bbNext`-polling pattern already
established in Task 5, Step 6 of the try-page-infra plan — reuse the poll, add a second
condition rather than a second poll loop):

```html
<script>
(function () {
  var FINAL_STEP_INDEX = 3; // "Mission Complete" — see utils/project_try_it.py's SKETCH
  var overlay = document.getElementById('try-subscribe-prompt-overlay');
  var dismissBtn = document.getElementById('try-subscribe-dismiss');
  dismissBtn.addEventListener('click', function () { overlay.style.display = 'none'; });

  var shown = sessionStorage.getItem('try_subscribe_prompt_shown') === 'true';
  var checkInterval = setInterval(function () {
    if (shown || !window.BB || typeof BB.CURRENT_STEP !== 'number') return;
    if (BB.CURRENT_STEP >= FINAL_STEP_INDEX) {
      shown = true;
      sessionStorage.setItem('try_subscribe_prompt_shown', 'true');
      overlay.style.display = 'flex';
      clearInterval(checkInterval);
    }
  }, 300);
})();
</script>
```

Note: this polls `BB.CURRENT_STEP` rather than wrapping `window.bbNext` (unlike the email
gate) because the trigger condition here is "has reached the final step" (a state check),
not "is about to advance past a specific step" (an action interception) — the email gate
needs to interpose *before* the advance to the next step; this prompt only needs to notice
*after* the visitor has already arrived at the last step. Confirm `BB.CURRENT_STEP` is the
correct/existing global by checking `static/js/block_builder.js` for how the email gate's own
`atGateStep` check reads it (`window.BB && BB.CURRENT_STEP === GATE_AFTER_STEP_INDEX` per the
already-merged code) — reuse the exact same global, do not introduce a new one.

- [ ] **Step 3: Manual smoke check**

Run: `grep -n "try-subscribe-prompt-overlay\|FINAL_STEP_INDEX" templates/try_it_builder.html`
Expected: both present, no traceback needed since this is a template/JS-only check — verify
by loading `/try` in a browser, completing all 4 steps, and confirming the overlay appears
once and not again on further interaction within the same tab.

- [ ] **Step 4: Commit**

```bash
git add templates/try_it_builder.html
git commit -m "Add trial-completion subscribe prompt to /try"
```

---

## Handing off to you (Bill)

- Task 1's SQL migration is not run by any task here — same convention as the two prior
  migrations. Run `migrations/add_subscription_columns.sql` in the Supabase SQL editor once
  Task 1 is merged, before Task 4/5 are deployed (registration will fail on every attempt
  until the columns exist).
- You'll need to create the Stripe product/price in the Stripe dashboard yourself and set
  `STRIPE_SECRET_KEY`, `STRIPE_PUBLISHABLE_KEY`, `STRIPE_WEBHOOK_SECRET`, `STRIPE_PRICE_ID` in
  the deploy environment — none of this plan creates Stripe-dashboard-side objects.
  `STRIPE_WEBHOOK_SECRET` specifically comes from registering the `/webhooks/stripe` endpoint
  URL in the Stripe dashboard (or via the Stripe CLI for local testing) — that registration
  step also isn't something this plan can do for you.
- Recommend testing the whole loop once against Stripe's test mode (test API keys, test
  card `4242 4242 4242 4242`) before flipping to live keys.

## Explicitly out of scope (unchanged from the spec)

- Teacher/cohort license payment flow.
- Self-service billing portal (plan changes, cancellation, card updates from account
  settings).
- Multiple pricing tiers.
- Revenue/subscriber reporting dashboards / Stripe reporting-API integration.
- Automated cleanup of abandoned `pending` signup rows (flagged, not built).
