# `/try` Page Infrastructure — Design Spec

Status: approved (infra) — project content and Stripe checkout/registration flow are separate, not-yet-scoped follow-ups.

## Context

This is the first sub-project of a larger "gate registration behind Stripe" initiative. The
overall shape of that initiative (decided, not yet fully spec'd):

- **Payer**: individual parent/adult accounts. Teacher/cohort licenses are out of scope —
  spec'd separately.
- **Gate model**: registration itself is gated behind Stripe Checkout (no free row in `users`
  until payment succeeds). This preserves a clean invariant: every `users` row is a paying
  (or admin-provisioned) account, which keeps subscriber/revenue metrics simple.
- **Why not freemium instead**: a free registration endpoint is a soft target for abuse (fake
  signups, bot farms) in a way a Stripe-gated one isn't. To recover some of freemium's
  top-of-funnel visibility without exposing a real signup endpoint, we're building a
  standalone, account-less "try it" experience instead (this doc).
- **Parked idea (explicitly out of scope here)**: `circuit_renderer.js` (breadboard wiring
  diagrams) and `SimEngine` (declarative code-driven component simulation) render overlapping
  hardware visuals via different mechanisms. Whether these should be unified is a separate
  future conversation, not part of this work.

This doc specs the `/try` page infrastructure only — the framing/plumbing. The actual curated
project content (`utils/project_try_it.py` — steps, sketch, sim_config, drawer) is a follow-up
piece of work once this infra is in place.

## Goals

- Let an anonymous visitor experience the real block builder + Monaco toggle + simulated
  hardware feedback (LED reacting to their code), with no login and no `users` row created.
- Capture a lead (email) after the first taste of interactivity, as a light funnel/tire-kicker
  filter and a remarketing channel — without polluting the paid-customer-only `users` table.
- Keep the anonymous surface area cheap to defend: bounded inputs + existing rate limiter,
  not a bespoke abuse-prevention system.

## Relationship to the existing splash demo

`templates/splash.html` already embeds `/demo/builder` (routes/builder.py:40) — a minimal,
no-login, blocks-only widget (`lock_view: true`, no sim, no drawer) used as an ambient teaser
on the marketing page. **This is unchanged by this work.**

`/try` is a separate, deeper, standalone page reached via a CTA. It shares no config with the
splash widget's hardcoded `_DEMO_SKETCH`; both will eventually read from the same
`utils/project_try_it.py` `PROJECT` module (splash keeps rendering it minimally, `/try` renders
it fully with SimEngine + Monaco toggle + drawer) — but wiring the splash widget to that shared
module is optional polish, not required by this spec.

## Architecture

### New blueprint: `routes/try_it.py`

Anonymous (no `@login_required`) Flask blueprint, registered alongside the existing blueprints
in `app.py`. Kept separate from `routes/builder.py` rather than added to it, since every route
in it is deliberately unauthenticated and that's worth being able to see at a glance.

Routes:

| Route | Method | Purpose |
|---|---|---|
| `/try` | GET | Renders the curated try-it project via a new template, `templates/try_it_builder.html` (see "Template: stripped-down IDE" below), sourced from `utils/project_try_it.py` instead of a hardcoded sketch string. No circuit tab — SimEngine is the only visual, per the decision below. |
| `/try/parse` | POST | Anonymous equivalent of `/parse` (routes/builder.py:73) — turns edited sketch text into block JSON. Input-capped (see Abuse boundary). |
| `/try/sim` | POST | Anonymous equivalent of `/sim/run` (routes/builder.py:81) — runs `utils.sim_engine.run()` against the client's current sketch and returns the animation timeline. Input-capped (see Abuse boundary). No `award_simulator_badge` call (that's tied to a logged-in `session["user_id"]`, doesn't apply here). |
| `/try/lead` | POST | Captures the email-gate submission (see Email gate below). CSRF-exempt (anonymous, same treatment as other public POST endpoints in this app), honeypot-protected, rate-limited. |

### Template: stripped-down IDE (correction from initial draft)

Investigated during planning: neither existing template fits.

- `templates/block_builder_fragment.html` (used by the existing `/demo/builder` splash
  widget) is blocks-only — it has **no Monaco editor**, so it can't deliver the blocks↔Monaco
  toggle this page needs.
- `templates/components/arduino_interface.html` (used by the login-gated `standalone_ide`
  route, where Monaco and `/parse` actually live) **is the full hardware IDE** — compile/upload
  buttons, a USB port picker, and live calls to `http://127.0.0.1:52010/...` (the local
  KidsCode Link companion app that talks to a physical Arduino). Unusable as-is for an
  anonymous browser visitor with no hardware.

Resolution (matches the earlier framing decision to "strip all of the Arduino interface off
the block builder"): a new template, `templates/try_it_builder.html`, is a trimmed copy of
`arduino_interface.html` with the compile/upload/port-picker/serial-agent chrome removed,
keeping only the blocks↔Monaco toggle, the drawer panel, and the sim tab. Its `/parse` calls
point at `/try/parse` instead of `/parse` (see Abuse boundary — same reasoning, different
route). `/try` renders this template instead of `block_builder_fragment.html`.

### Why the sim endpoints can safely accept client-submitted code

Confirmed by reading `utils/sim_engine.py`: `run()` does **not** execute code. It's pure regex
extraction — it pattern-matches `digitalWrite(...)`, `delay(...)`, `pinMode(...)`,
`int x = N;` out of sketch text and builds an animation timeline from whatever it finds.
Anything that doesn't match a known pattern is silently ignored, not executed. There is no
`eval`/`exec`/interpreter to sandbox-escape.

This matters because a fixed, server-side canned sketch was considered and rejected: it would
make the LED "work" regardless of whether the visitor placed the right blocks, defeating the
point of a try-it experience (wrong code should visibly do nothing, which the regex approach
already handles correctly — no match, no timeline event).

So `/try/parse` and `/try/sim` accept real client-submitted sketch text, same as the
authenticated versions. The abuse surface is volume/size, not code injection.

**Frontend wiring note**: `SimEngine.initCodeDriven()` (static/js/sim-engine.js:656) currently
hardcodes `fetch('/sim/run', ...)`. This needs a small additive change — accept an optional
endpoint override on `simConfig` (e.g. `simConfig.endpoint`), defaulting to `/sim/run` when
absent so all 19 existing lesson drawer sim tabs are unaffected. `utils/project_try_it.py`'s
`sim_config` sets `endpoint: "/try/sim"`. Same treatment needed wherever `/try_it_builder.html`
wires up its copy of `arduino_interface.html`'s `/parse` calls (routes/builder.py:73) — point
them at `/try/parse` instead.

### Abuse boundary (anonymous endpoints only)

Applies to `/try/parse`, `/try/sim`, `/try/lead`:

1. **Sketch length cap** — reject sketch text over ~2KB (a try-it sketch is a handful of
   lines; this bounds regex work regardless of adversarial input).
2. **Clamped `sim_config`** — `loop_iterations` / `max_ms` (client-supplied today on the
   authenticated endpoint, routes/builder.py:88) are ignored on the anonymous endpoint and
   forced to fixed server-side constants, since they control response size/compute, not
   correctness.
3. **IP rate limiting** — via the existing `extensions.limiter` (flask-limiter, already used
   in `routes/help.py`), same pattern: something like `10 per minute` / `100 per hour` per IP
   on each of the three POST routes.
4. **Non-leaking errors** — anonymous endpoints return a generic error message on exception,
   never `str(e)` (the authenticated `/sim/run` currently does leak `str(e)` at
   routes/builder.py:94 — do not carry that pattern into the anonymous versions).
5. **`/try/lead` honeypot** — a hidden form field that must stay empty; a filled honeypot is
   silently accepted (200 OK, no row written) rather than rejected, so bots don't learn they
   were caught.

No CAPTCHA, no bespoke abuse system — bounded inputs plus the rate limiter already in the app.

### SimEngine drives the interactive experience — no circuit build tab

The `/try` page never renders the interactive per-step breadboard build tab: no
`circuit_image`, no wiring `STEPS`, no walkthrough. `SimEngine` (static/js/sim-engine.js) is a
self-contained, code-driven visual simulator that needs no photos or physical-hardware
assumptions — a visitor writes/places blocks, runs, and watches a component (e.g. LED) react
on screen. This also means `utils/project_try_it.py` needs no `circuit_image` asset and no
wiring `STEPS`, only a `sim_config` (per the `SimEngine.init` shape documented at the top of
sim-engine.js) plus the sketch/steps/drawer content that *is* in scope for the follow-up
content spec.

This does *not* rule out `circuit_renderer.js` entirely: the drawer's Welcome step shows a
static illustrative diagram of the same LED-on-pin-13 circuit (`utils/demo_circuit.py`'s
`LED_DEMO_CIRCUIT`, rendered via a `type: "circuit"` drawer tab), the same "teaser graphic,
no lesson STEPS behind it" pattern splash.html already uses for its marketing demo. The line
is: a static one-shot diagram is fine anywhere; the interactive build-tab/walkthrough
machinery (circuit_image + wiring STEPS) is what stays out of `/try`.

### Email gate

Trigger: not time- or scroll-based. The gate fires on the specific UI event of completing
step 1 and clicking "Next Step" (the existing `bb_next_state` step-advance event that
`splash.html` already listens to — routes/builder.py's block builder fires this same event,
so `/try`'s step-advance handler adds a condition on it rather than needing new tracking).

Flow:
1. Visitor completes step 1 interactively (places blocks, sees SimEngine react).
2. Clicks "Next Step" → modal appears: email field + required consent checkbox (CASL: a
   follow-up email is a commercial electronic message and needs explicit consent captured at
   time of collection, not just an email field) + honeypot field (hidden).
3. On submit → `POST /try/lead` writes a row to the new `leads` table, sets
   `session['try_email_captured'] = True` and `session['try_lead_email'] = <email>`.
4. Confirmation popup: "Thanks for your interest!" → immediately proceeds to step 2 (no
   separate reload/redirect).
5. On any later step-advance in the same session, the gate is skipped (flag already set).

**Persistence**: Flask's default (non-permanent) session — dies when the browser closes, not
`PERMANENT_SESSION_LIFETIME`. Confirmed acceptable: a returning visitor on a new browser
session sees the gate again. Reuses the app's existing signed-session mechanism (already used
for `session["user_id"]` etc. throughout `routes/auth.py`) rather than introducing a new raw
cookie — this also means it can't be trivially spoofed via devtools cookie editing, and doubles
as a place to stash the email for Stripe Checkout prefill later (linking a `leads` row to a
future `users` row by email for funnel/conversion reporting is a natural follow-on, not built
here).

**Gate enforcement is client-side/UX only**, not a security boundary — there's nothing
sensitive behind step 2 (it's free content either way), so this is a conversion nudge, not
access control. Worth remembering if a future change to `/try` ever adds something worth
actually protecting.

### `leads` table (new)

| Column | Type | Notes |
|---|---|---|
| `id` | uuid/serial | PK |
| `email` | text | required |
| `consent_given_at` | timestamptz | required (CASL) — null/absent means the row shouldn't exist |
| `source` | text | e.g. `"try_page"`, for future lead sources |
| `created_at` | timestamptz | default now() |
| `followed_up_at` | timestamptz, nullable | set by the weekly follow-up cron |

Deliberately **not** a row in `users` — preserves the "every `users` row is a paying (or
admin-provisioned) account" invariant that the overall gate design relies on.

### Weekly follow-up cron (not instant send)

New standalone script `utils/send_try_followups.py`, run via OS-level crontab — same pattern
as the existing `utils/purge_deleted_accounts.py` (see its module docstring for the crontab
convention used in this deploy). No task queue or background worker introduced.

Logic:
1. Select `leads` where `followed_up_at IS NULL`.
2. For each: check whether that email already exists in `users`.
   - If yes (they converted on their own) → stamp `followed_up_at = now()`, do not send.
   - If no → send one Resend email (reuse the pattern in `utils/auth.py`'s
     `send_verification_email` / `send_reset_email`), then stamp `followed_up_at = now()`.
3. Each lead is only ever followed up once (single reminder, not a drip sequence).

Rationale: batching into a weekly job (vs. an instant send on capture) reads as genuine,
human-paced communication rather than an automated trigger firing the moment a tab closes —
better deliverability optics and better CASL posture — and the self-deduping check against
`users` gives a passive conversion signal for free (rows with `followed_up_at` set but no
Resend send are visitors who converted before the reminder went out).

## Explicitly out of scope for this spec

- The actual `/try` project content (`utils/project_try_it.py` — steps, sketch, `sim_config`,
  drawer copy). Follow-up spec.
- Stripe Checkout / registration / webhook flow. Follow-up spec.
- Logging/observability for the payment flow and any Stripe reporting-API integration for
  subscriber/revenue metrics. Follow-up spec.
- Teacher/cohort license payment flow. Spec'd separately, not related to this initiative.
- Unifying `circuit_renderer.js` and `SimEngine` rendering. Parked idea, not scheduled.
- Wiring the existing splash-page demo widget to read from the new shared
  `project_try_it.py` module. Optional polish, not required for `/try` to function.
