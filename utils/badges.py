import requests
from config import SUPABASE_URL, SUPABASE_KEY

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

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
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/badges?user_id=eq.{user_id}",
        headers=HEADERS
    )
    return [row["badge_key"] for row in resp.json()]

def award_badge(user_id, badge_key):
    requests.post(
        f"{SUPABASE_URL}/rest/v1/badges",
        headers={**HEADERS, "Prefer": "resolution=merge-duplicates"},
        json={"user_id": user_id, "badge_key": badge_key}
    )

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

    if any("challenge" in l for l in completed_lessons) and "challenger" not in awarded:
        award_badge(user_id, "challenger")

    if len(completed_lessons) >= len(BADGE_DEFINITIONS) and "all_done" not in awarded:
        award_badge(user_id, "all_done")