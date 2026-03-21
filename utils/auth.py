import os
import requests
from config import SUPABASE_URL, SUPABASE_KEY, RESEND_API_KEY
import bcrypt
import hashlib
HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

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
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/users?username=eq.{username}&limit=1",
        headers=HEADERS
    )
    data = resp.json()
    return data[0] if data else None

def get_user_by_email(email):
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/users?email=eq.{email}&limit=1",
        headers=HEADERS
    )
    data = resp.json()
    return data[0] if data else None

def create_user(email, username, password_hash, is_parent=False):
    token = secrets.token_urlsafe(32)
    resp = requests.post(
        f"{SUPABASE_URL}/rest/v1/users",
        headers={**HEADERS, "Prefer": "return=representation"},
        json={
            "email": email,
            "username": username,
            "password_hash": password_hash,
            "is_parent": is_parent,
            "is_verified": False,
            "is_admin": False,
            "verification_token": token
        }
    )
    return resp.json()[0] if resp.status_code == 201 else None

def verify_token(token):
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/users?verification_token=eq.{token}&limit=1",
        headers=HEADERS
    )
    data = resp.json()
    if not data:
        return False
    user = data[0]
    requests.patch(
        f"{SUPABASE_URL}/rest/v1/users?id=eq.{user['id']}",
        headers=HEADERS,
        json={"is_verified": True, "verification_token": None}
    )
    return True

def send_verification_email(to_email, token):
    base_url = os.getenv("BASE_URL", "http://127.0.0.1:5001")
    verify_url = f"{base_url}/verify/{token}"
    requests.post(
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

def count_students_for_parent(parent_id):
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/parent_student_links"
        f"?parent_id=eq.{parent_id}&select=id",
        headers=HEADERS
    )
    return len(resp.json())

def get_students_for_parent(parent_id):
    """Get all students linked to a parent."""
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/parent_student_links"
        f"?parent_id=eq.{parent_id}&select=student_id",
        headers=HEADERS
    )
    links = resp.json()
    if not links:
        return []
    
    student_ids = [l["student_id"] for l in links]
    students = []
    for sid in student_ids:
        resp = requests.get(
            f"{SUPABASE_URL}/rest/v1/users?id=eq.{sid}",
            headers=HEADERS
        )
        data = resp.json()
        if data:
            students.append(data[0])
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
    resp = requests.post(
        f"{SUPABASE_URL}/rest/v1/users",
        headers={**HEADERS, "Prefer": "return=representation"},
        json={
            "email": email,
            "username": username,
            "password_hash": password_hash,
            "is_parent": False,
            "is_verified": True,
            "is_admin": False,
            "verification_token": None
        }
    )
    print(f"CREATE STUDENT STATUS: {resp.status_code}")
    print(f"CREATE STUDENT RESPONSE: {resp.text}")
    if resp.status_code != 201:
        return None, "Failed to create account"
    
    student = resp.json()[0]
    requests.post(
        f"{SUPABASE_URL}/rest/v1/parent_student_links",
        headers=HEADERS,
        json={"parent_id": parent_id, "student_id": student["id"]}
    )
    from utils.progression import unlock_lesson, LESSON_SEQUENCE
    unlock_lesson(student["id"], LESSON_SEQUENCE[0])
    return student, None

def reset_student_password(student_id, new_password):
    """Reset a student's password."""
    password_hash = hash_password(new_password)
    resp = requests.patch(
        f"{SUPABASE_URL}/rest/v1/users?id=eq.{student_id}",
        headers=HEADERS,
        json={"password_hash": password_hash}
    )
    return resp.status_code == 204

import datetime

def create_reset_token(email):
    """Generate a reset token and save it to the user record."""
    user_resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/users?email=eq.{email}&limit=1",
        headers=HEADERS
    )
    data = user_resp.json()
    if not data:
        return None, "No account found with that email"
    
    user = data[0]
    
    # Don't allow reset for internal student accounts
    if user["email"].endswith("@kidscode.internal"):
        return None, "This account does not have a real email address. Ask your parent to reset your password."
    
    token = secrets.token_urlsafe(32)
    expires = (datetime.datetime.utcnow() + datetime.timedelta(hours=1)).isoformat()
    
    requests.patch(
        f"{SUPABASE_URL}/rest/v1/users?id=eq.{user['id']}",
        headers=HEADERS,
        json={"reset_token": token, "reset_token_expires": expires}
    )
    return token, None

def verify_reset_token(token):
    """Check if a reset token is valid and not expired."""
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/users?reset_token=eq.{token}&limit=1",
        headers=HEADERS
    )
    data = resp.json()
    if not data:
        return None, "Invalid or expired reset link"
    
    user = data[0]
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
    requests.patch(
        f"{SUPABASE_URL}/rest/v1/users?id=eq.{user['id']}",
        headers=HEADERS,
        json={
            "password_hash": password_hash,
            "reset_token": None,
            "reset_token_expires": None
        }
    )
    return True, None

def send_reset_email(to_email, token):
    """Send password reset email via Resend."""
    import os
    base_url = os.getenv("BASE_URL", "http://127.0.0.1:5001")
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