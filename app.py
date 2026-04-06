from flask import Flask, render_template, session, request, redirect, url_for, flash, abort
import json
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
from config import SUPABASE_URL, SUPABASE_KEY, SUPABASE_ANON_KEY
from utils.challenges import get_all_submissions, review_submission
from utils.assembly_guide_flask import render_assembly_guide
from utils.contents_flask import DRAWER_CONTENT
from utils.block_builder import get_builder_html
import requests
from utils.code_breaker import serial_monitor
from utils.project_registry import PROJECTS

# Map challenge keys to what they unlock on approval
CHALLENGE_UNLOCKS = {
    "challenge_one": "project_eleven",
    # add more as needed
}

from datetime import timedelta


import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address



# In the login route, after setting session variables add:

app = Flask(__name__)
app.secret_key = SECRET_KEY
app.permanent_session_lifetime = timedelta(days=30)
app.json.sort_keys = False

def normalize_drawer_steps(steps):
    """Convert each step's tabs dict to an ordered list so JSON serialization preserves insertion order."""
    result = []
    for step in steps:
        s = dict(step)
        if isinstance(s.get('tabs'), dict):
            s['tabs'] = [{'id': k, **v} for k, v in s['tabs'].items()]
        result.append(s)
    return result
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=[],
    storage_uri="memory://"
)

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
@app.route("/ping")
def ping():
    return "ok", 200

@app.route("/")
def index():
    if "user_id" in session:
        if session.get("is_parent"):
            return redirect(url_for("parent_dashboard"))
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
@limiter.limit("10 per minute")
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
        session.permanent = True
        seed_first_lesson(user["id"])
        if user["is_parent"]:
            return redirect(url_for("parent_dashboard"))
        return redirect(url_for("dashboard"))
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
@limiter.limit("5 per minute")
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
            if "challenge" in lesson["key"]:
                continue
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

from utils.activity import get_most_active_users, get_all_activity
from utils.progression import get_completed_lessons

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
                add_message(thread_id, session["user_id"],
                           session["username"], message, is_admin=True)
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
                    f"{SUPABASE_URL}/rest/v1/feedback_threads?id=eq.{thread_id}",
                    headers={
                        "apikey": SUPABASE_KEY,
                        "Authorization": f"Bearer {SUPABASE_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={"status": "resolved"}
                )
                flash("Thread marked as resolved.")

        elif action == "review_challenge":
            submission_id = request.form.get("submission_id")
            user_id = request.form.get("user_id")
            challenge_key = request.form.get("challenge_key")
            status = request.form.get("status")
            feedback = request.form.get("feedback", "")
            next_key = CHALLENGE_UNLOCKS.get(challenge_key)
            review_submission(submission_id, status, feedback,
                            user_id, challenge_key, next_key)
            flash(f"Submission marked as {status}")

        elif action == "toggle_admin":
            user_id = request.form.get("user_id")
            is_admin = request.form.get("is_admin") == "true"
            requests.patch(
                f"{SUPABASE_URL}/rest/v1/users?id=eq.{user_id}",
                headers={
                    "apikey": SUPABASE_KEY,
                    "Authorization": f"Bearer {SUPABASE_KEY}",
                    "Content-Type": "application/json"
                },
                json={"is_admin": is_admin}
            )
            flash("Admin status updated.")

        elif action == "delete_user":
            user_id = request.form.get("user_id")
            requests.delete(
                f"{SUPABASE_URL}/rest/v1/users?id=eq.{user_id}",
                headers={
                    "apikey": SUPABASE_KEY,
                    "Authorization": f"Bearer {SUPABASE_KEY}"
                }
            )
            flash("User deleted.")

        return redirect(url_for("admin_dashboard"))

    # Fetch all data
    threads = get_all_threads()
    submissions = get_all_submissions()
    active_users = get_most_active_users()
    project_time = get_all_activity()

    # Fetch users with progress
    from utils.lessons import LESSONS
    total_lessons = len([l for l in LESSONS
                        if not l["key"].startswith("challenge")])
    users_resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/users?order=created_at.desc",
        headers={
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}"
        }
    )
    users = users_resp.json()
    for user in users:
        completed = get_completed_lessons(user["id"])
        user["completed_count"] = len(completed)
        user["total_lessons"] = total_lessons
        user["progress_pct"] = int((len(completed) / total_lessons) * 100)

    return render_template(
        "admin/index.html",
        threads=threads,
        submissions=submissions,
        users=users,
        active_users=active_users,
        project_time=project_time
    )

from utils.activity import log_activity

@app.route("/api/log-activity", methods=["POST"])
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
    # Fetch lesson data
    lesson_data = get_lesson(lesson_key)
    if not lesson_data:
        abort(404)

    # Check if lesson is unlocked for user
    if not is_unlocked(session["user_id"], lesson_key):
        flash("Complete the previous project to unlock this one")
        return redirect(url_for("dashboard"))

    extra = {}

    # --- Assembly guides handled dynamically via PROJECTS dict ---
    project_data = PROJECTS.get(lesson_key)
    if project_data:
        meta = project_data.get("meta", {})
        img = meta.get("circuit_image") or project_data.get("image")
        steps = project_data.get("steps", [])
        title = meta.get("title") or project_data.get("title")
        if img and steps:
            extra["assembly_guide_html"] = render_assembly_guide(img, steps, title)

    # --- Special cases ---
    if lesson_key == "project_five":
        pass  # no assembly guide

    elif lesson_key == "project_thirteen":
        pass  # no assembly guide

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

    elif lesson_key in ["project_fourteen_part_two", "project_fourteen_part_three"]:
        pass  # special cases with no guide yet
    # Block builder — only if explicitly set in registry
    preset = lesson_data.get("block_builder")
    if preset:
        from utils.block_builder import get_builder_html
        from utils.contents_flask import DRAWER_CONTENT
        from config import SUPABASE_URL, SUPABASE_KEY

        # Update FAB to point to the standalone IDE instead of just the blocks
        base_url = request.host_url.rstrip('/')
        ide_url = f"{base_url}/standalone_ide/{preset}?preset={preset}&page={lesson_key}"

        # Find drawer content: check project file first, then fallback to global
        drawer_content = None
        if project_data and "drawer" in project_data:
            d = project_data["drawer"]
            if isinstance(d, dict):
                drawer_content = d.get(preset) or d.get("default") or (d if "title" in d or "tabs" in d else None)
            else:
                drawer_content = d
        
        if not drawer_content:
            drawer_content = DRAWER_CONTENT.get(preset)

        # Ensure tab order is preserved for drawer content (check for dict to avoid list conversion error)
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
        
        # Provide drawer data to the interface
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
@app.route("/forgot-password", methods=["GET", "POST"])
@limiter.limit("5 per minute")
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

import os

@app.route("/admin/preset-builder")
@login_required
@admin_required
def preset_builder():
    return render_template("admin/preset_builder.html")

@app.route("/admin/step-builder")
@login_required
@admin_required
def step_builder():
    static_folder = app.static_folder or "static"
    graphics_dir = os.path.join(static_folder, "graphics")
    graphics = sorted([
        f for f in os.listdir(graphics_dir)
        if f.lower().endswith(('.png', '.jpg', '.jpeg'))
    ]) if os.path.exists(graphics_dir) else []
    return render_template("admin/step_builder.html", graphics=graphics)

from utils.challenges import (
    get_submission, submit_challenge,
    get_all_submissions, review_submission
)

@app.route("/challenges/<challenge_key>", methods=["GET", "POST"])
@login_required
def challenge(challenge_key):
    if session.get("is_parent"):
        return redirect(url_for("parent_dashboard"))

    from utils.lessons import get_lesson
    lesson_data = get_lesson(challenge_key)
    if not lesson_data:
        abort(404)

    from utils.progression import is_unlocked
    if not is_unlocked(session["user_id"], challenge_key):
        flash("Complete the previous projects to unlock this challenge")
        return redirect(url_for("dashboard"))

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
                f"Challenge: {challenge_key}")

    return render_template(
        lesson_data["template"],
        lesson=lesson_data,
        lesson_key=challenge_key,
        submission=submission,
        error=error,
        success=success
    )


@app.route("/admin/step-builder-preview", methods=["POST"])
@login_required
@admin_required
def step_builder_preview():
    from PIL import Image, ImageDraw
    from io import BytesIO
    from flask import send_file
    data = request.get_json()
    image_src = data.get("image_src")
    highlights = data.get("highlights", [])

    if not image_src:
        img = Image.new("RGB", (400, 200), "#f4f8ff")
    elif image_src.startswith("data:"):
        import base64
        header, b64data = image_src.split(",", 1)
        img_bytes = base64.b64decode(b64data)
        img = Image.open(BytesIO(img_bytes)).convert("RGBA")
    else:
        path = image_src.lstrip("/")
        try:
            img = Image.open(path).convert("RGBA")
        except Exception:
            img = Image.new("RGB", (400, 200), "#f4f8ff")

    draw = ImageDraw.Draw(img)
    ORANGE = (255, 165, 0)
    BLUE = (33, 150, 243)

    for h in highlights:
        shape = h.get("shape")
        pos = h.get("pos")
        if shape == "rect" and len(pos) == 4:
            draw.rectangle([pos[0],pos[1],pos[2],pos[3]], outline=ORANGE, width=4)
        elif shape == "circle" and len(pos) == 2:
            r = h.get("radius", 60)
            draw.ellipse([pos[0]-r, pos[1]-r, pos[0]+r, pos[1]+r], outline=ORANGE, width=4)
        elif shape == "polyline":
            pts = [tuple(p) for p in pos]
            w = h.get("width", 20)
            if len(pts) >= 2:
                for i in range(len(pts)-1):
                    draw.line([pts[i], pts[i+1]], fill=BLUE, width=w)
    # Draw labels
    for lb in data.get("labels", []):
        try:
            from PIL import ImageFont
            font = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                lb.get("font_size", 16)
            )
        except:
            font = ImageFont.load_default()
        lx, ly = lb["pos"][0], lb["pos"][1]
        text = lb.get("text", "")
        bbox = draw.textbbox((0,0), text, font=font)
        tw, th = bbox[2]-bbox[0]+14, bbox[3]-bbox[1]+8
        draw.rounded_rectangle([(lx-6,ly-4),(lx+tw,ly+th)], radius=6, fill=(20,20,20))
        draw.text((lx, ly), text, fill=(255,255,255), font=font)

    buf = BytesIO()
    img.convert("RGB").save(buf, format="PNG")
    buf.seek(0)
    return send_file(buf, mimetype="image/png")

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

@app.route("/parse", methods=["POST"])
def parse():
    from utils.block_parser import parse_sketch
    data = request.get_json()
    code = data.get("code", "")
    return parse_sketch(code, fill_conditions=True, fill_values=True)

@app.route("/builder")
@login_required
def builder_endpoint():
    from utils.block_builder_config import build_config
    
    preset = request.args.get("preset", "codebreaker")
    page = request.args.get("page") or preset

    config = build_config(
        preset=preset,
        username=session.get("user_id"),
        page=page,
        supabase_url=SUPABASE_URL,
        supabase_key=SUPABASE_ANON_KEY,
        is_overlay=False,
    )
    print(f"[DEBUG] builder_endpoint: preset={preset}, page={page}")
    print(f"[DEBUG] CONFIG MODE: {config.get('mode')}")
    print(f"[DEBUG] CONFIG STEPS: {len(config.get('steps') or [])}")
    print(f"[DEBUG] CONFIG BLOCKS length: {len(str(config.get('blocks')))}")
    config_json = json.dumps(config).replace('</', '<\\/')
    print("[DEBUG] STEP 1 FULL:", json.dumps(config['steps'][0] if config.get('steps') else config.get('blocks'), indent=2))
    print("[DEBUG] FULL CONFIG JSON:")
    print(config_json[:500])
    return render_template("block_builder_fragment.html", config=config_json)

@app.route("/preset/<name>")
@login_required
def get_preset(name):
    from utils.block_parser import parse_steps, parse_sketch
    from utils.project_registry import PROJECTS
    from utils.presets import PRESETS
    from utils.contents_flask import DRAWER_CONTENT

    sketch_code = None
    drawer_content = None
    default_view = "blocks"
    fill_values = False
    fill_conditions = False

    # Try new registry format first
    if name in PROJECTS:
        p = PROJECTS[name]
        preset_obj = p.get("presets", {}).get("default", {})
        if isinstance(preset_obj, dict):
            sketch_code = preset_obj.get("sketch")
            default_view = preset_obj.get("default_view", "blocks")
            fill_values = preset_obj.get("fill_values", False)
            fill_conditions = preset_obj.get("fill_conditions", False)
        else:
            sketch_code = preset_obj

        d = p.get("drawer")
        if d:
            if isinstance(d, dict):
                drawer_content = d.get(name) or d.get("default") or (d if "title" in d or "tabs" in d else None)
            else:
                drawer_content = d
    else:
        for p in PROJECTS.values():
            if "presets" in p and name in p["presets"]:
                preset_obj = p["presets"][name]
                if isinstance(preset_obj, dict):
                    sketch_code = preset_obj.get("sketch")
                    default_view = preset_obj.get("default_view", "blocks")
                    fill_values = preset_obj.get("fill_values", False)
                    fill_conditions = preset_obj.get("fill_conditions", False)
                else:
                    sketch_code = preset_obj
                d = p.get("drawer")
                if d:
                    if isinstance(d, dict):
                        drawer_content = d.get(name) or d.get("default") or (d if "title" in d or "tabs" in d else None)
                    else:
                        drawer_content = d
                break

    # Fallback to legacy global dicts
    if not sketch_code:
        preset = PRESETS.get(name)
        if not preset: abort(404)
        if isinstance(preset, dict):
            sketch_code = preset['sketch']
            default_view = preset.get('default_view', 'blocks')
            fill_values = preset.get('fill_values', False)
            fill_conditions = preset.get('fill_conditions', False)
        else:
            sketch_code = preset
        drawer_content = DRAWER_CONTENT.get(name)

    if '//>>' in sketch_code:
        progression_data = parse_steps(sketch_code)
        parsed_sketch = None
    else:
        progression_data = None
        parsed_sketch = parse_sketch(sketch_code, fill_conditions=fill_conditions, fill_values=fill_values)

    return {
        "sketch": sketch_code,
        "drawer_content": drawer_content,
        "default_view": default_view,
        "progression_data": progression_data,
        "parsed_sketch": parsed_sketch,
    }

@app.route("/standalone_ide/<preset>")
@login_required
def standalone_ide(preset):
    from utils.project_registry import PROJECTS
    from utils.contents_flask import DRAWER_CONTENT

    page = request.args.get("page") or preset
    drawer_content = None
    default_view = "blocks"

    # 1. Try project specified by 'page'
    if page in PROJECTS:
        proj = PROJECTS[page]
        d = proj.get("drawer")
        if d:
            if isinstance(d, dict):
                drawer_content = d.get(preset) or d.get("default") or (d if "title" in d or "tabs" in d else None)
            else:
                drawer_content = d
        
        # Look for default_view in the project presets
        p_data = proj.get("presets", {}).get(preset) or proj.get("presets", {}).get("default")
        if isinstance(p_data, dict):
            default_view = p_data.get("default_view", "blocks")
    
    # 2. Try searching all projects for this preset's drawer
    if not drawer_content:
        for p in PROJECTS.values():
            if "drawer" in p and isinstance(p["drawer"], dict) and preset in p["drawer"]:
                drawer_content = p["drawer"][preset]
                break

    # 3. Fallback to global drawer
    if not drawer_content:
        drawer_content = DRAWER_CONTENT.get(preset)

    # Ensure tab order is preserved for drawer content (check for dict to avoid list conversion error)
    if drawer_content and isinstance(drawer_content, dict) and isinstance(drawer_content.get("tabs"), dict):
        drawer_content = drawer_content.copy()
        drawer_content["tabs"] = list(drawer_content["tabs"].values())

    drawer_steps = []
    if isinstance(drawer_content, list):
        drawer_steps = normalize_drawer_steps(drawer_content)
    elif isinstance(drawer_content, dict):
        drawer_steps = normalize_drawer_steps(drawer_content.get("steps") or [drawer_content])
        
    return render_template(
        "components/arduino_interface.html",
        drawer_steps=drawer_steps,
        preset=preset,
        default_view=default_view
    )

if __name__ == "__main__":
    app.run(debug=True, port=5001)