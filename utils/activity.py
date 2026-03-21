import requests
from config import SUPABASE_URL, SUPABASE_KEY

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

def log_activity(user_id, username, lesson_key, duration_seconds):
    """Log time spent on a lesson."""
    if duration_seconds < 5:
        return
    requests.post(
        f"{SUPABASE_URL}/rest/v1/activity_logs",
        headers=HEADERS,
        json={
            "user_id": user_id,
            "username": username,
            "lesson_key": lesson_key,
            "duration_seconds": duration_seconds
        }
    )

def get_user_activity(user_id):
    """Get total time per lesson for a user."""
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/activity_logs"
        f"?user_id=eq.{user_id}&select=lesson_key,duration_seconds",
        headers=HEADERS
    )
    data = resp.json()
    totals = {}
    for row in data:
        key = row["lesson_key"]
        totals[key] = totals.get(key, 0) + row["duration_seconds"]
    return totals

def get_all_activity():
    """Get total time per lesson across all users."""
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/activity_logs"
        f"?select=lesson_key,duration_seconds",
        headers=HEADERS
    )
    data = resp.json()
    totals = {}
    for row in data:
        key = row["lesson_key"]
        totals[key] = totals.get(key, 0) + row["duration_seconds"]
    return totals

def get_most_active_users():
    """Get total time per user."""
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/activity_logs"
        f"?select=username,duration_seconds",
        headers=HEADERS
    )
    data = resp.json()
    totals = {}
    for row in data:
        u = row["username"]
        totals[u] = totals.get(u, 0) + row["duration_seconds"]
    return dict(sorted(totals.items(), key=lambda x: x[1], reverse=True)[:20])

def get_all_users_activity():
    """Get per-user per-lesson time for admin view."""
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/activity_logs"
        f"?select=user_id,username,lesson_key,duration_seconds",
        headers=HEADERS
    )
    return resp.json()