"""
utils/step_builder.py
─────────────────────
Clean helper functions for building assembly_guide step dicts.

These produce exactly the same dict format that assembly_guide.py already
accepts — they just remove the boilerplate so your page files stay short.

WORKFLOW
────────
1.  Use coordinate_picker() in assembly_guide.py to click coords on your image.
    It copies the raw snippet to your clipboard automatically.

2.  Paste the snippet, then wrap it with build_step() here:

        # Raw snippet from coordinate_picker:
        {"pos": (601, 216, 719, 310), "shape": "rect"}

        # Becomes:
        build_step("Place switch in row 4, col H.", "Arms the engine.", rect(601, 216, 719, 310))

3.  For wire polylines, coordinate_picker also gives you the full polyline dict.
    Same deal — paste it as line((x,y), (x,y), ...) inside build_step().

IMPORT
──────
    from utils.step_builder import build_step, intro_step, rect, circle, line, lbl
"""


# ══════════════════════════════════════════════════════════
#  SHAPE HELPERS
#  These produce the highlight dicts assembly_guide expects
# ══════════════════════════════════════════════════════════

def rect(x1, y1, x2, y2):
    """Rectangle highlight around a component area."""
    return {"pos": (x1, y1, x2, y2), "shape": "rect"}


def circle(cx, cy, radius=60):
    """Circle highlight on a single pin or hole."""
    return {"pos": (cx, cy), "shape": "circle", "radius": radius}


def line(*points, width=20):
    """
    Polyline highlight — traces a wire path across multiple points.
    Pass each point as a (x, y) tuple.

        line((370, 340), (723, 341), (722, 209), (680, 208))
    """
    return {"pos": list(points), "shape": "polyline", "width": width}


def arrow(x1, y1, x2, y2):
    """
    Straight arrow from (x1, y1) to (x2, y2). Arrowhead at the end point.

        arrow(200, 150, 450, 320)
    """
    return {"pos": [(x1, y1), (x2, y2)], "shape": "directed_arrow"}


def lbl(text, offset_x=0, offset_y=90, font_size=16, pos=None):
    """
    A text label to overlay on the image.

    Two placement modes:
      Offset from first highlight (original behaviour):
        lbl("Long Leg", offset_x=100, offset_y=90)

      Absolute pixel position — use when placing via the step builder tool:
        lbl("Long Leg", pos=(420, 310))

    Pass a list of these as the `labels` keyword arg in build_step().
    """
    d = {"text": text, "offset_x": offset_x, "offset_y": offset_y, "font_size": font_size}
    if pos is not None:
        d["pos"] = pos
    return d


# ══════════════════════════════════════════════════════════
#  STEP BUILDERS
# ══════════════════════════════════════════════════════════

def intro_step(instruction, tip):
    """
    The first step in every guide — no highlights, just a title card.

        intro_step("Engage Engines!!!!", "Press next for a step-by-step guide")
    """
    return {"instruction": instruction, "tip": tip}


def build_step(instruction, tip, *highlights, labels=None, greyout=True, color=None):
    """
    Build a single assembly step dict.

    Args:
        instruction  HTML string — the main instruction shown on the card.
        tip          Plain string — the green tip box below the instruction.
        *highlights  Any number of rect(), circle(), or line() dicts.
        labels       Optional list of lbl() dicts overlaid on the image.
        greyout      Dim everything outside the highlights (default True).
        color        Optional hex color string e.g. "#e74c3c".

    Returns:
        dict ready to drop straight into your STEPS list.

    ── Examples ──────────────────────────────────────────────────────────────

    Simplest — one rect:
        build_step(
            "Place the switch in row 4, column H.",
            "This arms the engine system.",
            rect(601, 216, 719, 310),
        )

    Wire trace:
        build_step(
            "Place one end of the wire into Arduino Pin 9.<br>"
            "Place the other end in row 5, column I.",
            "This lets the Arduino see the switch position.",
            line((370, 340), (723, 341), (722, 209), (680, 208)),
        )

    Multiple shapes + labels:
        build_step(
            "Place the long leg of the LED in row 22, column E.<br>"
            "Place the short leg in row 21, column E.",
            "This is the Engines Armed light.",
            rect(935, 175, 1069, 347),
            line((919, 57), (995, 317)),
            circle(922, 44),
            labels=[lbl("Long Leg", offset_x=100), lbl("Short Leg", offset_x=-100)],
        )
    """
    step = {
        "instruction": instruction,
        "tip":         tip,
        "greyout":     greyout,
    }
    if highlights:
        step["highlights"] = list(highlights)
    if labels:
        step["labels"] = labels
    if color:
        step["color"] = color
    return step