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
from utils.teacher_authoring_serializer import materialize, hydrate_steps, validate_step_shape
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
            shape_error = validate_step_shape(steps)
            if shape_error:
                error = shape_error
            else:
                draft_data = dict(project["draft_data"])
                draft_data["steps"] = steps
                save_draft(project_id, draft_data)
                flash("Draft saved.")
                return redirect(url_for("teacher_authoring.build", project_id=project_id))

    existing_steps = project["draft_data"].get("steps", [])
    steps_json = json.dumps(existing_steps, indent=2)

    # Load a previously-saved draft back into the live workspace (build order
    # step 4 — the reverse of extractStepDraft()). Any failure here (e.g. a
    # draft hand-edited via the raw JSON view into something the real grammar
    # can't parse) must not break the page — fall back to a blank workspace
    # and let hydrate_failed steer the teacher at the raw JSON view instead.
    hydrated_steps = None
    hydrate_failed = False
    if existing_steps:
        try:
            hydrated_steps = hydrate_steps(existing_steps)
        except Exception:
            hydrate_failed = True

    # Live block-builder authoring surface (plans/TEACHER_AUTHORING_LIVE_BUILDER_UI_SPEC.md
    # §5/§6, build order step 3). Freeform mode — the step-tabs shell
    # (static/js/teacher-authoring.js) owns BB.SECTIONS from here on, seeded
    # from `initial_steps` when a draft already has hydratable content.
    # `username: None` deliberately keeps block_builder.js's Supabase-backed
    # BB.loadBlocks()/autosave paths dark; this tool's own "Save Draft (Live)"
    # button is the only persistence path.
    live_config = {
        "mode": "freeform",
        "steps": None,
        "palette": None,
        "master": None,
        "username": None,
        "page": project["project_key"],
        "drawer": {},
        "lock_mode": False,
        "is_overlay": False,
        "default_view": "blocks",
        "lock_view": False,
        "readonly_mode": False,
        "authoring_mode": True,
        "force_preset": True,
        "initial_steps": hydrated_steps,
        "supabase_url": SUPABASE_URL,
        "supabase_key": SUPABASE_KEY,
    }
    live_config_json = json.dumps(live_config).replace('</', '<\\/')

    return render_template(
        "teacher_authoring_build.html", project=project, steps_json=steps_json,
        error=error, config=live_config_json,
        show_raw=(request.args.get("raw") == "1"),
        hydrate_failed=hydrate_failed,
    )


@teacher_authoring_bp.route("/<project_id>/preview")
@login_required
@teacher_required
def preview(project_id):
    project = _get_owned_project(project_id)
    steps = project["draft_data"].get("steps", [])

    try:
        materialize(steps)  # validate only — real config-building happens in /builder
    except Exception as e:
        flash(f"Preview failed: {e}", "error")
        return redirect(url_for("teacher_authoring.build", project_id=project_id))

    # Full student-facing IDE (drawer, blocks/editor toggle, compile/upload/
    # serial monitor via the local KidsCode Link agent) — not the bare
    # workspace fragment. arduino_interface.html's own loadBlockBuilder() JS
    # fetches /builder?preset=<val>&page=<val>, reading preset/page from
    # *this page's own URL query string* (window.location.search), not from
    # any Jinja var — so the caller's link MUST be
    # ".../preview?preset=<project_id>&page=<project_id>"
    # (see templates/teacher_authoring_build.html) for loadBlockBuilder() to
    # resolve the right draft. routes/builder.py's builder_endpoint()
    # recognizes that preset value as a draft id (owned by this session) and
    # builds the real progression config from it, via the same
    # materialize()/parse_steps() pipeline this route just validated with.
    from routes.builder import normalize_drawer_steps

    drawer_content = project["draft_data"].get("drawer", {})
    drawer_steps = normalize_drawer_steps(list(drawer_content.values())) if isinstance(drawer_content, dict) else []

    return render_template(
        "components/arduino_interface.html",
        preset=project_id, drawer_steps=drawer_steps,
    )


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

    shape_error = validate_step_shape(steps)
    if shape_error:
        flash(f"Publish failed — {shape_error}", "error")
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
