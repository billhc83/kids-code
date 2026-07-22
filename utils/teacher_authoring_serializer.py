"""
utils/teacher_authoring_serializer.py — the one new server-side piece the
blocks-first teacher-authoring tool needs (plans/SCHOOL_INFRASTRUCTURE_PLAN.md
§4). Full algorithm design:
docs/superpowers/specs/2026-07-21-teacher-authoring-serializer-design.md

materialize(steps) -> annotated_sketch_string
hydrate_steps(steps) -> [live-workspace step, ...]  (the reverse direction)

Pure functions: no DB access, no Flask imports, deterministic. materialize()
turns a teacher's ordered list of step drafts (a block tree per section, the
same shape bb-render.js's live workspace already uses, plus `flag`/`hint`
layered on top) into the `//>>`/`//??`/`//##`-annotated sketch string
utils/block_parser.py's parse_steps() already consumes for every
hand-authored lesson today. hydrate_steps() is its mirror image, used to load
a previously-saved draft back into the live block-builder workspace.

Node shapes (plain dicts, matching the design doc's §2 input contract):

    LeafNode     = {id, kind:'leaf', flag, hint, line}
    CompoundNode = {id, kind:'compound', compound_type: 'ifblock'|'whileloop'|'forloop',
                     flag, hint, header, body:[Node], elseifs:[ElseifClause], elsebody:ElseClause|None}
    ElseifClause = {id, header, flag, hint, body:[Node]}
    ElseClause   = {id, flag, hint, body:[Node]}

`flag` is 'phantom' or 'locked'. `hint` is required iff flag == 'phantom'.
Global-section nodes are always LeafNode (no compound ever appears at global
scope in the real corpus).

StepDraft = {
    'label': str, 'guidance': 'guided'|'free'|'full'|'open', 'view': 'blocks'|'editor',
    'read_only': bool,               # optional, defaults per guidance
    'global': [LeafNode], 'setup': [Node], 'loop': [Node],   # guided/free/full steps
    'raw': str,                       # open steps only — see below
}

`open`-guidance steps are never modeled as a block tree. Per the plan owner's
call: an aside is the teacher's to do with as they like — it doesn't need to
match the circuit, doesn't need to compile, isn't validated. `raw` (if given)
is emitted byte-for-byte after the step header; an empty/absent `raw` (e.g.
the trailing Mission Complete step, which materialize() appends itself and
callers must not include in `steps`) emits a header-only chunk.
"""

_KEYWORD = {'ifblock': 'if', 'whileloop': 'while', 'forloop': 'for'}

# Matches utils/block_parser.py's guidance -> is_readonly base mapping
# (lines ~690-720: open/verify -> False, guided/free/full -> True).
_DEFAULT_READONLY = {'open': False, 'guided': True, 'free': True, 'full': True}

FINAL_STEP = '//>> Mission Complete | open | blocks'


def _emit_header(text, flag, hint, out):
    if flag == 'phantom':
        out.append('//?? ' + (hint or ''))
        out.append(text)
    else:
        out.append('//## ' + text)


def _emit_leaf(node, seen_before, out):
    introduced = node['id'] not in seen_before
    flag = node['flag'] if introduced else 'locked'
    if flag == 'phantom':
        out.append('//?? ' + (node.get('hint') or ''))
        out.append(node['line'])
    else:
        out.append('//## ' + node['line'])


def emit_node(node, seen_before, out):
    """Recursive: applies uniformly to leaves and every compound-node
    position (top level, elseifs, elsebody). A compound's flag governs only
    its own header line; its body is always walked recursively."""
    if node['kind'] == 'leaf':
        _emit_leaf(node, seen_before, out)
        return

    introduced = node['id'] not in seen_before
    flag = node['flag'] if introduced else 'locked'

    keyword = _KEYWORD[node['compound_type']]
    _emit_header('{} ({}) {{'.format(keyword, node['header']), flag, node.get('hint'), out)
    for child in node['body']:
        emit_node(child, seen_before, out)
    out.append('}' if flag == 'phantom' else '//## }')

    for ei in node.get('elseifs') or []:
        ei_introduced = ei['id'] not in seen_before
        ei_flag = ei['flag'] if ei_introduced else 'locked'
        _emit_header('else if ({}) {{'.format(ei['header']), ei_flag, ei.get('hint'), out)
        for child in ei['body']:
            emit_node(child, seen_before, out)
        out.append('}' if ei_flag == 'phantom' else '//## }')

    eb = node.get('elsebody')
    if eb:
        eb_introduced = eb['id'] not in seen_before
        eb_flag = eb['flag'] if eb_introduced else 'locked'
        _emit_header('else {', eb_flag, eb.get('hint'), out)
        for child in eb['body']:
            emit_node(child, seen_before, out)
        out.append('}' if eb_flag == 'phantom' else '//## }')


def _walk(nodes):
    """Every node (leaf or compound, including elseif/else clauses) reachable
    from an ordered node list — used to decide "does this section have
    anything new this step" and to fold ids into `seen` after a step."""
    for node in nodes:
        yield node
        if node['kind'] == 'compound':
            yield from _walk(node['body'])
            for ei in node.get('elseifs') or []:
                yield ei
                yield from _walk(ei['body'])
            eb = node.get('elsebody')
            if eb:
                yield eb
                yield from _walk(eb['body'])


def _indent(lines):
    return '\n'.join('  ' + line for line in lines)


def materialize_step(step, seen_before):
    guidance = step['guidance']
    header = '//>> {} | {} | {}'.format(step['label'], guidance, step['view'])
    default_readonly = _DEFAULT_READONLY[guidance]
    read_only = step.get('read_only', default_readonly)
    if read_only != default_readonly:
        header += ' | readonly:' + str(bool(read_only)).lower()

    if guidance == 'open':
        raw = step.get('raw') or ''
        return header + ('\n\n' + raw if raw else '')

    global_lines = []
    for node in step.get('global', []):
        if node['id'] not in seen_before:
            emit_node(node, seen_before, global_lines)

    setup_lines, loop_lines = [], []
    for node in step.get('setup', []):
        emit_node(node, seen_before, setup_lines)
    for node in step.get('loop', []):
        emit_node(node, seen_before, loop_lines)

    setup_has_new = any(n['id'] not in seen_before for n in _walk(step.get('setup', [])))
    loop_has_new = any(n['id'] not in seen_before for n in _walk(step.get('loop', [])))

    body = header
    if global_lines:
        body += '\n\n' + '\n'.join(global_lines)
    if setup_has_new or loop_has_new:
        body += '\n\nvoid setup() {\n' + _indent(setup_lines) + '\n}'
        body += '\n\nvoid loop() {\n' + _indent(loop_lines) + '\n}'
    return body


def materialize(steps):
    """steps: ordered list of StepDraft, NOT including the trailing Mission
    Complete step — materialize() always appends that itself, per §4."""
    seen = set()
    chunks = []

    for step in steps:
        step_seen_before = set(seen)
        chunks.append(materialize_step(step, step_seen_before))

        if step['guidance'] != 'open':
            for node in step.get('global', []):
                seen.add(node['id'])
            for n in _walk(step.get('setup', [])):
                seen.add(n['id'])
            for n in _walk(step.get('loop', [])):
                seen.add(n['id'])

    chunks.append(FINAL_STEP)
    return '\n\n'.join(chunks) + '\n'


# ── hydrate_steps() — the reverse direction (build order step 4) ────────────
#
# Turns a saved StepDraft list back into the shape
# static/js/teacher-authoring.js's TA.STEPS needs to re-populate the live
# workspace (BB.SECTIONS-shaped block trees, id/flag/hint attached to every
# node) — the mirror image of emit_node()/extractNode(). There is no
# "un-generate code" step per se: each node's stored `line`/`header` text is
# valid Arduino already (that's what materialize() emits and what compiles
# on real hardware), so we re-run it through utils/block_parser.py's real
# grammar (the exact same parser every published lesson's sketch goes
# through) and re-attach id/flag/hint from the StepDraft onto the resulting
# block dicts, position-for-position. If the parse doesn't line up
# structurally with the node tree that generated it (a hand-edited raw JSON
# draft with a `line` the grammar can't parse, for instance), this raises
# ValueError — callers should catch that and fall back to the raw JSON view,
# never show a broken workspace.


def _emit_plain(node, out):
    """Like emit_node(), but without the //??///## directives — just real
    Arduino text, since we're about to hand it back to the same grammar."""
    if node['kind'] == 'leaf':
        out.append(node['line'])
        return
    keyword = _KEYWORD[node['compound_type']]
    out.append('{} ({}) {{'.format(keyword, node['header']))
    for child in node['body']:
        _emit_plain(child, out)
    out.append('}')
    for ei in node.get('elseifs') or []:
        out.append('else if ({}) {{'.format(ei['header']))
        for child in ei['body']:
            _emit_plain(child, out)
        out.append('}')
    eb = node.get('elsebody')
    if eb:
        out.append('else {')
        for child in eb['body']:
            _emit_plain(child, out)
        out.append('}')


def _zip_node(node, block):
    """Merge one StepDraft node's id/flag/hint onto the runtime block dict
    parse_sketch() produced from its text, recursing into compound bodies in
    lockstep. Raises ValueError on any shape mismatch instead of silently
    misattaching metadata to the wrong block."""
    block = dict(block)
    block.pop('locked', None)  # parse_sketch's own readonly marker — not
    block.pop('parser_error', None)  # teacher-authoring's flag/hint concept.
    block['id'] = node['id']
    block['flag'] = node['flag']
    block['hint'] = node.get('hint')

    if node['kind'] == 'leaf':
        return block

    ctype = node['compound_type']
    if block.get('type') != ctype:
        raise ValueError('expected {}, parsed {}'.format(ctype, block.get('type')))

    if ctype == 'ifblock':
        body, parsed_body = node['body'], block.get('ifbody') or []
        if len(body) != len(parsed_body):
            raise ValueError('ifbody length mismatch')
        block['ifbody'] = [_zip_node(n, b) for n, b in zip(body, parsed_body)]

        elseifs, parsed_elseifs = node.get('elseifs') or [], block.get('elseifs') or []
        if len(elseifs) != len(parsed_elseifs):
            raise ValueError('elseifs length mismatch')
        zipped_elseifs = []
        for ei, eib in zip(elseifs, parsed_elseifs):
            ei_body, parsed_ei_body = ei['body'], eib.get('body') or []
            if len(ei_body) != len(parsed_ei_body):
                raise ValueError('elseif body length mismatch')
            zipped_elseifs.append({
                'id': ei['id'], 'flag': ei['flag'], 'hint': ei.get('hint'),
                'condition': eib.get('condition'),
                'body': [_zip_node(n, b) for n, b in zip(ei_body, parsed_ei_body)],
            })
        block['elseifs'] = zipped_elseifs

        eb, ebb = node.get('elsebody'), block.get('elsebody')
        if bool(eb) != bool(ebb):
            raise ValueError('elsebody presence mismatch')
        if eb:
            eb_body, parsed_eb_body = eb['body'], ebb.get('body') or []
            if len(eb_body) != len(parsed_eb_body):
                raise ValueError('elsebody body length mismatch')
            block['elsebody'] = {
                'id': eb['id'], 'flag': eb['flag'], 'hint': eb.get('hint'),
                'body': [_zip_node(n, b) for n, b in zip(eb_body, parsed_eb_body)],
            }
        else:
            block['elsebody'] = None
        return block

    # forloop / whileloop — single body list.
    body, parsed_body = node['body'], block.get('body') or []
    if len(body) != len(parsed_body):
        raise ValueError('body length mismatch')
    block['body'] = [_zip_node(n, b) for n, b in zip(body, parsed_body)]
    return block


def hydrate_step(step):
    """The reverse of materialize_step()/extractStepDraft(): turns one
    StepDraft back into {label, guidance, view, read_only, sections, raw} —
    the shape TA.STEPS entries need. Raises ValueError if the stored code
    text doesn't round-trip through the real grammar structurally."""
    from utils.block_parser import parse_sketch

    result = {
        'label': step['label'], 'guidance': step['guidance'],
        'view': step.get('view', 'blocks'), 'read_only': step.get('read_only'),
    }

    if step['guidance'] == 'open':
        result['raw'] = step.get('raw') or ''
        result['sections'] = {'global': [], 'setup': [], 'loop': []}
        return result

    global_nodes = step.get('global', [])
    setup_nodes = step.get('setup', [])
    loop_nodes = step.get('loop', [])

    global_lines, setup_lines, loop_lines = [], [], []
    for node in global_nodes:
        _emit_plain(node, global_lines)
    for node in setup_nodes:
        _emit_plain(node, setup_lines)
    for node in loop_nodes:
        _emit_plain(node, loop_lines)

    parts = []
    if global_lines:
        parts.append('\n'.join(global_lines))
    parts.append('void setup() {\n' + _indent(setup_lines) + '\n}')
    parts.append('void loop() {\n' + _indent(loop_lines) + '\n}')
    code = '\n\n'.join(parts)

    # fill_conditions/fill_values=True: this is reloading a teacher's own
    # already-decided draft, not building a blank student-facing progression
    # step — resolve_phantom_items() strips concrete param/condition values
    # from every non-phantom block when these are False (see
    # utils/block_parser.py's fill_values docstring), which would blank out
    # every locked block's pin numbers/values on reload.
    parsed = parse_sketch(code, fill_conditions=True, fill_values=True, initial_fill_content=True)

    if len(global_nodes) != len(parsed['global']):
        raise ValueError('global section length mismatch')
    if len(setup_nodes) != len(parsed['setup']):
        raise ValueError('setup section length mismatch')
    if len(loop_nodes) != len(parsed['loop']):
        raise ValueError('loop section length mismatch')

    result['raw'] = ''
    result['sections'] = {
        'global': [_zip_node(n, b) for n, b in zip(global_nodes, parsed['global'])],
        'setup': [_zip_node(n, b) for n, b in zip(setup_nodes, parsed['setup'])],
        'loop': [_zip_node(n, b) for n, b in zip(loop_nodes, parsed['loop'])],
    }
    return result


def hydrate_steps(steps):
    return [hydrate_step(step) for step in steps]


# ── What the teacher-authoring tool itself is allowed to produce ────────────
#
# Deliberately narrower than what utils/block_parser.py's engine can parse.
# A corpus audit (2026-07-22) of every real, published lesson's steps showed
# `editor` view has exactly one safe real-world pairing — `guidance: verify`
# (project_try_it's "Turn it ON") — which this tool has no UI for at all
# (verify's answer-key shape isn't representable by StepDraft/materialize()).
# `guided`/`free`/`open` never appear with `editor` anywhere in the corpus,
# and `full` never appears at all. So rather than defending the engine
# against every theoretical combination, the tool just refuses to produce
# anything outside what's already shipped and working.
ALLOWED_GUIDANCE = {"guided", "free", "open"}


def validate_step_shape(steps):
    """Returns an error string on the first step outside the supported set,
    or None if every step is within it. Called both from build()'s save path
    and publish_project(), so the raw-JSON fallback textarea can't be used to
    smuggle in a combination the settings-panel UI no longer offers."""
    for i, step in enumerate(steps):
        guidance = step.get("guidance")
        if guidance not in ALLOWED_GUIDANCE:
            return f"Step {i + 1}: guidance {guidance!r} isn't supported by this tool — use guided, free, or open."
        view = step.get("view", "blocks")
        if view != "blocks":
            return f"Step {i + 1}: only 'blocks' view is supported by this tool right now."
    return None
