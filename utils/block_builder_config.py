from utils.presets import PRESETS, PIN_REFS
from flask import render_template
import json
from utils.block_parser import parse_sketch, parse_steps, collect_types

def build_config(preset, username=None, page=None, supabase_url=None, supabase_key=None, lock_mode=None, is_overlay=False):    
    # resolve preset → sketch string + drawer + meta
    from utils.project_registry import PROJECTS
    from utils.presets import PRESETS
    if preset in PROJECTS:
        proj = PROJECTS[preset]
        p = proj.get("presets", {}).get("default")
    elif preset in PRESETS:
        p = PRESETS[preset]
        # Get view settings from preset
    else:
        for proj in PROJECTS.values():
            if "presets" in proj and preset in proj["presets"]:
                p = proj["presets"][preset]
                break

    dv = p.get('default_view', 'blocks') if isinstance(p, dict) else 'blocks'
    lv = p.get('lock_view', False) if isinstance(p, dict) else False
    rv = p.get('read_only', False) if isinstance(p, dict) else False

    sketch = proj["presets"]["default"]["sketch"]
    drawer = proj.get("drawer", {})
    
    # parse
    is_progression = '//>> ' in sketch
    if is_progression:
        steps = parse_steps(sketch)
        config = {
            "mode": "progression",
            "steps": steps,
            "palette": None,
            "master": None,
        }
    else:
        _fill_conditions = p.get('fill_conditions', False) if isinstance(p, dict) else False
        _fill_values = p.get('fill_values', False) if isinstance(p, dict) else False

        blocks = parse_sketch(sketch, fill_conditions=_fill_conditions, fill_values=_fill_values)
        master = parse_sketch(sketch, fill_conditions=True, fill_values=True)
        palette = list(collect_types(blocks['global'] + blocks['setup'] + blocks['loop']))
        config = {
            "mode": "free",
            "blocks": blocks,
            "master": master,
            "palette": palette,
        }
    
    # add everything else
    config.update({
        "username": username,
        "page": str(page) if page else None,
        "supabase_url": supabase_url or "",
        "supabase_key": supabase_key or "",
        "drawer": drawer,
        "lock_mode": lock_mode or False,
        "is_overlay": is_overlay,
        "default_view": dv,      # ← is this here?
        "lock_view": lv,         # ← and this?
        "readonly_mode": rv
    })
    
    return config


def render_builder(preset, username=None, page=None, **kwargs):
    config = build_config(preset, username, page, **kwargs)
    config_json = json.dumps(config)
    return render_template("block_builder.html", config=config_json)




  