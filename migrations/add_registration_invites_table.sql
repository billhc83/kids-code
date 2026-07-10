-- Registration-access gate: /register requires a one-time emailed link.
-- See docs/superpowers/specs/2026-07-10-stripe-registration-gate-design.md
-- ("Registration-access gate" section) for the full flow this supports.
-- Run manually in the Supabase SQL editor, same pattern as add_leads_table.sql.

CREATE TABLE IF NOT EXISTS registration_invites (
    token          TEXT PRIMARY KEY,
    email          TEXT NOT NULL,
    referral_code  TEXT DEFAULT NULL,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at     TIMESTAMPTZ NOT NULL,
    used_at        TIMESTAMPTZ DEFAULT NULL
);
