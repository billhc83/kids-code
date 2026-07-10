import os
import csv
import string
import datetime
import requests
from config import SUPABASE_URL, SUPABASE_KEY, RESEND_API_KEY
import bcrypt
import hashlib, secrets
from utils.db_client import supabase

def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def check_password(password, stored):
    # bcrypt hashes start with $2b$ or $2a$
    if stored.startswith("$2b$") or stored.startswith("$2a$"):
        try:
            return bcrypt.checkpw(password.encode(), stored.encode())
        except Exception:
            return False
    # Legacy sha256 format salt:hash
    if ":" in stored:
        salt, hashed = stored.split(":", 1)
        return hashlib.sha256((salt + password).encode()).hexdigest() == hashed
    return False

def is_legacy_hash(stored):
    return not (stored.startswith("$2b$") or stored.startswith("$2a$"))

def upgrade_password_hash(user_id, password):
    new_hash = hash_password(password)
    try:
        supabase.table("users").update({"password_hash": new_hash}).eq("id", user_id).execute()
    except Exception:
        pass

def get_user_by_username(username):
    resp = supabase.table("users").select("*").eq("username", username).execute()
    return resp.data[0] if resp.data else None

def get_user_by_email(email):
    resp = supabase.table("users").select("*").eq("email", email).execute()
    return resp.data[0] if resp.data else None

def get_user_by_id(user_id):
    resp = supabase.table("users").select("*").eq("id", user_id).execute()
    return resp.data[0] if resp.data else None

def get_user_by_stripe_subscription_id(subscription_id):
    resp = supabase.table("users").select("*").eq("stripe_subscription_id", subscription_id).execute()
    return resp.data[0] if resp.data else None

def get_linking_parent(student_id):
    """If student_id is a parent-created student sub-account (utils.auth.create_student_for_parent),
    return the linking parent's user row. Returns None for a standalone self-registered account —
    used by the login gate (routes/auth.py) to check the parent's live subscription_status instead
    of the student row's own (which is never independently paid for)."""
    link_resp = supabase.table("parent_student_links").select("parent_id").eq("student_id", student_id).execute()
    if not link_resp.data:
        return None
    return get_user_by_id(link_resp.data[0]["parent_id"])

def create_user(email, username, password_hash, is_parent=False, agreed_at=None, subscription_status="none"):
    token = secrets.token_urlsafe(32)
    expires = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=48)).isoformat()
    resp = supabase.table("users").insert({
        "email": email,
        "username": username,
        "password_hash": password_hash,
        "is_parent": is_parent,
        "is_verified": False,
        "is_admin": False,
        "verification_token": token,
        "verification_token_expires": expires,
        "first_login_completed": False,
        "agreed_at": agreed_at,
        "subscription_status": subscription_status,
    }).execute()
    return resp.data[0] if resp.data else None

def mark_first_login_complete(user_id):
    try:
        supabase.table("users").update({"first_login_completed": True}).eq("id", user_id).execute()
    except Exception:
        pass

def verify_token(token):
    resp = supabase.table("users").select("*").eq("verification_token", token).execute()
    if not resp.data:
        return False
    user = resp.data[0]
    expires = user.get("verification_token_expires")
    if expires:
        expires_dt = datetime.datetime.fromisoformat(expires.replace("Z", "+00:00"))
        if expires_dt.tzinfo is None:
            expires_dt = expires_dt.replace(tzinfo=datetime.timezone.utc)
        if datetime.datetime.now(datetime.timezone.utc) > expires_dt:
            return False
    supabase.table("users").update({
        "is_verified": True,
        "verification_token": None,
        "verification_token_expires": None
    }).eq("id", user['id']).execute()
    return True

def resend_verification_email(email):
    print(f"[resend_verification_email] looking up email: {email!r}")
    resp = supabase.table("users").select("*").eq("email", email).execute()
    if not resp.data:
        print(f"[resend_verification_email] no user found for {email!r}")
        return False, "No account found with that email"
    user = resp.data[0]
    if user.get("is_verified"):
        print(f"[resend_verification_email] user {email!r} already verified")
        return False, "This account is already verified"
    token = secrets.token_urlsafe(32)
    expires = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=48)).isoformat()
    supabase.table("users").update({
        "verification_token": token,
        "verification_token_expires": expires
    }).eq("id", user["id"]).execute()
    print(f"[resend_verification_email] sending email to {email!r}")
    send_verification_email(email, token)
    print(f"[resend_verification_email] done")
    return True, None

def send_verification_email(to_email, token):
    base_url = os.getenv("BASE_URL", "https://app.kidscode.ca")
    verify_url = f"{base_url}/verify/{token}"
    resp = requests.post(
        "https://api.resend.com/emails",
        headers={
            "Authorization": f"Bearer {RESEND_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "from": "KidsCode <no-reply@kidscode.ca>",
            "to": to_email,
            "subject": "Verify your KidsCode account",
            "html": f"""
                <h2>Welcome to KidsCode!</h2>
                <p>Click the link below to verify your account:</p>
                <a href="{verify_url}">{verify_url}</a>
            """
        }
    )
    if not resp.ok:
        print(f"[send_verification_email] Resend error {resp.status_code}: {resp.text}")

def create_registration_invite(email, referral_code=None):
    """Issue a one-time registration-invite token for /register/invite. See
    docs/superpowers/specs/2026-07-10-stripe-registration-gate-design.md
    ('Registration-access gate') for why /register requires one of these."""
    token = secrets.token_urlsafe(32)
    expires = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=60)).isoformat()
    supabase.table("registration_invites").insert({
        "token": token,
        "email": email,
        "referral_code": referral_code,
        "expires_at": expires,
    }).execute()
    return token

def get_valid_registration_invite(token):
    """Return the invite row if token exists, isn't expired, and hasn't been used yet.
    None otherwise (covers missing/unknown/expired/already-used) — callers redirect back
    to /register/invite in every None case, no need to distinguish why."""
    if not token:
        return None
    resp = supabase.table("registration_invites").select("*").eq("token", token).execute()
    if not resp.data:
        return None
    invite = resp.data[0]
    if invite.get("used_at"):
        return None
    expires_at = invite.get("expires_at")
    if expires_at:
        expires_dt = datetime.datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
        if expires_dt.tzinfo is None:
            expires_dt = expires_dt.replace(tzinfo=datetime.timezone.utc)
        if datetime.datetime.now(datetime.timezone.utc) > expires_dt:
            return None
    return invite

def mark_registration_invite_used(token):
    supabase.table("registration_invites").update({
        "used_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }).eq("token", token).execute()

def send_registration_invite_email(to_email, token):
    base_url = os.getenv("BASE_URL", "https://app.kidscode.ca")
    register_url = f"{base_url}/register?token={token}"
    resp = requests.post(
        "https://api.resend.com/emails",
        headers={
            "Authorization": f"Bearer {RESEND_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "from": "KidsCode <no-reply@kidscode.ca>",
            "to": to_email,
            "subject": "Your KidsCode registration link",
            "html": f"""
                <h2>Ready to start building?</h2>
                <p>Click the link below to create your KidsCode account:</p>
                <a href="{register_url}">{register_url}</a>
                <p>This link expires in 60 minutes.</p>
            """
        }
    )
    if not resp.ok:
        print(f"[send_registration_invite_email] Resend error {resp.status_code}: {resp.text}")

def count_students_for_parent(parent_id):
    resp = supabase.table("parent_student_links").select("id", count="exact").eq("parent_id", parent_id).execute()
    return resp.count if resp.count is not None else 0

def get_students_for_parent(parent_id):
    """Get all students linked to a parent."""
    resp = supabase.table("parent_student_links").select("student_id").eq("parent_id", parent_id).execute()
    links = resp.data
    if not links:
        return []
    
    student_ids = [l["student_id"] for l in links]
    students = []
    for sid in student_ids:
        resp = supabase.table("users").select("*").eq("id", sid).execute()
        if resp.data:
            students.append(resp.data[0])
    return students

def create_student_for_parent(parent_id, username, password, email=None, consent_given_at=None):
    if count_students_for_parent(parent_id) >= 3:
        return None, "Maximum of 3 student accounts reached"

    if len(password) < 8:
        return None, "Password must be at least 8 characters"

    if get_user_by_username(username):
        return None, "Username already taken"

    # Generate unique internal email if none provided
    if not email:
        import uuid
        email = f"{username}.{str(uuid.uuid4())[:8]}@kidscode.internal"

    password_hash = hash_password(password)
    resp = supabase.table("users").insert({
        "email": email,
        "username": username,
        "password_hash": password_hash,
        "is_parent": False,
        "is_verified": True,
        "is_admin": False,
        "verification_token": None
    }).execute()
    
    if not resp.data:
        return None, "Failed to create account"
    
    student = resp.data[0]
    supabase.table("parent_student_links").insert({
        "parent_id": parent_id,
        "student_id": student["id"],
        "consent_given_at": consent_given_at,
    }).execute()
    
    from utils.progression import unlock_lesson, LESSON_SEQUENCE
    unlock_lesson(student["id"], LESSON_SEQUENCE[0])
    return student, None

def reset_student_password(student_id, new_password):
    """Reset a student's password."""
    password_hash = hash_password(new_password)
    resp = supabase.table("users").update({"password_hash": password_hash}).eq("id", student_id).execute()
    return len(resp.data) > 0

def create_reset_token(email):
    """Generate a reset token and save it to the user record."""
    user_resp = supabase.table("users").select("*").eq("email", email).execute()
    if not user_resp.data:
        return None, "No account found with that email"
    
    user = user_resp.data[0]
    
    # Don't allow reset for internal student accounts
    if user["email"].endswith("@kidscode.internal"):
        return None, "This account does not have a real email address. Ask your parent to reset your password."
    
    token = secrets.token_urlsafe(32)
    expires = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1)).isoformat()
    
    supabase.table("users").update({"reset_token": token, "reset_token_expires": expires}).eq("id", user["id"]).execute()
    return token, None

def verify_reset_token(token):
    """Check if a reset token is valid and not expired."""
    resp = supabase.table("users").select("*").eq("reset_token", token).execute()
    if not resp.data:
        return None, "Invalid or expired reset link"
    
    user = resp.data[0]
    expires = user.get("reset_token_expires")
    if not expires:
        return None, "Invalid or expired reset link"
    
    expires_dt = datetime.datetime.fromisoformat(expires.replace("Z", "+00:00"))
    now = datetime.datetime.now(datetime.timezone.utc)
    if now > expires_dt:
        return None, "Reset link has expired. Please request a new one."
    
    return user, None

def reset_password_with_token(token, new_password):
    """Reset the password and clear the token."""
    user, err = verify_reset_token(token)
    if err:
        return False, err
        
    password_hash = hash_password(new_password)
    supabase.table("users").update({
        "password_hash": password_hash,
        "reset_token": None,
        "reset_token_expires": None
    }).eq("id", user["id"]).execute()
    return True, None

# ── Provisioning helpers ──────────────────────────────────────────────────────

def _gen_temp_password(length=12):
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def _internal_email(username):
    import uuid
    return f"{username}.{str(uuid.uuid4())[:8]}@kidscode.internal"

def create_cohort_teacher(username, cohort):
    """Create the anchor teacher account for a cohort. Returns (user, temp_password, error)."""
    if not cohort:
        return None, None, "Cohort name is required"
    if get_user_by_username(username):
        return None, None, "Username already taken"
    temp_password = _gen_temp_password()
    password_hash = hash_password(temp_password)
    resp = supabase.table("users").insert({
        "email": _internal_email(username),
        "username": username,
        "password_hash": password_hash,
        "is_parent": False,
        "is_teacher": True,
        "is_verified": True,
        "is_admin": False,
        "is_test": False,
        "user_type": "class",
        "cohort": cohort,
        "verification_token": None,
        "first_login_completed": False,
        "agreed_at": None,
    }).execute()
    if not resp.data:
        return None, None, "Failed to create teacher account"
    user = resp.data[0]
    from utils.progression import unlock_lesson, LESSON_SEQUENCE
    unlock_lesson(user["id"], LESSON_SEQUENCE[0])
    return user, temp_password, None

def create_student_for_teacher(teacher_id, username, password=None):
    """Create a student linked to a teacher, inheriting the teacher's cohort. No cap enforced."""
    if get_user_by_username(username):
        return None, None, "Username already taken"
    temp_password = password or _gen_temp_password()
    if len(temp_password) < 8:
        return None, None, "Password must be at least 8 characters"

    t_resp = supabase.table("users").select("cohort").eq("id", teacher_id).execute()
    cohort = t_resp.data[0]["cohort"] if t_resp.data else None

    password_hash = hash_password(temp_password)
    resp = supabase.table("users").insert({
        "email": _internal_email(username),
        "username": username,
        "password_hash": password_hash,
        "is_parent": False,
        "is_teacher": False,
        "is_verified": True,
        "is_admin": False,
        "is_test": False,
        "user_type": "class",
        "cohort": cohort,
        "verification_token": None,
        "first_login_completed": False,
        "agreed_at": None,
    }).execute()
    if not resp.data:
        return None, None, "Failed to create student account"
    student = resp.data[0]
    supabase.table("parent_student_links").insert({
        "parent_id": teacher_id,
        "student_id": student["id"],
        "consent_given_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }).execute()
    from utils.progression import unlock_lesson, LESSON_SEQUENCE
    unlock_lesson(student["id"], LESSON_SEQUENCE[0])
    return student, temp_password, None

def create_batch_students_for_teacher(teacher_id, prefix, count):
    """Create `count` students with usernames `prefix1`, `prefix2`, …
    Returns (rows, errors) where rows = list of {username, password}."""
    rows = []
    errors = []
    for i in range(1, count + 1):
        username = f"{prefix}{i}"
        student, temp_pw, err = create_student_for_teacher(teacher_id, username)
        if err:
            errors.append(f"{username}: {err}")
        else:
            rows.append({"username": username, "password": temp_pw})
    return rows, errors

def create_test_user(username, cohort=None):
    """Admin-provision an internal test account (skips ToS gate). Returns (user, temp_password, error)."""
    if get_user_by_username(username):
        return None, None, "Username already taken"
    temp_password = _gen_temp_password()
    password_hash = hash_password(temp_password)
    resp = supabase.table("users").insert({
        "email": _internal_email(username),
        "username": username,
        "password_hash": password_hash,
        "is_parent": False,
        "is_teacher": False,
        "is_verified": True,
        "is_admin": False,
        "is_test": True,
        "user_type": "test",
        "cohort": cohort,
        "verification_token": None,
        "first_login_completed": False,
        "agreed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }).execute()
    if not resp.data:
        return None, None, "Failed to create test account"
    user = resp.data[0]
    from utils.progression import unlock_lesson, LESSON_SEQUENCE
    unlock_lesson(user["id"], LESSON_SEQUENCE[0])
    return user, temp_password, None

def get_teachers():
    """Return all teacher accounts with their cohort, ordered by cohort then username."""
    resp = (supabase.table("users")
            .select("id,username,cohort,created_at")
            .eq("is_teacher", True)
            .order("cohort")
            .execute())
    return resp.data or []

def get_all_cohorts():
    """Return a list of cohort summary dicts for the provisioning panel."""
    resp = (supabase.table("users")
            .select("id,username,cohort,is_teacher,created_at")
            .not_.is_("cohort", "null")
            .order("cohort")
            .execute())
    users = resp.data or []

    cohorts = {}
    for u in users:
        c = u["cohort"]
        if c not in cohorts:
            cohorts[c] = {
                "cohort": c,
                "teacher": None,
                "member_count": 0,
                "created_at": u["created_at"],
            }
        cohorts[c]["member_count"] += 1
        if u.get("is_teacher"):
            cohorts[c]["teacher"] = u["username"]
        if u["created_at"] and u["created_at"] < cohorts[c]["created_at"]:
            cohorts[c]["created_at"] = u["created_at"]

    return list(cohorts.values())

def delete_cohort(cohort_name):
    """Hard-delete all users and their links belonging to a cohort. Returns count deleted."""
    resp = supabase.table("users").select("id").eq("cohort", cohort_name).execute()
    user_ids = [u["id"] for u in (resp.data or [])]
    for uid in user_ids:
        supabase.table("parent_student_links").delete().or_(
            f"parent_id.eq.{uid},student_id.eq.{uid}"
        ).execute()
        supabase.table("users").delete().eq("id", uid).execute()
    return len(user_ids)

def rows_to_csv_string(rows):
    """Convert a list of dicts to a CSV string."""
    import io
    buf = io.StringIO()
    if not rows:
        return ""
    writer = csv.DictWriter(buf, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue()


def send_reset_email(to_email, token):
    """Send password reset email via Resend."""
    import os
    base_url = os.getenv("BASE_URL", "http://app.kidscode.ca")
    reset_url = f"{base_url}/reset-password/{token}"
    requests.post(
        "https://api.resend.com/emails",
        headers={
            "Authorization": f"Bearer {RESEND_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "from": "KidsCode <no-reply@kidscode.ca>",
            "to": to_email,
            "subject": "Reset your KidsCode password",
            "html": f"""
                <h2>Password Reset</h2>
                <p>Someone requested a password reset for your KidsCode account.</p>
                <p>Click the link below to reset your password:</p>
                <a href="{reset_url}">{reset_url}</a>
                <p>This link expires in 1 hour.</p>
                <p>If you didn't request this, you can ignore this email.</p>
            """
        }
    )