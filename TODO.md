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

- [x] **Add a proper `micros()` block to the block builder.** Done
      2026-07-11: added a `micros` expression block mirroring `millis`
      throughout the pipeline — `block_parser.py`'s `func_expr`
      (`micros` → `{'type': 'micros', ...}`) and `strip_expr_values`,
      `bb-blocks.js`'s `BLOCKS.micros` entry (+ `EXPR_COLORS`), a
      `data-type="micros"` palette button in
      `block_builder_fragment.html`, and a `block_vocabulary.py` /
      `project_analyzer.py` concept entry. Verified end-to-end with
      `parse_steps()` on a phantom-line sketch: `expectedExTypes` correctly
      resolves to `'micros'`, which the (already-generic, no code changes
      needed) palette-filter logic in `bb-render.js` uses to show only the
      `micros()` button for that slot. `sim_engine.py` already executed
      `micros()` correctly (Phase 1 work) — no interpreter changes needed.
      `project_eighteen.py`'s speed-trap lesson was switched to use the new
      teachable block in Steps 8/9 (`timeA = micros();` / `timeB = micros();`
      are phantoms again). `timeA`/`timeB`'s `unsigned long` *declarations*
      in Step 2 stay locked regardless (per `block_vocabulary.py`'s own
      "always lock" note on that type) — unrelated to `micros()` support.

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

- [ ] Two non-blocking follow-ups flagged in that same spec, not yet built:
      - Cleanup cron for abandoned `pending` users rows and expired
        `registration_invites` rows (see "Abandoned `pending` rows" /
        "Abandoned-row cleanup now covers two tables" in the spec).
      - Referral-code attribution logic — `referral_code` is already captured
        on `registration_invites` but nothing acts on it yet (see "Referral
        code — captured, not yet acted on" in the spec).
