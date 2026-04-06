from flask import Blueprint, request, session, render_template, redirect, url_for, flash
from utils.decorators import login_required
from utils.progression import get_user_progression, get_completed_lessons
from utils.badges import get_user_badges, BADGE_DEFINITIONS
from utils.feedback import get_threads_for_user, CATEGORIES, create_thread, add_message, notify_discord_feedback
from utils.activity import log_activity
from utils.lessons import LESSONS

main_bp = Blueprint('main', __name__)

@main_bp.route("/ping")
def ping():
    return "ok", 200

@main_bp.route("/")
def index():
    if "user_id" in session:
        if session.get("is_parent"):
            return redirect(url_for("parent.parent_dashboard"))
        return redirect(url_for("main.dashboard"))
    return redirect(url_for("auth.login"))

@main_bp.route("/dashboard")
@login_required
def dashboard():
    completed = get_completed_lessons(session["user_id"])
    user_badges = get_user_badges(session["user_id"])
    unlocked = get_user_progression(session["user_id"])

    current_lesson = None
    for lesson in LESSONS:
        if lesson["key"] in unlocked and lesson["key"] not in completed:
            if "challenge" in lesson["key"]:
                continue
            current_lesson = lesson
            break

    badges = []
    for key, defn in BADGE_DEFINITIONS.items():
        badges.append({
            **defn,
            "earned": key in user_badges
        })

    return render_template(
        "dashboard.html",
        completed=completed,
        current_lesson=current_lesson,
        badges=badges,
        total_lessons=14
    )

@main_bp.route("/api/log-activity", methods=["POST"])
@login_required
def log_activity_route():
    data = request.get_json()
    lesson_key = data.get("lesson_key")
    duration = data.get("duration_seconds", 0)
    if lesson_key and duration > 5:
        log_activity(
            session["user_id"],
            session["username"],
            lesson_key,
            int(duration)
        )
    return {"ok": True}

@main_bp.route("/feedback", methods=["GET", "POST"])
@login_required
def feedback():
    threads = get_threads_for_user(session["user_id"])
    if request.method == "POST":
        action = request.form.get("action")
        if action == "new_thread":
            category = request.form.get("category")
            subject = request.form.get("subject", "").strip()
            message = request.form.get("message", "").strip()
            if category and subject and message:
                create_thread(
                    session["user_id"],
                    session["username"],
                    category, subject, message
                )
                notify_discord_feedback(
                    session["username"], category, subject
                )
                flash("Feedback submitted!")
        elif action == "reply":
            thread_id = request.form.get("thread_id")
            message = request.form.get("message", "").strip()
            if thread_id and message:
                add_message(
                    thread_id,
                    session["user_id"],
                    session["username"],
                    message,
                    is_admin=False
                )
                flash("Reply sent!")
        return redirect(url_for("main.feedback"))
    return render_template(
        "feedback.html",
        threads=threads,
        categories=CATEGORIES
    )
