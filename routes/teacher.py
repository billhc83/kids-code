import datetime
from flask import Blueprint, request, session, render_template, flash, redirect, url_for, abort
from utils.decorators import login_required, teacher_required
from utils.auth import get_students_for_parent, create_student_for_teacher, reset_student_password
from utils.progression import get_completed_lessons
from utils.deletion import request_account_deletion
from utils.classes import (
    create_class, get_classes_for_teacher, get_class, get_roster,
    enroll_student, remove_student, create_assignment, get_assignments_for_class,
)
from utils.lessons import LESSONS

teacher_bp = Blueprint('teacher', __name__)

CATALOG = [l for l in LESSONS if l["key"] != "challenge_one"]

@teacher_bp.route("/teacher", methods=["GET", "POST"])
@login_required
@teacher_required
def teacher_dashboard():
    students = get_students_for_parent(session["user_id"])

    total = len(CATALOG)
    for s in students:
        completed = get_completed_lessons(s["id"])
        s["completed_count"] = len(completed)
        s["total"] = total
        s["progress_pct"] = int((len(completed) / total) * 100) if total else 0

    classes = get_classes_for_teacher(session["user_id"])
    for c in classes:
        c["roster_count"] = len(get_roster(c["id"]))

    error = None
    success = None

    if request.method == "POST":
        action = request.form.get("action")

        if action == "create_class":
            name = request.form.get("class_name", "").strip()
            if not name:
                error = "Class name is required."
            else:
                create_class(session["user_id"], session["username"], name)
                success = f"Class \"{name}\" created!"
                classes = get_classes_for_teacher(session["user_id"])
                for c in classes:
                    c["roster_count"] = len(get_roster(c["id"]))

        elif action == "create":
            # Lowercased so this shares the same case-insensitive username space as
            # self-registration (routes/auth.py) — otherwise e.g. a teacher-created
            # "Sam" and a self-registered "sam" could collide only in appearance,
            # or a family logging in with different casing than was typed at creation.
            username = request.form.get("username", "").strip().lower()
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
            linked = [s for s in students if s["id"] == student_id]
            if not linked:
                error = "Student not found."
            elif reset_student_password(student_id, new_password):
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
        classes=classes,
        error=error,
        success=success,
        show_welcome=session.get("show_welcome", False),
    )


@teacher_bp.route("/teacher/classes/<class_id>", methods=["GET", "POST"])
@login_required
@teacher_required
def class_detail(class_id):
    cls = get_class(class_id)
    if not cls or cls["teacher_id"] != session["user_id"]:
        abort(404)

    all_students = get_students_for_parent(session["user_id"])

    error = None
    success = None

    if request.method == "POST":
        action = request.form.get("action")

        if action == "enroll_student":
            student_id = request.form.get("student_id")
            linked = [s for s in all_students if s["id"] == student_id]
            if not linked:
                error = "Student not found."
            else:
                enroll_student(class_id, student_id)
                success = f"{linked[0]['username']} enrolled."

        elif action == "remove_student":
            enrollment_id = request.form.get("enrollment_id")
            roster_ids = [s["enrollment_id"] for s in get_roster(class_id)]
            if enrollment_id not in roster_ids:
                error = "Enrollment not found."
            else:
                remove_student(enrollment_id)
                success = "Student removed from class."

        elif action == "push_assignment":
            project_key = request.form.get("project_key")
            target = request.form.get("target", "")
            due_at = request.form.get("due_at") or None
            valid_keys = {l["key"] for l in CATALOG}

            if project_key not in valid_keys:
                error = "Pick a valid project."
            elif target == "class":
                create_assignment(project_key, "class", class_id, session["user_id"], due_at)
                success = f"Pushed \"{project_key}\" to the whole class."
            else:
                roster_ids = {s["id"] for s in get_roster(class_id)}
                if target not in roster_ids:
                    error = "Pick a valid student."
                else:
                    create_assignment(project_key, "student", target, session["user_id"], due_at)
                    success = f"Pushed \"{project_key}\" to one student."

    roster = get_roster(class_id)
    roster_ids = [s["id"] for s in roster]
    enrollable = [s for s in all_students if s["id"] not in roster_ids]
    assignments = get_assignments_for_class(class_id, roster_ids)
    catalog_by_key = {l["key"]: l["title"] for l in CATALOG}
    for a in assignments:
        a["project_title"] = catalog_by_key.get(a["project_key"], a["project_key"])

    return render_template(
        "teacher_class.html",
        cls=cls,
        roster=roster,
        enrollable=enrollable,
        catalog=CATALOG,
        assignments=assignments,
        error=error,
        success=success,
    )
