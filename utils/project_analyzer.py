"""
Project Analyzer — reads all existing project_*.py modules and returns
a structured analysis dict for use by the concept generator.

Extracts: component usage frequency, difficulty distribution, age groups,
themes, step counts, sketch complexity, and what's been covered so far.
Run as a script to print the analysis as JSON.
"""

import importlib
import json
import re
import sys
import os

# Component signatures in sketches — used to infer components when not
# explicitly listed anywhere accessible.
_COMPONENT_SIGNATURES = {
    "LED":          [r"digitalWrite\(", r"ledPin", r"LED"],
    "BUTTON":       [r"digitalRead\(", r"buttonPin", r"INPUT_PULLUP", r"BTN"],
    "BUZZER":       [r"tone\(", r"noTone\(", r"buzzer", r"BUZZ"],
    "LDR":          [r"analogRead\(", r"ldrPin", r"LDR", r"photoresistor", r"lightPin"],
    "HC_SR04":      [r"pulseIn\(", r"trigPin", r"echoPin", r"HC_SR04", r"sonar"],
    "SLIDE_SWITCH": [r"slidePin", r"switchPin", r"SLIDE", r"SW\d"],
    "SERVO":        [r"servo\.", r"Servo\s", r"servoPin", r"\.attach\(", r"\.write\("],
}


def _infer_components(sketch_text):
    """Return the set of component types detectable in a sketch string."""
    found = set()
    for ctype, patterns in _COMPONENT_SIGNATURES.items():
        for pat in patterns:
            if re.search(pat, sketch_text, re.IGNORECASE):
                found.add(ctype)
                break
    return sorted(found)


def _count_steps(sketch_text):
    """Count //>> step markers, excluding Mission Complete."""
    markers = [l for l in sketch_text.splitlines() if l.startswith("//>>")]
    coding_steps = [m for m in markers if "Mission Complete" not in m]
    return len(coding_steps), len(markers)


def _detect_concepts(sketch_text):
    """Return a list of Arduino concepts used in the sketch."""
    concepts = []
    checks = {
        "if/else":      r"\belse\b",
        "while loop":   r"\bwhile\s*\(",
        "for loop":     r"\bfor\s*\(",
        "analogRead":   r"\banalogRead\b",
        "pulseIn":      r"\bpulseIn\b",
        "millis":       r"\bmillis\b",
        "micros":       r"\bmicros\b",
        "tone":         r"\btone\b",
        "map":          r"\bmap\b",
        "constrain":    r"\bconstrain\b",
        "Serial":       r"\bSerial\b",
        "servo":        r"\bServo\b",
        "random":       r"\brandom\b",
        "analogWrite":  r"\banalogWrite\b",
    }
    for concept, pat in checks.items():
        if re.search(pat, sketch_text):
            concepts.append(concept)
    return concepts


def analyze_all():
    """
    Scan utils/project_*.py files and return a full analysis dict.

    Returns:
    {
      "project_count": 18,
      "next_number":   19,
      "next_key":      "project_nineteen",
      "projects": [
        {
          "key":        "project_one",
          "number":     1,
          "title":      "Project 1: ...",
          "lesson_type": "progression",
          "components": ["LED", "BUTTON"],
          "step_count": 6,
          "total_steps": 7,   # including Mission Complete
          "concepts":   ["if/else", "tone"],
          "has_servo":  False,
          "has_sensor": False,
        }, ...
      ],
      "component_frequency": {"LED": 12, "BUTTON": 8, ...},
      "least_used_components": ["SERVO", "SLIDE_SWITCH"],
      "concepts_covered": ["if/else", "tone", "analogRead", ...],
      "concepts_not_yet_covered": [...],
      "difficulty_distribution": {"easy": 6, "medium": 8, "hard": 4},
      "avg_step_count": 7.4,
      "themes_titles": ["Project 1: Blink", "Project 2: ..."],
    }
    """
    utils_dir = os.path.join(os.path.dirname(__file__))
    project_files = sorted(
        f for f in os.listdir(utils_dir)
        if re.match(r"project_\w+\.py$", f) and f != "project_registry.py"
    )

    # Word-to-number map for key → number extraction
    _WORD_TO_NUM = {
        "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
        "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
        "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14,
        "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18,
        "nineteen": 19, "twenty": 20,
    }
    _NUM_TO_WORD = {v: k for k, v in _WORD_TO_NUM.items()}

    projects = []
    component_freq = {}
    all_concepts = set()
    difficulty_dist = {"easy": 0, "medium": 0, "hard": 0}

    for fname in project_files:
        module_name = fname.replace(".py", "")
        word = module_name.replace("project_", "")
        number = _WORD_TO_NUM.get(word, 0)

        try:
            # Ensure the project root (parent of utils/) is on sys.path
            project_root = os.path.dirname(utils_dir)
            if project_root not in sys.path:
                sys.path.insert(0, project_root)
            mod = importlib.import_module(f"utils.{module_name}")
        except Exception:
            continue

        proj = getattr(mod, "PROJECT", None)
        if proj is None:
            continue

        meta  = proj.get("meta", {})
        title = meta.get("title", module_name)
        lesson_type = meta.get("lesson_type", "progression")

        sketch_text = ""
        presets = proj.get("presets", {})
        if isinstance(presets, dict):
            default = presets.get("default", {})
            if isinstance(default, dict):
                sketch_text = default.get("sketch", "")

        components    = _infer_components(sketch_text)
        coding_steps, total_steps = _count_steps(sketch_text)
        concepts      = _detect_concepts(sketch_text)

        # Rough difficulty from step count
        if coding_steps <= 5:
            difficulty = "easy"
        elif coding_steps <= 9:
            difficulty = "medium"
        else:
            difficulty = "hard"
        difficulty_dist[difficulty] += 1

        for ctype in components:
            component_freq[ctype] = component_freq.get(ctype, 0) + 1

        all_concepts.update(concepts)

        projects.append({
            "key":         module_name,
            "number":      number,
            "title":       title,
            "lesson_type": lesson_type,
            "components":  components,
            "step_count":  coding_steps,
            "total_steps": total_steps,
            "concepts":    concepts,
            "has_servo":   "SERVO" in components,
            "has_sensor":  any(c in components for c in ("LDR", "HC_SR04")),
            "difficulty":  difficulty,
        })

    projects.sort(key=lambda p: p["number"])

    max_num      = max((p["number"] for p in projects), default=0)
    next_number  = max_num + 1
    next_key     = f"project_{_NUM_TO_WORD.get(next_number, str(next_number))}"

    all_possible_concepts = {
        "if/else", "while loop", "for loop", "analogRead", "pulseIn",
        "millis", "micros", "tone", "map", "constrain", "Serial", "servo",
        "random", "analogWrite",
    }

    # What components exist in the registry but haven't been used much
    all_registry_components = {"LED", "BUTTON", "BUZZER", "LDR", "HC_SR04", "SLIDE_SWITCH", "SERVO"}
    sorted_by_use = sorted(all_registry_components, key=lambda c: component_freq.get(c, 0))
    least_used = [c for c in sorted_by_use if component_freq.get(c, 0) < 3]

    avg_steps = (sum(p["step_count"] for p in projects) / len(projects)) if projects else 0

    return {
        "project_count":             len(projects),
        "next_number":               next_number,
        "next_key":                  next_key,
        "projects":                  projects,
        "component_frequency":       component_freq,
        "least_used_components":     least_used,
        "concepts_covered":          sorted(all_concepts),
        "concepts_not_yet_covered":  sorted(all_possible_concepts - all_concepts),
        "difficulty_distribution":   difficulty_dist,
        "avg_step_count":            round(avg_steps, 1),
        "themes_titles":             [p["title"] for p in projects],
    }


if __name__ == "__main__":
    analysis = analyze_all()
    print(json.dumps(analysis, indent=2))
