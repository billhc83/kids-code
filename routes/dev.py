from flask import Blueprint, render_template, abort
from utils.project_registry import PROJECTS
from utils.assembly_guide_flask import render_assembly_guide
import importlib
import json
import os

dev_bp = Blueprint('dev', __name__, url_prefix='/dev')

_COMPARE_DIR = os.path.join(os.path.dirname(__file__), '..', 'static', 'circuit_compare')


@dev_bp.route('/circuit/sandbox')
def circuit_sandbox():
    all_keys = [k for k, p in PROJECTS.items() if p.get('circuit_definition')]
    return render_template(
        'dev/circuit_preview.html',
        project_key='sandbox',
        project_title='JSON Sandbox',
        circuit_json=None,
        circuit_keys=all_keys,
    )


@dev_bp.route('/circuit/compare/<project_key>')
def circuit_compare(project_key):
    path = os.path.join(_COMPARE_DIR, f'{project_key}.json')
    if not os.path.exists(path):
        abort(404, description=f"No comparison found for '{project_key}'. Run: python -m utils.circuit_compare {project_key}")
    with open(path) as f:
        data = json.load(f)

    # Load the project module to build the PNG step builder for the left panel
    assembly_guide_html = None
    try:
        module = importlib.import_module(f'utils.project_{project_key}')
        steps = getattr(module, 'STEPS', [])
        meta  = getattr(module, 'META', {})
        image_path = meta.get('circuit_image', '')
        title = meta.get('title', project_key)
        if steps and image_path and os.path.exists(image_path):
            assembly_guide_html = render_assembly_guide(image_path, steps, title)
    except Exception:
        pass  # left panel degrades gracefully if module or image missing

    all_keys = [
        fn[:-5] for fn in os.listdir(_COMPARE_DIR)
        if fn.endswith('.json')
    ] if os.path.isdir(_COMPARE_DIR) else []

    return render_template(
        'dev/circuit_compare.html',
        project_key=project_key,
        assembly_guide_html=assembly_guide_html,
        generated_json=json.dumps(data['generated'], indent=2),
        llm_input=data.get('llm_input', {}),
        llm_output_json=json.dumps(data.get('llm_output', {}), indent=2),
        compare_keys=sorted(all_keys),
    )


@dev_bp.route('/circuit/<project_key>')
def circuit_preview(project_key):
    project = PROJECTS.get(project_key)
    if project is None:
        abort(404)
    circuit_def = project.get('circuit_definition')
    all_keys = [k for k, p in PROJECTS.items() if p.get('circuit_definition')]
    return render_template(
        'dev/circuit_preview.html',
        project_key=project_key,
        project_title=project.get('meta', {}).get('title', project_key),
        circuit_json=json.dumps(circuit_def, indent=2) if circuit_def else None,
        circuit_keys=all_keys,
    )
