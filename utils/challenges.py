from utils.db_client import supabase

def get_submission(user_id, challenge_key):
    resp = supabase.table("challenge_submissions").select("*").eq("user_id", user_id).eq("challenge_key", challenge_key).execute()
    return resp.data[0] if resp.data else None

def submit_challenge(user_id, username, challenge_key, sketch_code):
    existing = get_submission(user_id, challenge_key)
    if existing:
        if existing["status"] == "pending":
            return None, "Your submission is pending review. Please wait for feedback."
        if existing["status"] == "approved":
            return None, "This challenge is already approved!"
        # rejected — allow resubmit via patch
        resp = supabase.table("challenge_submissions").update({
            "sketch_code": sketch_code,
            "status": "pending",
            "admin_feedback": None,
            "updated_at": "now()"
        }).eq("user_id", user_id).eq("challenge_key", challenge_key).execute()
        return resp.data[0] if resp.data else None, None
    else:
        resp = supabase.table("challenge_submissions").insert({
            "user_id": user_id,
            "username": username,
            "challenge_key": challenge_key,
            "sketch_code": sketch_code,
            "status": "pending"
        }).execute()
        return resp.data[0] if resp.data else None, None

def get_all_submissions():
    resp = supabase.table("challenge_submissions").select("*").order("submitted_at", desc=True).execute()
    return resp.data

def review_submission(submission_id, status, feedback, user_id,
                      challenge_key, next_lesson_key=None):
    supabase.table("challenge_submissions").update({
        "status": status,
        "admin_feedback": feedback,
        "updated_at": "now()"
    }).eq("id", submission_id).execute()
    if status == "approved" and next_lesson_key:
        from utils.progression import unlock_lesson
        unlock_lesson(user_id, next_lesson_key)