"""
utils/authored_projects.py — data access for the `authored_projects` table
(teacher-authoring tool, plans/SCHOOL_INFRASTRUCTURE_PLAN.md §4). Draft
storage + publish. The actual block-structure -> sketch conversion lives in
utils/teacher_authoring_serializer.py; this module just persists/retrieves.
"""

import re
import datetime
from utils.db_client import supabase
from utils.project_registry import PROJECTS


def _now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _slugify(title):
    slug = re.sub(r'[^a-z0-9]+', '_', title.lower()).strip('_')
    return slug or 'untitled'


def assignable_circuit_projects():
    """Built-in projects a teacher can base a new lesson's wiring on —
    same set routes/dev.py's circuit sandbox already computes."""
    return [k for k, p in PROJECTS.items() if p.get('circuit_definition')]


def create_authored_project(organization_id, created_by, circuit_source_key, title):
    if circuit_source_key not in PROJECTS or not PROJECTS[circuit_source_key].get('circuit_definition'):
        return None, "Pick a valid circuit."

    base_key = _slugify(title)
    project_key = base_key
    suffix = 2
    while supabase.table("authored_projects").select("id").eq("project_key", project_key).execute().data:
        project_key = f"{base_key}_{suffix}"
        suffix += 1

    source = PROJECTS[circuit_source_key]
    draft_data = {
        "meta": {"title": title},
        "circuit": {
            "circuit_source_key": circuit_source_key,
            "circuit_definition": source.get("circuit_definition"),
            "circuit_image": source.get("meta", {}).get("circuit_image"),
        },
        "steps": [],
        "drawer": {},
    }

    resp = supabase.table("authored_projects").insert({
        "organization_id": organization_id,
        "created_by": created_by,
        "project_key": project_key,
        "circuit_source_key": circuit_source_key,
        "draft_data": draft_data,
    }).execute()
    return (resp.data[0] if resp.data else None), None


def get_authored_projects_for_teacher(teacher_id):
    resp = (
        supabase.table("authored_projects")
        .select("*")
        .eq("created_by", teacher_id)
        .order("created_at", desc=True)
        .execute()
    )
    return resp.data or []


def get_authored_project(project_id):
    resp = supabase.table("authored_projects").select("*").eq("id", project_id).execute()
    return resp.data[0] if resp.data else None


def save_draft(project_id, draft_data):
    supabase.table("authored_projects").update({
        "draft_data": draft_data,
        "updated_at": _now(),
    }).eq("id", project_id).execute()


def publish(project_id, published_data, current_version):
    supabase.table("authored_projects").update({
        "published_data": published_data,
        "published_version": current_version + 1,
        "published_at": _now(),
        "updated_at": _now(),
        "status": "published",
    }).eq("id", project_id).execute()
