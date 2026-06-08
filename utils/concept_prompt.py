"""
LLM prompt builder for project concept generation.

Reads the project_analyzer output and produces a prompt asking the LLM
to decide what the next project should be — balancing component variety,
concept progression, difficulty curve, and theme freshness.

Output is a JSON object describing the next project concept.
"""

import json

SYSTEM_PROMPT = "Output only raw JSON. No markdown fences. No explanation. No preamble."

USER_PROMPT_TEMPLATE = """\
You are a curriculum designer for a kids Arduino coding platform (ages 8–14).
Based on analysis of {project_count} existing projects, decide what project #{next_number} should be.

══ EXISTING PROJECT ANALYSIS ══

Component usage frequency (how many projects use each):
{component_frequency}

Components NOT yet used or barely used (prioritise these):
{least_used}

Arduino concepts NOT yet covered in any project:
{concepts_not_covered}

Difficulty distribution so far: {difficulty_distribution}
(We need more medium and hard projects — skew toward medium or hard)

Existing project titles (avoid repeating themes):
{existing_titles}

Average step count in progression projects: ~{avg_steps}
Target: 6–10 coding steps for medium, 10–13 for hard.

══ AVAILABLE COMPONENTS ══
LED, BUTTON, BUZZER, LDR (light sensor), HC_SR04 (ultrasonic distance),
SLIDE_SWITCH, SERVO

Choose 2–4 components. Prefer at least one underused component.
Multi-component combinations make more interesting projects.

══ NARRATIVE THEMES (pick something fresh) ══
Used before: basic blink, traffic light, alarm systems, distance sensors.
Fresh ideas: weather station, game controller, robot arm, music machine,
greenhouse monitor, escape room prop, scoreboard, pet feeder, intruder alert,
race car, magic wand, safe cracker, submarine sonar, haunted house effect.

══ OUTPUT FORMAT ══
{{
  "project_key":    "project_{next_key_word}",
  "project_number": {next_number},
  "title":          "Project {next_number}: Short Title",
  "meta_title":     "Project {next_number}: Short Title",
  "display_title":  "🎯 Project {next_number} — Full Title with Emoji",
  "theme":          "one sentence describing the narrative context",
  "narrative":      "one sentence describing the student's role",
  "age_group":      "8-10" | "11-12" | "13-14",
  "difficulty":     "easy" | "medium" | "hard",
  "lesson_type":    "progression",
  "components":     ["COMPONENT1", "COMPONENT2"],
  "step_count":     8,
  "topic":          "one sentence — what the system does, for the sketch generator"
}}

Rules:
- difficulty must be medium or hard (we have too many easy projects)
- age_group should vary (we need more 13-14 projects)
- components list must only use: LED, BUTTON, BUZZER, LDR, HC_SR04, SLIDE_SWITCH, SERVO
- step_count: easy=5-7, medium=8-11, hard=12-14
- topic must describe the Arduino behaviour precisely enough to write code from it

Generate the concept JSON now:
"""


def build_prompt(analysis):
    """
    Return (system_prompt, user_message) for the concept LLM call.

    Args:
        analysis — dict returned by project_analyzer.analyze_all()
    """
    freq = analysis["component_frequency"]
    freq_lines = "\n".join(
        f"  {c}: {n} project(s)" for c, n in sorted(freq.items(), key=lambda x: -x[1])
    )
    # Add components with 0 uses
    all_comps = {"LED", "BUTTON", "BUZZER", "LDR", "HC_SR04", "SLIDE_SWITCH", "SERVO"}
    for c in sorted(all_comps):
        if c not in freq:
            freq_lines += f"\n  {c}: 0 project(s)"

    least_used = ", ".join(analysis["least_used_components"]) or "none"
    not_covered = ", ".join(analysis["concepts_not_yet_covered"]) or "none"

    diff = analysis["difficulty_distribution"]
    diff_str = f"easy={diff['easy']}, medium={diff['medium']}, hard={diff['hard']}"

    titles = "\n".join(f"  - {t}" for t in analysis["themes_titles"])

    # Derive the word form of next_number (e.g. 19 → "nineteen")
    _NUM_TO_WORD = {
        1: "one", 2: "two", 3: "three", 4: "four", 5: "five",
        6: "six", 7: "seven", 8: "eight", 9: "nine", 10: "ten",
        11: "eleven", 12: "twelve", 13: "thirteen", 14: "fourteen",
        15: "fifteen", 16: "sixteen", 17: "seventeen", 18: "eighteen",
        19: "nineteen", 20: "twenty",
    }
    next_number  = analysis["next_number"]
    next_key     = analysis["next_key"]  # e.g. "project_nineteen"
    next_key_word = next_key.replace("project_", "")  # e.g. "nineteen"

    user_message = USER_PROMPT_TEMPLATE.format(
        project_count=analysis["project_count"],
        next_number=next_number,
        next_key_word=next_key_word,
        component_frequency=freq_lines,
        least_used=least_used,
        concepts_not_covered=not_covered,
        difficulty_distribution=diff_str,
        existing_titles=titles,
        avg_steps=analysis["avg_step_count"],
    )
    return SYSTEM_PROMPT, user_message


if __name__ == "__main__":
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from utils.project_analyzer import analyze_all
    analysis = analyze_all()
    system, user = build_prompt(analysis)
    print("=" * 60)
    print("SYSTEM")
    print("=" * 60)
    print(system)
    print()
    print("=" * 60)
    print("USER")
    print("=" * 60)
    print(user)
