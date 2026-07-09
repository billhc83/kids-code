-- Migration: add leads table
-- Run in the Supabase SQL editor before deploying the /try page.
-- Leads are deliberately NOT rows in `users` — every `users` row must stay
-- either a paying or admin-provisioned account (see docs/superpowers/specs/
-- 2026-07-09-try-page-infra-design.md).

CREATE TABLE IF NOT EXISTS leads (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email             TEXT NOT NULL,
    consent_given_at  TIMESTAMPTZ NOT NULL,
    source            TEXT NOT NULL DEFAULT 'try_page',
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    followed_up_at    TIMESTAMPTZ DEFAULT NULL
);

CREATE INDEX IF NOT EXISTS idx_leads_followed_up_at ON leads (followed_up_at);
