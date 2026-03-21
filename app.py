from flask import Flask, render_template, session, request, redirect, url_for, flash, abort
from config import SECRET_KEY
from utils.auth import (
    get_user_by_username, check_password, create_user,
    hash_password, send_verification_email, verify_token,
    get_students_for_parent, create_student_for_parent,
    reset_student_password, reset_password_with_token,
    create_reset_token, send_reset_email, verify_reset_token
)
from utils.progression import (
    complete_lesson, is_unlocked, seed_first_lesson,
    get_user_progression, get_completed_lessons
)
from utils.decorators import login_required, admin_required, parent_required
from utils.lessons import get_lesson, get_sidebar_groups, LESSON_BY_KEY
from utils.hover_zoom import hover_zoom_html
from utils.badges import check_and_award_badges, BADGE_DEFINITIONS

from utils.feedback import (
    get_threads_for_user, create_thread, add_message,
    delete_thread, get_all_threads, CATEGORIES,
    notify_discord_feedback
)
from config import SUPABASE_URL, SUPABASE_KEY

from utils.assembly_guide_flask import render_assembly_guide
from utils.contents_flask import DRAWER_CONTENT
from utils.block_builder import get_builder_html
import requests
from utils.code_breaker import serial_monitor
from utils.project_one import STEPS as p1_steps, CIRCUIT_IMAGE as p1_image, PAGE_TITLE as p1_title
from utils.project_eleven import STEPS as p11_steps, CIRCUIT_IMAGE as p11_image, PAGE_TITLE as p11_title
from utils.project_three import STEPS as p3_steps, CIRCUIT_IMAGE as p3_image, PAGE_TITLE as p3_title
from utils.project_four import STEPS as p4_steps, CIRCUIT_IMAGE as p4_image, PAGE_TITLE as p4_title
from utils.project_six import STEPS as p6_steps, CIRCUIT_IMAGE as p6_image, PAGE_TITLE as p6_title
from utils.project_seven import STEPS as p7_steps, CIRCUIT_IMAGE as p7_image, PAGE_TITLE as p7_title
from utils.project_eight import STEPS as p8_steps, CIRCUIT_IMAGE as p8_image, PAGE_TITLE as p8_title
from utils.project_nine import STEPS as p9_steps, CIRCUIT_IMAGE as p9_image, PAGE_TITLE as p9_title
from utils.project_ten import STEPS as p10_steps, CIRCUIT_IMAGE as p10_image, PAGE_TITLE as p10_title
from utils.project_twelve import STEPS as p12_steps, CIRCUIT_IMAGE as p12_image, PAGE_TITLE as p12_title, BANNER_IMAGE as p12_banner
from utils.project_thirteen import STEPS as p13_steps, CIRCUIT_IMAGE as p13_image, PAGE_TITLE as p13_title

app = Flask(__name__)
app.secret_key = SECRET_KEY

@app.context_processor
def inject_globals():
    unlocked = []
    sidebar_standalone = []
    sidebar_groups = {}
    if "user_id" in session:
        unlocked = get_user_progression(session["user_id"])
        sidebar_standalone, sidebar_groups = get_sidebar_groups(unlocked)
    return {
        "unlocked_lessons": unlocked,
        "sidebar_standalone": sidebar_standalone,
        "sidebar_groups": sidebar_groups,
        "current_endpoint": request.endpoint,
        "hover_zoom": hover_zoom_html,
        "lesson_by_key": LESSON_BY_KEY
    }

@app.route("/")
def index():
    if "user_id" in session:
        if session.get("is_parent"):
            return redirect(url_for("parent_dashboard"))
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = get_user_by_username(username)
        if not user:
            flash("Username not found")
            return render_template("login.html")
        if not check_password(password, user["password_hash"]):
            flash("Incorrect password")
            return render_template("login.html")
        if not user["is_verified"]:
            flash("Please verify your email before logging in")
            return render_template("login.html")
        session["user_id"] = user["id"]
        session["username"] = user["username"]
        session["is_parent"] = user["is_parent"]
        session["is_admin"] = user["is_admin"]
        seed_first_lesson(user["id"])
        if user["is_parent"]:
            return redirect(url_for("parent_dashboard"))
        return redirect(url_for("dashboard"))
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        is_parent_val = request.form.get("is_parent", "")
        
        # Must select an account type
        if is_parent_val not in ("true", "false"):
            flash("Please select an account type")
            return render_template("register.html")
        
        is_parent = is_parent_val == "true"

        if get_user_by_username(username):
            flash("Username already taken")
            return render_template("register.html")
        
        password_hash = hash_password(password)
        user = create_user(email, username, password_hash, is_parent)
        if not user:
            flash("Registration failed, please try again")
            return render_template("register.html")
        
        send_verification_email(email, user["verification_token"])
        return redirect(url_for("check_email"))
    return render_template("register.html")

@app.route("/verify/<token>")
def verify(token):
    if verify_token(token):
        flash("Email verified! You can now log in.")
        return redirect(url_for("login"))
    flash("Invalid or expired verification link")
    return redirect(url_for("login"))

@app.route("/check-email")
def check_email():
    return render_template("check_email.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

from utils.badges import get_user_badges, BADGE_DEFINITIONS

@app.route("/dashboard")
@login_required
def dashboard():
    completed = get_completed_lessons(session["user_id"])
    user_badges = get_user_badges(session["user_id"])
    unlocked = get_user_progression(session["user_id"])

    # Find current lesson — first unlocked but not completed
    current_lesson = None
    from utils.lessons import LESSONS
    for lesson in LESSONS:
        if lesson["key"] in unlocked and lesson["key"] not in completed:
            current_lesson = lesson
            break

    # Build badge display list
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

@app.route("/parent", methods=["GET", "POST"])
@login_required
@parent_required
def parent_dashboard():
    students = get_students_for_parent(session["user_id"])
    
    # Add progress info to each student
    from utils.lessons import LESSONS
    total = len([l for l in LESSONS if l["key"] != "challenge_one"])
    for s in students:
        completed = get_completed_lessons(s["id"])
        s["completed_count"] = len(completed)
        s["total"] = total
        s["progress_pct"] = int((len(completed) / total) * 100)

    error = None
    success = None

    if request.method == "POST":
        action = request.form.get("action")

        if action == "create":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            student, err = create_student_for_parent(
                session["user_id"], username, password
            )
            if err:
                error = err
            else:
                success = f"Account created for {username}!"
                students = get_students_for_parent(session["user_id"])
                for s in students:
                    completed = get_completed_lessons(s["id"])
                    s["completed_count"] = len(completed)
                    s["total"] = total
                    s["progress_pct"] = int((len(completed) / total) * 100)

        elif action == "reset_password":
            student_id = request.form.get("student_id")
            new_password = request.form.get("new_password", "")
            if reset_student_password(student_id, new_password):
                success = "Password reset successfully"
            else:
                error = "Failed to reset password"

    return render_template(
        "parent.html",
        students=students,
        student_count=len(students),
        max_students=3,
        error=error,
        success=success
    )

@app.route("/admin", methods=["GET", "POST"])
@login_required
@admin_required
def admin_dashboard():
    if request.method == "POST":
        action = request.form.get("action")
        
        if action == "reply":
            thread_id = request.form.get("thread_id")
            message = request.form.get("message", "").strip()
            if thread_id and message:
                add_message(
                    thread_id,
                    session["user_id"],
                    session["username"],
                    message,
                    is_admin=True
                )
                flash("Reply sent!")

        elif action == "delete":
            thread_id = request.form.get("thread_id")
            if thread_id:
                delete_thread(thread_id)
                flash("Thread deleted.")

        elif action == "resolve":
            thread_id = request.form.get("thread_id")
            if thread_id:
                requests.patch(
                    f"{SUPABASE_URL}/rest/v1/feedback_threads"
                    f"?id=eq.{thread_id}",
                    headers={
                        "apikey": SUPABASE_KEY,
                        "Authorization": f"Bearer {SUPABASE_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={"status": "resolved"}
                )
                flash("Thread marked as resolved.")

        return redirect(url_for("admin_dashboard"))  # ← inside POST block

    # GET request reaches here
    threads = get_all_threads()
    return render_template("admin/index.html", threads=threads)


# ── Complete lesson ───────────────────────────────────────────────────────────
@app.route("/lessons/complete", methods=["POST"])
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
    return redirect(url_for("dashboard"))

# ── Dynamic lesson route ──────────────────────────────────────────────────────

from utils.assembly_guide_flask import render_assembly_guide

@app.route("/lessons/<lesson_key>")
@login_required
def lesson(lesson_key):
    lesson_data = get_lesson(lesson_key)
    if not lesson_data:
        abort(404)
    if not is_unlocked(session["user_id"], lesson_key):
        flash("Complete the previous project to unlock this one")
        return redirect(url_for("dashboard"))

    extra = {}

    # Assembly guide — only if lesson has step data
    if lesson_key == "project_one":
            extra["assembly_guide_html"] = render_assembly_guide(
                p1_image, p1_steps, p1_title
            )
    elif lesson_key == "project_two":
            extra["assembly_guide_html"] = render_assembly_guide(
                p1_image, p1_steps, "Project 2: Blinking Beacon!"
            )
    elif lesson_key == "project_three":
            extra["assembly_guide_html"] = render_assembly_guide(
                p3_image, p3_steps, p3_title
            )
    elif lesson_key == "project_four":
            extra["assembly_guide_html"] = render_assembly_guide(
                p4_image, p4_steps, p4_title
            )
    elif lesson_key == "project_five":
            pass  # no assembly guide for this project
    elif lesson_key == "project_six":
            extra["assembly_guide_html"] = render_assembly_guide(
                p6_image, p6_steps, p6_title
            )
    elif lesson_key == "project_seven":
            extra["assembly_guide_html"] = render_assembly_guide(
                p7_image, p7_steps, p7_title
            )
    elif lesson_key == "project_eight":
            extra["assembly_guide_html"] = render_assembly_guide(
                p8_image, p8_steps, p8_title
            )
    elif lesson_key == "project_nine":
            extra["assembly_guide_html"] = render_assembly_guide(
                p9_image, p9_steps, p9_title
            )
    elif lesson_key == "project_ten":
            extra["assembly_guide_html"] = render_assembly_guide(
                p10_image, p10_steps, p10_title
            )
    elif lesson_key == "project_eleven":
            extra["assembly_guide_html"] = render_assembly_guide(
                p11_image, p11_steps, p11_title
            )
    elif lesson_key == "project_twelve":
            extra["assembly_guide_html"] = render_assembly_guide(
                p12_image, p12_steps, p12_title
            )
    elif lesson_key == "project_thirteen":
            extra["assembly_guide_html"] = render_assembly_guide(
                p13_image, p13_steps, p13_title
            )
    elif lesson_key == "project_fourteen_part_one":
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
    elif lesson_key == "project_fourteen_part_two":
            pass

    # Block builder — only if explicitly set in registry
    preset = lesson_data.get("block_builder")
    if preset:
        from utils.block_builder import get_builder_html
        from utils.contents_flask import DRAWER_CONTENT
        from config import SUPABASE_URL, SUPABASE_KEY
        extra["block_builder_html"] = get_builder_html(
            preset=preset,
            drawer_content=DRAWER_CONTENT.get(preset),
            username=session.get("user_id"),
            page=lesson_key,
            pin_refs=preset,
            supabase_url=SUPABASE_URL,
            supabase_key=SUPABASE_KEY
        )

    return render_template(
        lesson_data["template"],
        lesson=lesson_data,
        lesson_key=lesson_key,
        **extra
    )
@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        token, err = create_reset_token(email)
        if err:
            flash(err)
            return render_template("forgot_password.html")
        send_reset_email(email, token)
        flash("Reset link sent! Check your email.")
        return redirect(url_for("login"))
    return render_template("forgot_password.html")

@app.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    user, err = verify_reset_token(token)
    if err:
        flash(err)
        return redirect(url_for("forgot_password"))
    
    if request.method == "POST":
        new_password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")
        if new_password != confirm:
            flash("Passwords do not match")
            return render_template("reset_password.html", token=token)
        success, err = reset_password_with_token(token, new_password)
        if err:
            flash(err)
            return render_template("reset_password.html", token=token)
        flash("Password reset successfully! You can now log in.")
        return redirect(url_for("login"))
    
    return render_template("reset_password.html", token=token)

@app.route("/feedback", methods=["GET", "POST"])
@login_required
def feedback():
    if session.get("is_parent"):
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
            return redirect(url_for("feedback"))
        return render_template(
            "feedback.html",
            threads=threads,
            categories=CATEGORIES
        )
    else:
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
            return redirect(url_for("feedback"))
        return render_template(
            "feedback.html",
            threads=threads,
            categories=CATEGORIES
        )
if __name__ == "__main__":
    app.run(debug=True, port=5001)