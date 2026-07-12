# TODO

- [ ] Run `migrations/add_leads_table.sql` against Supabase (user will do
      this manually).

- [ ] Merge/PR `try-page-infra` branch once `/try` is fully verified —
      explicitly held back per "we will not push until we have implemented
      this full feature."

- [ ] Stripe Checkout / registration / webhook flow — implemented (see
      `docs/superpowers/specs/2026-07-10-stripe-registration-gate-design.md`).
      Remaining before launch, all on Bill's side ("Config / dependencies" +
      handoff section of that doc):
      - Run `migrations/add_subscription_columns.sql` and
        `migrations/add_registration_invites_table.sql` against Supabase.
      - Set up the Stripe product/price + dashboard, and the
        `STRIPE_SECRET_KEY` / `STRIPE_PUBLISHABLE_KEY` / `STRIPE_WEBHOOK_SECRET`
        / `STRIPE_PRICE_ID` env vars.

- [ ] **Fix the 3-way `&&` condition bug in `utils/block_parser.py`.** The
      `BlockTransformer.condition()` method only flattens two comparisons
      (`leftExpr`/`op`/`rightExpr` + `leftExpr2`/`op2`/`rightExpr2`) when
      building a phantom `if` slot's answer-key template. A condition chained
      three deep (`A && B && C`) recurses one level too shallow and silently
      drops the third clause from the master/hash — so a student who builds
      the if-statement exactly as instructed can never match the (silently
      truncated) answer key. No other lesson uses a 3-way `&&` today, but
      `project_eighteen.py`'s Step 9 originally did
      (`distanceB < 30 && sawA == true && sawB == false`) and was
      permanently stuck on it — worked around by locking that if-statement
      instead of teaching it as blocks. This is a latent bug in the shared
      engine and will bite the next lesson that tries a 3-way `&&`. Found
      2026-07-11.

- [ ] Cleanup cron for abandoned `pending` users rows and expired
      `registration_invites` rows (see "Abandoned `pending` rows" /
      "Abandoned-row cleanup now covers two tables" in the
      2026-07-10-stripe-registration-gate-design.md spec). Non-blocking,
      not yet built.

- [ ] Referral/discount codes — implemented per
      `docs/superpowers/specs/2026-07-12-referral-codes-design.md`: schema,
      `utils/referrals.py` data-access layer, `/register/invite` →
      `register()` → `subscribe_checkout()` code resolution/carry-through,
      `handle_checkout_completed`'s redemption (self-referral check,
      webhook-redelivery dedup, concurrency-safe redemption cap, `trial_end`
      month credit, referrer annual cap), admin discount-code
      create/list/disable UI (Provisioning tab), and the parent dashboard's
      referral-code card (only shown while the parent's subscription is
      active/past_due).
      **Still needs, before this is live:**
      - Run `migrations/add_referral_codes_tables.sql` and
        `migrations/add_referral_redemption_lock_column.sql` against
        Supabase (user will do this manually, same as the other migrations
        above).
      - Hasn't been exercised end-to-end against real Stripe test-mode
        Checkout/webhooks yet — only checked for import/template-syntax
        correctness so far.
