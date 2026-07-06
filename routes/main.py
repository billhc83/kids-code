from flask import Blueprint, request, session, render_template, redirect, url_for, flash, jsonify
from utils.decorators import login_required
from utils.progression import get_user_progression, get_completed_lessons
from utils.badges import get_user_badges, BADGE_DEFINITIONS
from utils.feedback import get_threads_for_user, CATEGORIES, create_thread, add_message, notify_discord_feedback
from utils.activity import log_activity
from utils.lessons import LESSONS, LESSON_BY_KEY, count_unique_projects, TOTAL_PROJECTS
from utils.auth import mark_first_login_complete
from extensions import limiter
import requests as http_requests
from config import RESEND_API_KEY

main_bp = Blueprint('main', __name__)

_PRIVACY_EMAIL = "no-reply@kidscode.ca"
_PRIVACY_TO    = "billhc83@gmail.com"

@main_bp.route("/ping")
def ping():
    return "ok", 200

@main_bp.route("/")
def index():
    if "user_id" in session:
        if session.get("is_parent"):
            return redirect(url_for("parent.parent_dashboard"))
        return redirect(url_for("main.dashboard"))
    return render_template("splash.html")

@main_bp.route("/dashboard")
@login_required
def dashboard():
    completed = get_completed_lessons(session["user_id"])
    user_badges = get_user_badges(session["user_id"])
    unlocked = get_user_progression(session["user_id"])

    completed_count = count_unique_projects(completed)

    current_lesson = None
    for lesson in LESSONS:
        if lesson["key"] in unlocked and lesson["key"] not in completed:
            if "challenge" in lesson["key"]:
                continue
            current_lesson = lesson
            break

    badges = [defn for key, defn in BADGE_DEFINITIONS.items() if key in user_badges]

    return render_template(
        "dashboard.html",
        completed=completed,
        completed_count=completed_count,
        current_lesson=current_lesson,
        badges=badges,
        total_lessons=TOTAL_PROJECTS,
        show_welcome=session.get("show_welcome", False)
    )

@main_bp.route("/api/welcome-complete", methods=["POST"])
@login_required
def welcome_complete():
    mark_first_login_complete(session["user_id"])
    session["show_welcome"] = False
    return jsonify({"ok": True})

@main_bp.route("/api/log-activity", methods=["POST"])
@login_required
def log_activity_route():
    data = request.get_json()
    lesson_key = data.get("lesson_key")
    duration = data.get("duration_seconds", 0)
    if lesson_key and duration > 5:
        log_activity(session["user_id"], lesson_key, int(duration))
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

@main_bp.route("/open-coding")
@login_required
def open_coding():
    return render_template("open_coding.html")

@main_bp.route("/download")
def download_page():
    return render_template("download.html")

@main_bp.route("/privacy")
def privacy():
    return render_template("privacy.html")

@main_bp.route("/terms")
def terms():
    return render_template("terms.html")

@main_bp.route("/privacy/contact", methods=["GET", "POST"])
@limiter.limit("3 per hour")
def privacy_contact():
    if request.method == "POST":
        name         = request.form.get("name", "").strip()
        email        = request.form.get("email", "").strip()
        request_type = request.form.get("request_type", "General inquiry")
        message      = request.form.get("message", "").strip()
        if not name or not email or not message:
            flash("Please fill in all required fields.")
            return render_template("privacy_contact.html")
        body = (
            f"<h3>Privacy / Data Request</h3>"
            f"<p><strong>Name:</strong> {name}</p>"
            f"<p><strong>Email:</strong> {email}</p>"
            f"<p><strong>Request type:</strong> {request_type}</p>"
            f"<p><strong>Message:</strong><br>{message}</p>"
        )
        http_requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {RESEND_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "from": f"KidsCode Privacy Form <{_PRIVACY_EMAIL}>",
                "to": _PRIVACY_TO,
                "reply_to": email,
                "subject": f"[Privacy Request] {request_type} — {name}",
                "html": body
            }
        )
        flash("Your request has been received. We will respond within 30 days.")
        return redirect(url_for("main.privacy_contact"))
    return render_template("privacy_contact.html")
