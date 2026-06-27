from flask import Blueprint, request, session, render_template, redirect, url_for, flash
from utils.decorators import login_required
from utils.deletion import request_account_deletion

account_bp = Blueprint('account', __name__)


@account_bp.route("/account/delete", methods=["GET", "POST"])
@login_required
def request_deletion():
    if session.get("is_admin"):
        flash("Admin accounts cannot be self-deleted. Remove admin status first.")
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        confirm = request.form.get("confirm", "")
        if confirm != "DELETE":
            flash("Type DELETE exactly to confirm.")
            return render_template("account_delete.html")

        request_account_deletion(session["user_id"])
        session.clear()
        return redirect(url_for("account.deletion_confirmed"))

    return render_template("account_delete.html")


@account_bp.route("/account/delete/confirmed")
def deletion_confirmed():
    return render_template("account_delete_confirmed.html")
