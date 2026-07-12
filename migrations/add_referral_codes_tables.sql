-- Referral / discount codes: admin_discount and parent_referral code types.
-- See docs/superpowers/specs/2026-07-12-referral-codes-design.md for the full
-- design (validation, redemption, concurrency, and the referrer annual cap).
-- Run manually in the Supabase SQL editor, same pattern as add_leads_table.sql.

CREATE TABLE IF NOT EXISTS referral_codes (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code              TEXT UNIQUE NOT NULL,
    code_type         TEXT NOT NULL,              -- 'admin_discount' | 'parent_referral'
    created_by        UUID NOT NULL REFERENCES users(id),
    discount_type     TEXT DEFAULT NULL,           -- 'percent' | 'fixed' (admin_discount only)
    discount_value    NUMERIC DEFAULT NULL,        -- admin_discount only
    stripe_coupon_id  TEXT DEFAULT NULL,           -- admin_discount only, set at creation
    reward_months     INT DEFAULT NULL,            -- parent_referral only; applied to BOTH sides
    max_redemptions   INT DEFAULT NULL,            -- null = unlimited
    redemption_count  INT NOT NULL DEFAULT 0,
    valid_till        TIMESTAMPTZ DEFAULT NULL,    -- null = no expiry
    status            TEXT NOT NULL DEFAULT 'active', -- 'active' | 'disabled' | 'expired'
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_referral_codes_created_by ON referral_codes (created_by);

CREATE TABLE IF NOT EXISTS referral_code_redemptions (
    id                       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code_id                  UUID NOT NULL REFERENCES referral_codes(id),
    -- UNIQUE: a given user account can redeem at most one code, ever. This is also
    -- what makes webhook-redelivery dedup and "did this user already use a code"
    -- the same check — see "Concurrency & idempotency" in the design doc.
    redeemed_by              UUID NOT NULL UNIQUE REFERENCES users(id),
    redeemed_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    discount_applied         NUMERIC DEFAULT NULL,
    months_credited_invitee  NUMERIC DEFAULT NULL,
    months_credited_referrer NUMERIC DEFAULT NULL
);

CREATE INDEX IF NOT EXISTS idx_referral_code_redemptions_code_id ON referral_code_redemptions (code_id);

-- registration_invites.referral_code (TEXT) becomes a FK instead of free text.
-- The old `referral_code` text column stays for now (existing rows); stop
-- writing to it once /register/invite is updated to populate this instead.
ALTER TABLE registration_invites ADD COLUMN IF NOT EXISTS referral_code_id UUID REFERENCES referral_codes(id);
