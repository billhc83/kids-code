# School / Teacher / Batch Infrastructure — Design Spec

Status: proposal — no schema changes or code written yet. This doc exists to get the data
model and phasing right *before* real tables are created, per Bill's instruction on
2026-07-13 ("we will create real tables once we have a solid and thorough plan").

Branch note: this doc assumes the Stripe individual-subscription gate
(`routes/billing.py`, `docs/superpowers/specs/2026-07-10-stripe-registration-gate-design.md`)
that currently lives on `main` but not on `dev1`. Any school-billing work is an *extension*
of that system, not a replacement — it needs to be merged into whatever branch this ships on
before org billing lands.

## What exists today (confirmed in code, not aspiration)

- **No School/Class/Batch tables.** Everything is a flat `users` row. "Teacher" = `is_teacher`
  boolean flag (`utils/auth.py:256-284`, set via admin action `create_cohort`,
  `routes/admin.py:184-197`). "Batch"/"class" = a free-text `cohort` string column, not an
  entity — it has no name, no settings, no teacher-of-record beyond whoever the admin typed it
  for.
- **Teacher↔student linking reuses `parent_student_links` verbatim** (`utils/auth.py:316-320`)
  — the same table that links parents to their kids, just with a teacher's user id in the
  `parent_id` column. There is no dedicated enrollment table.
- **Teacher dashboard is a clone of the parent dashboard** (`routes/teacher.py` /
  `templates/teacher.html`), sharing `get_students_for_parent()` with the parent flow
  (`utils/auth.py:135-148`), just without the 3-child cap.
- **Project assignment does not exist in any form.** Every account — individual, cohort-batch,
  whatever — walks the identical fixed `LESSON_SEQUENCE` (`utils/progression.py`). There is no
  code path today where two students see different available projects.
- **Billing is per-individual only** (on `main`): one Stripe subscription per registering
  parent (`subscription_status` column on `users`), gated at registration and login. No
  org/seat concept anywhere.

This means the school/teacher build is not "extend an existing system" — it's building the
org/class/assignment layer from zero on top of a single flat `users` table.

## Decided (2026-07-13 conversation)

1. **Assignment UX**: school students get an *assignment queue*, not the existing
   sequence/progression UI. No fixed `LESSON_SEQUENCE`, no lock/unlock semantics — the
   teacher's pushes are the entire list of what a student sees. This is a materially different
   home-dashboard experience for `user_type == 'class'` (or equivalent) students than the
   individual/parent flow, not a variant of it.
2. **Data model**: build real `School` / `Class` / `Enrollment` / `Assignment` tables from the
   start rather than extending the `cohort`-string hack. The hack is explicitly being replaced,
   not layered under.
3. **Teacher authoring tools**: intentionally **not decided yet** — see below. Scoped as "a lot
   more bare-bones project frameworks" that teachers build on top of, with the circuit locked
   (given) and the sketch/steps/content editable, but the exact editing surface is open.

## Proposed data model (draft — for review, not applied)

```
organizations
  id, name, type ('school' | 'district' | TBD), billing_plan_id (fk, nullable until billing
  design lands), created_at

org_members
  id, organization_id (fk), user_id (fk -> users), role ('school_admin' | 'teacher'),
  created_at
  -- a user can belong to zero or more orgs; role is per-membership, not per-user, so someone
  -- can be a teacher in one org and school_admin in another without a boolean-flag explosion

classes
  id, organization_id (fk), teacher_id (fk -> users), name, created_at, archived_at
  -- replaces the free-text `cohort` column as the grouping primitive

class_enrollments
  id, class_id (fk), student_id (fk -> users), enrolled_at, removed_at
  -- replaces the teacher-flavored rows in parent_student_links; parent_student_links stays
  -- untouched for actual parent/child relationships

project_assignments
  id, project_key, assigned_to_type ('student' | 'class'), assigned_to_id (student_id or
  class_id depending on above), assigned_by (teacher user_id), assigned_at, due_at (nullable),
  visible_from (nullable, for scheduling a push ahead of time)
  -- covers both "push to one student" and "push to the whole class" from a single table;
  -- a class-level row expands to all current class_enrollments at read time rather than
  -- fanning out N rows at write time, so removing/adding a student to a class doesn't require
  -- rewriting historical assignments
```

Open questions on this schema, flagged rather than resolved:

- Does a student need to belong to exactly one `class`, or could a teacher assign work to a
  student directly without a class wrapper (e.g. a "just me" 1:1 tutoring case)? The
  `project_assignments.assigned_to_type` split above allows either, but it's worth confirming
  that's a real use case before building for it.
- What happens to `project_assignments` history when a class is archived or a student is
  removed from a class — retained for the student's own record, or scoped to class lifetime?
  Matters for a "what did I complete last year" view.
- Should `org_members` roles be a fixed enum or a permissions table? Enum is enough for
  `school_admin`/`teacher`; only worth revisiting if a third tier (e.g. "department lead" with
  cross-class visibility) shows up in real requests.

## Teacher project-authoring tools — open design space

Bill's framing (verbatim intent, not yet resolved): teachers get bare-bones project frameworks
to build on. **The circuit is locked** — teachers aren't designing new wiring or submitting new
circuit images. What's editable is the **sketch**: setting the `//>>` step markers, `//??`
phantom slots, and `//##` locked-block lines through an interactive UI (rather than hand-editing
directive comments the way `/lesson-sketch` does today), plus choosing per-step view mode
(blocks / editor / read-only) — i.e., exposing a teacher-facing UI over the same directive
grammar documented in `BLOCK_BUILDER_SYNC.md` and used internally by the `/lesson-sketch` skill.

Two sub-questions raised, both still open:

1. **Sketch sourcing**: does the teacher get a circuit + a curated list of sketches known to be
   compatible with it (constrained authoring — pick from a working set, then re-slice into
   steps), or can they paste/write any sketch against a locked circuit (open authoring — much
   larger validation surface, since an arbitrary sketch may not match the wiring at all)?
2. **Lesson content (drawer text)**: fully manual entry by the teacher (explain/howto/logic
   tabs, step tips), or pre-authored content that ships with each framework and the teacher can
   edit rather than write from scratch? These aren't mutually exclusive — could default to
   pre-authored-and-editable with an "start blank" escape hatch — but which is v1 changes the
   authoring UI's shape substantially (rich editor for freeform content vs. a lighter
   review/tweak interface over existing copy).

Recommend treating this as its own follow-up spec once there's a rough answer to those two,
rather than folding it into the org/class/assignment schema work above — the two are separable
(assignment infra doesn't depend on how authoring works, only on `project_assignments` being
able to reference a teacher-authored project the same way it references a built-in one).

## Billing / school signup portal

Pricing model explicitly TBD (per-seat, per-class, flat per-school, tiered — nothing decided).
Structurally, this needs an org-level extension of the existing per-user Stripe gate on `main`:
`organizations.billing_plan_id` (or a separate `org_subscriptions` table mirroring the
per-user `subscription_status` pattern) gating `org_members` access the way `subscription_status`
currently gates individual login. Not designing further until pricing is decided — flagging now
only so the `organizations` table above doesn't need a breaking migration later to add it.

## Suggested phasing

1. **Schema**: `organizations`, `org_members`, `classes`, `class_enrollments`,
   `project_assignments` — additive only, no changes to existing `users`/`parent_student_links`
   behavior.
2. **Teacher dashboard v2**: class roster management (create class, enroll/remove students) +
   assignment queue push (individual and batch) against the *existing* project catalog only —
   proves out the assignment-queue UX end to end before authoring tools exist.
3. **Student assignment-queue UI**: new home view for `class`-enrolled students, replacing
   progression UI for that user type only — individual/parent-flow students untouched.
4. **Teacher authoring tools**: separate spec, per open questions above.
5. **School signup portal + billing**: separate spec, blocked on pricing decision.

Steps 2–3 alone deliver "admin creates a class, teacher pushes existing projects to students,
students see an assignment queue" — a usable v1 without touching authoring or billing at all,
and without inventing schema that later steps would have to migrate away from.
