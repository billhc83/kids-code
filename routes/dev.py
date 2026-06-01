from flask import Blueprint, render_template, abort
from utils.project_registry import PROJECTS
import json

dev_bp = Blueprint('dev', __name__, url_prefix='/dev')


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
