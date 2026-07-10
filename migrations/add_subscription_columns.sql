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

-- Grandfather every account that existed before this gate shipped — without this,
-- every pre-existing 'standard' row (self-registered accounts and parent-created
-- student sub-accounts alike) would default to subscription_status='none' and be
-- locked out of login the instant the gated login code deploys. This is a one-time
-- backfill for rows that exist right now; it deliberately does NOT apply going
-- forward — new parent-created student rows are meant to stay at the 'none' default
-- so the login gate's live parent-subscription check (routes/auth.py) applies to them.
UPDATE users SET subscription_status = 'active'
WHERE user_type = 'standard' AND subscription_status = 'none';

-- subscription_status values: 'none' (provisioned accounts, and parent-linked student
-- accounts created after this migration — see utils.auth.get_linking_parent) |
-- 'pending' (row created, Checkout not yet confirmed) | 'active' | 'past_due' | 'canceled'
