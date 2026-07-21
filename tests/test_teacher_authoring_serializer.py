"""
Round-trip test for utils/teacher_authoring_serializer.py's materialize().

Fixture below hand-builds the StepDraft tree a teacher-authoring UI would
have produced for utils/project_eleven.py's real first four steps ("Setup
Pins" through "Capture: Buzzer Needs the Button Too") — the same steps
docs/superpowers/specs/2026-07-21-teacher-authoring-serializer-design.md
traces by hand in its own worked example. materialize()'s output is fed back
through the real parse_steps() and compared, structurally, against parsing
project_eleven's actual hand-authored sketch text — proving the serializer
produces something the existing block-builder pipeline can actually consume,
not just text that looks right.
"""

import utils.project_eleven as project_eleven
from utils.block_parser import parse_steps
from utils.teacher_authoring_serializer import materialize

FINAL_STEP_LINE = '//>> Mission Complete | open | blocks'


def _leaf(id_, flag, line, hint=None):
    return {'id': id_, 'kind': 'leaf', 'flag': flag, 'hint': hint, 'line': line}


def _build_steps():
    n1 = _leaf('s1a', 'phantom', 'pinMode(9, INPUT_PULLUP);', 'Set the arm switch pin as an input')
    n2 = _leaf('s1b', 'locked', 'pinMode(7, INPUT_PULLUP);')
    n3 = _leaf('s1c', 'phantom', 'pinMode(2, OUTPUT);', 'Set the engine light pin as an output')
    n4 = _leaf('s1d', 'locked', 'pinMode(5, OUTPUT);')
    setup_pins = [n1, n2, n3, n4]

    step1 = {'label': 'Setup Pins', 'guidance': 'guided', 'view': 'blocks',
             'global': [], 'setup': setup_pins, 'loop': []}

    n5 = _leaf('l2a', 'phantom', 'digitalWrite(2, HIGH);', 'Turn on the engine light')
    n6 = _leaf('l2b', 'phantom', 'digitalWrite(5, HIGH);', 'Turn on the engine buzzer')

    step2 = {'label': 'Reward-First: Light the Engine', 'guidance': 'guided', 'view': 'blocks',
             'global': [], 'setup': setup_pins, 'loop': [n5, n6]}

    n7 = _leaf('l3a', 'phantom', 'digitalWrite(2, LOW);', 'Turn off the engine light')
    n8 = _leaf('l3b', 'phantom', 'digitalWrite(5, LOW);', 'Turn off the engine buzzer')
    if3 = {
        'id': 'if3', 'kind': 'compound', 'compound_type': 'ifblock',
        'flag': 'phantom', 'hint': 'Check if the arm switch is on',
        'header': 'digitalRead(9) == LOW',
        'body': [n5, n6],
        'elseifs': [],
        'elsebody': {'id': 'eb3', 'flag': 'locked', 'hint': None, 'body': [n7, n8]},
    }

    step3 = {'label': 'Capture: Only Run When Armed', 'guidance': 'guided', 'view': 'blocks',
             'global': [], 'setup': setup_pins, 'loop': [if3]}

    n9 = _leaf('l4a', 'phantom', 'digitalWrite(5, LOW);', 'Turn off the engine buzzer')
    if4 = {
        'id': 'if4', 'kind': 'compound', 'compound_type': 'ifblock',
        'flag': 'phantom', 'hint': 'Check if the start button is pressed',
        'header': 'digitalRead(7) == LOW',
        'body': [n6],
        'elseifs': [],
        'elsebody': {'id': 'eb4', 'flag': 'locked', 'hint': None, 'body': [n9]},
    }
    if3_updated = {
        'id': 'if3', 'kind': 'compound', 'compound_type': 'ifblock',
        'flag': 'phantom', 'hint': 'Check if the arm switch is on',
        'header': 'digitalRead(9) == LOW',
        'body': [n5, if4],
        'elseifs': [],
        'elsebody': {'id': 'eb3', 'flag': 'locked', 'hint': None, 'body': [n7, n8]},
    }

    step4 = {'label': 'Capture: Buzzer Needs the Button Too', 'guidance': 'guided', 'view': 'blocks',
             'global': [], 'setup': setup_pins, 'loop': [if3_updated]}

    return [step1, step2, step3, step4]


def _strip(obj):
    """Structural comparison only — drop ids/parser_error, keep everything
    that determines what the block builder actually renders."""
    if isinstance(obj, dict):
        return {k: _strip(v) for k, v in obj.items() if k not in ('id', 'parser_error')}
    if isinstance(obj, list):
        return [_strip(v) for v in obj]
    return obj


def test_materialize_round_trips_through_parse_steps():
    materialized = materialize(_build_steps())
    real_sketch = project_eleven.SKETCH_PRESET['sketch']

    materialized_steps = parse_steps(materialized)
    real_steps = parse_steps(real_sketch)

    # First 5 steps of project_eleven: the 4 modeled here + Mission Complete.
    assert len(materialized_steps) == 5
    assert len(real_steps) >= 5

    for i in range(5):
        for section in ('global', 'setup', 'loop'):
            assert _strip(materialized_steps[i][section]) == _strip(real_steps[i][section]), (
                f"step {i} ({materialized_steps[i]['label']!r}) section {section!r} mismatch"
            )


def test_materialize_ends_with_mission_complete():
    materialized = materialize(_build_steps())
    assert materialized.rstrip().endswith('//>> Mission Complete | open | blocks')


def test_open_step_is_raw_passthrough():
    steps = _build_steps() + [{
        'label': 'Find the Bug', 'guidance': 'open', 'view': 'blocks',
        'raw': 'void loop() {\n  digitalWrite(2, HIGH); // oops, wrong pin\n}',
    }]
    materialized = materialize(steps)
    assert '//>> Find the Bug | open | blocks' in materialized
    assert 'digitalWrite(2, HIGH); // oops, wrong pin' in materialized


def test_open_step_with_no_raw_is_header_only():
    steps = [{'label': 'Explore', 'guidance': 'open', 'view': 'blocks'}]
    materialized = materialize(steps)
    lines = [l for l in materialized.split('\n') if l.strip()]
    assert lines == ['//>> Explore | open | blocks', FINAL_STEP_LINE]
