import json
from flask import Blueprint, request, session, render_template, abort
from utils.decorators import login_required
from config import SUPABASE_URL, SUPABASE_ANON_KEY

builder_bp = Blueprint('builder', __name__)

def normalize_drawer_steps(steps):
    result = []
    for step in steps:
        s = dict(step)
        if isinstance(s.get('tabs'), dict):
            s['tabs'] = [{'id': k, **v} for k, v in s['tabs'].items()]
        result.append(s)
    return result

@builder_bp.route("/parse", methods=["POST"])
def parse():
    from utils.block_parser import parse_sketch
    data = request.get_json()
    code = data.get("code", "")
    return parse_sketch(code, fill_conditions=True, fill_values=True)

@builder_bp.route("/sim/run", methods=["POST"])
@login_required
def sim_run():
    from utils.sim_engine import run as engine_run
    data = request.get_json(silent=True) or {}
    sketch = data.get('sketch', '')
    sim_config = data.get('sim_config', {})
    try:
        result = engine_run(sketch, sim_config)
        return result
    except Exception as e:
        return {'error': str(e)}, 400

@builder_bp.route("/builder")
@login_required
def builder_endpoint():
    from utils.block_builder_config import build_config
    
    preset = request.args.get("preset", "codebreaker")
    page = request.args.get("page") or preset

    config = build_config(
        preset=preset,
        username=session.get("user_id"),
        page=page,
        supabase_url=SUPABASE_URL,
        supabase_key=SUPABASE_ANON_KEY,
        is_overlay=False,
    )
    config_json = json.dumps(config).replace('</', '<\\/')
    return render_template("block_builder_fragment.html", config=config_json)

@builder_bp.route("/preset/<name>")
@login_required
def get_preset(name):
    from utils.block_parser import parse_steps, parse_sketch
    from utils.project_registry import PROJECTS
    from utils.presets import PRESETS
    from utils.contents_flask import DRAWER_CONTENT

    sketch_code = None
    drawer_content = None
    default_view = "blocks"
    fill_values = False
    fill_conditions = False

    if name in PROJECTS:
        p = PROJECTS[name]
        preset_obj = p.get("presets", {}).get("default", {})
        if isinstance(preset_obj, dict):
            sketch_code = preset_obj.get("sketch")
            default_view = preset_obj.get("default_view", "blocks")
            fill_values = preset_obj.get("fill_values", False)
            fill_conditions = preset_obj.get("fill_conditions", False)
        else:
            sketch_code = preset_obj

        d = p.get("drawer")
        if d:
            if isinstance(d, dict):
                drawer_content = d.get(name) or d.get("default") or (d if "title" in d or "tabs" in d else None)
            else:
                drawer_content = d
    else:
        for p in PROJECTS.values():
            if "presets" in p and name in p["presets"]:
                preset_obj = p["presets"][name]
                if isinstance(preset_obj, dict):
                    sketch_code = preset_obj.get("sketch")
                    default_view = preset_obj.get("default_view", "blocks")
                    fill_values = preset_obj.get("fill_values", False)
                    fill_conditions = preset_obj.get("fill_conditions", False)
                else:
                    sketch_code = preset_obj
                d = p.get("drawer")
                if d:
                    if isinstance(d, dict):
                        drawer_content = d.get(name) or d.get("default") or (d if "title" in d or "tabs" in d else None)
                    else:
                        drawer_content = d
                break

    if not sketch_code:
        preset = PRESETS.get(name)
        if not preset: abort(404)
        if isinstance(preset, dict):
            sketch_code = preset['sketch']
            default_view = preset.get('default_view', 'blocks')
            fill_values = preset.get('fill_values', False)
            fill_conditions = preset.get('fill_conditions', False)
        else:
            sketch_code = preset
        drawer_content = DRAWER_CONTENT.get(name)

    if sketch_code and '//>>' in sketch_code:
        progression_data = parse_steps(sketch_code)
        parsed_sketch = None
    elif sketch_code:
        progression_data = None
        parsed_sketch = parse_sketch(sketch_code, fill_conditions=fill_conditions, fill_values=fill_values)
    else:
        progression_data = None
        parsed_sketch = None

    return {
        "sketch": sketch_code,
        "drawer_content": drawer_content,
        "default_view": default_view,
        "progression_data": progression_data,
        "parsed_sketch": parsed_sketch,
    }

@builder_bp.route("/standalone_ide/<preset>")
@login_required
def standalone_ide(preset):
    from utils.project_registry import PROJECTS
    from utils.contents_flask import DRAWER_CONTENT

    page = request.args.get("page") or preset
    drawer_content = None
    default_view = "blocks"

    if page in PROJECTS:
        proj = PROJECTS[page]
        d = proj.get("drawer")
        if d:
            if isinstance(d, dict):
                drawer_content = d.get(preset) or d.get("default") or (d if "title" in d or "tabs" in d else None)
            else:
                drawer_content = d
        
        p_data = proj.get("presets", {}).get(preset) or proj.get("presets", {}).get("default")
        if isinstance(p_data, dict):
            default_view = p_data.get("default_view", "blocks")
    
    if not drawer_content:
        for p in PROJECTS.values():
            if "drawer" in p and isinstance(p["drawer"], dict) and preset in p["drawer"]:
                drawer_content = p["drawer"][preset]
                break

    if not drawer_content:
        drawer_content = DRAWER_CONTENT.get(preset)

    if drawer_content and isinstance(drawer_content, dict) and isinstance(drawer_content.get("tabs"), dict):
        drawer_content = drawer_content.copy()
        drawer_content["tabs"] = list(drawer_content["tabs"].values())

    drawer_steps = []
    if isinstance(drawer_content, list):
        drawer_steps = normalize_drawer_steps(drawer_content)
    elif isinstance(drawer_content, dict):
        drawer_steps = normalize_drawer_steps(drawer_content.get("steps") or [drawer_content])
        
    return render_template(
        "components/arduino_interface.html",
        drawer_steps=drawer_steps,
        preset=preset,
        default_view=default_view
    )
