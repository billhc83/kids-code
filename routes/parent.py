from flask import Blueprint, request, session, render_template
from utils.decorators import login_required, parent_required
from utils.auth import get_students_for_parent, create_student_for_parent, reset_student_password
from utils.progression import get_completed_lessons

parent_bp = Blueprint('parent', __name__)

@parent_bp.route("/parent", methods=["GET", "POST"])
@login_required
@parent_required
def parent_dashboard():
    students = get_students_for_parent(session["user_id"])
    
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
