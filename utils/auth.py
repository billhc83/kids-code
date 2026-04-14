import os
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

def get_user_by_username(username):
    resp = supabase.table("users").select("*").eq("username", username).execute()
    return resp.data[0] if resp.data else None

def get_user_by_email(email):
    resp = supabase.table("users").select("*").eq("email", email).execute()
    return resp.data[0] if resp.data else None

def create_user(email, username, password_hash, is_parent=False):
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
        "first_login_completed": False
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

def create_student_for_parent(parent_id, username, password, email=None):
    if count_students_for_parent(parent_id) >= 3:
        return None, "Maximum of 3 student accounts reached"
    
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
    supabase.table("parent_student_links").insert({"parent_id": parent_id, "student_id": student["id"]}).execute()
    
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