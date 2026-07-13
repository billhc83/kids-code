from flask import Blueprint, request, session, render_template, redirect, url_for, flash
from extensions import limiter
import datetime
from utils.auth import (
    get_user_by_username, get_user_by_email, check_password, create_user,
    hash_password, verify_token,
    resend_verification_email, create_reset_token, send_reset_email,
    verify_reset_token, reset_password_with_token, mark_first_login_complete,
    is_legacy_hash, upgrade_password_hash, get_linking_parent,
    create_registration_invite, get_valid_registration_invite,
    mark_registration_invite_used, send_registration_invite_email
)
from utils.progression import seed_first_lesson
from utils.referrals import resolve_valid_referral_code

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
        if is_legacy_hash(user["password_hash"]):
            upgrade_password_hash(user["id"], password)
        # Checked before is_verified: a standard signup's verification email isn't sent
        # until the Stripe webhook fires (see routes/billing.py's handle_checkout_completed),
        # so an unpaid account is always both unverified AND subscription-pending. Checking
        # subscription first avoids telling someone "check your email for a link" when no
        # link was ever sent — the real blocker is the missing subscription, not email.
        if user["user_type"] == "standard" and user.get("subscription_status") not in ("active", "past_due"):
            # Parent-created student sub-accounts (utils.auth.create_student_for_parent)
            # never have their own Stripe subscription — their access rides on the
            # linking parent's live status instead of their own (frozen) row.
            linking_parent = get_linking_parent(user["id"])
            if linking_parent:
                if linking_parent.get("subscription_status") not in ("active", "past_due"):
                    session["pending_subscription_user_id"] = linking_parent["id"]
                    flash("Your parent's subscription isn't active. Ask them to renew it.")
                    return redirect(url_for("billing.subscribe_pending"))
            else:
                session["pending_subscription_user_id"] = user["id"]
                flash("Your subscription isn't active yet.")
                return redirect(url_for("billing.subscribe_pending"))
        if not user["is_verified"]:
            session["pending_email"] = user["email"]
            flash("Please verify your email before logging in.")
            return redirect(url_for("auth.check_email"))
        session["user_id"] = user["id"]
        session["username"] = user["username"]
        session["is_parent"] = user["is_parent"]
        session["is_admin"] = user["is_admin"]
        session["is_teacher"] = user.get("is_teacher", False)
        session["show_welcome"] = not user.get("first_login_completed", False)
        # Flag for first-login ToS gate (class and beta accounts provisioned without agreed_at)
        needs_tos = (
            not user.get("agreed_at")
            and user.get("user_type") in ("class", "beta")
            and not user.get("is_test", False)
        )
        session["needs_tos_agreement"] = needs_tos
        session.permanent = True
        seed_first_lesson(user["id"])
        if needs_tos:
            return redirect(url_for("onboarding.agree_tos"))
        if user.get("is_teacher"):
            return redirect(url_for("teacher.teacher_dashboard"))
        if user["is_parent"]:
            return redirect(url_for("parent.parent_dashboard"))
        return redirect(url_for("main.dashboard"))
    return render_template("login.html")

@auth_bp.route("/register/invite", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def register_invite():
    # Front door for /register: proves control of an inbox before anyone can reach
    # the registration form. See "Registration-access gate" in
    # docs/superpowers/specs/2026-07-10-stripe-registration-gate-design.md.
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        referral_code_input = request.form.get("referral_code", "").strip() or None
        # Resolve to a referral_code_id, silently dropping anything invalid/expired/
        # capped/dead — never a distinct rejection. See "Validation at request time"
        # in docs/superpowers/specs/2026-07-12-referral-codes-design.md: flashing a
        # different response for a bad code turns this rate-limited endpoint into an
        # oracle for harvesting live parent codes or exhausting a capped admin promo.
        referral_code_id = None
        if referral_code_input:
            code_row = resolve_valid_referral_code(referral_code_input)
            if code_row:
                referral_code_id = code_row["id"]
        if email:
            token = create_registration_invite(email, referral_code_id)
            send_registration_invite_email(email, token)
        # Always the same response whether or not the address is real/already in the
        # system — same enumeration-prevention pattern as forgot-password-style flows.
        return render_template("register_invite_sent.html")
    return render_template("register_invite.html")

@auth_bp.route("/register", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def register():
    if request.method == "POST":
        token = request.form.get("token", "")
        invite = get_valid_registration_invite(token)
        if not invite:
            flash("Your registration link has expired or already been used. Please request a new one.")
            return redirect(url_for("auth.register_invite"))

        # Email comes from the invite row, not the (read-only) form field — the token
        # was issued for this specific address, don't trust a client-editable copy of it.
        email = invite["email"]

        # /register/invite deliberately issues a token for any email, registered or not
        # (anti-enumeration — see its comment). This is the first point where we've
        # confirmed the requester actually controls that inbox, so telling them here
        # that an account already exists isn't an enumeration leak. Without this check,
        # create_user's insert hits the DB's unique constraint on email and raises an
        # unhandled APIError (500) instead of a friendly redirect.
        if get_user_by_email(email):
            mark_registration_invite_used(token)
            flash("An account with this email already exists. Please log in instead.")
            return redirect(url_for("auth.login"))

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        is_parent_val = request.form.get("is_parent", "")

        if is_parent_val not in ("true", "false"):
            flash("Please select an account type")
            return render_template("register.html", token=token, invite_email=email)

        is_parent = is_parent_val == "true"

        if not request.form.get("agree_tos"):
            flash("You must agree to the Privacy Policy and Terms of Use to create an account.")
            return render_template("register.html", token=token, invite_email=email)

        if len(password) < 8:
            flash("Password must be at least 8 characters")
            return render_template("register.html", token=token, invite_email=email)

        if get_user_by_username(username):
            flash("Username already taken")
            return render_template("register.html", token=token, invite_email=email)

        agreed_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
        password_hash = hash_password(password)
        user = create_user(email, username, password_hash, is_parent, agreed_at=agreed_at, subscription_status="pending")
        if not user:
            flash("Registration failed, please try again")
            return render_template("register.html", token=token, invite_email=email)

        # Single-use: stops a still-fresh link being replayed to spin up multiple
        # pending rows from one proof of email ownership.
        mark_registration_invite_used(token)

        session["pending_subscription_user_id"] = user["id"]
        # Carried into billing.subscribe_checkout (piece 4) to build the Checkout
        # session's discount/metadata. Not re-validated here — /register/invite
        # already validated it; a final live check happens again at redemption
        # (handle_checkout_completed), since time passes during Checkout.
        session["pending_referral_code_id"] = invite.get("referral_code_id")
        return redirect(url_for("billing.subscribe_checkout"))

    token = request.args.get("token", "")
    invite = get_valid_registration_invite(token)
    if not invite:
        return redirect(url_for("auth.register_invite"))
    return render_template("register.html", token=token, invite_email=invite["email"])

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
        if len(new_password) < 8:
            flash("Password must be at least 8 characters")
            return render_template("reset_password.html", token=token)
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
