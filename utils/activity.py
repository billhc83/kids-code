from utils.db_client import supabase

def log_activity(user_id, lesson_key, duration_seconds):
    """Log time spent on a lesson."""
    if duration_seconds < 5:
        return
    supabase.table("activity_logs").insert({
        "user_id": user_id,
        "lesson_key": lesson_key,
        "duration_seconds": duration_seconds
    }).execute()

def get_user_activity(user_id):
    """Get total time per lesson for a user."""
    resp = supabase.table("activity_logs").select("lesson_key,duration_seconds").eq("user_id", user_id).execute()
    data = resp.data
    totals = {}
    for row in data:
        key = row["lesson_key"]
        totals[key] = totals.get(key, 0) + row["duration_seconds"]
    return totals

def get_all_activity():
    """Get total time per lesson across all users."""
    resp = supabase.table("activity_logs").select("lesson_key,duration_seconds").execute()
    data = resp.data
    totals = {}
    for row in data:
        key = row["lesson_key"]
        totals[key] = totals.get(key, 0) + row["duration_seconds"]
    return totals

def get_most_active_users():
    """Get total time per user, joined to users table for display names."""
    resp = supabase.table("activity_logs").select("user_id,duration_seconds").execute()
    totals = {}
    for row in resp.data:
        uid = row["user_id"]
        totals[uid] = totals.get(uid, 0) + row["duration_seconds"]
    top = sorted(totals.items(), key=lambda x: x[1], reverse=True)[:20]
    if not top:
        return {}
    top_ids = [uid for uid, _ in top]
    users_resp = supabase.table("users").select("id,username").in_("id", top_ids).execute()
    user_map = {u["id"]: u["username"] for u in users_resp.data}
    return {user_map.get(uid, uid[:8]): seconds for uid, seconds in top}

def get_all_users_activity():
    """Get per-user per-lesson time for admin view."""
    resp = supabase.table("activity_logs").select("user_id,lesson_key,duration_seconds").execute()
    return resp.data