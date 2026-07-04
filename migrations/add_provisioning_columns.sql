-- Migration: add provisioning columns
-- Run in the Supabase SQL editor before deploying the provisioning feature.

ALTER TABLE users ADD COLUMN IF NOT EXISTS is_teacher  BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS user_type   TEXT    NOT NULL DEFAULT 'standard';
ALTER TABLE users ADD COLUMN IF NOT EXISTS is_test     BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS cohort      TEXT    DEFAULT NULL;

-- user_type values: 'standard' | 'class' | 'beta' | 'test'
-- is_teacher: TRUE for the anchor account of a cohort
-- is_test:    TRUE for internal test accounts (skips ToS gate)
-- cohort:     shared label for all members of a provisioned group (teacher + students)
