-- Teacher-authored projects: the blocks-first authoring tool described in
-- plans/SCHOOL_INFRASTRUCTURE_PLAN.md §4. Phase 4 of that plan's §6 phasing.
-- Additive only. Run manually in the Supabase SQL editor, same pattern as
-- add_school_infrastructure_tables.sql (Phase 1).

CREATE TABLE IF NOT EXISTS authored_projects (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id     UUID NOT NULL REFERENCES organizations(id),
    created_by          UUID NOT NULL REFERENCES users(id),
    project_key         TEXT UNIQUE NOT NULL,
    -- References an existing built-in project's key (utils/project_registry.py's
    -- PROJECTS dict) whose circuit_definition was copied into draft_data.circuit
    -- at creation time — not re-resolved live, so a later change to the
    -- built-in project doesn't retroactively alter a published lesson. Not a
    -- DB foreign key: the built-in catalog is file-based, not a table.
    circuit_source_key  TEXT NOT NULL,
    status              TEXT NOT NULL DEFAULT 'draft',   -- 'draft' | 'published' | 'archived'
    -- Working state: block-structure-plus-phantom/locked-flags draft (the
    -- teacher_authoring_serializer.py StepDraft shape) + drawer content in
    -- progress. Freely mutable, never served to students.
    draft_data          JSONB NOT NULL DEFAULT '{}'::jsonb,
    -- The fully materialized PROJECT-shape dict (meta/steps/drawer/presets),
    -- frozen at publish time via materialize() + parse_steps() round-trip
    -- validation. NULL until first publish.
    published_data      JSONB DEFAULT NULL,
    published_version   INT NOT NULL DEFAULT 0,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    published_at        TIMESTAMPTZ DEFAULT NULL
);

CREATE INDEX IF NOT EXISTS idx_authored_projects_organization_id ON authored_projects (organization_id);
CREATE INDEX IF NOT EXISTS idx_authored_projects_created_by ON authored_projects (created_by);
