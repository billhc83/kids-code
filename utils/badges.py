from collections import Counter
from utils.db_client import supabase
from utils.lessons import LESSON_BY_KEY, count_unique_projects
from utils.progression import get_completion_dates

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
    "troubleshooter": {
        "key": "troubleshooter",
        "title": "Bug Squasher",
        "icon": "🔧",
        "description": "Fixed a broken circuit in a troubleshoot lesson"
    },
    "simulator": {
        "key": "simulator",
        "title": "Simulator Ace",
        "icon": "🖥️",
        "description": "Ran a project in the simulator"
    },
    "streak_3": {
        "key": "streak_3",
        "title": "On a Roll",
        "icon": "🌅",
        "description": "Completed a project 3 days in a row"
    },
    "streak_7": {
        "key": "streak_7",
        "title": "Week of Wonder",
        "icon": "🌟",
        "description": "Completed a project 7 days in a row"
    },
    "quick_study": {
        "key": "quick_study",
        "title": "Quick Study",
        "icon": "⚡",
        "description": "Completed 3 projects in a single day"
    },
}

def get_user_badges(user_id):
    resp = supabase.table("badges").select("badge_key").eq("user_id", user_id).execute()
    return [row["badge_key"] for row in resp.data]

def award_badge(user_id, badge_key):
    supabase.table("badges").upsert(
        {"user_id": user_id, "badge_key": badge_key},
        on_conflict="user_id,badge_key"
    ).execute()

def award_simulator_badge(user_id):
    """Call this whenever a user runs a project in the simulator (/sim/run)."""
    if "simulator" not in get_user_badges(user_id):
        award_badge(user_id, "simulator")

def _is_troubleshoot_lesson(lesson_key):
    from utils.project_registry import PROJECTS
    lesson = LESSON_BY_KEY.get(lesson_key)
    if not lesson:
        return False
    module_key = lesson.get("block_builder") or lesson_key
    project = PROJECTS.get(module_key)
    if not project:
        return False
    return project.get("meta", {}).get("lesson_type") == "troubleshoot"

def _longest_day_streak(dates):
    """Longest run of consecutive calendar days with at least one completion."""
    unique_days = sorted(set(dates))
    if not unique_days:
        return 0
    best = streak = 1
    for prev, curr in zip(unique_days, unique_days[1:]):
        streak = streak + 1 if (curr - prev).days == 1 else 1
        best = max(best, streak)
    return best

def _max_completions_in_a_day(dates):
    if not dates:
        return 0
    return max(Counter(dates).values())

def check_and_award_badges(user_id, completed_lessons):
    """Call this after completing a lesson to award any earned badges."""
    awarded = get_user_badges(user_id)
    count = count_unique_projects(completed_lessons)

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

    if any(_is_troubleshoot_lesson(l) for l in completed_lessons) and "troubleshooter" not in awarded:
        award_badge(user_id, "troubleshooter")

    completion_dates = get_completion_dates(user_id)
    streak = _longest_day_streak(completion_dates)

    if streak >= 3 and "streak_3" not in awarded:
        award_badge(user_id, "streak_3")

    if streak >= 7 and "streak_7" not in awarded:
        award_badge(user_id, "streak_7")

    if _max_completions_in_a_day(completion_dates) >= 3 and "quick_study" not in awarded:
        award_badge(user_id, "quick_study")