import datetime
from flask import Blueprint, request, session, render_template, flash, redirect, url_for
from utils.decorators import login_required, teacher_required
from utils.auth import get_students_for_parent, create_student_for_teacher, reset_student_password
from utils.progression import get_completed_lessons
from utils.deletion import request_account_deletion

teacher_bp = Blueprint('teacher', __name__)

@teacher_bp.route("/teacher", methods=["GET", "POST"])
@login_required
@teacher_required
def teacher_dashboard():
    students = get_students_for_parent(session["user_id"])

    from utils.lessons import LESSONS
    total = len([l for l in LESSONS if l["key"] != "challenge_one"])
    for s in students:
        completed = get_completed_lessons(s["id"])
        s["completed_count"] = len(completed)
        s["total"] = total
        s["progress_pct"] = int((len(completed) / total) * 100) if total else 0

    error = None
    success = None

    if request.method == "POST":
        action = request.form.get("action")

        if action == "create":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            if not username:
                error = "Username is required."
            else:
                _, _, err = create_student_for_teacher(session["user_id"], username, password or None)
                if err:
                    error = err
                else:
                    success = f"Account created for {username}!"
                    students = get_students_for_parent(session["user_id"])
                    for s in students:
                        completed = get_completed_lessons(s["id"])
                        s["completed_count"] = len(completed)
                        s["total"] = total
                        s["progress_pct"] = int((len(completed) / total) * 100) if total else 0

        elif action == "reset_password":
            student_id = request.form.get("student_id")
            new_password = request.form.get("new_password", "")
            if reset_student_password(student_id, new_password):
                success = "Password reset successfully."
            else:
                error = "Failed to reset password."

        elif action == "request_student_deletion":
            student_id = request.form.get("student_id")
            linked = [s for s in students if s["id"] == student_id]
            if linked:
                request_account_deletion(student_id)
                success = f"Deletion scheduled for {linked[0]['username']}. Data removed within 30 days."
                students = get_students_for_parent(session["user_id"])
                for s in students:
                    completed = get_completed_lessons(s["id"])
                    s["completed_count"] = len(completed)
                    s["total"] = total
                    s["progress_pct"] = int((len(completed) / total) * 100) if total else 0
            else:
                error = "Student not found."

    return render_template(
        "teacher.html",
        students=students,
        student_count=len(students),
        error=error,
        success=success,
        show_welcome=session.get("show_welcome", False),
    )
