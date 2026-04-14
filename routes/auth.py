from flask import Blueprint, request, session, render_template, redirect, url_for, flash
from extensions import limiter
from utils.auth import (
    get_user_by_username, check_password, create_user,
    hash_password, send_verification_email, verify_token,
    resend_verification_email, create_reset_token, send_reset_email,
    verify_reset_token, reset_password_with_token, mark_first_login_complete
)
from utils.progression import seed_first_lesson

auth_bp = Blueprint('auth', __name__)

@auth_bp.route("/login", methods=["GET", "POST"])
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
        session["show_welcome"] = not user.get("first_login_completed", False)
        session.permanent = True
        seed_first_lesson(user["id"])
        if user["is_parent"]:
            return redirect(url_for("parent.parent_dashboard"))
        return redirect(url_for("main.dashboard"))
    return render_template("login.html")

@auth_bp.route("/register", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def register():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        is_parent_val = request.form.get("is_parent", "")
        
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
        session["pending_email"] = email
        return redirect(url_for("auth.check_email"))
    return render_template("register.html")

@auth_bp.route("/verify/<token>")
def verify(token):
    if verify_token(token):
        flash("Email verified! You can now log in.")
        return redirect(url_for("auth.login"))
    flash("Invalid or expired verification link")
    return redirect(url_for("auth.login"))

@auth_bp.route("/check-email")
def check_email():
    email = session.get("pending_email", "")
    return render_template("check_email.html", email=email)

@auth_bp.route("/resend-verification", methods=["POST"])
@limiter.limit("3 per hour")
def resend_verification():
    email = request.form.get("email", "").strip().lower()
    if not email:
        flash("Email address is required")
        return redirect(url_for("auth.check_email"))
    success, err = resend_verification_email(email)
    if err:
        flash(err)
    else:
        flash("Verification email sent! Check your inbox.")
    return redirect(url_for("auth.check_email"))

@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))

@auth_bp.route("/forgot-password", methods=["GET", "POST"])
@limiter.limit("5 per minute")
@limiter.limit("10 per hour")
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        token, err = create_reset_token(email)
        if err:
            flash(err)
            return render_template("forgot_password.html")
        send_reset_email(email, token)
        flash("Reset link sent! Check your email.")
        return redirect(url_for("auth.login"))
    return render_template("forgot_password.html")

@auth_bp.route("/reset-password/<token>", methods=["GET", "POST"])
@limiter.limit("10 per minute")
def reset_password(token):
    user, err = verify_reset_token(token)
    if err:
        flash(err)
        return redirect(url_for("auth.forgot_password"))
    
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
        return redirect(url_for("auth.login"))
    
    return render_template("reset_password.html", token=token)
