# /lesson-landing — Generate Landing Page(s) for a New Lesson

This skill creates all landing page templates, the project module stub, and the lessons.py
registry entries for a new lesson. It handles single-page lessons and multi-part lessons
of any length.

Read CLAUDE.md before doing anything else — it contains the full architecture reference.

---

## Step 1 — Auto-detect next project number

Before asking the user anything, scan `utils/` for all `project_*.py` files and identify
the highest existing project number. Suggest the next one as the default key.

Also check `utils/lessons.py` to confirm no key collision.

Report to the user:
> "Next available project number is **16** — suggested key: `project_sixteen`
> (or tell me a different key/name)"

---

## Step 2 — Gather inputs

Ask for ALL missing inputs in a single message. Do not ask one at a time.

### Required inputs

**`key`**
Snake_case identifier. Used in filenames, URLs, and the registry.
Examples: `project_sixteen`, `project_dragon_alarm`
Default: auto-suggested from Step 1.

**`title`** (single page) or **`title_group`** (multi-part)
Display title with emoji. For multi-part this is the group name shown in the sidebar.
Example: `🐉 Dragon Fire Alarm`

**`description`**
Free text. What does this lesson do? What is the student building or learning?
No length limit — more detail produces better content.

**`age_range`**
One of: `8-10` / `11-12` / `13-14`

**`theme`**
The narrative wrapper for the lesson. Examples: spy mission, dragon taming, space station,
jungle expedition, undersea lab. If the user says "decide for me" or leaves it blank,
choose a theme that fits the description and age range, then state your choice.

**`number_of_pages`**
How many pages does this lesson have?
- `1` = standard single-page lesson (uses `project_base.html`)
- `2+` = multi-part lesson (uses `lesson_base.html` directly for each page)

**If number_of_pages > 1**, also ask:
- **Part group name** — the label shown in the sidebar grouping all parts together.
  Example: `"Backup Alarm"`, `"Dragon Fire Alarm"`
- **Role of each page** — for each page (Part 1, Part 2, etc.), what is its role?
  Offer these defaults and let the user adjust:
  - 2 pages: `intro` + `build`
  - 3 pages: `intro` + `build` + `completion`
  - 4 pages: `intro` + `build` + `build` + `completion`
  - Custom: user can specify any combination of `intro`, `build`, `completion`

**`has_circuit`**
Does this lesson involve a physical circuit the student builds?
Yes/No. If yes, circuit tabs (Quick Overview + Step-by-Step) appear on `build` pages.
Default: Yes.

**`banner_exists`**
Will a banner image be provided? Yes/No.
If yes, the filename defaults to `project_{key}_banner.png`.
If no, the template falls back to the `<h1>` title only.

**`block_builder`**
Does this lesson use the block builder IDE?
Yes/No. If yes, which pages? (Defaults to all `build` pages.)

**`lesson_type`**
`progression` (default) or `troubleshoot`.

This is stored in the project's `META` dict and read automatically by
`/lesson-sketch` and `/lesson-drawer` — the user never has to specify it again.

- `progression` — standard build-up lesson. Student constructs code step by step.
- `troubleshoot` — broken code is pre-loaded. Student diagnoses and fixes it.

**If `lesson_type = troubleshoot`**, the page structure changes automatically:
- Number of pages defaults to **2**: `intro` + `build`
  - `intro` page — sets up the broken scenario: what the system *should* do,
    what is currently going wrong, and the student's mission to fix it.
    No parts list. No "what you'll learn" list. Pure narrative setup.
  - `build` page — no circuit tabs. Open block builder. This is the workspace
    where the student edits the broken code. The drawer provides the hints.
- `has_circuit` still applies — if the lesson has a circuit it built in a prior
  lesson, the circuit image can optionally be shown for reference.

---

## Step 3 — Plan

Before generating any content, present a plan to the user:

```
Lesson plan: [key]
─────────────────────────────────────────────
Theme: [chosen theme]
Age range: [age_range]
Pages: [N]

Page 1 ([page_type]): [suggested title] — [one-line role description]
Page 2 ([page_type]): [suggested title] — [one-line role description]
...

Files to be created:
  utils/project_{key}.py
  templates/lessons/{page_key}.html  (× N)
  utils/lessons.py — N entries added under part group "[part_group]"

Banner: project_{key}_banner.png [exists / text fallback]
Circuit: project_{key}_circuit.png [yes / no]
```

Ask: "Does this look right? Any changes before I generate the content?"

Do not proceed until the user confirms.

---

## Step 4 — Generate page content

Generate content for each page one at a time. Show each page to the user and wait
for approval or corrections before moving to the next.

### Age calibration (apply to ALL content)

**Ages 8–10:**
- Maximum 2 sentences per paragraph.
- Use physical, tangible analogies (toys, games, food).
- Heavy emoji. Short words. Avoid all jargon.
- Active voice always: "Your Arduino sends a signal" not "A signal is sent."

**Ages 11–12:**
- Up to 4 sentences per paragraph.
- Analogies can involve machines, vehicles, gadgets.
- Some technical terms introduced with inline plain-English definitions.
- Emoji used for emphasis, not decoration.

**Ages 13–14:**
- Full sentences, paragraph-length explanations acceptable.
- Technical vocabulary used properly, defined on first use.
- Analogies can reference real-world engineering or science concepts.
- Fewer emoji, more substance.

---

### Content for each page type

#### `standard` page (single-page lesson)

Generate three HTML blocks:

**`intro_html`** — goes into `{% block intro %}`
- `<h2>Goal</h2>` with a one-sentence mission statement and emoji
- `<h3>New ideas 💭</h3>` section with `<hr>` separators
- 2–4 concept subsections, each with:
  - `<h4>` heading (themed to the narrative)
  - Age-appropriate explanation
  - Concrete analogy or example
- The concepts should directly relate to what the sketch teaches

**`parts_html`** — goes into `{% block parts %}`
- `<h2>🔌 Build the circuit</h2>` (or equivalent themed heading)
- `<h4>What parts do I need?</h4>`
- `<ul class="parts-list">` with one `<li>` per component
  - Each item: emoji + component name in bold + fun themed description
  - Example: `<li>🔴 <strong>Red LED</strong> — The dragon's eye!</li>`

**`tips_html`** — goes into `{% block tips %}`
- 2–3 practical tips specific to this lesson
- Each tip: emoji + bold title + one or two sentences
- Focus on common mistakes or "aha moments" for this specific project
- Not generic Arduino advice — specific to THIS lesson's components and code

---

#### `intro` page (multi-part)

Generate these fields:

**`headline`**
The `<h2>` text. Theme-driven. Example: `🕵️ Mission Briefing: Dragon Fire System`

**`intro_html`**
2–4 paragraphs. Sets the scene. Introduces the student's role in the narrative.
Ends by creating anticipation for what they are about to build.

**`mission_box_html`** (optional but recommended)
A callout box with a clear description of what the system will do.
Format: 1–3 short bullet points or sentences inside a `<p>` tag.
Example: "Your system will detect heat using a sensor and trigger a fire alarm."

**`learn_html`** (optional)
`<h3>🛠 What You Will Learn</h3>` + `<ul>` with 3–5 items.
List the skills and concepts this lesson covers.
Phrase as outcomes: "How to read a sensor", "How to use conditional logic", etc.

**`next_button_label`**
Text on the "Next" button. Theme it.
Examples: `"Begin Mission →"`, `"Start Building →"`, `"Accept Mission →"`

**`next_button_note`**
Small text next to the button. Example: `"Click here to start your mission!"`

---

#### `build` page (multi-part)

Generate these fields:

**`headline`**
The `<h2>` text. Role + project name.
Example: `🔧 Engineer: Dragon Fire Detection System`

**`intro_html`**
1–2 paragraphs. Brief reminder of what the student is building and why this page matters.
Then `<h3>🧠 How the System Works</h3>` followed by a `<ul style="list-style:none;padding-left:0;">` 
with 3–6 items showing the data/logic flow of the system using this pattern:
```html
<li>🔥 <b>DETECT</b> → The sensor reads heat levels<br><br></li>
<li>🧠 <b>DECIDE</b> → The system checks if it is dangerous<br><br></li>
<li>🚨 <b>REACT</b> → LEDs and buzzer trigger the alarm</li>
```
Each item: emoji + `<b>VERB</b>` + arrow + plain-English description.

**`flow_html`**
One sentence showing the program loop as a chain.
Wrap in: `<p style="text-align:center;font-weight:bold;background:#f0f0f0;padding:10px;border-radius:8px;">`
Example: `READ SENSOR → CALCULATE → CHECK ZONES → TRIGGER ALARM`

**`builder_note_html`**
One sentence telling the student where the block builder is and what categories they'll use.
Example: `<p>Use the block builder in the bottom right to assemble: <b>Variables</b>, <b>Sensors</b>, <b>Logic</b>, and <b>Outputs</b>.</p>`

**`checklist_items`**
Array of strings. 4–6 mission objectives. Short verb phrases.
Example: `["Set up system memory", "Read the sensor", "Calculate distance", "Control LEDs", "Trigger the buzzer"]`

**`next_button_label`** and **`next_button_note`**
As above.

---

#### `completion` page (multi-part)

Generate these fields:

**`headline`**
Just the title text (the template adds 🎉 automatically).
Example: `Mission Complete: Dragon Fire Alarm`

**`celebration_html`**
1–2 short celebratory sentences. Address the student by their role in the narrative.
Example: `<p>🐉 Outstanding work, Dragon Tamer!</p><p>You have built a fully working fire detection system.</p>`

**`built_items`**
Array of strings. What the system can now do. 4–6 items.
Start with emoji. Use present tense.
Example: `"🔥 Detect heat levels using a temperature sensor"`

**`learned_items`**
Array of strings. Programming/hardware concepts mastered. 4–6 items.
Start with emoji. Brief.
Example: `"📦 Variables to store sensor readings"`

**`next_ideas`**
Array of objects. 3–4 project ideas that extend what was built.
Each: `{ "emoji": "🚗", "title": "Vehicle Heat Monitor", "desc": "Track engine temperature and warn when it overheats." }`
Ideas should feel achievable and directly connected to what was just built.

---

## Step 5 — Build the spec and write the files

Once all pages are approved, construct the full `lesson_spec.json`.

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

For a **single page** lesson, `is_multipart` is `false`, `part_group` is `null`, and
`pages` contains one entry with `page_type: "standard"` and the fields
`intro_html`, `parts_html`, `tips_html`, `project_title_display`.

### Write the spec file

Write the complete JSON to `lesson_spec.json` in the project root.

### Run the scaffold

```bash
python utils/lesson_scaffold.py lesson_spec.json
```

Show the user the output from the script.

---

## Step 6 — Post-generation summary

After the script runs successfully, give the user this checklist:

```
✅ Files created:
   utils/project_{key}.py
   templates/lessons/{page_key}.html  (× N)
   utils/lessons.py updated

📋 Still needed:
   [ ] Add banner image  → static/graphics/project_{key}_banner.png
   [ ] Add circuit image → static/graphics/project_{key}_circuit.png  (if circuit lesson)
   [ ] Run /lesson-sketch to generate the Arduino sketch and coding steps
   [ ] Run /lesson-drawer to generate drawer content from the sketch steps
   [ ] Update rect()/line() coordinates in utils/project_{key}.py after circuit image is ready
   [ ] Add wiring build_step entries in utils/project_{key}.py
   [ ] Test each page at /lessons/{page_key}
   [ ] Delete lesson_spec.json
```
