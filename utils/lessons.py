# All lessons in order — this is the single source of truth
# key: used in URL and progression table
# title: shown in sidebar
# template: file in templates/lessons/

LESSONS = [
    {
        "key": "getting_started",
        "title": "🚀 Getting Started",
        "template": "lessons/getting_started.html",
        "part": None,
        "block_builder": None
    },
    {
        "key": "project_one",
        "title": "💡 Project 1 — Lights On",
        "template": "lessons/project_one.html",
        "part": None,
        "block_builder": None
    },
    # ... projects 2-10 same, block_builder: None

    {
        "key": "project_eleven",
        "title": "⚙️ Project 11 — Part 1",
        "template": "lessons/project_eleven_part_one.html",
        "part": "11",
        "block_builder": None        # ← no block builder on part 1
    },
    {
        "key": "project_twelve",
        "title": "🚨 Project 12 — Part 1",
        "template": "lessons/project_twelve_part_one.html",
        "part": "12",
        "block_builder": None
    },
    {
        "key": "project_thirteen",
        "title": "🔍 Project 13 — Part 1",
        "template": "lessons/project_thirteen_part_one.html",
        "part": "13",
        "block_builder": None
    },
    {
        "key": "project_fourteen_part_one",
        "title": "🏆 Project 14 — Part 1",
        "template": "lessons/project_fourteen_part_one.html",
        "part": "14",
        "block_builder": None
    },
    {
        "key": "project_fourteen_part_two",
        "title": "🏆 Project 14 — Part 2",
        "template": "lessons/project_fourteen_part_two.html",
        "part": "14",
        "block_builder": "patrol_alarm"  # ← update to correct preset
    },
    {
        "key": "challenge_one",
        "title": "🎯 Challenge",
        "template": "lessons/challenge_one.html",
        "part": None,
        "block_builder": None
    },
]

# Quick lookups
LESSON_BY_KEY = {l["key"]: l for l in LESSONS}
LESSON_SEQUENCE = [l["key"] for l in LESSONS]

def get_lesson(key):
    return LESSON_BY_KEY.get(key)

def get_next_lesson(key):
    if key in LESSON_SEQUENCE:
        idx = LESSON_SEQUENCE.index(key)
        if idx + 1 < len(LESSON_SEQUENCE):
            return LESSON_SEQUENCE[idx + 1]
    return None

def get_sidebar_groups(unlocked_keys):
    groups = {}
    standalone = []
    for lesson in LESSONS:
        if lesson["key"] not in unlocked_keys:
            continue
        if lesson["part"]:
            part = lesson["part"]
            if part not in groups:
                groups[part] = []
            groups[part].append(lesson)
        else:
            standalone.append(lesson)
    return standalone, groups