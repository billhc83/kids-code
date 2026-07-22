"""
Round-trip test for utils/teacher_authoring_serializer.py's materialize().

Fixture below hand-builds a StepDraft tree ("Setup Pins" through "Capture:
Buzzer Needs the Button Too") modeled on the worked example in
docs/superpowers/specs/2026-07-21-teacher-authoring-serializer-design.md.
materialize()'s output is fed back through the real parse_steps() and
compared, structurally, against parsing an independent hand-authored sketch
string with the same intended structure — proving the serializer produces
something the existing block-builder pipeline can actually consume, not just
text that looks right.

This used to compare against utils/project_eleven.py's real sketch instead of
a hand-authored oracle. That broke (not from anything in this file — see
plans/TEACHER_AUTHORING_LIVE_BUILDER_UI_SPEC.md §4) the moment
project_eleven.py's sketch content diverged from what this fixture modeled,
which it has: the file no longer has 4+ steps shaped like this at all.
Comparing against a self-contained oracle instead means this test can never
drift out from under a lesson file someone else edits for pedagogical
reasons unrelated to serializer correctness.
"""

import pytest

from utils.block_parser import parse_steps
from utils.teacher_authoring_serializer import materialize, hydrate_steps, hydrate_step, validate_step_shape

FINAL_STEP_LINE = '//>> Mission Complete | open | blocks'

# Independent oracle: the annotated sketch text a human would hand-author for
# the exact StepDraft tree _build_steps() constructs below. Deliberately
# written in a different whitespace style than materialize()'s own output
# (see the elsebody trace in plans/TEACHER_AUTHORING_LIVE_BUILDER_UI_SPEC.md
# §4) so this isn't just materialize() being compared against itself.
_HAND_AUTHORED_SKETCH = """
//>> Setup Pins | guided | blocks
void setup() {
//?? Set the arm switch pin as an input
  pinMode(9, INPUT_PULLUP);
//## pinMode(7, INPUT_PULLUP);
//?? Set the engine light pin as an output
  pinMode(2, OUTPUT);
//## pinMode(5, OUTPUT);
}
void loop() {
}

//>> Reward-First: Light the Engine | guided | blocks
void setup() {
//## pinMode(9, INPUT_PULLUP);
//## pinMode(7, INPUT_PULLUP);
//## pinMode(2, OUTPUT);
//## pinMode(5, OUTPUT);
}
void loop() {
//?? Turn on the engine light
  digitalWrite(2, HIGH);
//?? Turn on the engine buzzer
  digitalWrite(5, HIGH);
}

//>> Capture: Only Run When Armed | guided | blocks
void setup() {
//## pinMode(9, INPUT_PULLUP);
//## pinMode(7, INPUT_PULLUP);
//## pinMode(2, OUTPUT);
//## pinMode(5, OUTPUT);
}
void loop() {
//?? Check if the arm switch is on
  if (digitalRead(9) == LOW) {
//## digitalWrite(2, HIGH);
//## digitalWrite(5, HIGH);
  }
//## else {
//?? Turn off the engine light
  digitalWrite(2, LOW);
//?? Turn off the engine buzzer
  digitalWrite(5, LOW);
//## }
}

//>> Capture: Buzzer Needs the Button Too | guided | blocks
void setup() {
//## pinMode(9, INPUT_PULLUP);
//## pinMode(7, INPUT_PULLUP);
//## pinMode(2, OUTPUT);
//## pinMode(5, OUTPUT);
}
void loop() {
//## if (digitalRead(9) == LOW) {
//## digitalWrite(2, HIGH);
//?? Check if the start button is pressed
  if (digitalRead(7) == LOW) {
//## digitalWrite(5, HIGH);
  }
//## else {
//?? Turn off the engine buzzer
  digitalWrite(5, LOW);
//## }
//## }
//## else {
//## digitalWrite(2, LOW);
//## digitalWrite(5, LOW);
//## }
}

//>> Mission Complete | open | blocks
"""


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

    materialized_steps = parse_steps(materialized)
    oracle_steps = parse_steps(_HAND_AUTHORED_SKETCH)

    # The 4 steps modeled in _build_steps() + Mission Complete.
    assert len(materialized_steps) == 5
    assert len(oracle_steps) == 5

    for i in range(5):
        for section in ('global', 'setup', 'loop'):
            assert _strip(materialized_steps[i][section]) == _strip(oracle_steps[i][section]), (
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


# ── hydrate_steps() — build order step 4, the reverse direction ────────────


def _node_ids_flags_hints(nodes):
    """Walk a StepDraft node list and collect (id, flag, hint) triples in
    tree order — used to compare against the same walk over hydrate_steps()'
    output, which nests hydrated blocks (ifbody/elseifs/elsebody/body)
    exactly the same way."""
    out = []
    for node in nodes:
        out.append((node['id'], node['flag'], node.get('hint')))
        if node['kind'] == 'compound':
            out.extend(_node_ids_flags_hints(node['body']))
            for ei in node.get('elseifs') or []:
                out.append((ei['id'], ei['flag'], ei.get('hint')))
                out.extend(_node_ids_flags_hints(ei['body']))
            eb = node.get('elsebody')
            if eb:
                out.append((eb['id'], eb['flag'], eb.get('hint')))
                out.extend(_node_ids_flags_hints(eb['body']))
    return out


def _block_ids_flags_hints(blocks):
    out = []
    for block in blocks:
        out.append((block['id'], block['flag'], block.get('hint')))
        if block['type'] == 'ifblock':
            out.extend(_block_ids_flags_hints(block['ifbody']))
            for ei in block.get('elseifs') or []:
                out.append((ei['id'], ei['flag'], ei.get('hint')))
                out.extend(_block_ids_flags_hints(ei['body']))
            if block.get('elsebody'):
                eb = block['elsebody']
                out.append((eb['id'], eb['flag'], eb.get('hint')))
                out.extend(_block_ids_flags_hints(eb['body']))
        elif block['type'] in ('forloop', 'whileloop'):
            out.extend(_block_ids_flags_hints(block['body']))
    return out


def test_hydrate_steps_reconstructs_ids_flags_and_hints():
    steps = _build_steps()
    hydrated = hydrate_steps(steps)

    assert len(hydrated) == len(steps)
    for step, hstep in zip(steps, hydrated):
        expected = (
            _node_ids_flags_hints(step.get('global', []))
            + _node_ids_flags_hints(step.get('setup', []))
            + _node_ids_flags_hints(step.get('loop', []))
        )
        actual = (
            _block_ids_flags_hints(hstep['sections']['global'])
            + _block_ids_flags_hints(hstep['sections']['setup'])
            + _block_ids_flags_hints(hstep['sections']['loop'])
        )
        assert actual == expected, f"step {step['label']!r} id/flag/hint mismatch"


def test_hydrate_steps_preserves_concrete_values_not_just_structure():
    # fill_values/fill_conditions must be True internally — a naive re-parse
    # with the defaults strips every non-phantom block's real param values
    # (see utils/block_parser.py's resolve_phantom_items), which would
    # silently blank out every locked block's pin numbers on reload.
    hydrated = hydrate_steps(_build_steps())
    setup = hydrated[0]['sections']['setup']
    assert [b['params'] for b in setup] == [
        ['9', 'INPUT_PULLUP'], ['7', 'INPUT_PULLUP'], ['2', 'OUTPUT'], ['5', 'OUTPUT'],
    ]

    if3 = hydrated[2]['sections']['loop'][0]
    assert if3['condition']['left'] == 'digitalRead(9)'
    assert if3['condition']['right'] == 'LOW'
    assert if3['ifbody'][0]['params'] == ['2', 'HIGH']
    assert if3['elsebody']['body'][0]['params'] == ['2', 'LOW']


def test_hydrate_open_step_is_raw_passthrough():
    step = {
        'label': 'Find the Bug', 'guidance': 'open', 'view': 'blocks',
        'raw': 'void loop() {\n  digitalWrite(2, HIGH); // oops, wrong pin\n}',
    }
    hydrated = hydrate_step(step)
    assert hydrated['raw'] == step['raw']
    assert hydrated['sections'] == {'global': [], 'setup': [], 'loop': []}


def test_hydrate_step_raises_on_structural_mismatch():
    # A malformed condition breaks the whole loop() chunk's grammar parse,
    # collapsing it to a flat per-line 'codeblock' fallback — a different
    # shape than the single ifblock node that generated it. hydrate_step()
    # must raise rather than silently attach the ifblock's id/flag/hint to
    # whatever fallback block happened to land in that position.
    bad_if = {
        'id': 'if1', 'kind': 'compound', 'compound_type': 'ifblock',
        'flag': 'phantom', 'hint': 'broken on purpose',
        'header': ')))not valid(((',
        'body': [_leaf('l1', 'locked', 'digitalWrite(2, HIGH);')],
        'elseifs': [], 'elsebody': None,
    }
    step = {'label': 'Broken', 'guidance': 'guided', 'view': 'blocks',
            'global': [], 'setup': [], 'loop': [bad_if]}
    with pytest.raises(ValueError):
        hydrate_step(step)


# ── validate_step_shape() — teacher-authoring only offers what's actually
# shipped and tested (2026-07-22 corpus audit), not everything the engine
# can parse. `full` guidance and `editor` view have no real precedent paired
# with anything this tool builds. ────────────────────────────────────────────


def _step(guidance='guided', view='blocks'):
    return {'label': 'S', 'guidance': guidance, 'view': view, 'global': [], 'setup': [], 'loop': []}


def test_validate_step_shape_accepts_guided_free_open_blocks():
    steps = [_step('guided'), _step('free'), _step('open')]
    assert validate_step_shape(steps) is None


def test_validate_step_shape_rejects_full_guidance():
    err = validate_step_shape([_step('guided'), _step('full')])
    assert err is not None
    assert 'Step 2' in err and 'full' in err


def test_validate_step_shape_rejects_verify_guidance():
    err = validate_step_shape([_step('verify')])
    assert err is not None and 'verify' in err


def test_validate_step_shape_rejects_editor_view():
    err = validate_step_shape([_step('guided'), _step('guided', view='editor')])
    assert err is not None
    assert 'Step 2' in err and 'blocks' in err


def test_validate_step_shape_view_defaults_to_blocks_when_omitted():
    step = {'label': 'S', 'guidance': 'guided', 'global': [], 'setup': [], 'loop': []}
    assert validate_step_shape([step]) is None
