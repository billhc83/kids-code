# TODO

- [ ] **Apply `BLOCK_BUILDER_SYNC.md` invariants to existing lessons.** These
      were discovered/fixed only on `/try` (`utils/project_try_it.py`,
      `templates/try_it_builder.html`) — the shared-file fixes
      (`bb-validation.js`, `block_builder.js`, `sim-engine.js`) are safe
      no-ops elsewhere, but no existing lesson template has been audited for
      whether it mixes an `editor`-view step with blocks and/or a
      code-driven sim tab and needs the `window.getCurrentSketch` /
      `window.syncEditorToBlocks` wiring. Audit `templates/lessons/*.html`
      for any step using `view: editor` alongside a `sim`-type drawer tab.

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

- [ ] Two non-blocking follow-ups flagged in that same spec, not yet built:
      - Cleanup cron for abandoned `pending` users rows and expired
        `registration_invites` rows (see "Abandoned `pending` rows" /
        "Abandoned-row cleanup now covers two tables" in the spec).
      - Referral-code attribution logic — `referral_code` is already captured
        on `registration_invites` but nothing acts on it yet (see "Referral
        code — captured, not yet acted on" in the spec).
