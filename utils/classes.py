"""
utils/classes.py — data access for the school-infrastructure tables
(organizations, org_members, classes, class_enrollments, project_assignments).

See plans/SCHOOL_INFRASTRUCTURE_PLAN.md for the schema/design. Phase 2 scope:
class roster management + assignment-queue push against the existing project
catalog only — no teacher-authored projects, no student-facing queue UI yet.
"""

import datetime
from utils.db_client import supabase


def _now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def get_or_create_teacher_org(teacher_id, teacher_username):
    """Every class needs an organization_id. There's no signup-portal org
    creation flow yet (blocked on pricing, plan §5/§7), so a teacher's first
    class creation auto-provisions a personal org for them."""
    resp = supabase.table("org_members").select("organization_id").eq("user_id", teacher_id).execute()
    if resp.data:
        return resp.data[0]["organization_id"]

    org_resp = supabase.table("organizations").insert({
        "name": f"{teacher_username}'s Classroom",
        "type": "school",
    }).execute()
    organization_id = org_resp.data[0]["id"]

    supabase.table("org_members").insert({
        "organization_id": organization_id,
        "user_id": teacher_id,
        "role": "teacher",
    }).execute()
    return organization_id


def create_class(teacher_id, teacher_username, name):
    organization_id = get_or_create_teacher_org(teacher_id, teacher_username)
    resp = supabase.table("classes").insert({
        "organization_id": organization_id,
        "teacher_id": teacher_id,
        "name": name,
    }).execute()
    return resp.data[0] if resp.data else None


def get_classes_for_teacher(teacher_id):
    resp = (
        supabase.table("classes")
        .select("*")
        .eq("teacher_id", teacher_id)
        .is_("archived_at", "null")
        .order("created_at")
        .execute()
    )
    return resp.data or []


def get_class(class_id):
    resp = supabase.table("classes").select("*").eq("id", class_id).execute()
    return resp.data[0] if resp.data else None


def get_roster(class_id):
    """Active (non-removed) enrollments for a class, with student user rows attached."""
    resp = (
        supabase.table("class_enrollments")
        .select("*")
        .eq("class_id", class_id)
        .is_("removed_at", "null")
        .execute()
    )
    enrollments = resp.data or []

    roster = []
    for enrollment in enrollments:
        student_resp = supabase.table("users").select("*").eq("id", enrollment["student_id"]).execute()
        if student_resp.data:
            student = student_resp.data[0]
            student["enrollment_id"] = enrollment["id"]
            student["enrolled_at"] = enrollment["enrolled_at"]
            roster.append(student)
    return roster


def enroll_student(class_id, student_id):
    supabase.table("class_enrollments").insert({
        "class_id": class_id,
        "student_id": student_id,
    }).execute()


def remove_student(enrollment_id):
    supabase.table("class_enrollments").update({"removed_at": _now()}).eq("id", enrollment_id).execute()


def create_assignment(project_key, assigned_to_type, assigned_to_id, assigned_by, due_at=None):
    return supabase.table("project_assignments").insert({
        "project_key": project_key,
        "assigned_to_type": assigned_to_type,
        "assigned_to_id": assigned_to_id,
        "assigned_by": assigned_by,
        "due_at": due_at,
    }).execute()


def get_active_class_ids_for_student(student_id):
    resp = (
        supabase.table("class_enrollments")
        .select("class_id")
        .eq("student_id", student_id)
        .is_("removed_at", "null")
        .execute()
    )
    return [row["class_id"] for row in (resp.data or [])]


def is_class_enrolled(student_id):
    """True if this student has any active (non-removed) class enrollment —
    the signal that switches their home dashboard to the assignment-queue
    view (Phase 3) instead of the fixed-sequence progression view."""
    return len(get_active_class_ids_for_student(student_id)) > 0


def get_assignment_queue_for_student(student_id):
    """Individual + class-level assignments currently visible to this
    student, merged and deduplicated by project_key (if pushed both
    individually and via a class, the row with the soonest due_at wins)."""
    class_ids = get_active_class_ids_for_student(student_id)

    student_resp = (
        supabase.table("project_assignments")
        .select("*")
        .eq("assigned_to_type", "student")
        .eq("assigned_to_id", student_id)
        .execute()
    )
    rows = list(student_resp.data or [])

    if class_ids:
        class_resp = (
            supabase.table("project_assignments")
            .select("*")
            .eq("assigned_to_type", "class")
            .in_("assigned_to_id", class_ids)
            .execute()
        )
        rows.extend(class_resp.data or [])

    by_key = {}
    for row in rows:
        key = row["project_key"]
        existing = by_key.get(key)
        if existing is None or (row.get("due_at") and (not existing.get("due_at") or row["due_at"] < existing["due_at"])):
            by_key[key] = row

    return sorted(by_key.values(), key=lambda r: (r["due_at"] is None, r.get("due_at"), r["assigned_at"]))


def get_assignment_keys_for_student(student_id):
    """Just the project_keys, for the /lessons/<key> unlock-bypass check."""
    return {a["project_key"] for a in get_assignment_queue_for_student(student_id)}


def get_assignments_for_class(class_id, student_ids):
    """Everything pushed to this class as a whole, or to any student currently
    on its roster — for the teacher's own confirmation view. (Not the
    student-facing merged queue; that's Phase 3.)"""
    class_resp = (
        supabase.table("project_assignments")
        .select("*")
        .eq("assigned_to_type", "class")
        .eq("assigned_to_id", class_id)
        .execute()
    )
    assignments = list(class_resp.data or [])

    if student_ids:
        student_resp = (
            supabase.table("project_assignments")
            .select("*")
            .eq("assigned_to_type", "student")
            .in_("assigned_to_id", student_ids)
            .execute()
        )
        assignments.extend(student_resp.data or [])

    assignments.sort(key=lambda a: a["assigned_at"], reverse=True)
    return assignments
