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
    {
        "key": "project_two",
        "title": "🚦 Project 2 — Blinking Beacon",
        "template": "lessons/project_two.html",
        "part": None,
        "block_builder": None
    },
    {
        "key": "project_three",
        "title": "🎚️ Project 3 — Fading Light",
        "template": "lessons/project_three.html",
        "part": None,
        "block_builder": None
    },
    {
        "key": "project_four",
        "title": "🎨 Project 4 — Color Mixer",
        "template": "lessons/project_four.html",
        "part": None,
        "block_builder": None
    },
    {
        "key": "project_five",
        "title": "🎶 Project 5 — The Light Harp",
        "template": "lessons/project_five.html",
        "part": None,
        "block_builder": None
    },
    {
        "key": "project_six",
        "title": "🌊 Project 6 — Deep Sea Explorer",
        "template": "lessons/project_six.html",
        "part": None,
        "block_builder": None
    },
    {
        "key": "project_seven",
        "title": "🚨 Project 7 — Intruder Alarm",
        "template": "lessons/project_seven.html",
        "part": None,
        "block_builder": None
    },
    {
        "key": "project_eight",
        "title": "🎱 Project 8 — Magic 8-Ball",
        "template": "lessons/project_eight.html",
        "part": None,
        "block_builder": None
    },
    {
        "key": "project_nine",
        "title": "🔐 Project 9 — Password Vault",
        "template": "lessons/project_nine.html",
        "part": None,
        "block_builder": None
    },
    {
        "key": "project_ten",
        "title": "⚡️ Project 10 — Reaction Game",
        "template": "lessons/project_ten.html",
        "part": None,
        "block_builder": None
    },
    {
        "key": "challenge_one",
        "title": "🎯 Challenge",
        "template": "lessons/challenge_one.html",
        "part": None,
        "block_builder": None
    },
    {
        "key": "project_eleven",
        "title": "⚙️ Project 11 ",
        "template": "lessons/project_eleven.html",
        "part": None,
        "block_builder": "engine_start"    
    },
    {
        "key": "project_twelve",
        "title": "🚨 Project 12",
        "template": "lessons/project_twelve.html",
        "part": None,
        "block_builder": "patrol_alarm"
    },
    {
        "key": "project_thirteen",
        "title": "🔍 Project 13",
        "template": "lessons/project_thirteen.html",
        "part": None,
        "block_builder": "reaction_timer"
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
        "block_builder": "codebreaker"  # ← update to correct preset
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
    return list(reversed(standalone)), dict(reversed(groups.items()))