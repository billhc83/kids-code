import requests
from config import SUPABASE_URL, SUPABASE_KEY

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

def get_submission(user_id, challenge_key):
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/challenge_submissions"
        f"?user_id=eq.{user_id}&challenge_key=eq.{challenge_key}&limit=1",
        headers=HEADERS
    )
    data = resp.json()
    return data[0] if data else None

def submit_challenge(user_id, username, challenge_key, sketch_code):
    existing = get_submission(user_id, challenge_key)
    if existing:
        if existing["status"] == "pending":
            return None, "Your submission is pending review. Please wait for feedback."
        if existing["status"] == "approved":
            return None, "This challenge is already approved!"
        # rejected — allow resubmit via patch
        resp = requests.patch(
            f"{SUPABASE_URL}/rest/v1/challenge_submissions"
            f"?user_id=eq.{user_id}&challenge_key=eq.{challenge_key}",
            headers={**HEADERS, "Prefer": "return=representation"},
            json={
                "sketch_code": sketch_code,
                "status": "pending",
                "admin_feedback": None,
                "updated_at": "now()"
            }
        )
        return resp.json()[0] if resp.status_code == 200 else None, None
    else:
        resp = requests.post(
            f"{SUPABASE_URL}/rest/v1/challenge_submissions",
            headers={**HEADERS, "Prefer": "return=representation"},
            json={
                "user_id": user_id,
                "username": username,
                "challenge_key": challenge_key,
                "sketch_code": sketch_code,
                "status": "pending"
            }
        )
        return resp.json()[0] if resp.status_code == 201 else None, None

def get_all_submissions():
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/challenge_submissions"
        f"?order=submitted_at.desc",
        headers=HEADERS
    )
    return resp.json()

def review_submission(submission_id, status, feedback, user_id,
                      challenge_key, next_lesson_key=None):
    requests.patch(
        f"{SUPABASE_URL}/rest/v1/challenge_submissions?id=eq.{submission_id}",
        headers=HEADERS,
        json={
            "status": status,
            "admin_feedback": feedback,
            "updated_at": "now()"
        }
    )
    if status == "approved" and next_lesson_key:
        from utils.progression import unlock_lesson
        unlock_lesson(user_id, next_lesson_key)