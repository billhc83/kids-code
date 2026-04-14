from utils.lessons import LESSON_SEQUENCE, get_next_lesson
from utils.lessons import LESSON_SEQUENCE, get_next_lesson
from utils.db_client import supabase

def get_user_progression(user_id):
    resp = supabase.table("progression").select("lesson_key").eq("user_id", user_id).eq("unlocked", True).execute()
    return [row["lesson_key"] for row in resp.data]

def get_completed_lessons(user_id):
    resp = supabase.table("progression").select("lesson_key").eq("user_id", user_id).eq("completed", True).execute()
    return [row["lesson_key"] for row in resp.data]

def unlock_lesson(user_id, lesson_key):
    # Try to insert or update (upsert)
    # Note: In Supabase-py, we can use upsert if we have a unique constraint on (user_id, lesson_key)
    # For now, let's stick to the current logic: check if exists, then patch or post.
    check = supabase.table("progression").select("*").eq("user_id", user_id).eq("lesson_key", lesson_key).execute()
    
    if check.data:
        # Row exists, patch it
        supabase.table("progression").update({"unlocked": True}).eq("user_id", user_id).eq("lesson_key", lesson_key).execute()
    else:
        # Row doesn't exist, insert it
        supabase.table("progression").insert({
            "user_id": user_id,
            "lesson_key": lesson_key,
            "unlocked": True
        }).execute()

def complete_lesson(user_id, lesson_key):
    resp = supabase.table("progression").update({
        "completed": True,
        "completed_at": "now()"
    }).eq("user_id", user_id).eq("lesson_key", lesson_key).execute()
    next_key = get_next_lesson(lesson_key)
    if next_key:
        unlock_lesson(user_id, next_key)

    if lesson_key == "project_ten":
        unlock_lesson(user_id, "project_eleven")

    return next_key

def is_unlocked(user_id, lesson_key):
    resp = supabase.table("progression").select("*").eq("user_id", user_id).eq("lesson_key", lesson_key).eq("unlocked", True).execute()
    return len(resp.data) > 0

def seed_first_lesson(user_id):
    unlock_lesson(user_id, LESSON_SEQUENCE[0])