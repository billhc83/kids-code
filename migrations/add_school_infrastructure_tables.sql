-- School/teacher/batch infrastructure: organizations, memberships, classes,
-- enrollments, and project assignments. Phase 1 of the plan in
-- plans/SCHOOL_INFRASTRUCTURE_PLAN.md (see that file's §3 for the schema
-- rationale and §6 for phasing). Additive only — no changes to existing
-- `users`/`parent_student_links` behavior; the `cohort`/`is_teacher` columns
-- on `users` are untouched and superseded going forward, not migrated here.
-- Run manually in the Supabase SQL editor, same pattern as
-- add_referral_codes_tables.sql.

CREATE TABLE IF NOT EXISTS organizations (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name             TEXT NOT NULL,
    type             TEXT NOT NULL,              -- 'school' | 'district' | TBD
    -- No REFERENCES yet: the billing_plans/org_subscriptions table doesn't
    -- exist until the billing design in §5 of the plan lands. Placeholder
    -- column only, so that migration won't need a breaking schema change.
    billing_plan_id  UUID DEFAULT NULL,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS org_members (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id  UUID NOT NULL REFERENCES organizations(id),
    user_id          UUID NOT NULL REFERENCES users(id),
    role             TEXT NOT NULL,              -- 'school_admin' | 'teacher'
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    -- A user holds one role per org; use a second membership row in a
    -- different org for a different role there, not a second row here.
    UNIQUE (organization_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_org_members_organization_id ON org_members (organization_id);
CREATE INDEX IF NOT EXISTS idx_org_members_user_id ON org_members (user_id);

CREATE TABLE IF NOT EXISTS classes (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id  UUID NOT NULL REFERENCES organizations(id),
    teacher_id       UUID NOT NULL REFERENCES users(id),
    name             TEXT NOT NULL,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    archived_at      TIMESTAMPTZ DEFAULT NULL
);

CREATE INDEX IF NOT EXISTS idx_classes_organization_id ON classes (organization_id);
CREATE INDEX IF NOT EXISTS idx_classes_teacher_id ON classes (teacher_id);

CREATE TABLE IF NOT EXISTS class_enrollments (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    class_id      UUID NOT NULL REFERENCES classes(id),
    student_id    UUID NOT NULL REFERENCES users(id),
    enrolled_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    removed_at    TIMESTAMPTZ DEFAULT NULL
);

CREATE INDEX IF NOT EXISTS idx_class_enrollments_class_id ON class_enrollments (class_id);
CREATE INDEX IF NOT EXISTS idx_class_enrollments_student_id ON class_enrollments (student_id);
-- A student can be re-enrolled after removal (removed_at set on the old row),
-- but can't have two simultaneously-active enrollments in the same class.
CREATE UNIQUE INDEX IF NOT EXISTS uq_class_enrollments_active
    ON class_enrollments (class_id, student_id) WHERE removed_at IS NULL;

CREATE TABLE IF NOT EXISTS project_assignments (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_key       TEXT NOT NULL,
    assigned_to_type  TEXT NOT NULL,              -- 'student' | 'class'
    -- Polymorphic: either a users(id) or classes(id) depending on
    -- assigned_to_type above, so it can't carry a single REFERENCES target.
    assigned_to_id    UUID NOT NULL,
    assigned_by       UUID NOT NULL REFERENCES users(id),
    assigned_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    due_at            TIMESTAMPTZ DEFAULT NULL,
    visible_from      TIMESTAMPTZ DEFAULT NULL
);

CREATE INDEX IF NOT EXISTS idx_project_assignments_assigned_to ON project_assignments (assigned_to_type, assigned_to_id);
CREATE INDEX IF NOT EXISTS idx_project_assignments_assigned_by ON project_assignments (assigned_by);
