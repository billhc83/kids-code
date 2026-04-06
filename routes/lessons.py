from flask import Blueprint, request, session, render_template, redirect, url_for, flash, abort
from utils.decorators import login_required
from utils.progression import complete_lesson, is_unlocked, get_completed_lessons
from utils.badges import check_and_award_badges
from utils.lessons import get_lesson
from utils.project_registry import PROJECTS
from utils.assembly_guide_flask import render_assembly_guide
from config import SUPABASE_URL, SUPABASE_KEY
import json

lessons_bp = Blueprint('lessons', __name__)

def normalize_drawer_steps(steps):
    """Convert each step's tabs dict to an ordered list so JSON serialization preserves insertion order."""
    result = []
    for step in steps:
        s = dict(step)
        if isinstance(s.get('tabs'), dict):
            s['tabs'] = [{'id': k, **v} for k, v in s['tabs'].items()]
        result.append(s)
    return result

@lessons_bp.route("/lessons/complete", methods=["POST"])
@login_required
def complete_lesson_route():
    lesson_key = request.form.get("lesson_key")
    if lesson_key:
        next_key = complete_lesson(session["user_id"], lesson_key)
        completed = get_completed_lessons(session["user_id"])
        check_and_award_badges(session["user_id"], completed)
        if next_key:
            flash("Project complete! Next project unlocked 🎉")
        else:
            flash("Project complete! 🎉")
    return redirect(url_for("main.dashboard"))

@lessons_bp.route("/lessons/<lesson_key>")
@login_required
def lesson(lesson_key):
    lesson_data = get_lesson(lesson_key)
    if not lesson_data:
        abort(404)

    if not is_unlocked(session["user_id"], lesson_key):
        flash("Complete the previous project to unlock this one")
        return redirect(url_for("main.dashboard"))

    extra = {}
    project_data = PROJECTS.get(lesson_key)
    if project_data:
        meta = project_data.get("meta", {})
        img = meta.get("circuit_image") or project_data.get("image")
        steps = project_data.get("steps", [])
        title = meta.get("title") or project_data.get("title")
        if img and steps:
            extra["assembly_guide_html"] = render_assembly_guide(img, steps, title)

    if lesson_key == "project_fourteen_part_one":
        from utils.code_breaker import serial_monitor
        extra["serial_monitor_html"] = serial_monitor(
            answer='SPARK',
            cipher_lines=[
                'STSTARERT', 'PLSHAREMN', 'BNSHARKOP', 'QWSPARETY', 'ZXSPARKCV',
                'MKSNAREPL', 'HGSHAKEUI', 'LKDJSFPOIE', 'MNBVCXZAQS', 'POIUYTREWQ'
            ],
            message=[
                "CODE CRACKED", "", "GOOD WORK AGENT.", "",
                "YOU HAVE SUCCESSFULLY COMPLETED", "THE FIRST TRAINING EXERCISE.",
                "", "THIS SYSTEM WAS BUILT TO TEST", "YOUR ABILITY TO ANALYZE",
                "AND BREAK SECRET CODES.", "", "BUT EVERY TRAINING PROGRAM",
                "NEEDS NEW CHALLENGES.", "", "YOUR NEXT MISSION:",
                "BUILD A NEW CODE BREAKING TRAINING SYSTEM",
                "FOR THE NEXT GROUP OF TRAINEES.", "", "TRAINING COMMAND OUT."
            ]
        )

    preset = lesson_data.get("block_builder")
    if preset:
        from utils.block_builder import get_builder_html
        from utils.contents_flask import DRAWER_CONTENT

        base_url = request.host_url.rstrip('/')
        ide_url = f"{base_url}/standalone_ide/{preset}?preset={preset}&page={lesson_key}"

        drawer_content = None
        if project_data and "drawer" in project_data:
            d = project_data["drawer"]
            if isinstance(d, dict):
                drawer_content = d.get(preset) or d.get("default") or (d if "title" in d or "tabs" in d else None)
            else:
                drawer_content = d
        
        if not drawer_content:
            drawer_content = DRAWER_CONTENT.get(preset)

        if drawer_content and isinstance(drawer_content, dict) and isinstance(drawer_content.get("tabs"), dict):
            drawer_content = drawer_content.copy()
            drawer_content["tabs"] = list(drawer_content["tabs"].values())

        extra["block_builder_html"] = get_builder_html(
            preset=preset,
            username=session.get("user_id"),
            page=lesson_key,
            is_overlay=True,
            builder_url=ide_url
        )
        
        if drawer_content:
            if isinstance(drawer_content, list):
                extra["drawer_steps"] = normalize_drawer_steps(drawer_content)
            elif isinstance(drawer_content, dict):
                extra["drawer_steps"] = normalize_drawer_steps(drawer_content.get("steps") or [drawer_content])

    return render_template(
        lesson_data["template"],
        lesson=lesson_data,
        lesson_key=lesson_key,
        **extra
    )

from utils.challenges import get_submission, submit_challenge
from utils.feedback import notify_discord_feedback

@lessons_bp.route("/challenges/<challenge_key>", methods=["GET", "POST"])
@login_required
def challenge(challenge_key):
    if session.get("is_parent"):
        return redirect(url_for("parent.parent_dashboard"))

    lesson_data = get_lesson(challenge_key)
    if not lesson_data:
        abort(404)

    if not is_unlocked(session["user_id"], challenge_key):
        flash("Complete the previous projects to unlock this challenge")
        return redirect(url_for("main.dashboard"))

    submission = get_submission(session["user_id"], challenge_key)
    error = None
    success = None

    if request.method == "POST":
        sketch_code = request.form.get("sketch_code", "").strip()
        if not sketch_code:
            error = "Please paste your sketch code before submitting."
        else:
            result, err = submit_challenge(
                session["user_id"],
                session["username"],
                challenge_key,
                sketch_code
            )
            if err:
                error = err
            else:
                success = "Submission received! We will review it shortly."
                submission = get_submission(session["user_id"], challenge_key)
                notify_discord_feedback(
                    session["username"],
                    "Challenge Submission",
                    f"Challenge: {challenge_key}"
                )

    return render_template(
        lesson_data["template"],
        lesson=lesson_data,
        lesson_key=challenge_key,
        submission=submission,
        error=error,
        success=success
    )
