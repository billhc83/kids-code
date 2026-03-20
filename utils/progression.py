from utils.lessons import LESSON_SEQUENCE, get_next_lesson
import requests
from config import SUPABASE_URL, SUPABASE_KEY

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

def get_user_progression(user_id):
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/progression?user_id=eq.{user_id}&unlocked=eq.true",
        headers=HEADERS
    )
    return [row["lesson_key"] for row in resp.json()]

def get_completed_lessons(user_id):
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/progression?user_id=eq.{user_id}&completed=eq.true",
        headers=HEADERS
    )
    return [row["lesson_key"] for row in resp.json()]

def unlock_lesson(user_id, lesson_key):
    # Try to get existing row first
    check = requests.get(
        f"{SUPABASE_URL}/rest/v1/progression"
        f"?user_id=eq.{user_id}&lesson_key=eq.{lesson_key}",
        headers=HEADERS
    )
    if check.json():
        # Row exists, patch it
        requests.patch(
            f"{SUPABASE_URL}/rest/v1/progression"
            f"?user_id=eq.{user_id}&lesson_key=eq.{lesson_key}",
            headers=HEADERS,
            json={"unlocked": True}
        )
    else:
        # Row doesn't exist, insert it
        requests.post(
            f"{SUPABASE_URL}/rest/v1/progression",
            headers=HEADERS,
            json={
                "user_id": user_id,
                "lesson_key": lesson_key,
                "unlocked": True
            }
        )

def complete_lesson(user_id, lesson_key):
    resp = requests.patch(
        f"{SUPABASE_URL}/rest/v1/progression"
        f"?user_id=eq.{user_id}&lesson_key=eq.{lesson_key}",
        headers=HEADERS,
        json={
            "completed": True,
            "completed_at": "now()"
        }
    )
    next_key = get_next_lesson(lesson_key)
    if next_key:
        unlock_lesson(user_id, next_key)
    return next_key

def is_unlocked(user_id, lesson_key):
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/progression"
        f"?user_id=eq.{user_id}&lesson_key=eq.{lesson_key}&unlocked=eq.true",
        headers=HEADERS
    )
    return len(resp.json()) > 0

def seed_first_lesson(user_id):
    unlock_lesson(user_id, LESSON_SEQUENCE[0])