"""
lesson_scaffold.py — Generate lesson files from a JSON spec.

Usage:
    python utils/lesson_scaffold.py lesson_spec.json

Reads a unified spec and produces:
  - utils/project_{key}.py          (META + empty STEPS stub)
  - templates/lessons/{page_key}.html  (one per page)
  - Inserts entry/entries into utils/lessons.py

Spec format (see CLAUDE.md for full reference):
  is_multipart: false → single page, pages[0].page_type = "standard"
  is_multipart: true  → N pages, each with page_type: intro | build | completion
"""

import json
import os
import re
import sys


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_spec(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def safe_write(path, content, label):
    if os.path.exists(path):
        print(f"  ERROR: File already exists: {path}")
        print("  Delete it first or choose a different key.")
        sys.exit(1)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  Created: {label}")


def check_duplicate_key(key, lessons_path):
    with open(lessons_path, "r", encoding="utf-8") as f:
        content = f.read()
    if f'"key": "{key}"' in content:
        print(f"  WARNING: key '{key}' already in lessons.py — skipping that entry.")
        return True
    return False


# ---------------------------------------------------------------------------
# Project module (utils/project_{key}.py)
# ---------------------------------------------------------------------------

def generate_project_module(spec):
    key = spec["key"]
    meta_title = spec.get("meta_title", key)
    circuit_image = spec.get("circuit_image", f"{key}_circuit.png")
    banner_image = spec.get("banner_image")

    lesson_type = spec.get("lesson_type", "progression")

    lines = [
        "from utils.step_builder import build_step, intro_step, rect, circle, line, lbl",
        "",
        "",
        "META = {",
        f"    'title': {repr(meta_title)},",
        f"    'circuit_image': 'static/graphics/{circuit_image}',",
        f"    'banner_image': {repr(banner_image) if banner_image else 'None'},",
        f"    'lesson_type': {repr(lesson_type)},",
        "}",
        "",
        "",
        "# Wiring and component placement steps.",
        "# rect() / circle() / line() coordinates are placeholders —",
        "# update with real pixel coords once the circuit image is available.",
        "STEPS = []",
        "",
        "",
        "SKETCH_PRESET = {",
        "    'sketch': 'void setup() {}\\n\\nvoid loop() {}',",
        "    'default_view': 'blocks',",
        "    'read_only': False,",
        "    'lock_view': False,",
        "    'fill_values': True,",
        "    'fill_conditions': True,",
        "}",
        "",
        "",
        "PROJECT = {",
        '    "meta": META,',
        '    "steps": STEPS,',
        '    "drawer": {},',
        '    "presets": {',
        '        "default": SKETCH_PRESET,',
        '    }',
        "}",
        "",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Template generators
# ---------------------------------------------------------------------------

def _banner_block(banner_image, alt="Banner"):
    """Conditional banner snippet."""
    if not banner_image:
        return ""
    return (
        f'{{% set banner_image = "{banner_image}" %}}\n'
    )


def _banner_img_html():
    return (
        "{%- if banner_image %}\n"
        '<img src="{{ url_for(\'static\', filename=\'graphics/\' + banner_image) }}"\n'
        '     alt="Banner"\n'
        '     style="width:100%;border-radius:12px;margin-bottom:24px;">\n'
        "{%- endif %}"
    )


def _next_button(lesson_key, label, note):
    return (
        '<div style="display:flex;align-items:center;gap:16px;margin-top:24px;">\n'
        '    <form method="POST" action="{{ url_for(\'lessons.complete_lesson_route\') }}">\n'
        f'        <input type="hidden" name="lesson_key" value="{lesson_key}">\n'
        f'        <button type="submit" class="next-btn">{label}</button>\n'
        '    </form>\n'
        f'    <p>⬅️ {note}</p>\n'
        '</div>'
    )


def _circuit_tabs(circuit_image, lesson_key):
    return f"""<div class="lesson-tabs">
    <button class="lesson-tab-btn active" onclick="showTab('overview', this)">
        📋 Quick Overview
    </button>
    <button class="lesson-tab-btn" onclick="showTab('stepbystep', this)">
        🔧 Step-by-Step
    </button>
</div>

<div class="lesson-tab-panel active" id="tab-overview">
    {{{{ hover_zoom("static/graphics/{circuit_image}", height=500, key="{lesson_key}")|safe }}}}
</div>

<div class="lesson-tab-panel" id="tab-stepbystep">
    {{% if assembly_guide_html %}}
    {{{{ assembly_guide_html|safe }}}}
    {{% endif %}}
</div>

<script>
function showTab(name, btn) {{
    document.querySelectorAll('.lesson-tab-panel').forEach(function(p) {{
        p.classList.remove('active');
    }});
    document.querySelectorAll('.lesson-tab-btn').forEach(function(b) {{
        b.classList.remove('active');
    }});
    document.getElementById('tab-' + name).classList.add('active');
    btn.classList.add('active');
}}
</script>"""


# --- standard (single lesson, uses project_base.html) ---

def generate_standard_template(page, spec):
    key = page["key"]
    banner = page.get("banner_image", "")
    title = page.get("title", key)
    project_title_display = page.get("project_title_display", title)
    circuit_image = page.get("circuit_image", spec.get("circuit_image", ""))
    intro_html = page.get("intro_html", "<p>TODO: intro content</p>")
    parts_html = page.get("parts_html", "<ul class='parts-list'><li>TODO: parts list</li></ul>")
    tips_html = page.get("tips_html", "<p>TODO: tips</p>")

    lines = [
        '{% extends "lessons/project_base.html" %}',
    ]
    if banner:
        lines.append(f'{{% set banner_image = "{banner}" %}}')
    lines += [
        f'{{% block title %}}{title} — KidsCode{{% endblock %}}',
        "",
        f'{{% set project_title = "{project_title_display}" %}}',
        f'{{% set circuit_image = "{circuit_image}" %}}',
        "",
        "{% block intro %}",
        intro_html,
        "{% endblock %}",
        "",
        "{% block parts %}",
        parts_html,
        "{% endblock %}",
        "",
        "{% block tips %}",
        '<div class="tips-box">',
        tips_html,
        "</div>",
        "{% endblock %}",
        "",
    ]
    return "\n".join(lines)


# --- intro page (multi-part, no circuit, story setup) ---

def generate_intro_template(page, spec):
    key = page["key"]
    banner = page.get("banner_image", spec.get("banner_image", ""))
    title = page.get("title", key)
    headline = page.get("headline", title)
    intro_html = page.get("intro_html", "<p>TODO: intro narrative</p>")
    mission_box_html = page.get("mission_box_html", "")
    learn_html = page.get("learn_html", "")
    next_label = page.get("next_button_label", "Next Step →")
    next_note = page.get("next_button_note", "Click here to begin!")

    mission_block = ""
    if mission_box_html:
        mission_block = (
            '\n<div class="mission-box" '
            'style="background:#f8f9fa;padding:20px;border-left:5px solid #333;'
            'border-radius:8px;margin:20px 0;">\n'
            f"    {mission_box_html}\n"
            "</div>"
        )

    learn_block = f"\n{learn_html}" if learn_html else ""

    lines = [
        '{% extends "lesson_base.html" %}',
    ]
    if banner:
        lines.append(f'{{% set banner_image = "{banner}" %}}')
    lines += [
        f'{{% block title %}}{title} — KidsCode{{% endblock %}}',
        "",
        "{% block lesson_content %}",
        "",
        _banner_img_html(),
        "",
        '<div class="lesson-intro">',
        f"    <h2>{headline}</h2>",
        f"    {intro_html}",
        mission_block,
        learn_block,
        "</div>",
        "",
        "<hr>",
        "",
        _next_button(key, next_label, next_note),
        "",
        "{% endblock %}",
        "",
    ]
    return "\n".join(lines)


# --- build page (multi-part, has circuit + block builder + checklist) ---

def generate_build_template(page, spec):
    key = page["key"]
    banner = page.get("banner_image", spec.get("banner_image", ""))
    circuit_image = page.get("circuit_image", spec.get("circuit_image", ""))
    title = page.get("title", key)
    headline = page.get("headline", title)
    intro_html = page.get("intro_html", "<p>TODO: how the system works</p>")
    flow_html = page.get("flow_html", "")
    builder_note = page.get("builder_note_html",
        "<p>Use the block builder button in the bottom right corner to assemble your code.</p>")
    checklist_items = page.get("checklist_items", [])
    next_label = page.get("next_button_label", "Next Step →")
    next_note = page.get("next_button_note", "Click here to continue!")
    has_circuit = page.get("has_circuit", True)

    flow_block = ""
    if flow_html:
        flow_block = (
            "\n    <hr>\n\n"
            '    <h3>🔁 The Flow of Your Program</h3>\n'
            f"    {flow_html}"
        )

    checklist_block = ""
    if checklist_items:
        items_html = "\n".join(
            f'        <li>✅ {item}</li>' for item in checklist_items
        )
        checklist_block = (
            "\n<hr>\n\n"
            '<div class="mission-checklist" '
            'style="background:#e9f7ef;padding:20px;border-radius:12px;border-left:5px solid #28a745;">\n'
            "    <h3>🎯 Your Mission Objectives</h3>\n"
            '    <ul style="list-style:none;padding-left:0;">\n'
            f"{items_html}\n"
            "    </ul>\n"
            "</div>"
        )

    circuit_block = ""
    if has_circuit and circuit_image:
        circuit_block = f"\n<hr>\n\n{_circuit_tabs(circuit_image, key)}"

    lines = [
        '{% extends "lesson_base.html" %}',
    ]
    if banner:
        lines.append(f'{{% set banner_image = "{banner}" %}}')
    lines += [
        f'{{% block title %}}{title} — KidsCode{{% endblock %}}',
        "",
        "{% block lesson_content %}",
        "",
        _banner_img_html(),
        "",
        '<div class="lesson-intro">',
        f"    <h2>{headline}</h2>",
        f"    {intro_html}",
        flow_block,
        "</div>",
        circuit_block,
        "",
        "<hr>",
        "",
        '<div class="block-builder-section" style="margin:30px 0;">',
        "    <h3>🧩 Build Your Code</h3>",
        f"    {builder_note}",
        "</div>",
        checklist_block,
        "",
        "<hr>",
        "",
        _next_button(key, next_label, next_note),
        "",
        "{% endblock %}",
        "",
    ]
    return "\n".join(lines)


# --- completion page (multi-part, celebration + what's next) ---

def generate_completion_template(page, spec):
    key = page["key"]
    banner = page.get("banner_image", spec.get("banner_image", ""))
    title = page.get("title", key)
    headline = page.get("headline", "Mission Complete!")
    celebration_html = page.get("celebration_html", "<p>Congratulations!</p>")
    built_items = page.get("built_items", [])
    learned_items = page.get("learned_items", [])
    next_ideas = page.get("next_ideas", [])

    built_html = ""
    if built_items:
        items = "\n".join(f"            <li>{item}</li>" for item in built_items)
        built_html = (
            "\n    <div"
            ' class="mission-box" style="background:#f8f9fa;padding:20px;'
            'border-left:5px solid #333;border-radius:8px;margin:20px 0;">\n'
            "        <p>Your system can now:</p>\n"
            '        <ul>\n'
            f"{items}\n"
            "        </ul>\n"
            "    </div>"
        )

    learned_html = ""
    if learned_items:
        items = "\n".join(f"        <li>{item}</li>" for item in learned_items)
        learned_html = (
            "\n    <h3>🧠 What You Just Learned</h3>\n"
            '    <ul>\n'
            f"{items}\n"
            "    </ul>"
        )

    ideas_html = ""
    if next_ideas:
        idea_items = []
        for idea in next_ideas:
            emoji = idea.get("emoji", "🚀")
            idea_title = idea.get("title", "Next Project")
            desc = idea.get("desc", "")
            idea_items.append(
                f'            <li>{emoji} <strong>{idea_title}</strong>'
                + (f"<br>{desc}" if desc else "")
                + "</li>"
            )
        ideas_html = (
            "\n    <h3>🚀 What Else Can You Build?</h3>\n"
            '    <div class="mission-box" style="background:#eef6ff;padding:20px;'
            'border-left:5px solid #4a90e2;border-radius:8px;margin:20px 0;">\n'
            "        <ul>\n"
            + "\n".join(idea_items)
            + "\n        </ul>\n"
            "    </div>"
        )

    lines = [
        '{% extends "lesson_base.html" %}',
    ]
    if banner:
        lines.append(f'{{% set banner_image = "{banner}" %}}')
    lines += [
        f'{{% block title %}}{title} — KidsCode{{% endblock %}}',
        "",
        "{% block lesson_content %}",
        "",
        _banner_img_html(),
        "",
        '<div class="lesson-intro">',
        f"    <h2>🎉 {headline}</h2>",
        f"    {celebration_html}",
        built_html,
        learned_html,
        ideas_html,
        '    <p><strong>You are no longer just coding… you are engineering. 🚀</strong></p>',
        "</div>",
        "",
        "<hr>",
        "",
        "{% endblock %}",
        "",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Route dispatch
# ---------------------------------------------------------------------------

TEMPLATE_GENERATORS = {
    "standard":   generate_standard_template,
    "intro":      generate_intro_template,
    "build":      generate_build_template,
    "completion": generate_completion_template,
}


def generate_template_for_page(page, spec):
    page_type = page.get("page_type", "standard")
    gen = TEMPLATE_GENERATORS.get(page_type)
    if not gen:
        print(f"  WARNING: Unknown page_type '{page_type}' — falling back to intro template.")
        gen = generate_intro_template
    return gen(page, spec)


# ---------------------------------------------------------------------------
# lessons.py insertion
# ---------------------------------------------------------------------------

def build_registry_entry(page_key, title, part_group, block_builder):
    part_str = f'"{part_group}"' if part_group else "None"
    bb_str = f'"{block_builder}"' if block_builder else "None"
    return (
        f'    {{\n'
        f'        "key": "{page_key}",\n'
        f'        "title": "{title}",\n'
        f'        "template": "lessons/{page_key}.html",\n'
        f'        "part": {part_str},\n'
        f'        "block_builder": {bb_str}\n'
        f'    }},'
    )


def insert_registry_entries(entries, lessons_path):
    with open(lessons_path, "r", encoding="utf-8") as f:
        content = f.read()

    insert_marker = "\n]"
    insert_pos = content.rfind(insert_marker)
    if insert_pos == -1:
        print("  ERROR: Could not find end of LESSONS list in lessons.py")
        return

    block = "\n" + "\n".join(entries)
    new_content = content[:insert_pos] + block + "\n" + content[insert_pos:]

    with open(lessons_path, "w", encoding="utf-8") as f:
        f.write(new_content)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    if len(sys.argv) < 2:
        print("Usage: python utils/lesson_scaffold.py lesson_spec.json")
        sys.exit(1)

    spec_path = sys.argv[1]
    if not os.path.exists(spec_path):
        print(f"ERROR: Spec file not found: {spec_path}")
        sys.exit(1)

    spec = load_spec(spec_path)
    key = spec["key"]
    pages = spec.get("pages", [])
    part_group = spec.get("part_group")

    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    lessons_path = os.path.join(script_dir, "lessons.py")
    templates_dir = os.path.join(project_root, "templates", "lessons")

    print(f"\nGenerating lesson: {key}")
    print(f"  Pages: {len(pages)}")
    if part_group:
        print(f"  Part group: {part_group}")
    print()

    # 1. Project module
    module_path = os.path.join(script_dir, f"{key}.py")
    safe_write(module_path, generate_project_module(spec), f"utils/{key}.py")

    # 2. Templates — one per page
    for page in pages:
        page_key = page["key"]
        template_path = os.path.join(templates_dir, f"{page_key}.html")
        content = generate_template_for_page(page, spec)
        safe_write(template_path, content, f"templates/lessons/{page_key}.html")

    # 3. Registry entries
    entries_to_insert = []
    for page in pages:
        page_key = page["key"]
        if check_duplicate_key(page_key, lessons_path):
            continue
        entry = build_registry_entry(
            page_key=page_key,
            title=page.get("title", page_key),
            part_group=part_group if len(pages) > 1 else None,
            block_builder=page.get("block_builder"),
        )
        entries_to_insert.append(entry)

    if entries_to_insert:
        insert_registry_entries(entries_to_insert, lessons_path)
        print(f"  Updated: utils/lessons.py ({len(entries_to_insert)} entries added)")

    # 4. Post-generation checklist
    circuit_image = spec.get("circuit_image")
    banner_image = spec.get("banner_image")
    print()
    print("Done. Remaining manual steps:")
    if banner_image:
        print(f"  [ ] Add banner image  → static/graphics/{banner_image}")
    if circuit_image:
        print(f"  [ ] Add circuit image → static/graphics/{circuit_image}")
        print(f"  [ ] Update rect()/circle()/line() coordinates in utils/{key}.py")
        print(f"  [ ] Add wiring build_step entries for each wire connection")
    print(f"  [ ] Run /lesson-sketch to generate sketch steps")
    print(f"  [ ] Run /lesson-drawer to generate drawer content")
    for page in pages:
        print(f"  [ ] Test at /lessons/{page['key']}")
    print(f"  [ ] Delete lesson_spec.json")
    print()


if __name__ == "__main__":
    main()
