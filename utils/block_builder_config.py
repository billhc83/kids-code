from utils.presets import PRESETS, PIN_REFS
from flask import render_template
import json
from utils.block_parser import parse_sketch, parse_steps, collect_types

def build_config(preset, username=None, page=None, supabase_url=None, supabase_key=None, lock_mode=None, is_overlay=False):    
    # resolve preset → sketch string + drawer + meta
    from utils.project_registry import PROJECTS

    proj = None  # parent PROJECT (drawer, meta); None for legacy PRESETS-only entries
    p = None     # resolved preset dict: { sketch, default_view, ... }

    print(f"[build_config] preset={preset!r}  in_PROJECTS={preset in PROJECTS}  in_PRESETS={preset in PRESETS}", flush=True)
    if preset in PROJECTS:
        proj = PROJECTS[preset]
        p = proj.get("presets", {}).get("default")
        print(f"[build_config] found in PROJECTS  presets keys={list((proj.get('presets') or {}).keys())}  p type={type(p).__name__}", flush=True)
    elif preset in PRESETS:
        p = PRESETS[preset]
    else:
        for proj_candidate in PROJECTS.values():
            presets = proj_candidate.get("presets") or {}
            if preset in presets:
                proj = proj_candidate
                p = presets[preset]
                break

    if p is None:
        raise ValueError(f"Unknown block builder preset: {preset!r}")

    sketch = p.get("sketch") if isinstance(p, dict) else p
    print(f"[build_config] sketch present={bool(sketch)}  is_progression={'//>>' in (sketch or '')}  sketch[:80]={repr((sketch or '')[:80])}", flush=True)
    if not sketch or not isinstance(sketch, str):
        raise ValueError(f"Preset {preset!r} has no sketch string")

    drawer = proj.get("drawer", {}) if proj else {}

    dv = p.get('default_view', 'blocks') if isinstance(p, dict) else 'blocks'
    lv = p.get('lock_view', False) if isinstance(p, dict) else False
    rv = p.get('read_only', False) if isinstance(p, dict) else False
    
    # parse (progression markers are //>> lines; allow with or without space after >>)
    is_progression = '//>>' in sketch
    if is_progression:
        steps = parse_steps(sketch)
        print(f"[build_config] parse_steps → {len(steps) if steps else 'None'} steps  labels={[s['label'] for s in steps] if steps else []}", flush=True)
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
        "readonly_mode": rv,
        "force_preset": True
    })
    
    return config


def render_builder(preset, username=None, page=None, **kwargs):
    config = build_config(preset, username, page, **kwargs)
    config_json = json.dumps(config).replace('</', '<\\/')    
    return render_template("block_builder.html", config=config_json)




  