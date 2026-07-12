import datetime
from flask import Blueprint, request, session, render_template, flash, redirect, url_for
from utils.decorators import login_required, parent_required
from utils.auth import (
    get_students_for_parent, create_student_for_parent, reset_student_password,
    mark_first_login_complete, get_user_by_id
)
from utils.progression import get_completed_lessons
from utils.deletion import request_account_deletion
from utils.referrals import get_or_create_parent_referral_code, VALID_REDEMPTION_SUBSCRIPTION_STATUSES
from config import REFERRAL_REWARD_MONTHS

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
            if not request.form.get("parent_consent"):
                error = "You must confirm parental consent before creating a student account."
            else:
                consent_given_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
                student, err = create_student_for_parent(
                    session["user_id"], username, password,
                    consent_given_at=consent_given_at
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

        elif action == "request_student_deletion":
            student_id = request.form.get("student_id")
            # Verify this student belongs to the requesting parent
            linked = [s for s in students if s["id"] == student_id]
            if linked:
                request_account_deletion(student_id)
                success = f"Account deletion scheduled for {linked[0]['username']}. All data will be removed within 30 days."
                students = get_students_for_parent(session["user_id"])
                for s in students:
                    completed = get_completed_lessons(s["id"])
                    s["completed_count"] = len(completed)
                    s["total"] = total
                    s["progress_pct"] = int((len(completed) / total) * 100)
            else:
                error = "Student account not found."

    # Referral code: only rendered/revealed to a parent whose subscription is
    # currently active/past_due, per "Parent referral code provisioning" in
    # docs/superpowers/specs/2026-07-12-referral-codes-design.md — not deleted
    # or regenerated on lapse, just not shown while inert.
    referral_code = None
    parent_user = get_user_by_id(session["user_id"])
    if parent_user and parent_user.get("subscription_status") in VALID_REDEMPTION_SUBSCRIPTION_STATUSES:
        code_row = get_or_create_parent_referral_code(session["user_id"], REFERRAL_REWARD_MONTHS)
        referral_code = code_row["code"] if code_row else None

    return render_template(
        "parent.html",
        students=students,
        student_count=len(students),
        max_students=3,
        error=error,
        success=success,
        show_welcome=session.get("show_welcome", False),
        referral_code=referral_code,
        referral_reward_months=REFERRAL_REWARD_MONTHS,
    )
