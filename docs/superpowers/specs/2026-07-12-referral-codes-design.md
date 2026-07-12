# Referral / Discount Codes — Design Spec

Status: designed, not yet implemented.

## Motivation

`/register/invite` already has a `referral_code` text field
(`templates/register_invite.html`), added alongside the registration-access gate
(see [`2026-07-10-stripe-registration-gate-design.md`](2026-07-10-stripe-registration-gate-design.md)).
It's currently inert: captured, stored on `registration_invites.referral_code`, never
validated, never acted on. This spec gives it a real backend: two kinds of codes that
both grant real value, tracked through to Stripe.

## Two code types

1. **Admin discount code** — created by an admin from the admin dashboard
   (`routes/admin.py`). Locked to a `discount_type` (`percent` | `fixed`) and
   `discount_value` at creation time. Applies a discount to the invitee's Stripe
   Checkout session. Optionally capped (`max_redemptions`) and/or time-limited
   (`valid_till`).
2. **Parent referral code** — one auto-generated per parent account
   (`code_type='parent_referral'`, `created_by = parent.id`). Double-sided: on a
   successful redemption, **both** the inviting parent and the new invitee get
   `reward_months` (n+1, per Bill — same reward on both sides) credited to their
   subscription. Effectively unlimited `max_redemptions` (a parent can refer more
   than one family) unless we later decide to cap it.

**Single code per registration** — `/register/invite` keeps its one `referral_code`
input. A code's own `code_type` determines what happens on redemption; there is no
stacking of an admin code and a parent code in the same registration.

## Schema

```sql
CREATE TABLE referral_codes (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code              TEXT UNIQUE NOT NULL,
    code_type         TEXT NOT NULL,              -- 'admin_discount' | 'parent_referral'
    created_by        UUID NOT NULL REFERENCES users(id),
    discount_type     TEXT DEFAULT NULL,           -- 'percent' | 'fixed' (admin_discount only)
    discount_value    NUMERIC DEFAULT NULL,        -- admin_discount only
    stripe_coupon_id  TEXT DEFAULT NULL,            -- admin_discount only, set at creation
    reward_months     INT DEFAULT NULL,             -- parent_referral only; applied to BOTH sides
    max_redemptions   INT DEFAULT NULL,             -- null = unlimited
    redemption_count  INT NOT NULL DEFAULT 0,
    valid_till        TIMESTAMPTZ DEFAULT NULL,     -- null = no expiry
    status            TEXT NOT NULL DEFAULT 'active', -- 'active' | 'disabled' | 'expired'
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE referral_code_redemptions (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code_id           UUID NOT NULL REFERENCES referral_codes(id),
    redeemed_by       UUID NOT NULL UNIQUE REFERENCES users(id),  -- the new registrant; UNIQUE
                                                                    -- makes "already redeemed
                                                                    -- something" and webhook-
                                                                    -- redelivery dedup a single
                                                                    -- constraint (see Concurrency)
    redeemed_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    discount_applied  NUMERIC DEFAULT NULL,
    months_credited_invitee NUMERIC DEFAULT NULL,
    months_credited_referrer NUMERIC DEFAULT NULL
);

-- registration_invites.referral_code (TEXT) becomes a FK instead of free text:
ALTER TABLE registration_invites ADD COLUMN referral_code_id UUID REFERENCES referral_codes(id);
-- keep the old `referral_code` text column for now (existing rows), stop writing to it.
```

`referral_code_redemptions.redeemed_by` is `UNIQUE`: a given user account can redeem
at most one code, ever, ACROSS its whole lifetime — which also happens to be exactly
the constraint that makes webhook-redelivery dedup and "did this user already use a
code" the same check (see Concurrency & idempotency below).

**Code format (fixes gap #7):** generate with `secrets.token_urlsafe` or similar,
uppercased, from an unambiguous charset (no `0/O`, `1/I/l`), ~10-12 characters
long — long enough that brute-forcing a live code against the rate-limited
`/register/invite` endpoint isn't practical, short enough a parent can still read it
over the phone. Sequential or short (e.g. 6-char) codes are explicitly out — see the
enumeration risk below.

## Validation at request time (`/register/invite`)

**Fixes gap #2 (enumeration oracle).** The existing handler already gives the exact
same response regardless of whether the submitted email is real — "same
enumeration-prevention pattern as forgot-password flows," per its own comment. The
original version of this section broke that by flashing a distinct rejection for an
invalid code, which turns the endpoint into an oracle: someone can hammer the
5/min-limited route and use accept-vs-reject as a signal to harvest live parent
codes, or find and exhaust a capped admin promo, without ever paying a cent.

Fixed behavior: **the response is always the same "check your email" page,
regardless of whether the code is valid.** If the code resolves and passes
`status='active'`, not past `valid_till`, `redemption_count < max_redemptions`, and
(for `parent_referral`) `created_by.subscription_status IN ('active','past_due')` —
attach `referral_code_id` to the invite row. If it fails any check, silently drop it
— the invite still sends, just without a code attached, exactly like today's
handling of a syntactically-valid-but-nonexistent email. The user only finds out
their code didn't apply later, at `/register` itself (post-email-proof, where
enumeration is far less useful since each attempt now costs a real inbox) or at
Checkout — never at this pre-proof step.

## Redemption only happens on successful payment

Per your call: nothing is written to `referral_code_redemptions`, no discount is
finalized, and no month-credit is granted until `handle_checkout_completed` fires
in `utils/billing.py` — the same moment `subscription_status` flips to `active`.
Registering alone (`pending` status) never burns a code or credits anyone. This
matches the existing "no reward for an abandoned/never-paid signup" posture.

**Correction from the first draft of this doc:** `handle_checkout_completed` is
*not* actually idempotent against Stripe webhook redelivery today — it just
re-runs an unconditional `UPDATE` (harmless to repeat) and unconditionally calls
`send_verification_email` again (a pre-existing, separate quirk, not something
this spec touches). The new redemption logic can't inherit that looseness — see
"Concurrency & idempotency" below for how it's actually made safe.

Flow:
1. `register()` (`routes/auth.py`) reads `referral_code_id` off the invite row,
   stashes it in the session next to `pending_subscription_user_id`.
2. `create_checkout_session()` (`utils/billing.py`) looks up the code; if
   `code_type='admin_discount'`, passes `discounts=[{"coupon": stripe_coupon_id}]`
   to `stripe.checkout.Session.create`. Parent codes carry no Checkout-time
   discount — the invitee's reward is a post-payment month credit, same mechanism
   as the referrer's.
3. `handle_checkout_completed()` — after setting `subscription_status='active'` as
   today — resolves the code and, **only if `redeemed_by` (the new user) isn't
   already `created_by` on that code** (fixes gap #4, self-referral: a parent
   can't redeem their own code with a second account they control), attempts the
   redemption per "Concurrency & idempotency" below. Marks the code `expired` if
   `redemption_count` now hits `max_redemptions`.

Self-referral is checked here, at redemption — not earlier at invite-request —
because that's the first point a concrete `redeemed_by` user exists to compare
against `created_by`. It's a cheap, exact check (same `users.id` literally
redeeming their own code); it does not attempt to catch a parent using a
*different* email/account they also control, which isn't reliably detectable and
isn't this spec's job to solve.

## How a month credit is actually applied

Both sides (parent referrer and, for parent-referral codes, the invitee) already
have a live Stripe subscription by the time a credit is due — the invitee's
`checkout.session.completed` just fired, and the parent's subscription must
currently be active, per the provisioning rule above. That check already happened
once at invite-request time; redoing it here at redemption time is the safety net
for a parent whose subscription lapsed in the interim (see "Parent referral code
provisioning" below) — if it fails now, the code is invalid outright and neither
side gets a reward, rather than quietly downgrading to "invitee pays full price."

Mechanism: `stripe.Subscription.modify(subscription_id, trial_end=<current_period_end + reward_months>, proration_behavior="none")`.

**Anchor on `current_period_end`, not "now"** — this is the detail that matters for
the invitee. `handle_checkout_completed` fires the instant month 1's payment
succeeds, and at that point the invitee's `current_period_end` is already ~1 month
out (Checkout just charged month 1 normally; no discount is applied to it). Pushing
`trial_end` out from *that* timestamp by `reward_months` means month 1 stays paid
as normal and month 2 is the one that's skipped/free — not month 1. (Anchoring on
"now" instead would have collapsed month 1 itself into the free period, which is
wrong: the invitee already paid for it seconds earlier in the same request.)

For the referring parent, who's mid-subscription already, the same anchor
(`current_period_end`) just means "skip whichever billing cycle would otherwise
come next" — there's no month-1-vs-month-2 ambiguity on that side since they aren't
freshly registering.

This is Stripe's standard "push out the next invoice" trick — works on an
already-active subscription, not just one that hasn't started billing yet. It fires
a `customer.subscription.updated` webhook, which `handle_subscription_updated()`
**already handles with zero changes**: `trialing` is already mapped to `active` in
`_STRIPE_STATUS_MAP` (`utils/billing.py:74`), and `subscription_period_end` gets
refreshed from the same event. The login gate (`routes/auth.py`'s `subscription_status
in ("active", "past_due")` check) needs no changes at all.

This deliberately keeps Stripe as the single source of truth for subscription
access — no second "bonus days" column to keep in sync with `subscription_status`.

## Concurrency & idempotency (fixes gaps #1 and #3)

Two distinct races, both real given this runs inside a webhook handler Stripe can
redeliver:

**A. The same checkout.session.completed event processed twice.** Fixed by the
`UNIQUE` constraint on `referral_code_redemptions.redeemed_by` added above: the
redemption insert is attempted with that constraint doing the work — if it
conflicts (row already exists for this `redeemed_by`), the handler treats
everything past that point as already-done and skips straight to returning,
without touching `redemption_count` or calling `stripe.Subscription.modify` again.
One insert attempt, ON CONFLICT DO NOTHING semantics, is the entire dedup
mechanism — no separate "have I seen this event ID" table needed.

**B. Two different redemptions of the same popular parent code landing close
together.** This is the one that can silently under-credit: pushing `trial_end`
requires reading the target subscription's *current* `current_period_end`/
`trial_end` and adding `reward_months` on top. If redemption X and redemption Y for
the same `created_by` both read the same starting point before either writes back,
the second `modify()` call just overwrites the first with the same target instead
of stacking — the parent effectively only gets credited once. Fixed by always
calling `stripe.Subscription.retrieve(subscription_id)` for a fresh read
immediately before each `modify()` (never trust a locally-cached
`subscription_period_end` for this calculation), and by serializing the
read-then-modify sequence per `created_by` — e.g. a short-lived Postgres advisory
lock (`pg_advisory_xact_lock(hashtext(created_by::text))`) held for the duration of
that sequence, released automatically at transaction end. `max_redemptions`'s own
gate (the conditional `UPDATE ... WHERE redemption_count < max_redemptions
RETURNING`) uses the same atomic-conditional-update pattern for the same reason —
a plain read-check-then-write would let two concurrent redemptions both slip past
the cap.

**What happens if a race is caught (cap already hit, or the conditional update
returns zero rows) after the invitee has already paid?** It does not fail the
webhook or the invitee's subscription — they already paid and are already
`active` regardless of any code. The redemption is just skipped (no reward
either side), same as any other invalid-at-redemption-time code from the
provisioning-lapsed case above. Worth logging distinctly (not silently) since it
signals the cap is being hit in a hot window and might warrant raising it.

## Admin discount codes and Stripe Coupons

Created together: when an admin submits a new `admin_discount` code (new route,
e.g. `POST /admin/referral-codes`), we call `stripe.Coupon.create(...)` immediately
with the given percent/fixed value and store the returned coupon ID on the row.
The Stripe object is the thing actually enforced at Checkout; our row is the
lifecycle wrapper (who made it, is it still active, how many times has it been
used) Stripe's own promotion-code UI doesn't give us out of the box tied to our
own admin/user model.

**Duration (resolves gap #6):** every admin coupon is created with
`duration='once'` — it discounts exactly **one month's charge** (the first
invoice, via Checkout's `discounts` param), whether expressed as `percent_off` or
`amount_off`, computed against the plan's single monthly price. This is
deliberately the same "one month" unit as the parent-referral reward, just applied
at a different moment: admin codes discount month 1 *at the point of charge*
(Checkout), where parent-referral rewards give a free month *after* the fact (the
`trial_end` push onto a later invoice) — different mechanism, same currency
("one month"), matching how you described both: "1 free month, 20% off one
month... based on the monthly charge."

## Parent referral code provisioning

**Only a parent with an active subscription can give out a code at all** — not just
a rule about redemption, a gate on the code even existing/working:

- Auto-generate one `parent_referral` row per parent the first time it's needed
  (lazily, on first visit to wherever we surface it — likely the parent's existing
  dashboard branch in `routes/main.py`, which already branches on `session.is_parent`),
  but only render/reveal the code to a parent whose `subscription_status` is
  currently `active` (or `past_due`, matching the login gate's own definition of
  "still has access"). A parent on `none`/`pending`/`canceled` sees no code to share.
- Re-check the same condition at both validation time (`/register/invite` — per
  the enumeration fix above, a lapsed referrer's subscription makes the code
  silently not get attached, same generic response either way, no flash) and again
  at redemption time (`handle_checkout_completed`, since time passes between
  requesting the invite and completing Checkout). Either way the invitee still
  registers and pays normally — they just don't get a reward tied to a code that
  turned out to be dead, same as any other invalid-at-redemption-time code.
- This means `referral_codes.status` for a `parent_referral` row isn't purely a
  function of its own fields — validity is always `status='active' AND
  created_by.subscription_status IN ('active','past_due')`, checked live rather than
  synced onto the row (no webhook needs to reach into `referral_codes` when a
  parent's subscription lapses).
- **The row itself is never deleted, and `status` is never flipped, just because
  the parent's subscription lapses.** It sits inert (fails the live check above)
  for as long as the parent is unsubscribed, and starts working again immediately,
  with no regeneration or admin action, the moment they resubscribe. Deleting it on
  lapse would orphan `referral_code_redemptions.code_id` for anyone who already
  redeemed it, and force a new code (shared with whoever they'd already given it
  to) on every resubscribe. `status='disabled'`/`'expired'` stay reserved for admin
  action or hitting `max_redemptions`/`valid_till` — a lapsed subscription is a
  separate, orthogonal reason a code is unusable, not conflated with those.

`reward_months` for all parent codes comes from one config constant
(not admin-configurable per-code) — simplest thing that matches "n+1 to both sides"
as stated.

## Lifecycle states (`referral_codes.status`)

- `active` — usable, subject to `valid_till` / `max_redemptions` checks at
  validation time (no cron needed; expiry is evaluated lazily on read, same
  pattern as `get_valid_registration_invite`).
- `disabled` — admin manually kills a code (new admin action); parent codes are
  never disabled by anyone but an admin (abuse case).
- `expired` — reached naturally, either past `valid_till` or `redemption_count >=
  max_redemptions`. Set explicitly on the row when the cap is hit at redemption
  time (rather than left implicit) so the admin list view can show it without
  recomputing.

## Refund/chargeback clawback: explicitly deferred

If an invitee's payment is later refunded or disputed, nothing in this spec
reverses the `trial_end` push already applied to either side. **Decided: not
handling this now** — revisit only if it actually becomes a problem in practice,
per your call. Worth a one-line comment at the point in `handle_checkout_completed`
where the credit is granted, so a future reader knows this was a conscious
omission, not an oversight.

## Referrer reward cap: 2 months per year, resets on anniversary (resolved)

Decided: the code itself stays unlimited forever (an invitee always gets their own
free month 2, no matter how many times the parent's code has been used) — only the
*referrer's* accumulation is capped, at **2 credited months per rolling 12-month
year**, so a prolific referrer's own subscription can never be more than ~1/6 free
in any given year regardless of how many families they bring in.

**Anniversary anchor: `users.created_at` for the referring parent** — already
exists, no new column needed. (Not the ever-shifting `subscription_period_end`,
which moves every time a reward is applied — using that as the reset point would
make the window itself referral-driven, which is circular. Account creation and
first Checkout happen moments apart in the existing `register()` →
`billing.subscribe_checkout` redirect, so it's a fine, stable proxy for
"subscription anniversary" without tracking a separate start date.)

**Enforcement, at the point `handle_checkout_completed` would credit the
referrer** (per "Concurrency & idempotency," inside the same per-`created_by`-locked
sequence so this check and the credit are atomic together):
1. Compute the current window: the most recent anniversary of `created_by`'s
   `created_at` that is `<= now`, through one year later.
2. `SUM(months_credited_referrer)` from `referral_code_redemptions` where
   `code_id` = this parent's code and `redeemed_at` falls in that window.
3. If `sum + reward_months > 2`: **skip the referrer credit entirely for this
   redemption** (no partial/fractional month) — log it distinctly, same as a
   cap-hit skip elsewhere in this doc. The invitee's own reward is never affected
   by this check; it only gates the referrer's side.

No new schema — this is a query over data the redemption table already captures,
plus one config constant (`REFERRER_ANNUAL_CAP_MONTHS = 2`).

## Open items for implementation (not blocking this spec)

- Exact admin UI for creating/listing/disabling codes (new section in
  `templates/admin/index.html` + `routes/admin.py` handlers) — not designed here,
  routine CRUD.
- Where a parent actually sees/copies their own referral code — needs a small
  UI surface, likely near wherever `routes/main.py`'s parent-dashboard branch
  renders today.
- `reward_months` config constant value (e.g. 1) — pick at implementation time,
  doesn't affect this schema.
