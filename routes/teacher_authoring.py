"""
routes/teacher_authoring.py — teacher-authoring tool (plans/SCHOOL_INFRASTRUCTURE_PLAN.md §4).

Bare-minimum UI: this proves the pipeline (draft -> materialize() ->
parse_steps() -> real block-builder preview -> publish validation) end to
end, not the eventual drag-and-drop authoring UX. The "build"/"drawer"
screens are raw JSON textareas over the StepDraft shape documented in
utils/teacher_authoring_serializer.py, not a new frontend interaction model.
"""

import json
from flask import Blueprint, request, session, render_template, redirect, url_for, flash, abort
from utils.decorators import login_required, teacher_required
from utils.authored_projects import (
    assignable_circuit_projects, create_authored_project, get_authored_projects_for_teacher,
    get_authored_project, save_draft, publish,
)
from utils.classes import get_or_create_teacher_org
from utils.teacher_authoring_serializer import materialize
from utils.block_parser import parse_steps
from config import SUPABASE_URL, SUPABASE_KEY

teacher_authoring_bp = Blueprint('teacher_authoring', __name__, url_prefix='/teacher/projects')


def _get_owned_project(project_id):
    project = get_authored_project(project_id)
    if not project or project["created_by"] != session["user_id"]:
        abort(404)
    return project


@teacher_authoring_bp.route("")
@login_required
@teacher_required
def project_list():
    projects = get_authored_projects_for_teacher(session["user_id"])
    return render_template("teacher_authoring_list.html", projects=projects)


@teacher_authoring_bp.route("/new", methods=["GET", "POST"])
@login_required
@teacher_required
def new_project():
    circuits = assignable_circuit_projects()
    error = None

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        circuit_source_key = request.form.get("circuit_source_key", "")
        if not title:
            error = "Title is required."
        elif circuit_source_key not in circuits:
            error = "Pick a valid circuit."
        else:
            organization_id = get_or_create_teacher_org(session["user_id"], session["username"])
            project, err = create_authored_project(organization_id, session["user_id"], circuit_source_key, title)
            if err:
                error = err
            else:
                return redirect(url_for("teacher_authoring.build", project_id=project["id"]))

    return render_template("teacher_authoring_new.html", circuits=circuits, error=error)


@teacher_authoring_bp.route("/<project_id>/build", methods=["GET", "POST"])
@login_required
@teacher_required
def build(project_id):
    project = _get_owned_project(project_id)
    error = None

    if request.method == "POST":
        raw = request.form.get("steps_json", "")
        try:
            steps = json.loads(raw) if raw.strip() else []
            if not isinstance(steps, list):
                raise ValueError("Steps must be a JSON array.")
        except (ValueError, json.JSONDecodeError) as e:
            error = f"Invalid JSON: {e}"
        else:
            draft_data = dict(project["draft_data"])
            draft_data["steps"] = steps
            save_draft(project_id, draft_data)
            flash("Draft saved.")
            return redirect(url_for("teacher_authoring.build", project_id=project_id))

    steps_json = json.dumps(project["draft_data"].get("steps", []), indent=2)
    return render_template("teacher_authoring_build.html", project=project, steps_json=steps_json, error=error)


@teacher_authoring_bp.route("/<project_id>/preview")
@login_required
@teacher_required
def preview(project_id):
    project = _get_owned_project(project_id)
    steps = project["draft_data"].get("steps", [])

    try:
        sketch = materialize(steps)
        parsed_steps = parse_steps(sketch)
    except Exception as e:
        flash(f"Preview failed: {e}", "error")
        return redirect(url_for("teacher_authoring.build", project_id=project_id))

    config = {
        "mode": "progression",
        "steps": parsed_steps,
        "palette": None,
        "master": None,
        "username": None,
        "page": project["project_key"],
        "drawer": project["draft_data"].get("drawer", {}),
        "lock_mode": False,
        "is_overlay": False,
        "default_view": "blocks",
        "lock_view": False,
        "readonly_mode": False,
        "force_preset": True,
        "supabase_url": SUPABASE_URL,
        "supabase_key": SUPABASE_KEY,
    }
    config_json = json.dumps(config).replace('</', '<\\/')
    return render_template("block_builder_fragment.html", config=config_json)


@teacher_authoring_bp.route("/<project_id>/drawer", methods=["GET", "POST"])
@login_required
@teacher_required
def drawer(project_id):
    project = _get_owned_project(project_id)
    error = None

    if request.method == "POST":
        raw = request.form.get("drawer_json", "")
        try:
            drawer_content = json.loads(raw) if raw.strip() else {}
            if not isinstance(drawer_content, dict):
                raise ValueError("Drawer content must be a JSON object.")
        except (ValueError, json.JSONDecodeError) as e:
            error = f"Invalid JSON: {e}"
        else:
            draft_data = dict(project["draft_data"])
            draft_data["drawer"] = drawer_content
            save_draft(project_id, draft_data)
            flash("Drawer content saved.")
            return redirect(url_for("teacher_authoring.drawer", project_id=project_id))

    drawer_json = json.dumps(project["draft_data"].get("drawer", {}), indent=2)
    return render_template("teacher_authoring_drawer.html", project=project, drawer_json=drawer_json, error=error)


@teacher_authoring_bp.route("/<project_id>/publish", methods=["POST"])
@login_required
@teacher_required
def publish_project(project_id):
    project = _get_owned_project(project_id)
    draft = project["draft_data"]
    steps = draft.get("steps", [])

    if not steps:
        flash("Add at least one step before publishing.", "error")
        return redirect(url_for("teacher_authoring.build", project_id=project_id))

    try:
        sketch = materialize(steps)
        parsed_steps = parse_steps(sketch)
    except Exception as e:
        flash(f"Publish failed — sketch didn't validate: {e}", "error")
        return redirect(url_for("teacher_authoring.build", project_id=project_id))

    if len(parsed_steps) != len(steps) + 1:
        flash(
            f"Publish failed — expected {len(steps) + 1} parsed steps "
            f"(including Mission Complete), got {len(parsed_steps)}.",
            "error",
        )
        return redirect(url_for("teacher_authoring.build", project_id=project_id))

    drawer_content = draft.get("drawer", {})
    if len(drawer_content) != len(steps):
        flash(
            f"Publish failed — drawer has {len(drawer_content)} step(s), sketch has {len(steps)}. "
            "Step counts must match.",
            "error",
        )
        return redirect(url_for("teacher_authoring.drawer", project_id=project_id))

    circuit = draft.get("circuit", {})
    published_data = {
        "meta": {
            "title": draft.get("meta", {}).get("title", project["project_key"]),
            "circuit_image": circuit.get("circuit_image"),
            "banner_image": None,
        },
        "steps": [],
        "drawer": drawer_content,
        "presets": {
            "default": {
                "sketch": sketch,
                "default_view": "blocks",
                "read_only": False,
                "lock_view": False,
                "fill_values": True,
                "fill_conditions": True,
            }
        },
        "circuit_definition": circuit.get("circuit_definition"),
    }

    publish(project_id, published_data, project["published_version"])
    flash("Published!")
    return redirect(url_for("teacher_authoring.project_list"))
