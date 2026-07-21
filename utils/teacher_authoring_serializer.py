"""
utils/teacher_authoring_serializer.py — the one new server-side piece the
blocks-first teacher-authoring tool needs (plans/SCHOOL_INFRASTRUCTURE_PLAN.md
§4). Full algorithm design:
docs/superpowers/specs/2026-07-21-teacher-authoring-serializer-design.md

materialize(steps) -> annotated_sketch_string

Pure function: no DB access, no Flask imports, deterministic. Turns a
teacher's ordered list of step drafts (a block tree per section, the same
shape bb-render.js's live workspace already uses, plus `flag`/`hint` layered
on top) into the `//>>`/`//??`/`//##`-annotated sketch string
utils/block_parser.py's parse_steps() already consumes for every
hand-authored lesson today.

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
