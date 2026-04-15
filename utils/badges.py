from utils.db_client import supabase

# Define all badges
BADGE_DEFINITIONS = {
    "first_step": {
        "key": "first_step",
        "title": "First Step",
        "icon": "🚀",
        "description": "Completed Getting Started"
    },
    "project_five": {
        "key": "project_five",
        "title": "Halfway There",
        "icon": "⭐",
        "description": "Completed 5 projects"
    },
    "project_ten": {
        "key": "project_ten",
        "title": "10 Strong",
        "icon": "🔥",
        "description": "Completed 10 projects"
    },
    "block_builder": {
        "key": "block_builder",
        "title": "Block Builder",
        "icon": "🧱",
        "description": "Used the block builder"
    },
    "challenger": {
        "key": "challenger",
        "title": "Challenger",
        "icon": "🎯",
        "description": "Completed the challenge"
    },
    "all_done": {
        "key": "all_done",
        "title": "All Done",
        "icon": "🏆",
        "description": "Completed all projects"
    },
}

def get_user_badges(user_id):
    resp = supabase.table("badges").select("badge_key").eq("user_id", user_id).execute()
    return [row["badge_key"] for row in resp.data]

def award_badge(user_id, badge_key):
    # Note: resolution=merge-duplicates was used in the original REST call.
    # In supabase-py, we can use upsert(..., on_conflict="user_id,badge_key") or just insert.
    # For now, let's use upsert to mimic 'merge-duplicates' behavior if possible, 
    # but simple insert is usually fine if constraints are handled.
    supabase.table("badges").upsert({"user_id": user_id, "badge_key": badge_key}).execute()

def check_and_award_badges(user_id, completed_lessons):
    """Call this after completing a lesson to award any earned badges."""
    awarded = get_user_badges(user_id)
    count = len(completed_lessons)

    if "getting_started" in completed_lessons and "first_step" not in awarded:
        award_badge(user_id, "first_step")

    if count >= 5 and "project_five" not in awarded:
        award_badge(user_id, "project_five")

    if count >= 10 and "project_ten" not in awarded:
        award_badge(user_id, "project_ten")

    if "block_builder_tutorial" in completed_lessons and "block_builder" not in awarded:
        award_badge(user_id, "block_builder")

    if any("challenge" in l for l in completed_lessons) and "challenger" not in awarded:
        award_badge(user_id, "challenger")

    if len(completed_lessons) >= len(BADGE_DEFINITIONS) and "all_done" not in awarded:
        award_badge(user_id, "all_done")