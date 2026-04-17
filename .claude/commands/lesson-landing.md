# /lesson-landing — Generate Landing Page(s) for a New Lesson

Generates all landing page templates, the project module stub, and lessons.py registry entries
for a new lesson. Handles single-page and multi-part lessons.

---

## Step 1 — Gather inputs

Scan `utils/` for `project_*.py` files and identify the highest project number.
Check `utils/lessons.py` for key collisions.

Ask for all missing inputs in a **single message**:

- **`key`** — snake_case identifier. Default: next available (e.g. `project_eighteen`)
- **`title`** — display title with emoji
- **`description`** — what is the student building or learning? More detail = better content.
- **`age_range`** — `8-10` / `11-12` / `13-14`
- **`theme`** — narrative wrapper. If blank, choose one that fits and state your choice.
- **`number_of_pages`** — `1` = single page, `2+` = multi-part
- **`lesson_type`** — `progression` (default) or `troubleshoot`
- **`has_circuit`** — Yes/No. Default: Yes
- **`banner_exists`** — Yes/No

**If number_of_pages > 1**, also ask:
- Part group name (sidebar label grouping all parts)
- Role of each page. Offer these defaults:
  - 2 pages: `intro` + `build`
  - 3 pages: `intro` + `build` + `completion`
  - 4 pages: `intro` + `build` + `build` + `completion`

**If lesson_type = troubleshoot**, default to 2 pages: `intro` + `build`. No circuit tabs on build page.

Once the user replies, proceed immediately — no plan confirmation, no approval steps.

---

## Step 2 — Generate and write

Generate all content directly into `lesson_spec.json`. Do not display HTML in chat.

### Age calibration

**8–10:** Max 2 sentences/paragraph. Tangible analogies. Heavy emoji. Short words. Active voice.

**11–12:** Up to 4 sentences/paragraph. Machine/gadget analogies. Technical terms with inline definitions. Emoji for emphasis.

**13–14:** Full paragraphs. Technical vocabulary defined on first use. Real-world engineering analogies. Fewer emoji.

---

### Fields by page type

#### `standard` (single-page)

- `intro_html` — `<h2>Goal</h2>` one-sentence mission + emoji. Then `<h3>New ideas 💭</h3>` with `<hr>` separators and 2–4 concept subsections (`<h4>` + explanation + analogy). Concepts must relate directly to what the sketch teaches.
- `parts_html` — `<h2>🔌 Build the circuit</h2>` + `<h4>What parts do I need?</h4>` + `<ul class="parts-list">`. Each `<li>`: emoji + bold name + themed description.
- `tips_html` — 2–3 practical tips specific to THIS lesson. Emoji + bold title + 1–2 sentences. Not generic Arduino advice.

#### `intro` (multi-part)

- `headline` — themed `<h2>` text
- `intro_html` — 2–4 paragraphs setting the scene, ending with anticipation
- `mission_box_html` — callout box, 1–3 bullets describing what the system will do
- `learn_html` — `<h3>🛠 What You Will Learn</h3>` + `<ul>` with 3–5 outcome phrases
- `next_button_label` — themed. Example: `"Begin Mission →"`
- `next_button_note` — small helper text

#### `build` (multi-part)

- `headline` — role + project name
- `intro_html` — 1–2 paragraphs + `<h3>🧠 How the System Works</h3>` + `<ul style="list-style:none;padding-left:0;">` with 3–6 flow items: `emoji + <b>VERB</b> → plain description`
- `flow_html` — one sentence as a chain, wrapped in `<p style="text-align:center;font-weight:bold;background:#f0f0f0;padding:10px;border-radius:8px;">`
- `builder_note_html` — one sentence pointing to the block builder and listing categories
- `checklist_items` — array of 4–6 short verb-phrase mission objectives
- `next_button_label` and `next_button_note`

#### `completion` (multi-part)

- `headline` — title text (template adds 🎉)
- `celebration_html` — 1–2 celebratory sentences addressing the student by their role
- `built_items` — array of 4–6 strings, what the system can now do. Start with emoji. Present tense.
- `learned_items` — array of 4–6 strings, concepts mastered. Start with emoji.
- `next_ideas` — array of 3–4 objects: `{ "emoji": "🚀", "title": "...", "desc": "..." }`

---

### Spec structure

```json
{
  "key": "project_{key}",
  "meta_title": "Project N: Title",
  "age_group": "11-12",
  "theme": "chosen theme",
  "lesson_type": "progression",
  "banner_image": "project_{key}_banner.png",
  "circuit_image": "project_{key}_circuit.png",
  "is_multipart": true,
  "part_group": "Group Name",
  "pages": [
    {
      "key": "project_{key}_part_one",
      "title": "🎯 Title Part 1",
      "page_type": "intro",
      "block_builder": null,
      "banner_image": "project_{key}_banner.png",
      "has_circuit": false,
      "headline": "...",
      "intro_html": "...",
      "mission_box_html": "...",
      "learn_html": "...",
      "next_button_label": "Begin Mission →",
      "next_button_note": "Click here to begin!"
    },
    {
      "key": "project_{key}_part_two",
      "title": "🎯 Title Part 2",
      "page_type": "build",
      "block_builder": "project_{key}",
      "banner_image": "project_{key}_banner.png",
      "has_circuit": true,
      "circuit_image": "project_{key}_circuit.png",
      "headline": "...",
      "intro_html": "...",
      "flow_html": "...",
      "builder_note_html": "...",
      "checklist_items": ["...", "..."],
      "next_button_label": "Next Step →",
      "next_button_note": "Click here to continue!"
    },
    {
      "key": "project_{key}_part_three",
      "title": "🎯 Title Part 3",
      "page_type": "completion",
      "block_builder": null,
      "banner_image": "project_{key}_banner.png",
      "has_circuit": false,
      "headline": "Mission Complete: ...",
      "celebration_html": "...",
      "built_items": ["...", "..."],
      "learned_items": ["...", "..."],
      "next_ideas": [
        {"emoji": "🚀", "title": "...", "desc": "..."}
      ]
    }
  ]
}
```

For a **single page** lesson: `is_multipart: false`, `part_group: null`, one page entry with
`page_type: "standard"` and fields `intro_html`, `parts_html`, `tips_html`, `project_title_display`.

Write the complete JSON to `lesson_spec.json` in the project root, then run:

```bash
python utils/lesson_scaffold.py lesson_spec.json
```

---

## Step 3 — Post-generation summary

Report what was created and what still needs doing:

```
✅ Files created:
   utils/project_{key}.py
   templates/lessons/{page_key}.html  (× N)
   utils/lessons.py updated

📋 Still needed:
   [ ] Add banner image  → static/graphics/project_{key}_banner.png
   [ ] Add circuit image → static/graphics/project_{key}_circuit.png
   [ ] Preview pages at /lessons/{page_key} — tell me any changes
   [ ] Run /lesson-sketch to generate the Arduino sketch and coding steps
   [ ] Run /lesson-drawer to generate drawer content from the sketch steps
   [ ] Update rect()/line() coordinates in utils/project_{key}.py after circuit image is ready
   [ ] Add wiring build_step entries in utils/project_{key}.py
   [ ] Delete lesson_spec.json
```
