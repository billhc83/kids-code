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

-- subscription_status values: 'none' (provisioned accounts) | 'pending' (row created,
-- Checkout not yet confirmed) | 'active' | 'past_due' | 'canceled'
