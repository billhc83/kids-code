"""
Targeted migration script for 3 active users.
Run with: python migrate.py
"""
import requests
from dotenv import load_dotenv
import os

load_dotenv()

NEW_URL = os.getenv("SUPABASE_URL")
NEW_KEY = os.getenv("SUPABASE_KEY")

NEW_HEADERS = {
    "apikey": NEW_KEY,
    "Authorization": f"Bearer {NEW_KEY}",
    "Content-Type": "application/json"
}

# ── Hardcoded user data ────────────────────────────────────────────
USERS = [
    {
        "username": "Jacob_wulff",
        "email": "jacob@kidscode.internal",
        "password_hash": "$2b$12$ekqQGPHgJTYCK7frfLfQpOAd5z48FnWETe8mB3nDEkAvnP38I7Ji.",
        "is_parent": False,
        "is_admin": False,
    },
    {
        "username": "Jason_wulff",
        "email": "jason@kidscode.internal",
        "password_hash": "$2b$12$IveRSYjyOjm/BpsOtZ280eWVcD6CHyofXBk.NMQM.ykQpXPoFBt1e",
        "is_parent": False,
        "is_admin": False,
    },
    {
        "username": "William",
        "email": "william@kidscode.internal",
        "password_hash": "$2b$12$uoxl0wU2GbKgOMk73fVB2u5d8j9/6y3xv3fqMCNQgJNorl61zeEEi",
        "is_parent": False,
        "is_admin": False,
    },
]

# ── Step to lesson key mapping ─────────────────────────────────────
STEP_MAP = {
    "Getting Started":  "getting_started",
    "Project One":      "project_one",
    "Project Two":      "project_two",
    "Project Three":    "project_three",
    "Project Four":     "project_four",
    "Project Five":     "project_five",
    "Project Six":      "project_six",
    "Project Seven":    "project_seven",
    "Project Eight":    "project_eight",
    "Project Nine":     "project_nine",
    "Project Ten":      "project_ten",
    "Project Eleven":   "project_eleven",
    "Challenge One":    "challenge_one",
}

LESSON_SEQUENCE = [
    "getting_started",
    "project_one",
    "project_two",
    "project_three",
    "project_four",
    "project_five",
    "project_six",
    "project_seven",
    "project_eight",
    "project_nine",
    "project_ten",
    "challenge_one",
    "project_eleven",
    "project_twelve",
    "project_thirteen",
    "project_fourteen_part_one",
    "project_fourteen_part_two",

]

# ── Progress data ──────────────────────────────────────────────────
PROGRESS = {
    "Jacob_wulff": [
        "Getting Started", "Project One", "Project Two", "Project Three",
        "Project Four", "Project Five", "Project Six", "Project Seven",
        "Project Eight", "Project Nine", "Project Ten", "Project Eleven",
        "Challenge One"
    ],
    "Jason_wulff": [
        "Getting Started", "Project One", "Project Two", "Project Three",
        "Project Four", "Project Five", "Project Six", "Project Seven",
        "Project Eight", "Project Nine", "Project Ten", "Project Eleven",
        "Challenge One"
    ],
    "William": [
        "Getting Started", "Project One", "Project Two"
    ],
}


def migrate_users():
    print("\n── Migrating users ──")
    user_id_map = {}

    for user in USERS:
        username = user["username"]
        print(f"  Processing {username}...")

        # Check if already exists
        existing = requests.get(
            f"{NEW_URL}/rest/v1/users?username=eq.{username}",
            headers=NEW_HEADERS
        ).json()

        if existing:
            user_id_map[username] = existing[0]["id"]
            print(f"  ~ {username} already exists, using id {existing[0]['id']}")
            continue

        resp = requests.post(
            f"{NEW_URL}/rest/v1/users",
            headers={**NEW_HEADERS, "Prefer": "return=representation"},
            json={
                "email": user["email"],
                "username": username,
                "password_hash": user["password_hash"],
                "is_parent": user["is_parent"],
                "is_admin": user["is_admin"],
                "is_verified": True,
                "verification_token": None
            }
        )
        if resp.status_code == 201:
            new_id = resp.json()[0]["id"]
            user_id_map[username] = new_id
            print(f"  ✓ Created {username} with id {new_id}")
        else:
            print(f"  ✗ Failed to create {username}: {resp.text}")

    return user_id_map


def migrate_progress(user_id_map):
    print("\n── Migrating progress ──")

    for username, steps in PROGRESS.items():
        user_id = user_id_map.get(username)
        if not user_id:
            print(f"  ⚠ No id for {username} — skipping")
            continue

        print(f"\n  Progress for {username}:")

        # Convert steps to lesson keys
        completed_keys = set()
        for step in steps:
            key = STEP_MAP.get(step)
            if key:
                completed_keys.add(key)

        # Find furthest completed lesson index
        furthest_idx = -1
        for key in completed_keys:
            if key in LESSON_SEQUENCE:
                idx = LESSON_SEQUENCE.index(key)
                if idx > furthest_idx:
                    furthest_idx = idx

        if furthest_idx == -1:
            print(f"    No mappable steps")
            continue

        # Unlock next lesson after furthest completed
        unlock_up_to = min(furthest_idx + 1, len(LESSON_SEQUENCE) - 1)
        lessons_to_process = LESSON_SEQUENCE[:unlock_up_to + 1]

        for lesson_key in lessons_to_process:
            is_completed = lesson_key in completed_keys
            resp = requests.post(
                f"{NEW_URL}/rest/v1/progression",
                headers={**NEW_HEADERS, "Prefer": "resolution=merge-duplicates"},
                json={
                    "user_id": user_id,
                    "lesson_key": lesson_key,
                    "unlocked": True,
                    "completed": is_completed,
                    "completed_at": "now()" if is_completed else None
                }
            )
            status = "✓ completed" if is_completed else "~ unlocked"
            print(f"    {status}: {lesson_key}")


if __name__ == "__main__":
    print("═══ KidsCode User Migration ═══")
    print(f"Migrating 3 users to: {NEW_URL}")
    print()
    confirm = input("Continue? (yes/y): ")
    if confirm.lower() not in ("yes", "y"):
        print("Aborted.")
        exit()

    user_id_map = migrate_users()
    migrate_progress(user_id_map)

    print("\n═══ Migration Complete ═══")
    print(f"Migrated {len(user_id_map)} users")