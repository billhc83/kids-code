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
    {"key": "block_builder_tutorial",
        "title": "How to use the block builder",
        "template": "lessons/block_builder_tutorial.html",
        "part": None,
        "block_builder": "block_builder_tutorial"
    },
    {
        "key": "project_one",
        "title": "💡 Lights On",
        "template": "lessons/project_one.html",
        "part": None,
        "block_builder": "project_one"
    },
    {
        "key": "project_two",
        "title": "🚦 Blinking Beacon",
        "template": "lessons/project_two.html",
        "part": None,
        "block_builder": "project_two"
    },
    {
        "key": "project_three",
        "title": "🎚️ Mad Scientist Button",
        "template": "lessons/project_three.html",
        "part": None,
        "block_builder": "project_three"
    },
    {
        "key": "project_four",
        "title": "🎨 Launch Button",
        "template": "lessons/project_four.html",
        "part": None,
        "block_builder": "project_four"
    },
    {
        "key": "project_five",
        "title": "🎶 Spy Data",
        "template": "lessons/project_five.html",
        "part": None,
        "block_builder": "project_five"
    },
    {
        "key": "project_six",
        "title": "🌊 Deep Sea Explorer",
        "template": "lessons/project_six.html",
        "part": None,
        "block_builder": "project_six"
    },
    {
        "key": "project_seven",
        "title": "🚨 Automatic Night Light",
        "template": "lessons/project_seven.html",
        "part": None,
        "block_builder": "project_seven"
    },
    {
        "key": "project_eight",
        "title": "🎱 Dragon Alarm",
        "template": "lessons/project_eight.html",
        "part": None,
        "block_builder": "project_eight"
    },
    {
        "key": "project_nine",
        "title": "🔐 Universal Power Slot",
        "template": "lessons/project_nine.html",
        "part": None,
        "block_builder": "project_nine"
    },
    {
        "key": "project_ten",
        "title": "⚡️ Spy Vault",
        "template": "lessons/project_ten.html",
        "part": None,
        "block_builder": "project_ten"
    },
    {
        "key": "challenge_one",
        "title": "🎯 Challenge",
        "template": "lessons/challenge_one.html",
        "part": None,
        "block_builder": "open_coding"
    },
    {
        "key": "project_eleven",
        "title": "⚙️ Jet Engine Start",
        "template": "lessons/project_eleven.html",
        "part": None,
        "block_builder": "project_eleven"    
    },
    {
        "key": "project_twelve",
        "title": "🚨 Night Patrol Academy",
        "template": "lessons/project_twelve.html",
        "part": None,
        "block_builder": "project_twelve"
    },
    {
        "key": "project_thirteen",
        "title": "🔍 Reaction Timer",
        "template": "lessons/project_thirteen.html",
        "part": None,
        "block_builder": "project_thirteen"
    },
    {
        "key": "project_fourteen_part_one",
        "title": "🏆 Code Breaker Part 1",
        "template": "lessons/project_fourteen_part_one.html",
        "part": "Code Breaker",
        "block_builder": None
    },
    {
        "key": "project_fourteen_part_two",
        "title": "🏆 Code Breaker Part 2",
        "template": "lessons/project_fourteen_part_two.html",
        "part": "Code Breaker",
        "block_builder": "project_fourteen"  # ← update to correct preset
    },
    {
        "key": "project_fourteen_part_three",
        "title": "🏆 Code Breaker Part 3",
        "template": "lessons/project_fourteen_part_three.html",
        "part": "Code Breaker",
        "block_builder": None  # ← update to correct preset
    },
    {
        "key": "project_fifteen_part_one",
        "title": "🏆 Backup Alarm Part 1",
        "template": "lessons/project_fifteen_part_one.html",
        "part": "Backup Alarm",
        "block_builder": None # ← update to correct preset
    },
    {
        "key": "project_fifteen_part_two",
        "title": "🏆 Backup Alarm Part 2",
        "template": "lessons/project_fifteen_part_two.html",
        "part": "Backup Alarm",
        "block_builder": "project_fifteen"  # ← update to correct preset
    },
    {
        "key": "project_fifteen_part_three",
        "title": "🏆 Backup Alarm Part 3",
        "template": "lessons/project_fifteen_part_three.html",
        "part": "Backup Alarm",
        "block_builder": "project_fifteen"  # ← update to correct preset
    },
    {
        "key": "project_sixteen",
        "title": "🔧 Broken Blinker",
        "template": "lessons/project_sixteen.html",
        "part": None,
        "block_builder": "project_sixteen"
    },

    {
        "key": "project_seventeen_part_one",
        "title": "🎻 Magical Harp Part 1",
        "template": "lessons/project_seventeen_part_one.html",
        "part": "Magical Harp",
        "block_builder": None
    },
    {
        "key": "project_seventeen_part_two",
        "title": "🎼 Magical Harp Part 2",
        "template": "lessons/project_seventeen_part_two.html",
        "part": "Magical Harp",
        "block_builder": "project_seventeen"
    },
    {
        "key": "project_seventeen_part_three",
        "title": "🏆 Magical Harp Part 3",
        "template": "lessons/project_seventeen_part_three.html",
        "part": "Magical Harp",
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
        if "challenge" in lesson["key"]:
            continue
        if lesson["part"]:
            part = lesson["part"]
            if part not in groups:
                groups[part] = []
            groups[part].append(lesson)
        else:
            standalone.append(lesson)

    # Build combined list in order then reverse
    combined = []
    seen_parts = set()
    for lesson in LESSONS:
        if lesson["key"] not in unlocked_keys:
            continue
        if "challenge" in lesson["key"]:
            continue
        if lesson["part"]:
            if lesson["part"] not in seen_parts:
                seen_parts.add(lesson["part"])
                combined.append({
                    "type": "group",
                    "part": lesson["part"],
                    "steps": groups[lesson["part"]]
                })
        else:
            combined.append({
                "type": "single",
                "lesson": lesson
            })

    combined.reverse()
    return combined, {}