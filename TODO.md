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

- [ ] Stripe Checkout / registration / webhook flow — separate future spec,
      not started.
