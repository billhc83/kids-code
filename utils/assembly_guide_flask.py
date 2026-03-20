"""
Flask version of assembly_guide.
Pre-renders all step images server-side and returns an HTML widget
with JavaScript-driven step navigation.
"""
import io
import base64
import math
from PIL import Image, ImageDraw, ImageFont  # type: ignore


def draw_step_overlay(image_path: str, step: dict) -> bytes:
    """
    Draws highlight overlays for a single step.
    Returns PNG bytes.
    """
    img = Image.open(image_path).convert("RGBA")
    w, h = img.size

    COLORS = {
        "active":   (255, 165,   0, 220),
        "greyout":  (  0,   0,   0, 160),
        "label_bg": ( 20,  20,  20, 210),
        "label_fg": (255, 255, 255, 255),
        "arrow":    (255,  80,  80, 240),
    }

    active_color = COLORS["active"]
    if "color" in step:
        hx = step["color"].lstrip("#")
        r, g, b = tuple(int(hx[i:i+2], 16) for i in (0, 2, 4))
        active_color = (r, g, b, 220)

    raw_highlights = step.get("highlights", [])
    if "highlight" in step:
        raw_highlights = [{"pos": step["highlight"], "shape": "circle"}] + list(raw_highlights)

    # ── GREYOUT ──────────────────────────────────────────────────────────────
    if step.get("greyout", False) and raw_highlights:
        veil = Image.new("RGBA", img.size, (0, 0, 0, 0))
        vd = ImageDraw.Draw(veil)
        vd.rectangle([(0, 0), (w, h)], fill=COLORS["greyout"])

        for hl in raw_highlights:
            shape = hl.get("shape", "circle")
            pos = hl["pos"]
            pad = 2

            if shape == "rect":
                x1, y1, x2, y2 = pos
                vd.rounded_rectangle(
                    [(x1-pad, y1-pad), (x2+pad, y2+pad)],
                    radius=12, fill=(0, 0, 0, 0)
                )
            elif shape in ("line", "polyline"):
                points = pos
                line_width = hl.get("width", 20) + pad * 2
                for i in range(len(points) - 1):
                    x1, y1 = points[i]
                    x2, y2 = points[i + 1]
                    dx, dy = x2 - x1, y2 - y1
                    length = math.sqrt(dx*dx + dy*dy)
                    if length > 0:
                        angle = math.atan2(dy, dx)
                        half_w = line_width / 2
                        cos_a = math.cos(angle)
                        sin_a = math.sin(angle)
                        perp_x = -sin_a * half_w
                        perp_y = cos_a * half_w
                        poly = [
                            (x1 + perp_x, y1 + perp_y),
                            (x1 - perp_x, y1 - perp_y),
                            (x2 - perp_x, y2 - perp_y),
                            (x2 + perp_x, y2 + perp_y),
                        ]
                        vd.polygon(poly, fill=(0, 0, 0, 0))
                    vd.ellipse([
                        (x1 - line_width/2, y1 - line_width/2),
                        (x1 + line_width/2, y1 + line_width/2)
                    ], fill=(0, 0, 0, 0))
                    if i == len(points) - 2:
                        vd.ellipse([
                            (x2 - line_width/2, y2 - line_width/2),
                            (x2 + line_width/2, y2 + line_width/2)
                        ], fill=(0, 0, 0, 0))
            elif shape == "directed_arrow":
                x1, y1 = pos[0]
                x2, y2 = pos[1]
                arrow_w = 20 + pad * 2
                dx, dy = x2 - x1, y2 - y1
                length = math.sqrt(dx*dx + dy*dy)
                if length > 0:
                    angle = math.atan2(dy, dx)
                    hw = arrow_w / 2
                    cos_a, sin_a = math.cos(angle), math.sin(angle)
                    poly = [
                        (x1 + -sin_a*hw, y1 + cos_a*hw),
                        (x1 - -sin_a*hw, y1 - cos_a*hw),
                        (x2 - -sin_a*hw, y2 - cos_a*hw),
                        (x2 + -sin_a*hw, y2 + cos_a*hw),
                    ]
                    vd.polygon(poly, fill=(0, 0, 0, 0))
                vd.ellipse([(pos[0][0]-arrow_w//2, pos[0][1]-arrow_w//2),
                            (pos[0][0]+arrow_w//2, pos[0][1]+arrow_w//2)], fill=(0,0,0,0))
                vd.ellipse([(pos[1][0]-arrow_w//2, pos[1][1]-arrow_w//2),
                            (pos[1][0]+arrow_w//2, pos[1][1]+arrow_w//2)], fill=(0,0,0,0))
            else:
                cx, cy = pos[0], pos[1]
                r = hl.get("radius", 25) + 2
                vd.ellipse([(cx-r, cy-r), (cx+r, cy+r)], fill=(0, 0, 0, 0))

        img = Image.alpha_composite(img, veil)

    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # ── DRAW HIGHLIGHTS ───────────────────────────────────────────────────────
    for hl in raw_highlights:
        shape = hl.get("shape", "circle")
        pos = hl["pos"]

        if shape == "directed_arrow":
            ax, ay = pos[0]
            bx, by = pos[1]
            shaft_color = (255, 80, 80, 240)
            draw.line([(ax, ay), (bx, by)], fill=shaft_color, width=4)
            angle = math.atan2(by - ay, bx - ax)
            head_len = 22
            head_ang = math.pi / 6
            draw.polygon([
                (bx, by),
                (bx - head_len * math.cos(angle - head_ang),
                 by - head_len * math.sin(angle - head_ang)),
                (bx - head_len * math.cos(angle + head_ang),
                 by - head_len * math.sin(angle + head_ang)),
            ], fill=shaft_color)

    # ── LABELS ────────────────────────────────────────────────────────────────
    base_label_pos = None
    if raw_highlights:
        first = raw_highlights[0]
        pos = first["pos"]
        base_label_pos = (pos[0], pos[1])

    labels = []
    if "labels" in step:
        labels = step["labels"]
    elif "label" in step:
        labels = [step["label"]]

    for label_item in labels:
        if isinstance(label_item, dict):
            label_text = label_item.get("text", "")
            offset_x = label_item.get("offset_x", 30)
            offset_y = label_item.get("offset_y", -14)
            font_size = label_item.get("font_size", 14)
            custom_pos = label_item.get("pos")
        else:
            label_text = label_item
            offset_x = 30
            offset_y = -14
            font_size = 14
            custom_pos = None

        if custom_pos:
            lx, ly = custom_pos
        elif base_label_pos:
            lx = base_label_pos[0] + offset_x
            ly = base_label_pos[1] + offset_y
        else:
            continue

        try:
            font = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
        except:
            try:
                font = ImageFont.truetype(
                    "/System/Library/Fonts/Helvetica.ttc", font_size)
            except:
                font = ImageFont.load_default()

        bbox = draw.textbbox((0, 0), label_text, font=font)
        text_w = bbox[2] - bbox[0] + 14
        text_h = bbox[3] - bbox[1] + 8
        draw.rounded_rectangle(
            [(lx - 6, ly - 4), (lx + text_w, ly + text_h)],
            radius=6, fill=COLORS["label_bg"]
        )
        draw.text((lx, ly), label_text, fill=COLORS["label_fg"], font=font)

    final = Image.alpha_composite(img, overlay)
    buf = io.BytesIO()
    final.convert("RGB").save(buf, format="PNG")
    return buf.getvalue()


def image_to_b64(image_path: str) -> str:
    """Convert an image file to base64 string."""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def render_assembly_guide(image_path: str, steps: list, project_title: str) -> str:
    """
    Pre-renders all step images and returns a self-contained HTML widget
    with JavaScript-driven step navigation.
    """
    # Pre-render all step images as base64
    step_images = []
    for i, step in enumerate(steps):
        if step.get("highlights") or step.get("highlight"):
            img_bytes = draw_step_overlay(image_path, step)
            b64 = base64.b64encode(img_bytes).decode()
        else:
            # Intro step or no highlights — show plain image
            with open(image_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
        step_images.append(b64)

    # Build step data for JavaScript
    import json
    steps_js = json.dumps([
        {
            "instruction": s.get("instruction", ""),
            "tip": s.get("tip", ""),
            "image": step_images[i]
        }
        for i, s in enumerate(steps)
    ])

    total = len(steps)

    return f"""
<div class="assembly-guide" id="assembly-guide">
    <div class="ag-header">
        <h3>🔧 {project_title}</h3>
        <p>Follow the steps below — build one connection at a time!</p>
    </div>

    <div class="ag-progress">
        <span id="ag-step-label">STEP 1 OF {total}</span>
        <div class="ag-progress-bar">
            <div class="ag-progress-fill" id="ag-progress-fill"
                 style="width:{int(1/total*100)}%"></div>
        </div>
        <span id="ag-pct">{ int(1/total*100) }%</span>
    </div>

    <div class="ag-body">
        <div class="ag-image-wrap">
            <img id="ag-image" src="data:image/png;base64,{step_images[0]}"
                 alt="Circuit diagram step">
        </div>

        <div class="ag-card">
            <div class="ag-instruction" id="ag-instruction">
                {steps[0].get('instruction', '')}
            </div>
            <div class="ag-tip" id="ag-tip" style="display: {'block' if steps[0].get('tip') else 'none'}">
                { ('💡 ' + steps[0].get('tip', '')) if steps[0].get('tip') else '' }
            </div>
        </div>
    </div>

    <div class="ag-nav">
        <button class="ag-btn" id="ag-prev" onclick="agPrev()" disabled>
            ← Previous
        </button>
        <span id="ag-dots"></span>
        <button class="ag-btn ag-btn-primary" id="ag-next" onclick="agNext()">
            Next →
        </button>
    </div>
</div>

<script>
(function() {{
    var steps = {steps_js};
    var current = 0;
    var total = {total};

    function buildDots() {{
        var dots = document.getElementById('ag-dots');
        dots.innerHTML = '';
        for (var i = 0; i < total; i++) {{
            var d = document.createElement('span');
            d.className = 'ag-dot' + (i === current ? ' active' : '');
            d.setAttribute('data-idx', i);
            d.onclick = function() {{ goTo(parseInt(this.getAttribute('data-idx'))); }};
            dots.appendChild(d);
        }}
    }}

    function goTo(idx) {{
        current = idx;
        var step = steps[current];
        document.getElementById('ag-image').src = 'data:image/png;base64,' + step.image;
        document.getElementById('ag-instruction').innerHTML = step.instruction;
        var tip = document.getElementById('ag-tip');
        if (tip) {{
            tip.style.display = step.tip ? 'block' : 'none';
            tip.innerHTML = step.tip ? '💡 ' + step.tip : '';
        }}
        document.getElementById('ag-step-label').textContent =
            'STEP ' + (current + 1) + ' OF ' + total;
        var pct = Math.round((current + 1) / total * 100);
        document.getElementById('ag-progress-fill').style.width = pct + '%';
        document.getElementById('ag-pct').textContent = pct + '%';
        document.getElementById('ag-prev').disabled = current === 0;
        document.getElementById('ag-next').disabled = current === total - 1;
        buildDots();
    }}

    window.agPrev = function() {{ if (current > 0) goTo(current - 1); }};
    window.agNext = function() {{ if (current < total - 1) goTo(current + 1); }};

    buildDots();
}})();
</script>
"""