# Stripe-Gated Registration + `/try` Funnel Integration — Design Spec

Status: implemented (all 7 plan tasks + 3 post-implementation fixes below, plus the
registration-access gate below), pending Bill's Supabase migrations
(`add_subscription_columns.sql` and the new `add_registration_invites_table.sql`) + Stripe
dashboard setup per the plan's handoff section.

## Known unresolved gap: `/register` itself is not abuse-resistant

Flagged by Bill (2026-07-10) as a dissatisfaction with the shipped design, after asking why
"Subscribe & Start" lands on `/register` first: the gate as built only blocks *login* on an
unpaid account — it does **not** stop `/register` itself from being spammed.

**Why this matters:** the whole reason this initiative chose "gate registration behind
Stripe" over a freemium model, per this doc's own predecessor
([`2026-07-09-try-page-infra-design.md`](2026-07-09-try-page-infra-design.md)), was that *"a
free registration endpoint is a soft target for abuse (fake signups, bot farms) in a way a
Stripe-gated one isn't."* The stated invariant was: **no free row in `users` until payment
succeeds.** What actually shipped does not hold that invariant.

**What actually happens today:** `routes/auth.py`'s `register()` creates a real `users` row
(`subscription_status='pending'`) immediately on `POST /register`, before Stripe is ever
contacted. The only defenses are the pre-existing `@limiter.limit("5 per minute")` (per-IP,
trivially defeated by rotating IPs/proxies) and the fact that nothing currently cleans up
abandoned `pending` rows (already flagged as a follow-up in the implementation plan, never
built). A bot can freely burn usernames/emails and create disposable database rows all day
without ever touching Stripe — it just can never log into any of them. That is a materially
weaker guarantee than "no free row until payment."

**Alternatives considered:**

- **Defer `users` row creation to the webhook** (stash registration details in a
  `pending_registrations` token table, only materialize the row on
  `checkout.session.completed`) — fully restores the strict "no row until payment" invariant,
  but requires reworking the already-implemented, already-tested Checkout/webhook flow (moving
  the username/email uniqueness check onto the pending table, handling the reservation-race
  window). Rejected for now: it's the biggest diff on the part of the system that's already
  shipped and working, for a problem a lighter gate addresses well enough.
- **Reorder to payment-first** (Stripe Checkout collects just an email before any account form
  exists at all; `/register`'s username/password step only unlocks after payment succeeds) —
  the strongest possible gate on the page itself, but every failure mode (abandoned tab, lost
  session/cookie, different device) now strands someone who already **paid** with no way to
  reach their account. That's a materially worse support/trust problem than a harmless spam
  row, and fixing it properly converges back into needing webhook-driven, token-based account
  creation anyway — i.e., most of the complexity of the option above, plus new
  payment-reconciliation edge cases, for a worse worst case. Rejected.
- **CAPTCHA / edge bot-challenge only** — cheap, and worth adding regardless at some point, but
  doesn't gate the *page*, only raises the cost of hitting it. Treated as optional
  complementary hardening, not a replacement for a real access gate.

**Decided fix, implemented below:** gate `/register` itself behind a one-time emailed link,
requested via a new lightweight step in front of it. The existing Checkout/webhook/login-gate
flow (everything from "Registration flow" onward in this doc) does not change — this only adds
a new step *before* a visitor can ever see the `/register` form. See "Registration-access gate"
below for the full design.

## Post-implementation fixes (found during review, all applied)

1. **Migration now backfills existing users.** The original migration set
   `subscription_status` to default `'none'` with no backfill, which would have locked out
   every pre-existing `standard` account (including parent-created student sub-accounts,
   see #3) the instant the gated login code deployed. Fixed with a one-time
   `UPDATE ... WHERE user_type = 'standard' AND subscription_status = 'none'` in the
   migration — applies only to rows that exist at migration time, not going forward.
2. **`/subscribe/pending` no longer takes a `user_id` URL parameter.** The original route
   (`/subscribe/pending/<user_id>`) trusted an arbitrary client-supplied ID with no
   authentication and wrote it straight into the session, letting anyone start a Checkout
   session against an account they don't own (an IDOR). It's now parameterless and only
   reads `session['pending_subscription_user_id']`, which only `routes/auth.py`'s `login()`
   sets, after it has already verified the caller's username+password.
3. **Parent-created student sub-accounts (`utils.auth.create_student_for_parent`) are gated
   on the linking parent's live status, not their own row.** These accounts have no Stripe
   subscription of their own — their own `subscription_status` is always the column default.
   Copying the parent's status onto the student at creation time was considered and
   rejected: it would go permanently stale the moment the parent's subscription later lapses
   or is canceled, since Stripe's webhook only ever updates the parent's own row, silently
   breaking the "every `users` row is a paying account" invariant for every child account
   ever created. Instead, `routes/auth.py`'s login gate calls the new
   `utils.auth.get_linking_parent(student_id)` and checks the parent's current
   `subscription_status` at each login — one extra query, only on the (already rare) path
   where the student's own status looks inactive, so the cost is bounded to login time, not
   per-request. When blocked this way, `session['pending_subscription_user_id']` is set to
   the **parent's** id (not the student's, who has no real email to start Checkout with),
   and the flash message says "Ask them to renew it" instead of the generic
   "Your subscription isn't active yet."
4. **Login gate now checks `subscription_status` before `is_verified`.** Found by live-testing
   the registration-access-gate flow end to end: a standard signup's verification email is
   only ever sent by the Stripe webhook (`handle_checkout_completed`), so an account that
   hasn't finished Checkout yet is always *both* unverified *and* `subscription_status`
   `pending`. With the original ordering (`is_verified` checked first, matching this doc's
   original "Login gate" section below), that account hit the "Please verify your email
   before logging in" branch and got redirected to `/check-email` — which claims a
   verification link was already sent, when none ever was. Swapped the order in
   `routes/auth.py`'s `login()`: subscription status is now checked first for
   `user_type == 'standard'`, so an unpaid account is told about the missing subscription
   (the actual blocker) instead of a fictitious unsent email. Once a real subscription goes
   active and the webhook actually sends the verification email, the `is_verified` check
   still runs (now second) and behaves exactly as before for that case.

## Context

This is the deferred follow-up spec named by
[`2026-07-09-try-page-infra-design.md`](2026-07-09-try-page-infra-design.md) ("Stripe
Checkout / registration / webhook flow. Follow-up spec.") and by
[`TODO.md`](../../../TODO.md) ("Stripe Checkout / registration / webhook flow — separate
future spec, not started."). The gate model itself was already decided in that earlier doc
and is restated, not re-litigated, here:

- **Payer**: individual parent/adult accounts. Teacher/cohort licenses (provisioned via
  `routes/admin.py`'s cohort panel, `user_type='class'`) are out of scope — those accounts
  are created directly by an admin and never touch `/register`.
- **Gate model**: registration is gated behind a Stripe subscription — no row is created in
  `users` until Stripe confirms payment. This preserves the invariant that every `users` row
  is either a paying self-serve account or an admin-provisioned one (`class`/`beta`/`test`),
  which keeps subscriber/revenue metrics simple and avoids a free signup endpoint being a
  soft target for bot/fake-account abuse.
- **`/try` already exists** (see the try-page-infra spec) as the account-less trial surface
  that recovers top-of-funnel visibility without exposing a real signup endpoint.

This spec covers the piece those two didn't: actually wiring Stripe into `/register`, and
connecting `/try` into the paid funnel as the "try before you buy" branch.

## Goals

1. No `users` row is ever created for a self-serve (`user_type='standard'`) signup without an
   active Stripe subscription behind it.
2. Every "Get Started" / "Register" entry point on `splash.html` offers a choice — subscribe
   now, or try it free first — instead of dropping straight into the registration form.
3. `/try` gets a completion moment that converts: after the visitor finishes the trial
   sketch, prompt them to subscribe.
4. Admin-provisioned accounts (`class`/`beta`/`test`) are entirely unaffected — they don't
   go through `/register` today and won't go through Stripe either.

## Non-goals / explicitly out of scope

- Teacher/cohort license **payment** flow (provisioning itself already exists and stays
  free/admin-driven; billing a school/cohort is a separate future spec).
- A self-service billing portal (plan changes, cancellation from account settings, updating
  card on file). V1 ships Stripe Checkout + webhooks only; cancellation happens via the
  Stripe customer portal link or manually for now.
- Multiple pricing tiers/plans. One `STRIPE_PRICE_ID`, one subscription product.
- Proration, coupons, trials-with-card-required inside Stripe itself (`/try` *is* the trial;
  Stripe subscriptions start active-and-paid on Checkout completion, no Stripe-side trial
  period).
- Revenue/subscriber reporting dashboards. Data lands in `users` and Stripe's own dashboard;
  a reporting API integration is future work (also named out-of-scope by the prior spec).
- Reusing this popup pattern anywhere other than the CTAs enumerated below.
- Automated cleanup of abandoned `pending` signups (see "Abandoned pending rows" below) —
  flagged as a follow-up, not blocking.

## Gate model, precisely

Add four columns to `users` (migration below). `subscription_status` is the field every gate
check reads:

| Value | Meaning |
|---|---|
| `none` | Default for admin-provisioned rows (`class`/`beta`/`test`) — the gate never checks this value for them; see "Who is gated" below. |
| `pending` | Self-serve row created, Stripe Checkout session started, webhook confirmation not yet received. Cannot log in. |
| `active` | Stripe confirmed the subscription. Full access. |
| `past_due` | Stripe payment failed but subscription hasn't been canceled yet (Stripe's own retry schedule is mid-flight). Access preserved for now — see decision below. |
| `canceled` | Subscription ended (non-payment exhausted Stripe's retries, or explicit cancellation). Login blocked, same UX as `pending`. |

**Who is gated**: the login check only applies when `user_type == 'standard'`. This mirrors
the existing `needs_tos` special-case in `routes/auth.py:41-45`, which already branches on
`user_type` for a different reason — same field, same pattern, no new concept.

**`past_due` stays logged-in**: chosen because Stripe already retries failed payments over
~2-3 weeks before it cancels the subscription (`customer.subscription.deleted`); yanking
access on the first failed charge (e.g. an expired card) is a worse experience than letting
Stripe's own retry cadence play out. Revisit if this turns out to be too lenient in practice.

## New `users` columns (migration)

`migrations/add_subscription_columns.sql` (new, follows the existing
`add_provisioning_columns.sql` / `add_leads_table.sql` pattern — run manually in the Supabase
SQL editor, not an ORM-managed migration):

```sql
ALTER TABLE users ADD COLUMN IF NOT EXISTS stripe_customer_id     TEXT DEFAULT NULL;
ALTER TABLE users ADD COLUMN IF NOT EXISTS stripe_subscription_id TEXT DEFAULT NULL;
ALTER TABLE users ADD COLUMN IF NOT EXISTS subscription_status    TEXT NOT NULL DEFAULT 'none';
ALTER TABLE users ADD COLUMN IF NOT EXISTS subscription_period_end TIMESTAMPTZ DEFAULT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS idx_users_stripe_subscription_id
  ON users (stripe_subscription_id) WHERE stripe_subscription_id IS NOT NULL;
```

The unique index lets the webhook handler look up a user by `stripe_subscription_id` (needed
for `customer.subscription.updated`/`.deleted`, which carry a subscription ID but not the
`client_reference_id` that `checkout.session.completed` has).

## Registration-access gate (implemented)

Addresses the "Known unresolved gap" above: `/register` (`GET` and `POST`) is no longer
reachable without first proving control of a real inbox. This sits entirely in front of the
Registration flow section below — nothing past this point changes.

Implemented in `routes/auth.py` (`register_invite`, gated `register`), `utils/auth.py`
(`create_registration_invite`, `get_valid_registration_invite`,
`mark_registration_invite_used`, `send_registration_invite_email`), templates
`register_invite.html` / `register_invite_sent.html` / updated `register.html`, and
`migrations/add_registration_invites_table.sql`. Both `splash.html`'s "Subscribe & Start" CTA
and `try_it_builder.html`'s trial-completion "Subscribe →" button now point at
`auth.register_invite` instead of `auth.register` directly.

### New route: `GET/POST /register/invite`

Replaces the direct link to `/register` on every entry point (splash CTAs, `/try`
trial-completion prompt — see the updated links in their respective sections below).

- **`GET /register/invite`** renders a minimal form: email (required), referral/invite code
  (optional, free-text — see "Referral code" below).
- **`POST /register/invite`**, rate-limited the same as today's `/register`
  (`@limiter.limit("5 per minute")`, per-IP — same known limitation as today, but acceptable
  here since the worst this route enables is "someone requests emails to inboxes they don't
  control," which wastes an email send, not a `users` row):
  1. Generates a random token (`secrets.token_urlsafe(32)`, same pattern already used
     elsewhere for session/verification tokens).
  2. Inserts a row into a new `registration_invites` table: `token` (PK), `email`,
     `referral_code` (nullable), `created_at`, `expires_at` (`now() + 60 minutes`), `used_at`
     (nullable).
  3. Emails the link `{{ url_for('auth.register', token=token) }}` via the existing mail
     infra (new template alongside `send_verification_email`).
  4. Always redirects to a generic "check your email" confirmation regardless of whether the
     address is real — same enumeration-prevention pattern as any "forgot password"-style flow
     (don't reveal via response content/timing whether an email is already in the system).

`migrations/add_registration_invites_table.sql` (new, same manual-Supabase-SQL-editor pattern
as `add_leads_table.sql`):

```sql
CREATE TABLE IF NOT EXISTS registration_invites (
    token          TEXT PRIMARY KEY,
    email          TEXT NOT NULL,
    referral_code  TEXT DEFAULT NULL,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at     TIMESTAMPTZ NOT NULL,
    used_at        TIMESTAMPTZ DEFAULT NULL
);
```

### `/register` now requires a valid token

`GET /register`:
- Redirects to `/register/invite` if the `token` query param is missing, not found, expired
  (`expires_at < now()`), or already used (`used_at IS NOT NULL`).
- Otherwise renders today's form, pre-filling `email` from the invite row (read-only — the
  token was issued for that specific address) and threading `token` through as a hidden field
  for the `POST`.

`POST /register`: unchanged validation/logic (username/password/`agree_tos`,
`create_user(..., subscription_status='pending')`,
`session['pending_subscription_user_id']`, redirect to `/subscribe/checkout`) **plus** one new
step: re-validates the hidden `token` field the same way as the `GET` (missing/expired/used →
reject), and on success sets `used_at = now()` on the invite row in the same transaction as
`create_user(...)`. This is what makes the link single-use — stops someone from
replaying/sharing a still-fresh link to spin up multiple pending rows from one proof of email
ownership.

### Why this is robust, not just cheap

Every failure mode this introduces resolves before Stripe is ever involved:
- Link never clicked → nothing created, no cost.
- Link clicked, form abandoned → same "abandoned pending row" case already flagged below as a
  non-blocking follow-up, just far lower volume since reaching it now requires real inbox
  control.
- Link expired or reused → clean re-request, no state to reconcile, no support burden.

Nobody can end up having paid with nothing to show for it, because payment still only ever
happens after the existing, unchanged, already-tested Stripe Checkout step — this gate sits
strictly upstream of it. This was the deciding factor over the payment-first alternative above.

### Referral code — captured, not yet acted on

`referral_code` is stored on the invite row purely for future attribution (e.g. "credit
referrer X when this converts"). No new `users` column, no reward logic, no validation that a
code is real — in scope here is only *capturing* it so it isn't lost if/when a referral program
gets built. Flagged as a follow-up, not blocking.

### Abandoned-row cleanup now covers two tables

The cleanup cron already flagged below as a follow-up (see "Abandoned `pending` rows") should
purge both: `users` rows with `subscription_status='pending'` older than 24h, and
`registration_invites` rows past `expires_at` (safe to delete immediately on expiry, no grace
period needed). Still not built, still not blocking launch — noted here so it isn't scoped as
only half-done later.

## Registration flow

### Today (`routes/auth.py:58-95`)

`POST /register` validates the form, calls `create_user(...)` immediately, sends the
verification email, redirects to `/check-email`.

### New flow

`POST /register` keeps every existing validation (username/email/password/`agree_tos`), but:

1. Calls `create_user(..., subscription_status='pending')` — the row is created immediately
   (not deferred until after Stripe) so the username/email uniqueness check
   (`get_user_by_username`) has something to check against for the *next* signup attempt
   racing the same username, same as today.
2. **No verification email sent yet** — that moves to the webhook handler (step below), since
   sending it before payment is confirmed would let someone verify an account they never pay
   for.
3. Stores `session['pending_subscription_user_id'] = user['id']` (same pattern as the
   existing `session['pending_email']` used by `/check-email`) and redirects to
   `GET /subscribe/checkout` instead of `/check-email`.

`GET /subscribe/checkout` (new, in `routes/billing.py`):

1. Reads `session['pending_subscription_user_id']`; 400s if absent (direct navigation with no
   in-flight registration).
2. Creates a Stripe Checkout Session: `mode='subscription'`, one line item at
   `STRIPE_PRICE_ID`, `client_reference_id=user_id`, `customer_email=user['email']`,
   `success_url` → `/subscribe/success`, `cancel_url` → `/subscribe/cancelled`.
3. Redirects (302) to `session.url` (Stripe-hosted Checkout page — no Stripe Elements/card
   form built by us).

`GET /subscribe/success` (new): Stripe's redirect target after successful Checkout. The
webhook, not this page, is the source of truth for activation (Stripe's own guidance — the
redirect can race the webhook, usually by a second or two, no hard ordering guarantee). This
page does not flip `subscription_status` itself and renders no new template — it sets
`session['pending_email']` (looked up via `session['pending_subscription_user_id']`) and
redirects straight into the **existing** `/check-email` page (`routes/auth.py:105-108`,
`templates/check_email.html`), which already has copy plus a working **Resend verification**
button. This reuses 100% of existing infra: by the time a real user opens their inbox and
clicks the link, the webhook (arriving in ~1-2s) has almost always already flipped
`subscription_status` to `active`.

`GET /subscribe/cancelled` (new): user backed out of Checkout. Shows "no worries, you can
finish subscribing any time" with a link back to `/subscribe/checkout` (reuses the same
pending session key) and a note that they can also just try `/try` first.

### Webhook: `POST /webhooks/stripe` (new, in `routes/billing.py`)

CSRF-exempt (Stripe can't send a CSRF token — same treatment already given to `/try/parse`,
`/try/sim`, `/try/lead`). Signature-verified via `stripe.Webhook.construct_event(...)` using
`STRIPE_WEBHOOK_SECRET` — **this is the actual security boundary**, not obscurity, since the
endpoint is public by necessity.

Handles:

- **`checkout.session.completed`** — look up user by `client_reference_id`. Set
  `stripe_customer_id`, `stripe_subscription_id`, `subscription_status='active'`,
  `subscription_period_end`. Then send the verification email (reusing
  `utils.auth.send_verification_email`, unchanged) — this is now the trigger point instead of
  `register()`.
- **`customer.subscription.updated`** — look up user by `stripe_subscription_id`. Map Stripe's
  `status` (`active`, `past_due`, `canceled`, `unpaid`, etc.) to our four-value
  `subscription_status`, update `subscription_period_end`.
- **`customer.subscription.deleted`** — look up by `stripe_subscription_id`, set
  `subscription_status='canceled'`.

All handlers are idempotent by construction (each just overwrites the row's status fields —
replaying the same event twice is a no-op), which matters because Stripe retries webhook
deliveries that don't return 2xx.

### Login gate (`routes/auth.py:15-56`)

One new check, inserted alongside the existing `needs_tos` branch (after the `is_verified`
check, before setting up the dashboard session):

```python
if user["user_type"] == "standard" and user.get("subscription_status") not in ("active", "past_due"):
    flash("Your subscription isn't active yet.")
    return redirect(url_for("billing.subscription_pending", user_id=user["id"]))
```

Provisioned accounts (`class`/`beta`/`test`) never hit this branch — `user_type != 'standard'`
short-circuits it, identical in spirit to the existing `needs_tos` line's own `user_type`
check three lines above it.

**Race handling, not a duplicate-Checkout redirect**: this does *not* redirect straight back
into `/subscribe/checkout` (that would silently start a second Stripe Checkout Session on
every failed login attempt, including the common case where the webhook simply hasn't landed
yet — a real risk of duplicate subscriptions/confusing double charges). Instead it goes to a
small new holding page, `GET /subscribe/pending/<user_id>` (`billing.subscription_pending`):
copy along the lines of "Your subscription isn't active yet — if you just paid, give it a
moment and try logging in again," plus a **manual** "Resume Checkout" button that only starts
a fresh Checkout Session on explicit click (for the genuinely-abandoned or genuinely-canceled
case). No auto-retry, no polling — the user drives it, matching the "static holding page, no
polling machinery" choice made for `/subscribe/success` below.

### Abandoned `pending` rows

A visitor who creates the row in step 1 above and then closes the tab before finishing (or
completing) Checkout leaves a permanent `subscription_status='pending'` row that has
permanently claimed a username/email. Two visible mitigations, **neither built in this
pass** — flagged as follow-up:

- A cleanup cron (same shape as `utils/purge_deleted_accounts.py`) deleting `pending` rows
  older than e.g. 24 hours.
- Loosening `get_user_by_username` in the registration path to allow a *new* attempt to
  reclaim a stale `pending` username after some age cutoff.

Not blocking for launch since `pending` rows cost nothing and aren't visible anywhere; noted
so it doesn't get forgotten.

## `/try` → registration funnel integration

### Splash page CTAs become a choice, not a direct link

Every CTA on `templates/splash.html` that currently points straight at
`{{ url_for('auth.register') }}` — the nav "Get Started →" (line 345), hero "Start Your First
Mission →" (line 356), and the mid-page "Sign up to try the full platform →" (line 778) —
changes from an `<a href>` to a `<button>` that opens one shared modal:

```
┌─────────────────────────────────────┐
│  Ready to start building? 🚀         │
│                                       │
│  [ Subscribe & Start →ǀ ]  (primary) │
│  [ Try it free first → ]  (secondary)│
└─────────────────────────────────────┘
```

- **"Subscribe & Start"** → `{{ url_for('auth.register_invite') }}` (the new email-gate step,
  not `/register` directly — see "Registration-access gate" above; its flow now ends in Stripe
  Checkout per the "Registration flow" section below).
- **"Try it free first"** → `{{ url_for('try_it.try_page') }}` (`/try`, unchanged).

Implementation: one small reusable modal (plain inline HTML/CSS/JS in `splash.html`, same
"no new CSS framework, inline styles matching existing tokens" convention the try-page-infra
spec used for its overlays) triggered by `data-action="open-subscribe-modal"` on each of the
three CTA elements, replacing their `href` with a click handler. No new route — purely
client-side, same as the `/try` welcome splash overlay.

### `/try` trial-completion prompt

`utils/project_try_it.py`'s scaffold sketch ends at `//>> Mission Complete | open | blocks` —
the 4th and final parsed step. `templates/try_it_builder.html` already has one
step-advance-triggered overlay (`#try-email-gate-overlay`, firing at `GATE_AFTER_STEP_INDEX =
1`) with an established `window.bbNext` wrapping pattern (see
`2026-07-09-try-page-infra-design.md`'s Email gate section for why this is the correct hook
point, not a time/scroll trigger).

Add a second overlay, `#try-subscribe-prompt-overlay`, structurally identical to the existing
two (`#try-welcome-overlay`, `#try-email-gate-overlay`) — same backdrop/card/token styling —
shown once, the first time `BB.CURRENT_STEP` reaches the final step index (index 3, "Mission
Complete"). Copy: "You completed the free trial! 🎉" / "Ready to build 18 more real
projects?" / single primary button "Subscribe →" linking to
`{{ url_for('auth.register_invite') }}` (see "Registration-access gate" above — `/register`
itself is no longer a valid direct link anywhere in the product), plus a dismiss ("Keep
exploring") that just closes the overlay — the visitor can still poke around the finished
builder.

Dismissal/shown-once state uses `sessionStorage` (`try_subscribe_prompt_shown`), same
mechanism as the welcome overlay — not the Flask session, since (per the existing design)
this overlay has no server round-trip either.

No change to the existing email-gate overlay's own logic — the two are independent triggers
at different step indices, same as the welcome overlay is independent of the email gate.

## Config / dependencies

New env vars (`config.py`, following the existing `os.getenv(...)` convention):

```python
STRIPE_SECRET_KEY      = os.getenv("STRIPE_SECRET_KEY")
STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY")
STRIPE_WEBHOOK_SECRET  = os.getenv("STRIPE_WEBHOOK_SECRET")
STRIPE_PRICE_ID        = os.getenv("STRIPE_PRICE_ID")
```

New dependency: `stripe` (official Python SDK) added to `requirements.txt`.

## Testing strategy

Mirrors the existing pattern (`responses`/`respx` mocking `mock_supabase` in
`tests/conftest.py`, already used by `tests/test_leads.py` and `tests/test_try_it_routes.py`):

- `routes/billing.py` tests mock the `stripe` SDK calls directly via `monkeypatch` (e.g.
  `monkeypatch.setattr(stripe.checkout.Session, "create", lambda **kw: FakeSession(...))`) —
  no real network call to Stripe in the test suite, same spirit as never hitting real
  Supabase/OpenAI in tests today.
- Webhook signature verification is tested both ways: a validly-"signed" fake event (mock
  `stripe.Webhook.construct_event` to return a parsed dict) and a bad-signature case
  (mock it to raise `stripe.error.SignatureVerificationError`) → expect 400.
- `routes/auth.py` login-gate tests: `standard` user with `subscription_status='pending'`
  redirected to `billing.subscribe_checkout`; `class`/`beta`/`test` users bypass the check
  regardless of `subscription_status` (still `'none'`).

## Decisions (resolved)

1. **Single fixed price.** One `STRIPE_PRICE_ID`, no plan-picker UI. Multiple tiers are future
   work if needed.
2. **`past_due` keeps access.** Login stays allowed until Stripe exhausts retries and fires
   `customer.subscription.deleted`; avoids punishing a one-off expired card immediately.
3. **`/subscribe/success` is a static holding redirect, no polling.** It forwards straight into
   the existing `/check-email` page rather than inventing new UI or a status-polling endpoint
   (see "Registration flow" above for the full loop, including the `/subscribe/pending`
   race-handling page for the rare case where the webhook lags behind email verification).
