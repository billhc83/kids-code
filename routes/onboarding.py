import datetime
from flask import Blueprint, request, session, render_template, redirect, url_for
from utils.decorators import login_required
from utils.db_client import supabase

onboarding_bp = Blueprint('onboarding', __name__)

@onboarding_bp.route("/welcome/agree", methods=["GET", "POST"])
@login_required
def agree_tos():
    if not session.get("needs_tos_agreement"):
        return redirect(url_for("main.dashboard"))

    error = None
    if request.method == "POST":
        if not request.form.get("agree_tos"):
            error = "You must check the box to continue."
        else:
            agreed_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
            supabase.table("users").update({"agreed_at": agreed_at}).eq("id", session["user_id"]).execute()
            session["needs_tos_agreement"] = False
            if session.get("is_teacher"):
                return redirect(url_for("teacher.teacher_dashboard"))
            return redirect(url_for("main.dashboard"))

    return render_template("welcome_agree.html", error=error)
