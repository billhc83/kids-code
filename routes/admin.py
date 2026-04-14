import os
import requests
from flask import Blueprint, request, session, render_template, redirect, url_for, flash, current_app
from utils.decorators import login_required, admin_required
from utils.feedback import add_message, delete_thread, get_all_threads
from utils.challenges import get_all_submissions, review_submission
from utils.activity import get_most_active_users, get_all_activity
from utils.progression import get_completed_lessons
from config import SUPABASE_URL, SUPABASE_KEY

admin_bp = Blueprint('admin', __name__)

CHALLENGE_UNLOCKS = {
    "challenge_one": "project_eleven",
    # add more as needed
}

@admin_bp.route("/admin", methods=["GET", "POST"])
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

        return redirect(url_for("admin.admin_dashboard"))

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

@admin_bp.route("/admin/preset-builder")
@login_required
@admin_required
def preset_builder():
    return render_template("admin/preset_builder.html")

@admin_bp.route("/admin/step-builder")
@login_required
@admin_required
def step_builder():
    static_folder = current_app.static_folder or "static"
    graphics_dir = os.path.join(static_folder, "graphics")
    graphics = sorted([
        f for f in os.listdir(graphics_dir)
        if f.lower().endswith(('.png', '.jpg', '.jpeg'))
    ]) if os.path.exists(graphics_dir) else []
    return render_template("admin/step_builder.html", graphics=graphics)

@admin_bp.route("/admin/sim-builder")
@login_required
@admin_required
def sim_builder():
    return render_template("admin/sim_builder.html")

@admin_bp.route("/admin/step-builder-preview", methods=["POST"])
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
