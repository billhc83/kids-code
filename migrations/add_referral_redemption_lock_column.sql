-- Adds the column used as a lightweight per-code redemption lock.
-- See docs/superpowers/specs/2026-07-12-referral-codes-design.md,
-- "Concurrency & idempotency" (race B) — the doc suggests
-- pg_advisory_xact_lock held for the duration of a read-then-modify Stripe
-- sequence, but that requires a persistent Postgres connection this codebase
-- doesn't have (utils/db_client.py only talks to Postgres through the
-- Supabase PostgREST client, one HTTP request per call, no cross-request
-- transactions/locks). This column substitutes a hand-rolled lock built from
-- the same atomic-conditional-update pattern the doc already uses for the
-- max_redemptions gate: claim it with
--   UPDATE referral_codes SET redemption_locked_at = now()
--   WHERE id = :id AND (redemption_locked_at IS NULL OR redemption_locked_at < now() - interval '30 seconds')
-- release it by setting it back to NULL. See utils/referrals.py
-- try_acquire_redemption_lock / release_redemption_lock.

ALTER TABLE referral_codes ADD COLUMN IF NOT EXISTS redemption_locked_at TIMESTAMPTZ DEFAULT NULL;
