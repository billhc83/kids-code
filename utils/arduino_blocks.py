import re
import json
import random

from utils.presets import PRESETS, PIN_REFS


# ── Sketch parser ─────────────────────────────────────────────────────

def extract_brace_body(code, start):
    depth = 0
    i = start
    while i < len(code):
        if code[i] == '{': depth += 1
        elif code[i] == '}':
            depth -= 1
            if depth == 0:
                return code[start+1:i].strip(), i+1
        i += 1
    return '', len(code)


def extract_condition(code, start):
    depth = 0
    i = start
    while i < len(code):
        if code[i] == '(': depth += 1
        elif code[i] == ')':
            depth -= 1
            if depth == 0:
                return code[start+1:i].strip(), i+1
        i += 1
    return '', len(code)


def parse_condition(cond_str, fill_conditions=False):
    result = {
        'leftExpr': None, 'op': '==', 'rightExpr': None,
        'joiner': 'none', 'leftExpr2': None, 'op2': '==', 'rightExpr2': None
    }
    and_match = re.search(r'\s*(&&|\|\|)\s*', cond_str)
    if and_match:
        result['joiner'] = 'and' if and_match.group(1) == '&&' else 'or'
        parse_side(cond_str[:and_match.start()].strip(), result, 'leftExpr',  'op',  'rightExpr',  fill_conditions)
        parse_side(cond_str[and_match.end():].strip(),   result, 'leftExpr2', 'op2', 'rightExpr2', fill_conditions)
    else:
        parse_side(cond_str, result, 'leftExpr', 'op', 'rightExpr', fill_conditions)
    return result


def parse_side(s, result, lkey, opkey, rkey, fill_conditions=False):
    process = (lambda node: node) if fill_conditions else strip_expr_values
    for op in ['>=', '<=', '!=', '==', '>', '<']:
        if op in s:
            parts = s.split(op, 1)
            left_str  = parts[0].strip()
            right_str = parts[1].strip()
            result[opkey] = op
            result[lkey]  = process(parse_expr(left_str))  if left_str  else None
            result[rkey]  = process(parse_expr(right_str)) if right_str else None
            return
    result[lkey] = process(parse_expr(s.strip())) if s.strip() else None


def parse_expr(s):
    """Parse an expression string into an exChildren node tree.
    Returns a node dict: {type, params, children} matching JS makeExNode output.
    Falls back to a value node for anything unrecognised.
    """
    if not s: return {'type': 'value', 'params': [''], 'children': []}
    s = s.strip()

    # Strip outer parens: (expr) -> parse inside
    if s.startswith('(') and s.endswith(')'):
        inner = s[1:-1].strip()
        # Only strip if parens are balanced (not something like (a+b)*(c+d))
        depth = 0
        balanced = True
        for i, ch in enumerate(inner):
            if ch == '(': depth += 1
            elif ch == ')':
                depth -= 1
                if depth < 0:
                    balanced = False
                    break
        if balanced and depth == 0:
            return parse_expr(inner)

    # Binary math: find lowest-precedence operator outside parens
    # Precedence: + - (lowest), then * / %
    for ops in (['+', '-'], ['*', '/', '%']):
        depth = 0
        in_quotes = False
        # Scan right-to-left so left-associativity is preserved
        for i in range(len(s) - 1, -1, -1):
            ch = s[i]
            if ch == '"': in_quotes = not in_quotes
            if in_quotes:
                continue
            if ch == ')':
                depth += 1
            elif ch == '(':
                depth -= 1
            elif depth == 0 and ch in ops:
                # Make sure it's not a unary minus at start
                if ch == '-' and i == 0:
                    continue
                left  = s[:i].strip()
                right = s[i+1:].strip()
                if left and right:
                    op_map = {'+': '+', '-': '-', '*': '*', '/': '/', '%': '%'}
                    left_node  = parse_expr(left)
                    right_node = parse_expr(right)
                    return {
                        'type': 'math',
                        'params': ['', ch, ''],
                        'children': [left_node, None, right_node]
                    }

    # millis()
    if re.match(r'millis\s*\(\s*\)$', s):
        return {'type': 'millis', 'params': [], 'children': []}

    # Serial.available()
    if re.match(r'Serial\.available\s*\(\s*\)$', s):
        return {'type': 'serialavailable', 'params': [], 'children': []}

    # analogRead(pin)
    m = re.match(r'analogRead\s*\(\s*(\w+)\s*\)$', s)
    if m:
        return {'type': 'analogread', 'params': [m.group(1)], 'children': []}

    # digitalRead(pin)
    m = re.match(r'digitalRead\s*\(\s*(\w+)\s*\)$', s)
    if m:
        return {'type': 'digitalread', 'params': [m.group(1)], 'children': []}

    # random(min, max)
    m = re.match(r'random\s*\(\s*([^,]+?)\s*,\s*([^)]+?)\s*\)$', s)
    if m:
        return {'type': 'random', 'params': [m.group(1).strip(), m.group(2).strip()], 'children': []}

    # map(val, inLo, inHi, outLo, outHi)
    m = re.match(r'map\s*\((.+)\)$', s)
    if m:
        args = [a.strip() for a in m.group(1).split(',')]
        if len(args) == 5:
            return {
                'type': 'map',
                'params': ['', args[1], args[2], args[3], args[4]],
                'children': [parse_expr(args[0]), None, None, None, None]
            }

    # constrain(val, lo, hi)
    m = re.match(r'constrain\s*\((.+)\)$', s)
    if m:
        args = [a.strip() for a in m.group(1).split(',')]
        if len(args) == 3:
            return {
                'type': 'constrain',
                'params': ['', args[1], args[2]],
                'children': [parse_expr(args[0]), None, None]
            }

    # Fallback: bare value (number, variable name, or anything else)
    return {'type': 'value', 'params': [s], 'children': []}


def strip_expr_values(node):
    """Walk an expression node tree and clear all leaf values.
    Keeps structure (math ops, function types) but empties value nodes
    and numeric params so the user fills them in.
    """
    if node is None:
        return None
    t = node['type']
    # value leaf — clear it
    if t == 'value':
        return {'type': 'value', 'params': [''], 'children': []}
    # millis has no params to clear
    if t == 'millis':
        return node
    # serialavailable and serialreadstring have no params to clear
    if t == 'serialavailable':
        return node
    if t == 'serialreadstring':
        return node
    # analogread/digitalread — clear pin
    if t in ('analogread', 'digitalread'):
        return {'type': t, 'params': [''], 'children': []}
    # random — clear min/max
    if t == 'random':
        return {'type': 'random', 'params': ['', ''], 'children': []}
    # math — keep operator, recurse into children
    if t == 'math':
        op = node['params'][1] if len(node['params']) > 1 else '+'
        ch = node.get('children') or [None, None, None]
        return {
            'type': 'math',
            'params': ['', op, ''],
            'children': [strip_expr_values(ch[0]), None, strip_expr_values(ch[2])]
        }
    # map — clear numeric params, recurse into val child
    if t == 'map':
        ch = node.get('children') or [None]
        return {
            'type': 'map',
            'params': ['', '', '', '', ''],
            'children': [strip_expr_values(ch[0]), None, None, None, None]
        }
    # constrain — clear lo/hi, recurse into val child
    if t == 'constrain':
        ch = node.get('children') or [None]
        return {
            'type': 'constrain',
            'params': ['', '', ''],
            'children': [strip_expr_values(ch[0]), None, None]
        }
    # anything else — return as-is
    return node


def parse_blocks(code, fill_conditions=False, fill_values=False):
    process = (lambda node: node) if fill_values else strip_expr_values
    blocks = []
    i = 0
    code = code.strip()
    while i < len(code):
        while i < len(code) and code[i] in ' \t\n\r': i += 1
        if i >= len(code): break
        if code[i:i+2] == '//':
            # Check for locked block flag //##
            if code[i:i+4] == '//##':
                end = code.find('\n', i)
                line = code[i+4:end].strip() if end != -1 else code[i+4:].strip()
                if line:
                    blocks.append({'type': 'codeblock', 'params': [line]})
                i = end+1 if end != -1 else len(code)
                continue
            # Check for phantom block flag //??
            if code[i:i+4] == '//??' :
                end = code.find('\n', i)
                hint = code[i+4:end].strip() if end != -1 else code[i+4:].strip()
                i = end+1 if end != -1 else len(code)
                # Find start of next code
                j = i
                while j < len(code) and code[j] in ' \t\n\r': j += 1

                # Extract full statement/block for the phantom
                block_code = ""
                block_end_idx = -1

                if re.match(r'if\s*\(', code[j:]):
                    try:
                        p_start = code.index('(', j)
                        _, a_p = extract_condition(code, p_start)
                        b_start = code.index('{', a_p)
                        _, curr = extract_brace_body(code, b_start)
                        # Check for else chains
                        while True:
                            tmp = curr
                            while tmp < len(code) and code[tmp] in ' \t\n\r': tmp += 1
                            if re.match(r'else', code[tmp:]):
                                if re.match(r'else\s+if\s*\(', code[tmp:]):
                                    p_start = code.index('(', tmp)
                                    _, a_p = extract_condition(code, p_start)
                                    b_start = code.index('{', a_p)
                                    _, curr = extract_brace_body(code, b_start)
                                else:
                                    b_start = code.index('{', tmp)
                                    _, curr = extract_brace_body(code, b_start)
                                    break
                            else:
                                break
                        block_end_idx = curr
                    except ValueError: pass
                elif re.match(r'(while|for)\s*\(', code[j:]):
                    try:
                        p_start = code.index('(', j)
                        _, a_p = extract_condition(code, p_start)
                        b_start = code.index('{', a_p)
                        _, block_end_idx = extract_brace_body(code, b_start)
                    except ValueError: pass
                else:
                    # Statement ending in semicolon
                    k = j
                    depth = 0
                    while k < len(code):
                        if code[k] in '([': depth += 1
                        elif code[k] in ')]': depth -= 1
                        elif code[k] == ';' and depth == 0:
                            block_end_idx = k + 1
                            break
                        k += 1

                if block_end_idx != -1:
                    block_code = code[j:block_end_idx]
                    i = block_end_idx
                else:
                    # Fallback to single line
                    next_end = code.find('\n', j)
                    block_code = code[j:next_end].strip() if next_end != -1 else code[j:].strip()
                    i = next_end+1 if next_end != -1 else len(code)

                real_blocks = parse_blocks(block_code, fill_conditions, fill_values)
                if real_blocks and not real_blocks[0]['type'] == 'codeblock':
                    real = real_blocks[0]
                    blocks.append({
                        'type': 'phantom',
                        'hint': hint,
                        'expects': real['type'],
                        'params': real.get('params', []),
                        'exChildren': real.get('exChildren', []),
                        'condition': real.get('condition'),
                        'ifbody': real.get('ifbody', []),
                        'elseifs': real.get('elseifs', []),
                        'elsebody': real.get('elsebody'),
                        'body': real.get('body', []),
                        'forinit': real.get('forinit'),
                        'forcond': real.get('forcond'),
                        'forincr': real.get('forincr'),
                    })
                continue
            end = code.find('\n', i)
            i = end+1 if end != -1 else len(code)
            continue
        if code[i:i+2] == '/*':
            end = code.find('*/', i)
            i = end+2 if end != -1 else len(code)
            continue
        if code[i] == '#':
            end = code.find('\n', i)
            line = code[i:end].strip() if end != -1 else code[i:].strip()
            blocks.append({'type': 'codeblock', 'params': [line]})
            i = end + 1 if end != -1 else len(code)
            continue
        if re.match(r'if\s*\(', code[i:]):
            paren_start = code.index('(', i)
            cond_str, after_paren = extract_condition(code, paren_start)
            brace_start = code.index('{', after_paren)
            body_str, after_body = extract_brace_body(code, brace_start)
            block = {
                'type': 'ifblock',
                'condition': parse_condition(cond_str, fill_conditions),
                'ifbody':   parse_blocks(body_str, fill_conditions, fill_values),
                'elseifs':  [],
                'elsebody': None
            }
            i = after_body
            while i < len(code):
                while i < len(code) and code[i] in ' \t\n\r': i += 1
                if re.match(r'else\s+if\s*\(', code[i:]):
                    paren_start = code.index('(', i)
                    ei_cond, after_paren = extract_condition(code, paren_start)
                    brace_start = code.index('{', after_paren)
                    ei_body, after_body = extract_brace_body(code, brace_start)
                    block['elseifs'].append({
                        'condition': parse_condition(ei_cond, fill_conditions),
                        'body': parse_blocks(ei_body, fill_conditions, fill_values)
                    })
                    i = after_body
                elif re.match(r'else\s*\{', code[i:]) or (re.match(r'else', code[i:]) and not re.match(r'else\s+if', code[i:])):
                    brace_start = code.index('{', i)
                    else_body, after_body = extract_brace_body(code, brace_start)
                    block['elsebody'] = parse_blocks(else_body, fill_conditions, fill_values)
                    i = after_body
                    break
                else:
                    break
            blocks.append(block)
            continue
        if re.match(r'while\s*\(', code[i:]):
            paren_start = code.index('(', i)
            cond_str, after_paren = extract_condition(code, paren_start)
            brace_start = code.index('{', after_paren)
            body_str, after_body = extract_brace_body(code, brace_start)
            blocks.append({
                'type': 'whileloop',
                'condition': parse_condition(cond_str, fill_conditions),
                'body': parse_blocks(body_str, fill_conditions, fill_values)
            })
            i = after_body
            continue
        if re.match(r'for\s*\(', code[i:]):
            paren_start = code.index('(', i)
            for_str, after_paren = extract_condition(code, paren_start)
            brace_start = code.index('{', after_paren)
            body_str, after_body = extract_brace_body(code, brace_start)
            parts = for_str.split(';', 2)
            forinit = parts[0].strip() if len(parts) > 0 else 'int i = 0'
            forcond = parts[1].strip() if len(parts) > 1 else 'i < 10'
            forincr = parts[2].strip() if len(parts) > 2 else 'i++'
            blocks.append({
                'type': 'forloop',
                'forinit': forinit,
                'forcond': forcond,
                'forincr': forincr,
                'body': parse_blocks(body_str, fill_conditions, fill_values)
            })
            i = after_body
            continue
        # Find next semicolon not inside parens or brackets
        depth = 0
        semi = -1
        j = i
        while j < len(code):
            c = code[j]
            if c in '([': depth += 1
            elif c in ')]': depth -= 1
            elif c == ';' and depth == 0:
                semi = j
                break
            j += 1
        if semi == -1: break
        line = code[i:semi+1].strip()
        i = semi + 1
        m = re.match(r'int\s+(\w+)(?:\s*=\s*(.+?))?\s*;', line)
        if m:
            ex = process(parse_expr(m.group(2))) if m.group(2) else {'type': 'value', 'params': [''], 'children': []}
            blocks.append({'type':'intvar','params':[m.group(1),''],'exChildren':[None, ex]})
            continue
        m = re.match(r'long\s+r\s*=\s*random\s*\(\s*(-?\d+)\s*,\s*(-?\d+)\s*\)\s*;', line)
        if m: blocks.append({'type':'randomdelay','params':['','']}); continue
        m = re.match(r'long\s+(\w+)(?:\s*=\s*(.+?))?\s*;', line)
        if m:
            ex = process(parse_expr(m.group(2))) if m.group(2) else {'type': 'value', 'params': [''], 'children': []}
            blocks.append({'type':'longvar','params':[m.group(1),''],'exChildren':[None, ex]})
            continue
        m = re.match(r'unsigned\s+long\s+(\w+)(?:\s*=\s*(.+?))?\s*;', line)
        if m:
            ex = process(parse_expr(m.group(2))) if m.group(2) else {'type': 'value', 'params': [''], 'children': []}
            blocks.append({'type':'longvar','params':[m.group(1),''],'exChildren':[None, ex]})
            continue
        m = re.match(r'bool\s+(\w+)(?:\s*=\s*(true|false))?\s*;', line)
        if m:
            val = (m.group(2) if fill_values else '') if m.group(2) else ''
            blocks.append({'type':'boolvar','params':[m.group(1), val]})
            continue
        m = re.match(r'String\s+(\w+)\s*=\s*Serial\.readString\s*\(\s*\)\s*;', line)
        if m:
            ex = {'type': 'serialreadstring', 'params': [], 'children': []}
            blocks.append({'type':'stringvar','params':[m.group(1),''],'exChildren':[None, ex]})
            continue
        m = re.match(r'String\s+(\w+)(?:\s*=\s*"([^"]*)")?\s*;', line)
        if m:
            val = (m.group(2) if fill_values else '') if m.group(2) else ''
            ex = {'type': 'value', 'params': ['"' + val + '"' if val else ''], 'children': []}
            blocks.append({'type':'stringvar','params':[m.group(1),''],'exChildren':[None, ex]})
            continue
        m = re.match(r'pinMode\s*\(\s*(\w+)\s*,\s*(\w+)\s*\)\s*;', line)
        if m:
            p0 = m.group(1) if fill_values else ''
            p1 = m.group(2) if fill_values else ''
            blocks.append({'type':'pinmode','params':[p0, p1]})
            continue
        m = re.match(r'digitalWrite\s*\(\s*(\w+)\s*,\s*(\w+)\s*\)\s*;', line)
        if m:
            p0 = m.group(1) if fill_values else ''
            p1 = m.group(2) if fill_values else ''
            blocks.append({'type':'digitalwrite','params':[p0, p1]})
            continue
        m = re.match(r'analogWrite\s*\(\s*(\w+)\s*,\s*(\w+)\s*\)\s*;', line)
        if m:
            p0 = m.group(1) if fill_values else ''
            blocks.append({'type':'analogwrite','params':[p0,''],'exChildren':[process(parse_expr(m.group(2)))]})
            continue
        m = re.match(r'tone\s*\(\s*(\w+)\s*,\s*(\w+)\s*,\s*(\w+)\s*\)\s*;', line)
        if m:
            p0 = m.group(1) if fill_values else ''
            p2 = m.group(3) if fill_values else ''
            blocks.append({'type':'tone','params':[p0,'', p2],'exChildren':[process(parse_expr(m.group(2)))]})
            continue
        m = re.match(r'tone\s*\(\s*(\w+)\s*,\s*(\w+)\s*\)\s*;', line)
        if m:
            p0 = m.group(1) if fill_values else ''
            blocks.append({'type':'tone','params':[p0,'',None],'exChildren':[process(parse_expr(m.group(2)))]})
            continue
        m = re.match(r'noTone\s*\(\s*(.+?)\s*\)\s*;', line)
        if m:
            ex = process(parse_expr(m.group(1)))
            blocks.append({'type':'notone','params':[''],'exChildren':[ex]})
            continue
        m = re.match(r'delay\s*\(\s*(.+?)\s*\)\s*;', line)
        if m:
            ex = process(parse_expr(m.group(1)))
            blocks.append({'type':'delay','params':[''],'exChildren':[ex]})
            continue
        m = re.match(r'delayMicroseconds\s*\(\s*(.+?)\s*\)\s*;', line)
        if m:
            ex = process(parse_expr(m.group(1)))
            blocks.append({'type':'delaymicroseconds','params':[''],'exChildren':[ex]})
            continue
        m = re.match(r'Serial\.begin\s*\(\s*(\d+)\s*\)\s*;', line)
        if m:
            p0 = m.group(1) if fill_values else ''
            blocks.append({'type':'serialbegin','params':[p0]})
            continue
        m = re.match(r'Serial\.(print|println)\s*\(\s*(.+?)\s*\)\s*;', line)
        if m:
            fn_type = m.group(1)
            content = m.group(2).strip()
            ex = process(parse_expr(content))
            blocks.append({'type':'serialprint','params':['',fn_type],'exChildren':[ex]})
            continue
        m = re.match(r'(\w+)\s*\+\+\s*;', line)
        if m: blocks.append({'type':'increment','params':[m.group(1),'++','1']}); continue
        m = re.match(r'(\w+)\s*--\s*;', line)
        if m: blocks.append({'type':'increment','params':[m.group(1),'--','1']}); continue
        m = re.match(r'(\w+)\s*\+=\s*(.+?)\s*;', line)
        if m:
            val = m.group(2) if fill_values else ''
            blocks.append({'type':'increment','params':[m.group(1),'+=', val]})
            continue
        m = re.match(r'(\w+)\s*-=\s*(.+?)\s*;', line)
        if m:
            val = m.group(2) if fill_values else ''
            blocks.append({'type':'increment','params':[m.group(1),'-=', val]})
            continue
        m = re.match(r'(\w+)\s*=\s*(.+?)\s*;', line)
        if m and not re.match(r'(int|long|float|bool|byte|char|String|unsigned)\s', line):
            ex = process(parse_expr(m.group(2)))
            blocks.append({'type':'setvar','params':[m.group(1),''],'exChildren':[None, ex]})
            continue

        # Fallback for unrecognized statements ending in semicolon
        blocks.append({'type': 'codeblock', 'params': [line]})

    for b in blocks:
        if 'id' not in b:
            b['id'] = str(random.random() * 1000000000000000)
    return blocks


def parse_sketch(sketch_code, fill_conditions=False, fill_values=False):
    result = {'global': [], 'setup': [], 'loop': []}
    setup_start = re.search(r'void\s+setup\s*\(.*?\)', sketch_code)
    global_code = sketch_code[:setup_start.start()].strip() if setup_start else ''
    setup_m = re.search(r'void\s+setup\s*\(.*?\)\s*\{', sketch_code)
    loop_m  = re.search(r'void\s+loop\s*\(.*?\)\s*\{', sketch_code)
    setup_code = extract_brace_body(sketch_code, setup_m.end()-1)[0] if setup_m else ''
    loop_code  = extract_brace_body(sketch_code, loop_m.end()-1)[0]  if loop_m  else ''
    result['global'] = parse_blocks(global_code, fill_conditions, fill_values)
    result['setup']  = parse_blocks(setup_code,  fill_conditions, fill_values)
    result['loop']   = parse_blocks(loop_code,   fill_conditions, fill_values)
    return result


def collect_types(blocks):
    """Walk a block tree and return the set of all block types used."""
    types = set()
    for b in blocks:
        types.add(b['type'])
        if b['type'] == 'ifblock':
            types.update(collect_types(b.get('ifbody', [])))
            for ei in b.get('elseifs', []):
                types.update(collect_types(ei.get('body', [])))
            if b.get('elsebody'):
                types.update(collect_types(b['elsebody']))
        elif b['type'] in ('forloop', 'whileloop'):
            types.update(collect_types(b.get('body', [])))
    return types


def parse_progression(sketch_code):
    """
    Parse a multi-step progression sketch into a list of steps.

    Step boundaries are marked with //>> label | guidance | view
    Phantom blocks are marked with //?? hint followed by the real line.
    Locked blocks are marked with //## as usual.

    Returns a list of step dicts:
    [
        {
            'label': 'Step 1 — The Variables',
            'guidance': 'guided',    # or 'open' or 'free'
            'view': 'blocks',        # or 'editor'
            'global': [...],
            'setup':  [...],
            'loop':   [...],
        },
        ...
    ]

    Each step's blocks include all locked (//##) blocks from previous steps
    plus the new phantom and locked blocks for this step.
    """
    # Split on //>> boundaries
    step_pattern = re.compile(r'^//>>(.+)$', re.MULTILINE)
    boundaries = [(m.start(), m.group(1).strip()) for m in step_pattern.finditer(sketch_code)]

    if not boundaries:
        return None  # not a progression sketch

    # Build raw step chunks
    raw_steps = []
    for idx, (start, header) in enumerate(boundaries):
        end = boundaries[idx+1][0] if idx+1 < len(boundaries) else len(sketch_code)
        # Exclude the //>> line itself
        chunk_start = sketch_code.find('\n', start)
        chunk = sketch_code[chunk_start:end] if chunk_start != -1 else ''

        # Parse label, guidance, and view
        parts = [p.strip() for p in header.split('|')]
        label = parts[0]
        guidance = parts[1].lower() if len(parts) > 1 else 'guided'
        view = parts[2].lower() if len(parts) > 2 else 'blocks'
        palette_filter = parts[3].lower() if len(parts) > 3 else 'nofilter'

        raw_steps.append({
            'label': label,
            'guidance': guidance or 'guided',
            'view': view or 'blocks',
            'palette_filter': palette_filter or 'nofilter',
            'chunk': chunk
        })

    # Parse each step — collecting cumulative locked blocks
    # Only global section accumulates phantom_resolved markers.
    # Setup and loop are self-contained in each chunk via //## codeblocks.
    cumulative_global = []
    cumulative_setup = []
    cumulative_loop = []
    steps = []

    for step in raw_steps:
        # Parse this step's chunk as a sketch
        parsed = parse_sketch(step['chunk'], fill_conditions=True, fill_values=True)

        if step['palette_filter'] == 'filter':
            step_types = collect_types(
                parsed['global'] + parsed['setup'] + parsed['loop']
            )
            step['palette'] = list(step_types)
        else:
            step['palette'] = None

        # Determine active section based on where new blocks (phantoms) are located
        active_section = 'loop'
        if any(b['type'] == 'phantom' for b in parsed['global']):
            active_section = 'global'
        elif any(b['type'] == 'phantom' for b in parsed['setup']):
            active_section = 'setup'
        elif any(b['type'] == 'phantom' for b in parsed['loop']):
            active_section = 'loop'
        elif parsed['setup']:
            active_section = 'setup'
        elif parsed['global']:
            active_section = 'global'

        # Build full workspace for this step:
        # global: cumulative phantom_resolved markers + this chunk's global blocks
        # setup/loop: if chunk has content, use it (replacing cumulative). Else carry over.
        full = {
            'global': cumulative_global + parsed['global'],
            'setup': parsed['setup'] if parsed['setup'] else cumulative_setup,
            'loop': parsed['loop'] if parsed['loop'] else cumulative_loop,
        }
        
        steps.append({
            'label':  step['label'],
            'guidance': step['guidance'],
            'view':   step['view'],
            'palette': step['palette'],
            'active_section': active_section,
            'global': full['global'],
            'setup':  full['setup'],
            'loop':   full['loop'],
        })

        # Update cumulative global — only non-structural phantoms become phantom_resolved
        STRUCTURAL = ('ifblock', 'forloop', 'whileloop')
        for b in parsed['global']:
            if b['type'] == 'phantom':
                cumulative_global.append({
                    'type': 'phantom_resolved',
                    'expects': b['expects'],
                    'hint': b['hint'],
                })
            elif b['type'] != 'phantom':
                cumulative_global.append(b)

        if parsed['setup']:
            cumulative_setup = []
        for b in parsed['setup']:
            if b['type'] == 'phantom':
                cumulative_setup.append({
                    'type': 'phantom_resolved', # This becomes a slot for student work
                    'expects': b['expects'],
                    'hint': b['hint'],
                })
            elif b['type'] != 'phantom':
                cumulative_setup.append(b)

        if parsed['loop']:
            cumulative_loop = []
        for b in parsed['loop']:
            if b['type'] == 'phantom':
                cumulative_loop.append({
                    'type': 'phantom_resolved', # This becomes a slot for student work
                    'expects': b['expects'],
                    'hint': b['hint'],
                })
            elif b['type'] != 'phantom':
                cumulative_loop.append(b)

    return steps


# ── Component ─────────────────────────────────────────────────────────

def render_builder(height=550, preset=None, drawer_content=None, pin_refs=None, username=None, page=None, fill_conditions=None, fill_values=None, return_html=True, is_overlay=False, supabase_url=None, supabase_key=None, lock_mode=None):

    # Guard: if a string is passed positionally treat it as preset
    master_sketch_js = 'var MASTER_SKETCH=null;'
    if isinstance(height, str):
        preset = height
        height = 550

    dv = 'blocks'
    lv = False
    rv = False
    lm = lock_mode if lock_mode is not None else False
    p = None

    # Build initial block state from preset if provided
    if preset:
        from utils.project_registry import PROJECTS
        if preset in PROJECTS:
            proj = PROJECTS[preset]
            p = proj.get("presets", {}).get("default")
            if p is None and 'sketch' in proj:
                p = proj  # project itself is the preset
        elif preset in PRESETS:
            p = PRESETS[preset]
        else:
            # Search for the preset name inside all projects
            for proj in PROJECTS.values():
                if "presets" in proj and preset in proj["presets"]:
                    p = proj["presets"][preset]
                    break

    if p:
        if isinstance(p, dict):
            dv = p.get('default_view', 'blocks')
            lv = p.get('lock_view', False)
            rv = p.get('read_only', False) if isinstance(p, dict) else False
            if lock_mode is None:
                lm = p.get('lock_mode', False)
        sketch_code = p['sketch'] if isinstance(p, dict) else p

        # Determine fill_conditions and fill_values for parse_sketch
        # If not explicitly provided, and it's a non-progression sketch with default_view 'editor',
        # then we want to fill values.
        _fill_conditions = fill_conditions if fill_conditions is not None else (p.get('fill_conditions') if isinstance(p, dict) else None)
        _fill_values = fill_values if fill_values is not None else (p.get('fill_values') if isinstance(p, dict) else None)

        # Detect progression sketch early — skip parse_sketch entirely
        is_progression = '//>>' in sketch_code

        if not is_progression and dv == 'editor' and _fill_conditions is None and _fill_values is None:
            # This is the specific mode the user described:
            # non-progression sketch AND default view is 'editor'.
            # In this case, we want to preserve values when parsing the sketch.
            _fill_conditions = True
            _fill_values = True

        # Final fallback to False if still not set
        if _fill_conditions is None: _fill_conditions = False
        if _fill_values is None: _fill_values = False

        if not is_progression:
            blocks = parse_sketch(sketch_code, fill_conditions=_fill_conditions, fill_values=_fill_values)
            master_blocks = parse_sketch(sketch_code, fill_conditions=True, fill_values=True)
            # Build palette allowed set: always auto from sketch, then apply amendments
            base_types = collect_types(
                blocks['global'] + blocks['setup'] + blocks['loop']
            )
            if isinstance(p, dict):
                palette_add    = set(p.get('palette_add',    []))
                palette_remove = set(p.get('palette_remove', []))
            else:
                palette_add, palette_remove = set(), set()
            allowed = (base_types | palette_add) - palette_remove
            palette_js = 'var PALETTE_ALLOWED=' + str(list(allowed)).replace("'", '"') + ';'
        else:
            blocks = {'global': [], 'setup': [], 'loop': []}
            palette_js = 'var PALETTE_ALLOWED=null;'
        def cond_to_js(c):
            return ("{"
                    "leftExpr:"   + ex_node_to_js(c.get('leftExpr'))   + ","
                    "op:'"        + c.get('op','==')                   + "',"
                    "rightExpr:"  + ex_node_to_js(c.get('rightExpr'))  + ","
                    "joiner:'"    + c.get('joiner','none')              + "',"
                    "leftExpr2:"  + ex_node_to_js(c.get('leftExpr2'))  + ","
                    "op2:'"       + c.get('op2','==')                  + "',"
                    "rightExpr2:" + ex_node_to_js(c.get('rightExpr2')) + "}")
        def ex_node_to_js(node):
            if node is None:
                return 'null'
            children_js = '[' + ','.join(ex_node_to_js(c) for c in (node.get('children') or [])) + ']'
            params_js = json_list(node.get('params') or [])
            return ("{type:'" + node['type'] + "',"
                    "params:" + params_js + ","
                    "children:" + children_js + "}")

        def json_list(lst):
            if lst is None: return '[]'
            items = []
            for v in lst:
                if v is None:
                    items.append('null')
                elif isinstance(v, str):
                    escaped = v.replace('\\', '\\\\').replace("'", "\\'")
                    items.append("'" + escaped + "'")
                else:
                    items.append(str(v))
            return '[' + ','.join(items) + ']'

        def block_to_js(b):
            bid = b.get('id') or str(random.random() * 1000000000000000)
            bid_js = f"'{bid}'"
            if b['type'] == 'ifblock':
                ifbody_js  = '[' + ','.join(block_to_js(x) for x in b['ifbody']) + ']'
                elseifs_js = '[' + ','.join(
                    '{condition:' + cond_to_js(ei['condition']) + ',body:' +
                    '[' + ','.join(block_to_js(x) for x in ei['body']) + ']' + '}'
                    for ei in b['elseifs']
                ) + ']'
                else_js = ('null' if b['elsebody'] is None
                           else '[' + ','.join(block_to_js(x) for x in b['elsebody']) + ']')
                return ('{id:' + bid_js + ',type:\'ifblock\','
                        'condition:' + cond_to_js(b['condition']) + ','
                        'ifbody:' + ifbody_js + ','
                        'elseifs:' + elseifs_js + ','
                        'elsebody:' + else_js + '}')
            if b['type'] == 'forloop':
                body_js = '[' + ','.join(block_to_js(x) for x in b.get('body', [])) + ']'
                fi = b.get('forinit','int i = 0').replace("'","\\'")
                fc = b.get('forcond','i < 10').replace("'","\\'")
                fr = b.get('forincr','i++').replace("'","\\'")
                return ("{id:" + bid_js + ",type:'forloop',"
                        "forinit:'" + fi + "',forcond:'" + fc + "',forincr:'" + fr + "',"
                        "body:" + body_js + "}")
            if b['type'] == 'whileloop':
                body_js = '[' + ','.join(block_to_js(x) for x in b.get('body', [])) + ']'
                cond = b.get('condition') or {'leftExpr': None, 'op': '!=', 'rightExpr': None, 'joiner': 'none', 'leftExpr2': None, 'op2': '==', 'rightExpr2': None}
                return ("{id:" + bid_js + ",type:'whileloop',"
                        "condition:" + cond_to_js(cond) + ","
                        "body:" + body_js + "}")
            if b['type'] == 'codeblock':
                escaped = b['params'][0].replace('\\', '\\\\').replace("'", "\\'")
                return "{id:" + bid_js + ",type:'codeblock',params:['" + escaped + "']}"
            if b['type'] == 'phantom':
                hint    = b.get('hint','').replace("'", "\\'")
                expects = b.get('expects','')
                params_js = json_list(b.get('params', []))
                ex = b.get('exChildren') or []
                ex_js = '[' + ','.join(ex_node_to_js(n) for n in ex) + ']'
                cond = b.get('condition')
                cond_js = cond_to_js(cond) if cond else 'null'
                fi = (b.get('forinit') or '').replace("'", "\\'")
                fc = (b.get('forcond') or '').replace("'", "\\'")
                fr = (b.get('forincr') or '').replace("'", "\\'")
                
                # Serialise children for if/for/while phantoms
                ifbody_js = '[' + ','.join(block_to_js(x) for x in b.get('ifbody', [])) + ']'
                elseifs_js = '[' + ','.join(
                    '{condition:' + cond_to_js(ei['condition']) + ',body:' +
                    '[' + ','.join(block_to_js(x) for x in ei['body']) + ']' + '}'
                    for ei in b.get('elseifs', [])
                ) + ']'
                elsebody_js = ('null' if b.get('elsebody') is None else '[' + ','.join(block_to_js(x) for x in b['elsebody']) + ']')
                body_js = '[' + ','.join(block_to_js(x) for x in b.get('body', [])) + ']'

                return ("{id:" + bid_js + ",type:'phantom',"
                        "hint:'" + hint + "',"
                        "expects:'" + expects + "',"
                        "params:" + params_js + ","
                        "exChildren:" + ex_js + ","
                        "condition:" + cond_js + ","
                        "ifbody:" + ifbody_js + ",elseifs:" + elseifs_js + ",elsebody:" + elsebody_js + ",body:" + body_js + ","
                        "forinit:'" + fi + "',"
                        "forcond:'" + fc + "',"
                        "forincr:'" + fr + "'}")
            if b['type'] == 'phantom_resolved':
                hint    = b.get('hint','').replace("'", "\\'")
                expects = b.get('expects','')
                return ("{id:" + bid_js + ",type:'phantom_resolved',"
                        "hint:'" + hint + "',"
                        "expects:'" + expects + "'}")
            # General case — serialise params and exChildren
            params_js = json_list(b.get('params', []))
            ex = b.get('exChildren') or []
            ex_js = '[' + ','.join(ex_node_to_js(n) for n in ex) + ']'
            return ("{id:" + bid_js + ",type:'" + b['type'] + "',"
                    "params:" + params_js + ","
                    "exChildren:" + ex_js + "}")

        if not is_progression:
            mg = '[' + ','.join(block_to_js(b) for b in master_blocks['global']) + ']'
            ms = '[' + ','.join(block_to_js(b) for b in master_blocks['setup'])  + ']'
            ml = '[' + ','.join(block_to_js(b) for b in master_blocks['loop'])   + ']'
            master_sketch_js = "var MASTER_SKETCH={global:" + mg + ",setup:" + ms + ",loop:" + ml + "};"

        # Check if this is a progression sketch
        steps = parse_progression(sketch_code) if is_progression else None
        if steps:
            # Progression mode — inject STEPS array
            def step_to_js(step):
                gb = '[' + ','.join(block_to_js(b) for b in step['global']) + ']'
                sb = '[' + ','.join(block_to_js(b) for b in step['setup'])  + ']'
                lb = '[' + ','.join(block_to_js(b) for b in step['loop'])   + ']'
                label   = step['label'].replace("'", "\\'")
                guidance = step['guidance']
                view     = step['view']
                active  = step.get('active_section', 'loop')
                palette = step.get('palette')
                step_palette_js = 'null' if palette is None else str(palette).replace("'", '"')
                return ("{label:'" + label + "',guidance:'" + guidance + "',view:'" + view + "',"
                        "palette:" + step_palette_js + ","
                        "active:'" + active + "',"
                        "global:" + gb + ",setup:" + sb + ",loop:" + lb + "}")
            steps_js = '[' + ','.join(step_to_js(s) for s in steps) + ']'
            palette_js = 'var PALETTE_ALLOWED=null;'
            initial_js = ("PROGRESSION_MODE=true;"
                          "STEPS=" + steps_js + ";"
                          "CURRENT_STEP=0;"
                          "CHECK_FAIL_COUNT=0;"
                          "STUDENT_SAVES=[];"
                          "buildWorkspace(0,null);")
        else:
            gb = '[' + ','.join(block_to_js(b) for b in blocks['global']) + ']'
            sb = '[' + ','.join(block_to_js(b) for b in blocks['setup'])  + ']'
            lb = '[' + ','.join(block_to_js(b) for b in blocks['loop'])   + ']'
            initial_js = "SECTIONS.global=" + gb + ";SECTIONS.setup=" + sb + ";SECTIONS.loop=" + lb + ";genCode();render();"
    else:
        initial_js = ""
        palette_js = 'var PALETTE_ALLOWED=null;'
    css = (
        "#block-builder-ui * { box-sizing:border-box; margin:0; padding:0; }"
        "#block-builder-ui { width:100%; height:100%; overflow:hidden; position:relative; display:flex; flex-direction:column;"
        "  background:#f6f8fa; font-family: 'Nunito', 'Quicksand', system-ui, sans-serif; background: #f4f8ff; color:#24292f; }"
        "#block-builder-ui #palette { width:110px; flex-shrink:0; background:#ffffff;"
        "  border-right:1px solid #d0d7de; display:flex; flex-direction:column;"
        "  padding:6px; gap:4px; overflow-y:auto; }"
        "#block-builder-ui #palette::-webkit-scrollbar { width:3px; }"
        "#block-builder-ui #palette::-webkit-scrollbar-thumb { background:#d0d7de; }"
        ".pal-title { font-size:9px; color:#57606a; text-transform:uppercase;"
        "  letter-spacing:.06em; padding:2px 0 4px 0; border-bottom:1px solid #d0d7de; margin-bottom:2px; }"
        ".block-btn { width:100%; padding:5px 6px; border-radius:14px; border:none; box-shadow:0 4px 10px rgba(0,0,0,0.08);"
        "  background:#f6f8fa; cursor:pointer; font-size:14px; font-weight:600; color:#24292f;"
        "  font-family:inherit; text-align:left; }"
        ".block-btn:hover { border-color:#0969da; color:#0969da; background:#ddf4ff; }"
        "#block-builder-ui #workspace { flex:1; display:flex; flex-direction:column; gap:4px;"
        "  padding:6px 6px 10px 6px; overflow:hidden; min-width:0; justify-content:flex-start; }"
        ".section { flex:0 0 36px; border:2px solid #dbeafe; border-radius:14px;"
        "  box-shadow:0 4px 12px rgba(0,0,0,0.06); background:#ffffff;"
        "  display:flex; flex-direction:column; overflow:hidden;"
        "  transition:flex 0.3s ease, box-shadow 0.2s ease; min-height:0; }"
        ".section.expanded { flex:1 1 0; box-shadow:0 8px 24px rgba(0,0,0,0.1); min-height:0; max-height:none; }"
        ".section::-webkit-scrollbar { width:3px; }"
        ".section::-webkit-scrollbar-thumb { background:#d0d7de; }"
        ".s-global.active { border-color:#0969da; }"
        ".s-global.active .section-header { background:linear-gradient(135deg,#0969da,#54aeff); }"
        ".s-setup.active  { border-color:#1a7f37; }"
        ".s-setup.active  .section-header { background:linear-gradient(135deg,#1a7f37,#4ac26b); }"
        ".s-loop.active   { border-color:#9a6700; }"
        ".s-loop.active   .section-header { background:linear-gradient(135deg,#9a6700,#d4a72c); }"
        ".error-block { border: 2.5px solid #ff4d4f !important; background: #fff1f0 !important; box-shadow: 0 0 12px rgba(255, 77, 79, 0.6) !important; }"
        ".if-block.error-block > .if-header, .if-block.error-block > .elseif-header, .if-block.error-block > .else-header { background: #ffccc7 !important; border-color: #ff4d4f !important; flex-direction: column; align-items: flex-start !important; }"
        ".for-block.error-block > .for-header, .while-block.error-block > .while-header { background: #ffccc7 !important; border-color: #ff4d4f !important; flex-direction: column; align-items: flex-start !important; }"
        ".error-block .blk-name, .error-block .if-keyword, .error-block .for-keyword, .error-block .while-keyword { color: #820014 !important; }"
        ".block-hint { display:none; width:100%; font-size:12px; color:#cf222e; margin-top:6px; font-weight:800; white-space:normal; padding: 4px 8px; background: rgba(255,255,255,0.5); border-radius: 6px; }"
        ".error-block > .block-hint, .error-block > .if-header > .block-hint, .error-block > .for-header > .block-hint, .error-block > .while-header > .block-hint { display:block; }"
        ".ws-block { display:flex; align-items:center; flex-wrap:wrap; gap:4px;"
        "  background:#f6f8fa; border: none; border-radius:18px;"
        "  padding:14px 16px; margin-bottom:3px; box-shadow:0 6px 14px rgba(0,0,0,0.08); }"
        ".ws-block.codeblock-block { background:#fff8e1; border:2px dashed #f9a825; }"
        ".codeblock-code { font-family:monospace; font-size:13px; color:#6e4800;"
        "  background:none; border:none; padding:0; flex:1; }"
        ".blk-name { font-size:16px; font-weight:800; color:#0969da; min-width:60px; }"
        ".blk-field { display:flex; flex-direction:column; font-size:8px; }"
        ".blk-field label { color:#57606a; margin-bottom:1px; }"
        ".blk-input { font-size:14px; padding:6px 8px; width:80px; max-width:80px;"
        "  align-self:flex-start;"
        "  background:#ffffff; color:#24292f; border:2px solid #e5e7eb; border-radius:10px; font-family:inherit; }"
        ".blk-input:focus { outline:none; border-color:#0969da; }"
        ".act { background:none; border:1px solid #d0d7de; color:#57606a; cursor:pointer;"
        "  font-size:9px; padding:1px 3px; border-radius:3px; }"
        ".act:hover { color:#24292f; border-color:#57606a; background:#f6f8fa; }"
        ".if-block { margin-bottom:3px; }"
        ".if-header, .elseif-header, .else-header { display:flex; align-items:center;"
        "  gap:4px; flex-wrap:wrap; background:#fff8c5; border:1px solid #d4a72c; padding:3px 6px; }"
        ".if-header    { border-radius:5px 5px 0 0; }"
        ".elseif-header { border-top:none; }"
        ".else-header   { border-top:none; }"
        ".for-header { display:flex; align-items:center; gap:4px; flex-wrap:wrap;"
        "  background:#e8f5e9; border:1px solid #2e7d32; border-radius:5px 5px 0 0; padding:3px 6px; }"
        ".while-header { display:flex; align-items:center; gap:4px; flex-wrap:wrap;"
        "  background:#ede7f6; border:1px solid #6a1b9a; border-radius:5px 5px 0 0; padding:3px 6px; }"
        ".for-block, .while-block { margin-bottom:3px; }"
        ".for-body { border-left:1px dashed #2e7d32; border-right:1px dashed #2e7d32;"
        "  border-bottom:1px dashed #2e7d32; border-radius:0 0 5px 5px;"
        "  padding:4px 4px 4px 60px; min-height:28px; cursor:pointer; }"
        ".while-body { border-left:1px dashed #6a1b9a; border-right:1px dashed #6a1b9a;"
        "  border-bottom:1px dashed #6a1b9a; border-radius:0 0 5px 5px;"
        "  padding:4px 4px 4px 60px; min-height:28px; cursor:pointer; }"
        ".for-body:hover { border-color:#1b5e20; }"
        ".while-body:hover { border-color:#4a148c; }"
        ".for-body.selected, .while-body.selected { border-color:#0969da; border-style:solid; background:#ddf4ff; }"
        ".for-keyword { font-size:14px; font-weight:bold; color:#2e7d32; }"
        ".while-keyword { font-size:14px; font-weight:bold; color:#6a1b9a; }"
        ".if-keyword { font-size:14px; font-weight:bold; color:#cf222e; }"
        ".cond-field { display:flex; flex-direction:column; font-size:8px; }"
        ".cond-field label { color:#57606a; margin-bottom:1px; }"
        ".cond-input  { font-size:14px; padding:6px 8px; width:55px; background:#ffffff;"
        "  color:#24292f; border:2px solid #e5e7eb; border-radius:10px; font-family:inherit; }"
        ".cond-select { font-size:14px; padding:6px 8px; width:80px; background:#ffffff;"
        "  color:#24292f; border:2px solid #e5e7eb; border-radius:10px; font-family:inherit; }"
        ".cond-joiner { font-size:14px; padding:6px 8px; width:55px; background:#ffffff;"
        "  color:#9a6700; border:2px solid #e5e7eb; border-radius:10px; font-family:inherit; }"
        ".cond-input:focus, .cond-select:focus, .cond-joiner:focus { outline:none; border-color:#cf222e; }"
        ".if-body { border-left:1px dashed #d0d7de; border-right:1px dashed #d0d7de;"
        "  border-bottom:none; padding:4px 4px 4px 60px; min-height:28px; cursor:pointer; }"
        ".if-body.last { border-bottom:1px dashed #d0d7de; border-radius:0 0 5px 5px; }"
        ".if-body:hover { border-color:#57606a; }"
        ".if-body.selected { border-color:#0969da; border-style:solid; background:#ddf4ff; }"
        ".if-body.ancestor { border-color:#84c7fb; border-style:solid; }"
        ".if-block.ancestor > .if-header { border-color:#84c7fb !important; background:#eaf6ff !important; }"
        ".if-block.ancestor > .elseif-header { border-color:#84c7fb !important; background:#eaf6ff !important; }"
        ".if-block.ancestor > .else-header { border-color:#84c7fb !important; background:#eaf6ff !important; }"
        ".body-hint { font-size:8px; color:#bbb; pointer-events:none; padding:2px 0; }"
        "#block-builder-ui #statusbar { font-size:9px; color:#57606a; padding:3px 7px; flex-shrink:0;"
        "  background:#ffffff; border-bottom:1px solid #d0d7de; }"
        "#block-builder-ui #statusbar span { color:#0969da; }"
        "#block-builder-ui #codepanel { width:250px; flex-shrink:0; border-left:1px solid #d0d7de;"
        "  display:flex; flex-direction:column; padding:6px 30px 6px 6px; gap:5px; }"
        "#code-btns { display:flex; gap:5px; flex-shrink:0; padding-right: 28px; padding-top:10px; padding-left: 5px;}"
        "#nav-btns { display:flex; gap:5px; flex-shrink:0; padding-right: 28px; padding-left: 5px;}"
        "#block-builder-ui #msg { font-size:9px; color:#cf222e; opacity:0; transition:opacity 0.3s; flex-shrink:0; min-height:14px; }"
        "#block-builder-ui #msg.show { opacity:1; }"
        "#block-builder-ui #codeout { flex:1; background:#f6f8fa; border:1px solid #d0d7de; border-radius:6px;"
        "  padding:6px 7px; font-size:9px; white-space:pre; overflow-y:auto;"
        "  color:#0550ae; line-height:1.5; min-height:0; }"
        "#block-builder-ui #codeout::-webkit-scrollbar { width:3px; }"
        "#block-builder-ui #codeout::-webkit-scrollbar-thumb { background:#d0d7de; }"
        ".cbtn { flex:1; padding:4px; border-radius:5px; border:1px solid #d0d7de;"
        "  background:#f6f8fa; color:#24292f; cursor:pointer; font-family:inherit; font-size:9px; }"
        ".cbtn:hover { background:#e6ebf1; }"
        "#block-builder-ui #app { display:flex; flex-direction:row; width:100%; flex:1; position:relative; min-height:0; }"
        "#drawer-tab { position:absolute; right:0; top:0; height:100%; width:24px;"
        "  background:#e53935; border-left:1px solid #d0d7de;"
        "  display:flex; align-items:center; justify-content:center;"
        "  cursor:pointer; z-index:10; user-select:none; transition:background 0.15s; }"
        "#drawer-tab:hover { background:#e6ebf1; }"
        "#drawer-tab span { writing-mode:vertical-rl; text-orientation:mixed;"
        "  font-size:14px; letter-spacing:.1em; color:#ffffff;"
        "  text-transform:uppercase; transform:rotate(180deg); }"
        "#drawer-tab:hover span { color:#0969da; }"
        "#drawer-panel { position:absolute; right:18px; top:0; height:100%; width:0;"
        "  background:#ffffff; border-left:1px solid #d0d7de;"
        "  overflow:hidden; z-index:9; transition:width 0.25s ease; display:flex; flex-direction:column; }"
        "#drawer-panel.open { width:600px; }"
        "#drawer-inner { width:600px; height:100%; display:flex; flex-direction:column; flex-shrink:0; }"
        ".drawer-title { font-size:13px; font-weight:700; color:#0969da;"
        "  text-transform:uppercase; letter-spacing:.08em; flex-shrink:0;"
        "  border-bottom:1px solid #d0d7de; padding:12px 14px 8px 14px; }"
        ".drawer-tip { background:#ddf4ff; border-bottom:1px solid #84c7fb;"
        "  padding:8px 14px; font-size:11px; color:#0969da; line-height:1.7; flex-shrink:0; }"
        ".drawer-tabs { display:flex; flex-shrink:0; border-bottom:1px solid #d0d7de; }"
        ".drawer-tab-btn { flex:1; padding:8px 4px; font-size:11px; font-family:inherit;"
        "  background:none; border:none; border-bottom:2px solid transparent;"
        "  color:#57606a; cursor:pointer; text-align:center; transition:color 0.15s; }"
        ".drawer-tab-btn:hover { color:#24292f; }"
        ".drawer-tab-btn.active { color:#0969da; border-bottom-color:#0969da; }"
        ".drawer-tab-panels { flex:1; overflow-y:auto; }"
        ".drawer-tab-panels::-webkit-scrollbar { width:3px; }"
        ".drawer-tab-panels::-webkit-scrollbar-thumb { background:#d0d7de; }"
        ".drawer-tab-panel { display:none; padding:14px; font-family: 'Inter', sans-serif;}"
        ".drawer-tab-panel.active { display:block; }"
        ".drawer-tab-panel p { font-size:16px; color:#24292f; line-height:1.8; white-space:pre-wrap; margin-bottom:8px; }"
        ".drawer-tab-panel img { width:100%; border-radius:5px; border:1px solid #d0d7de; margin-top:8px; }"
        ".drawer-tab-panel code { display:inline-block; background:#f6f8fa; border:1px solid #d0d7de;"
        "  border-radius:3px; padding:2px 6px; font-size:11px; color:#953800; font-family:'Courier New',monospace; }"
        # === ACCORDION ===
        ".section-header { cursor:pointer; user-select:none; padding:8px 14px; height:36px;"
        "  display:flex; align-items:center; justify-content:space-between;"
        "  font-size:11px; font-weight:800; letter-spacing:0.5px; flex-shrink:0;"
        "  background:linear-gradient(135deg,#60a5fa,#818cf8); color:white; }"
        ".section-header h3 { font-size:11px; font-weight:800; letter-spacing:.06em;"
        "  text-transform:uppercase; color:white; margin:0; pointer-events:none; user-select:none; }"
        ".section-header .toggle-arrow { font-size:10px; transition:transform 0.25s ease; }"
        ".section.expanded .section-header .toggle-arrow { transform:rotate(180deg); }"
        ".section-body { flex:1; overflow-y:auto; padding:5px 7px; min-height:0; }"
        ".section-body::-webkit-scrollbar { width:3px; }"
        ".section-body::-webkit-scrollbar-thumb { background:#d0d7de; }"
        ".phantom-block { display:flex; align-items:center; gap:8px; padding:6px 10px;"
        "  border:2px dashed #0969da; border-radius:10px; background:#f0f9ff;"
        "  cursor:pointer; margin-bottom:3px; transition:all 0.15s; }"
        ".phantom-block:hover { background:#ddf4ff; border-color:#0550ae; }"
        ".phantom-block.active { background:#ddf4ff; border-style:solid; border-color:#0550ae; }"
        ".phantom-icon { font-size:14px; }"
        ".phantom-hint { font-size:12px; font-weight:600; color:#0969da; flex:1; }"
        ".phantom-expects { font-size:10px; color:#57606a; font-family:monospace; }"
        "#step-bar { display:none; background:#0969da; color:#fff; padding:6px 12px;"
        "  font-size:11px; font-weight:700; letter-spacing:.05em; text-transform:uppercase;"
        "  display:flex; align-items:center; justify-content:space-between; flex-shrink:0; }"
        "#step-label { flex:1; }"
        "#step-progress { font-size:10px; opacity:0.8; }"
        "#nextbtn { background:#2ea043; border:none; color:#fff; font-family:inherit;"
        "  font-size:11px; font-weight:700; padding:4px 12px; border-radius:8px;"
        "  cursor:pointer; opacity:0.5; pointer-events:none; transition:all 0.2s; }"
        "#nextbtn.ready { opacity:1; pointer-events:auto; }"
        "#nextbtn.ready:hover { background:#3bb54f; }"
        # Expression slot styles
        ".expr-slot { display:inline-flex; align-items:center; gap:2px; min-width:60px;"
        "  background:#fff; border:2px dashed #c0c0c0; border-radius:8px;"
        "  padding:2px 6px; cursor:pointer; font-size:11px; color:#888;"
        "  transition:border-color 0.15s, background 0.15s; vertical-align:middle; position:relative; }"
        ".expr-slot:hover { border-color:#0969da; color:#0969da; background:#ddf4ff; }"
        ".expr-slot.active { border-color:#0969da; border-style:solid; background:#ddf4ff; }"
        ".expr-slot.has-expr { border-style:solid; padding:2px 4px; background:#f0f6ff; }"
        ".expr-chip { display:inline-flex; align-items:center; gap:3px; border-radius:6px;"
        "  padding:2px 6px; font-size:11px; font-weight:700; color:#fff; }"
        ".expr-chip .expr-remove { font-size:9px; cursor:pointer; opacity:0.7; margin-left:2px; }"
        ".expr-chip .expr-remove:hover { opacity:1; }"
        ".expr-block-inline { display:inline-flex; align-items:center; flex-wrap:wrap; gap:3px;"
        "  border-radius:8px; padding:2px 6px; font-size:11px; font-weight:700; }"
        ".expr-input { font-size:12px; padding:2px 5px; width:55px; background:#fff;"
        "  border:1px solid #d0d7de; border-radius:6px; font-family:inherit; }"
        ".expr-input:focus { outline:none; border-color:#0969da; }"
        ".expr-sel { font-size:11px; padding:2px 4px; background:#fff;"
        "  border:1px solid #d0d7de; border-radius:6px; font-family:inherit; }"
        ".vartext-wrap { position:relative; display:inline-block; }"
        ".vartext-input { font-size:12px; padding:2px 5px; width:72px; background:#fff;"
        "  border:1px solid #d0d7de; border-radius:6px; font-family:inherit; }"
        ".vartext-input:focus { outline:none; border-color:#0969da; }"
        ".vartext-drop { position:absolute; top:100%; left:0; z-index:999;"
        "  background:#fff; border:1px solid #d0d7de; border-radius:6px;"
        "  box-shadow:0 4px 12px rgba(0,0,0,0.15); min-width:100px; max-height:140px;"
        "  overflow-y:auto; margin-top:2px; }"
        ".vartext-drop-item { padding:4px 8px; font-size:12px; cursor:pointer;"
        "  white-space:nowrap; color:#1f2328; }"
        ".vartext-drop-item:hover { background:#ddf4ff; color:#0969da; }"
        ".vartext-drop-empty { padding:4px 8px; font-size:11px; color:#57606a; font-style:italic; }"
        ".pal-title-expr { font-size:9px; color:#9a6700; text-transform:uppercase;"
        "  letter-spacing:.06em; padding:6px 0 4px 0; border-bottom:1px solid #d0d7de;"
        "  margin-top:6px; margin-bottom:2px; }"
        ".block-btn.expr-btn { background:#fff8c5; color:#9a6700; border:1px solid #d4a72c; }"
        ".block-btn.expr-btn:hover { background:#fffbea; border-color:#9a6700; color:#7a5200; }"
        ".expr-slot-label { font-size:8px; color:#57606a; display:block; margin-bottom:1px; }"
        "#pal-context { font-size:9px; font-weight:700; text-transform:uppercase;"
        "  letter-spacing:.06em; padding:4px 2px 6px 2px; color:#57606a;"
        "  border-bottom:1px solid #d0d7de; margin-bottom:4px; min-height:28px;"
        "  display:flex; align-items:center; line-height:1.3; }"
        "#pal-context.has-sel { color:#0969da; }"
        "#pal-context.has-expr { color:#9a6700; }"
        ".block-btn.hidden { display:none; }"
        "#pal-blocks-section { display:flex; flex-direction:column; gap:4px; }"
        "#pal-expr-section { display:flex; flex-direction:column; gap:4px; }"
    )

    extra_buttons = ""

    body = (
        "<div id='statusbar'>click a section or if body to select it</div>"
        "<div id='app'>"
        "<div id='palette'>"
        "<div id='pal-context'>select a section</div>"
        "<div id='pal-blocks-section'>"
        "<button class='block-btn' data-type='intvar'>int var</button>"
        "<button class='block-btn' data-type='longvar'>long var</button>"
        "<button class='block-btn' data-type='boolvar'>bool var</button>"
        "<button class='block-btn' data-type='setvar'>set var</button>"
        "<button class='block-btn' data-type='increment'>++ / --</button>"
        "<button class='block-btn' data-type='stringvar'>String var</button>"
        "<button class='block-btn' data-type='pinmode'>pinMode</button>"
        "<button class='block-btn' data-type='digitalwrite'>digitalWrite</button>"
        "<button class='block-btn' data-type='analogwrite'>analogWrite</button>"
        "<button class='block-btn' data-type='tone'>tone</button>"
        "<button class='block-btn' data-type='notone'>noTone</button>"
        "<button class='block-btn' data-type='delay'>delay</button>"
        "<button class='block-btn' data-type='delaymicroseconds'>delayMicroseconds</button>"
        "<button class='block-btn' data-type='serialbegin'>Serial.begin</button>"
        "<button class='block-btn' data-type='serialprint'>Serial.print</button>"
        "<button class='block-btn' data-type='ifblock'>if</button>"
        "<button class='block-btn' data-type='forloop'>for loop</button>"
        "<button class='block-btn' data-type='whileloop'>while loop</button>"
        "</div>"
        "<div id='pal-expr-section'>"
        "<div class='pal-title-expr' id='pal-expr-title'>Expressions</div>"
        "<button class='block-btn expr-btn' data-type='value'>value</button>"
        "<button class='block-btn expr-btn' data-type='millis'>millis()</button>"
        "<button class='block-btn expr-btn' data-type='analogread'>analogRead</button>"
        "<button class='block-btn expr-btn' data-type='digitalread'>digitalRead</button>"
        "<button class='block-btn expr-btn' data-type='random'>random()</button>"
        "<button class='block-btn expr-btn' data-type='math'>math</button>"
        "<button class='block-btn expr-btn' data-type='map'>map()</button>"
        "<button class='block-btn expr-btn' data-type='constrain'>constrain</button>"
        "<button class='block-btn expr-btn' data-type='serialavailable'>Serial.available</button>"
        "<button class='block-btn expr-btn' data-type='serialreadstring'>Serial.readString</button>"
        "</div>"
        "</div>"
        "<div id='workspace'>"
        "<div id='step-bar'>"
        "  <span id='step-label'>Step</span>"
        "  <span id='step-progress'></span>"
        "</div>"
        "<div class='section s-global' id='gs'>"
        "  <div class='section-header'><h3>&#127757; Global</h3><span class='toggle-arrow'>&#9660;</span></div>"
        "  <div class='section-body' id='gs-body'></div>"
        "</div>"
        "<div class='section s-setup expanded' id='ss'>"
        "  <div class='section-header'><h3>&#128295; setup()</h3><span class='toggle-arrow'>&#9660;</span></div>"
        "  <div class='section-body' id='ss-body'></div>"
        "</div>"
        "<div class='section s-loop' id='ls'>"
        "  <div class='section-header'><h3>&#128257; loop()</h3><span class='toggle-arrow'>&#9660;</span></div>"
        "  <div class='section-body' id='ls-body'></div>"
        "</div>"
        "</div>"
        "<div id='codepanel'>"
        "<div id='code-btns'>"
        + extra_buttons +
        "</div>"
        "<div id='nav-btns'>"
        "<button class='cbtn' id='prevbtn' style='display:none'>&#8592; Prev</button>"
        "<button class='cbtn' id='nextbtn' style='display:none'>Next &#8594;</button>"
        "</div>"
        "<div id='msg'></div>"
        "<div id='codeout'>// sketch&#10;// appears&#10;// here</div>"
        "</div>"
    )

    # Resolve the active pin reference list from the pin_refs parameter.
    # pin_refs can be a string key from PIN_REFS, or a plain list of strings.
    if isinstance(pin_refs, str):
        active_refs = PIN_REFS.get(pin_refs, [])
    elif isinstance(pin_refs, list):
        active_refs = pin_refs
    else:
        active_refs = []
    items_js = "[" + ",".join('"' + i.replace('\\', '\\\\').replace('"', '\\"') + '"' for i in active_refs) + "]"
    pin_refs_js = "var PIN_REFS=" + items_js + ";"
    
    overlay_js = ""
    if is_overlay:
        overlay_js = """
        window.addEventListener('message', function(e) {
            if (e.data && e.data.type === 'bb_save_request') {
                saveBlocks();
                setTimeout(function(){ window.parent.postMessage({type:'bb_close'}, '*'); }, 600);
            }
        });
        """

    js = (
        "var USERNAME=" + (("'" + username + "'") if username else "null") + ";"
        "var PAGE=" + (("'" + str(page) + "'") if (page is not None and str(page) != "") else "null") + ";"
        f"var SUPABASE_URL='{supabase_url or ''}';"
        f"var SUPABASE_KEY='{supabase_key or ''}';"
        f"var DEFAULT_VIEW='{dv}';"
        f"var LOCK_VIEW={'true' if lv else 'false'};"
        f"var READONLY_MODE={'true' if rv else 'false'};"
        f"var LOCK_MODE={'true' if lm else 'false'};"
        "var SAVE_DEBOUNCE=null;" +
        master_sketch_js + 
        pin_refs_js + 
        "(function(){"
        "var UNO_DIGITAL_PINS=['0','1','2','3','4','5','6','7','8','9','10','11','12','13'];"
        "var UNO_ANALOG_PINS=['A0','A1','A2','A3','A4','A5'];"
        "var UNO_DIGITAL_IO_PINS=UNO_DIGITAL_PINS.concat(UNO_ANALOG_PINS);"
        "var UNO_PWM_PINS=['3','5','6','9','10','11'];"
        "var BLOCKS={"
        "intvar:{allowed:['global','loop','if','for','while'],asStatement:true,asExpr:false,"
        "  inputs:[{t:'text',l:'Name'},{t:'expr',l:'Value',fallback:'0'}],"
        "  defaults:[null,{type:'value',params:['0'],children:[]}],"
        "  genStmt:function(p,ex){return 'int '+(p[0]||'myVar')+' = '+genExpr(ex&&ex[1],p[1],'0')+';';}},"
        "longvar:{allowed:['global','loop','if','for','while'],asStatement:true,asExpr:false,"
        "  inputs:[{t:'text',l:'Name'},{t:'expr',l:'Value',fallback:'0'}],"
        "  defaults:[null,{type:'value',params:['0'],children:[]}],"
        "  genStmt:function(p,ex){return 'long '+(p[0]||'myLong')+' = '+genExpr(ex&&ex[1],p[1],'0')+';';}},"
        "boolvar:{allowed:['global','loop','if','for','while'],asStatement:true,asExpr:false,"
        "  inputs:[{t:'text',l:'Name'},{t:'sel',l:'Value',o:['true','false']}],"
        "  genStmt:function(p){return 'bool '+(p[0]||'myFlag')+' = '+(p[1]||'false')+';';}},"
        "setvar:{allowed:['loop','if','for','while'],asStatement:true,asExpr:false,"
        "  inputs:[{t:'vartext',l:'Var'},{t:'expr',l:'Value',fallback:'0'}],"
        "  defaults:[null,{type:'value',params:['0'],children:[]}],"
        "  genStmt:function(p,ex){return (p[0]||'myVar')+' = '+genExpr(ex&&ex[1],p[1],'0')+';';}},"
        "increment:{allowed:['loop','if','for','while'],asStatement:true,asExpr:false,"
        "  inputs:[{t:'vartext',l:'Var'},{t:'sel',l:'Op',o:['++','--','+=','-=']},"
        "          {t:'number',l:'By'}],"
        "  genStmt:function(p){"
        "    var v=p[0]||'myVar',op=p[1]||'++',n=p[2]||'1';"
        "    if(op==='++'||op==='--')return v+op+';';"
        "    return v+' '+op+' '+n+';';}},"
        "stringvar:{allowed:['global','loop','if','for','while'],asStatement:true,asExpr:false,"
        "  inputs:[{t:'text',l:'Name'},{t:'expr',l:'Value',fallback:'\"\"'}],"
        "  defaults:[null,{type:'value',params:[''],children:[]}],"
        "  genStmt:function(p,ex){return 'String '+(p[0]||'myText')+' = '+genExpr(ex&&ex[1],p[1],'\"\"')+';';}},"
        "pinmode:{allowed:['setup'],asStatement:true,asExpr:false,"
        "  inputs:[{t:'vartext',l:'Pin',o:'DIGITAL_PIN_OPTIONS'},{t:'sel',l:'Mode',o:['OUTPUT','INPUT','INPUT_PULLUP']}],"
        "  genStmt:function(p){return 'pinMode('+(p[0])+', '+(p[1])+');';}},"
        "digitalwrite:{allowed:['loop','if','for','while'],asStatement:true,asExpr:false,"
        "  inputs:[{t:'sel',l:'Pin',o:'DIGITAL_PIN_OPTIONS'},{t:'sel',l:'Value',o:['HIGH','LOW']}],"
        "  genStmt:function(p){return 'digitalWrite('+(p[0])+', '+(p[1])+');';}},"
        "analogwrite:{allowed:['loop','if','for','while'],asStatement:true,asExpr:false,"
        "  inputs:[{t:'sel',l:'Pin',o:'PWM_PIN_OPTIONS'},{t:'expr',l:'Value',fallback:'128'}],"
        "  genStmt:function(p,ex){return 'analogWrite('+(p[0]||9)+', '+genExpr(ex&&ex[1],p[1],'128')+');';}},"
        "analogread:{allowed:['loop','if','for','while'],asStatement:false,asExpr:true,"
        "  inputs:[{t:'sel',l:'Pin',o:'ANALOG_PIN_OPTIONS'}],"
        "  genExpr:function(p){return 'analogRead('+(p[0]||'A0')+')';}},"
        "digitalread:{allowed:['loop','if','for','while'],asStatement:false,asExpr:true,"
        "  inputs:[{t:'sel',l:'Pin',o:'DIGITAL_PIN_OPTIONS'}],"
        "  genExpr:function(p){return 'digitalRead('+(p[0]||'2')+')';}},"
        "delay:{allowed:['loop','if','for','while'],asStatement:true,asExpr:false,"
        "  inputs:[{t:'expr',l:'ms',fallback:'1000'}],"
        "  genStmt:function(p,ex){return 'delay('+genExpr(ex&&ex[0],p[0],'1000')+');';}},"
        "delaymicroseconds:{allowed:['loop','if','for','while'],asStatement:true,asExpr:false,"
        "  inputs:[{t:'expr',l:'us',fallback:'100'}],"
        "  defaults:[{type:'value',params:['100'],children:[]}],"
        "  genStmt:function(p,ex){return 'delayMicroseconds('+genExpr(ex&&ex[0],p[0],'100')+');';}},"
        "millis:{allowed:['loop','if','for','while'],asStatement:false,asExpr:true,"
        "  inputs:[],"
        "  genExpr:function(p){return 'millis()';}},"
        "tone:{allowed:['loop','if','for','while'],asStatement:true,asExpr:false,"
        "  inputs:[{t:'sel',l:'Pin',o:'DIGITAL_PIN_OPTIONS'},{t:'expr',l:'Freq',fallback:'440'},{t:'number',l:'Duration'}],"
        "  genStmt:function(p,ex){var pin=(p[0]||5),f=genExpr(ex&&ex[1],p[1],'440'),d=p[2];"
        "    return (d!==''&&d!==null&&d!==undefined)?('tone('+pin+', '+f+', '+d+');'):('tone('+pin+', '+f+');');}},"
        "notone:{allowed:['loop','if','for','while'],asStatement:true,asExpr:false,"
        "  inputs:[{t:'expr',l:'Pin',fallback:'0'}],"
        "  genStmt:function(p,ex){return 'noTone('+genExpr(ex&&ex[0],p[0],'0')+');';}},"
        "random:{allowed:['loop','if','for','while'],asStatement:false,asExpr:true,"
        "  inputs:[{t:'number',l:'Min'},{t:'number',l:'Max'}],"
        "  genExpr:function(p){return 'random('+(p[0]||0)+', '+(p[1]||100)+')';}},"
        "math:{allowed:[],asStatement:false,asExpr:true,"
        "  inputs:[{t:'expr',l:'A',fallback:'0'},{t:'sel',l:'Op',o:[{v:'+',lb:'plus'},{v:'-',lb:'minus'},{v:'*',lb:'multiply'},{v:'/',lb:'divide'},{v:'%',lb:'modulo'}]},{t:'expr',l:'B',fallback:'0'}],"
        "  genExpr:function(p,ch){"
        "    var a=genExpr(ch&&ch[0],p[0],'0'),op=p[1]||'+',b=genExpr(ch&&ch[2],p[2],'0');"
        "    return '('+a+' '+op+' '+b+')';}},"
        "map:{allowed:[],asStatement:false,asExpr:true,"
        "  inputs:[{t:'expr',l:'Val',fallback:'0'},{t:'number',l:'inLo'},{t:'number',l:'inHi'},{t:'number',l:'outLo'},{t:'number',l:'outHi'}],"
        "  genExpr:function(p,ch){"
        "    var v=genExpr(ch&&ch[0],p[0],'0');"
        "    return 'map('+v+', '+(p[1]||0)+', '+(p[2]||1023)+', '+(p[3]||0)+', '+(p[4]||255)+')';}},"
        "constrain:{allowed:[],asStatement:false,asExpr:true,"
        "  inputs:[{t:'expr',l:'Val',fallback:'0'},{t:'number',l:'Lo'},{t:'number',l:'Hi'}],"
        "  genExpr:function(p,ch){"
        "    var v=genExpr(ch&&ch[0],p[0],'0');"
        "    return 'constrain('+v+', '+(p[1]||0)+', '+(p[2]||255)+')';}},"
        "value:{allowed:[],asStatement:false,asExpr:true,"
        "  inputs:[{t:'vartext',l:'Value'}],"
        "  genExpr:function(p){return (p[0]||'0');}},"
        "serialbegin:{allowed:['setup'],asStatement:true,asExpr:false,"
        "  inputs:[{t:'sel',l:'Baud',o:['9600','19200','38400','57600','115200']}],"
        "  genStmt:function(p){return 'Serial.begin('+(p[0]||'9600')+');';}},"
        "serialprint:{allowed:['setup','loop','if','for','while'],asStatement:true,asExpr:false,"
        "  inputs:[{t:'expr',l:'Value',fallback:'\"Hello\"'},{t:'sel',l:'',o:['println','print']}],"
        "  defaults:[{type:'value',params:['\"Hello\"'],children:[]},null],"
        "  genStmt:function(p,ex){var fn=p[1]==='print'?'Serial.print':'Serial.println';"
        "    return fn+'('+genExpr(ex&&ex[0],null,'\"Hello\"')+');';}},"
        "serialreadstring:{allowed:[],asStatement:false,asExpr:true,"
        "  inputs:[],"
        "  genExpr:function(p){return 'Serial.readString()';}},"
        "serialavailable:{allowed:[],asStatement:false,asExpr:true,"
        "  inputs:[],"
        "  genExpr:function(p){return 'Serial.available()';}},"
        "codeblock:{allowed:['global','setup','loop','if','for','while'],asStatement:true,asExpr:false,"
        "  inputs:[{t:'text',l:'Code'}],"
        "  genStmt:function(p){return (p[0]||'');}},"
        "phantom_resolved:{allowed:['global','setup','loop','if','for','while'],asStatement:true,asExpr:false,"
        "  inputs:[],genStmt:function(){return '';}},"
        "ifblock:{allowed:['loop','if','for','while'],asStatement:true,asExpr:false,"
        "  inputs:[],genStmt:function(){return '';}},"
        "forloop:{allowed:['loop','if','for','while'],asStatement:true,asExpr:false,"
        "  inputs:[],genStmt:function(){return '';}},"
        "whileloop:{allowed:['loop','if','for','while'],asStatement:true,asExpr:false,"
        "  inputs:[],genStmt:function(){return '';}},"
        "};"
        "var B=BLOCKS;"
        "var SECTIONS={global:[],setup:[],loop:[]};"
        "var exprSel=null;"
        "var EXPR_COLORS={'analogread':'#1a7f37','digitalread':'#1a7f37','millis':'#0969da',"
        "  'random':'#e36209','math':'#9a6700','map':'#6f42c1','constrain':'#cf222e','value':'#57606a'};"
        "function getExprColor(type){return EXPR_COLORS[type]||'#57606a';}"
        "function genExpr(exNode,fallbackParam,fallbackDefault){"
        "  if(exNode&&exNode.type){"
        "    var def=BLOCKS[exNode.type];"
        "    if(!def||!def.genExpr)return String(fallbackParam||fallbackDefault||'0');"
        "    return def.genExpr(exNode.params||[],exNode.children||[]);}"
        "  var v=fallbackParam;if(v===''||v===null||v===undefined)v=fallbackDefault||'0';"
        "  return String(v);}"
        "function makeExNode(type){"
        "  var def=BLOCKS[type];if(!def||!def.asExpr)return null;"
        "  var params=def.inputs.map(function(inp){"
        "    if(inp.t==='sel'){var f=inp.o[0];return typeof f==='object'?f.v:f;}"
        "    if(inp.t==='number')return '0'; if(inp.t==='expr')return '';"
        "    if(inp.t==='vartext')return '0'; return '';});"
        "  var children=def.inputs.map(function(inp){return inp.t==='expr'?null:undefined;});"
        "  return {type:type,params:params,children:children};}"
        "function renderExprSlot(block,slotIdx,label){"
        "  if(!block.exChildren)block.exChildren=[];"
        "  var exNode=block.exChildren[slotIdx]||null;"
        "  var wrap=document.createElement('div');wrap.className='blk-field';"
        "  var lbl=document.createElement('label');lbl.textContent=label;wrap.appendChild(lbl);"
        "  var slot=document.createElement('div');"
        "  slot.className='expr-slot'+(exNode?' has-expr':'');"
        "  var isActive=exprSel&&exprSel.block===block&&exprSel.slotIdx===slotIdx;"
        "  if(isActive)slot.classList.add('active');"
        "  if(exNode){"
        "    slot.appendChild(renderExprBlock(exNode,function(){block.exChildren[slotIdx]=null;exprSel=null;updatePalette();render();}));"
        "  }else{"
        "    var ph=document.createElement('span');ph.textContent=isActive?'> drop expr':'+ expr';slot.appendChild(ph);"
        "  }"
        "  slot.addEventListener('click',function(e){"
        "    e.stopPropagation();"
        "    if(exprSel&&exprSel.block===block&&exprSel.slotIdx===slotIdx){exprSel=null;updatePalette();render();return;}"
        "    exprSel={block:block,slotIdx:slotIdx};sel=null;"
        "    document.getElementById('statusbar').innerHTML='<span style=\"color:#9a6700\">click an expression block to snap it in</span>';"
        "    updatePalette();"
        "    render();});"
        "  wrap.appendChild(slot);return wrap;}"
        "function renderExprBlock(exNode,onRemove){"
        "  var def=BLOCKS[exNode.type];if(!def||!def.asExpr)return document.createTextNode('?');"
        "  var chip=document.createElement('span');"
        "  chip.className='expr-block-inline';"
        "  chip.style.background=getExprColor(exNode.type);"
        "  chip.style.color='#fff';"
        "  var lbl=document.createElement('span');lbl.textContent=exNode.type;chip.appendChild(lbl);"
        "  def.inputs.forEach(function(inp,ji){"
        "    if(inp.t==='expr'){"
        "      (function(capturedJi,capturedExNode){"
        "        var subSlot=document.createElement('span');"
        "        var isSubActive=exprSel&&exprSel.isSubSlot&&exprSel.exNode===capturedExNode&&exprSel.slotIdx===capturedJi;"
        "        subSlot.style.cssText='display:inline-flex;align-items:center;border-radius:5px;padding:2px 6px;cursor:pointer;font-size:11px;min-width:34px;border:2px '+(isSubActive?'solid #fff':'dashed rgba(255,255,255,0.6)')+';background:'+(isSubActive?'rgba(255,255,255,0.35)':'rgba(255,255,255,0.15)')+';';"
        "        var subNode=(capturedExNode.children&&capturedExNode.children[capturedJi])||null;"
        "        if(subNode){"
        "          subSlot.appendChild(renderExprBlock(subNode,function(){if(!capturedExNode.children)capturedExNode.children=[];capturedExNode.children[capturedJi]=null;exprSel=null;render();}));"
        "        }else{"
        "          var sph=document.createElement('span');sph.textContent=inp.l||'?';"
        "          sph.style.cssText='opacity:0.85;font-weight:700;color:#fff;pointer-events:none;';subSlot.appendChild(sph);"
        "        }"
        "        subSlot.addEventListener('click',function(e){"
        "          e.stopPropagation();"
        "          if(exprSel&&exprSel.isSubSlot&&exprSel.exNode===capturedExNode&&exprSel.slotIdx===capturedJi){"
        "            exprSel=null;updatePalette();render();return;}"
        "          exprSel={exNode:capturedExNode,slotIdx:capturedJi,isSubSlot:true};sel=null;"
        "          document.getElementById('statusbar').innerHTML='<span style=\"color:#9a6700\">slot '+inp.l+' selected - click an expression to fill it</span>';"
        "          document.querySelectorAll('.sub-slot-active').forEach(function(el){el.classList.remove('sub-slot-active');});"
        "          subSlot.style.border='2px solid #fff';subSlot.style.background='rgba(255,255,255,0.35)';"
        "          updatePalette();"
        "        });"
        "        chip.appendChild(subSlot);"
        "      })(ji,exNode);"
        "    }else if(inp.t==='sel'){"
        "      var es=document.createElement('select');es.className='expr-sel';"
        "      var opts=inp.o;if(typeof opts==='string')opts=getOptions(opts);"
        "      if(!exNode.params[ji]){var op=document.createElement('option');op.value='';op.textContent='\\u2014';es.appendChild(op);}"
        "      opts.forEach(function(opt){var o=document.createElement('option');"
        "        if(typeof opt==='object'){o.value=opt.v;o.textContent=opt.lb;}else{o.value=opt;o.textContent=opt;}"
        "        es.appendChild(o);});es.value=exNode.params[ji]||'';"
        "      es.addEventListener('click',function(e){e.stopPropagation();});"
        "      es.addEventListener('change',function(e){e.stopPropagation();exNode.params[ji]=e.target.value;genCode();});"
        "      chip.appendChild(es);"
        "    }else if(inp.t==='vartext'){"
        "      (function(capturedJiVt,capturedExNodeVt){"
        "        var wrap=document.createElement('span');wrap.className='vartext-wrap';"
        "        var ei=document.createElement('input');ei.type='text';ei.className='vartext-input';"
        "        ei.value=capturedExNodeVt.params[capturedJiVt]||'0';"
        "        ei.placeholder='0';"
        "        var drop=null;"
        "        function closeDrop(){if(drop){drop.remove();drop=null;}}"
        "        function openDrop(filter){"
        "          closeDrop();"
        "          var vars=getVarSuggestions();"
        "          var filtered=filter?vars.filter(function(v){return v.toLowerCase().indexOf(filter.toLowerCase())===0;}):vars;"
        "          if(filtered.length===0&&filter){return;}"
        "          drop=document.createElement('div');drop.className='vartext-drop';"
        "          if(filtered.length===0){"
        "            var empty=document.createElement('div');empty.className='vartext-drop-empty';"
        "            empty.textContent='no variables yet';drop.appendChild(empty);"
        "          }else{"
        "            filtered.forEach(function(v){"
        "              var item=document.createElement('div');item.className='vartext-drop-item';"
        "              item.textContent=v;"
        "              item.addEventListener('mousedown',function(e){"
        "                e.preventDefault();e.stopPropagation();"
        "                ei.value=v;capturedExNodeVt.params[capturedJiVt]=v;genCode();"
        "                closeDrop();});"
        "              drop.appendChild(item);});"
        "          }"
        "          wrap.appendChild(drop);"
        "        }"
        "        ei.addEventListener('click',function(e){e.stopPropagation();openDrop('');});"
        "        ei.addEventListener('focus',function(e){openDrop('');});"
        "        ei.addEventListener('input',function(e){"
        "          e.stopPropagation();"
        "          capturedExNodeVt.params[capturedJiVt]=e.target.value;genCode();"
        "          var v=e.target.value;"
        "          if(v===''){openDrop('');}else{openDrop(v);}"
        "        });"
        "        ei.addEventListener('blur',function(){setTimeout(closeDrop,150);});"
        "        ei.addEventListener('keydown',function(e){"
        "          e.stopPropagation();"
        "          if(e.key==='Escape'||e.key==='Enter'){closeDrop();}"
        "          if(e.key==='Enter'){ei.blur();}"
        "        });"
        "        wrap.appendChild(ei);chip.appendChild(wrap);"
        "      })(ji,exNode);"
        "    }else{"
        "      var ei=document.createElement('input');ei.type=inp.t==='number'?'number':'text';"
        "      ei.className='expr-input';ei.value=exNode.params[ji]||'';"
        "      ei.style.width=(inp.t==='number'?'48px':'60px');"
        "      ei.addEventListener('click',function(e){e.stopPropagation();});"
        "      ei.addEventListener('input',function(e){e.stopPropagation();exNode.params[ji]=e.target.value;genCode();});"
        "      chip.appendChild(ei);"
        "    }});"
        "  if(onRemove){"
        "    var rx=document.createElement('span');rx.className='expr-remove';rx.textContent='x';"
        "    rx.title='Remove expression';"
        "    rx.addEventListener('click',function(e){e.stopPropagation();onRemove();});chip.appendChild(rx);}"
        "  return chip;}"
        "function getOptions(key){"
        "  var base;"
        "  if(key==='DIGITAL_PIN_OPTIONS'){base=UNO_DIGITAL_IO_PINS;}"
        "  else if(key==='PWM_PIN_OPTIONS'){base=UNO_PWM_PINS;}"
        "  else if(key==='ANALOG_PIN_OPTIONS'){base=UNO_ANALOG_PINS;}"
        "  else{return [];}"
        "  var opts=base.slice();"
        "  SECTIONS.global.forEach(function(b){"
        "    if(b.type==='intvar'){"
        "      var n=b.params[0];"
        "      if(n&&opts.indexOf(n)===-1)opts.push(n);"
        "    }"
        "  });"
        "  return opts;"
        "}"
        "var sel=null;"
        "var activePhantoml=null;"
        "var PROGRESSION_MODE=false;"
        "var STEPS=null;"
        "var CURRENT_STEP=0;"
        "var STUDENT_SAVES=[];"
        "var CHECK_FAIL_COUNT=0;"
        "var SKETCH_ERROR_PATHS=[];"
        + palette_js
        + initial_js +
        "function updatePalette(){"
        "  var ctx=document.getElementById('pal-context');"
        "  var blockSec=document.getElementById('pal-blocks-section');"
        "  var exprSec=document.getElementById('pal-expr-section');"
        "  var exprTitle=document.getElementById('pal-expr-title');"
        "  if(exprSel){"
        "    activePhantoml=null;"
        "    ctx.className='has-expr';"
        "    ctx.textContent=exprSel.isSubSlot?'fill sub-slot:':'fill value slot:';"
        "    blockSec.style.display='none';"
        "    exprTitle.style.display='';"
        "    var guided=PROGRESSION_MODE&&STEPS&&STEPS[CURRENT_STEP]&&STEPS[CURRENT_STEP].guidance==='guided';"
        "    var expectedType=null;"
        "    if(exprSel.condObj){"
        "      var ec=exprSel.condObj._expectedCond;"
        "      if(ec){"
        "        var sideKey=exprSel.side==='leftExpr'?'left':exprSel.side==='rightExpr'?'right':exprSel.side==='leftExpr2'?'left2':'right2';"
        "        expectedType=ec[sideKey]||null;"
        "      }"
        "    }else if(!exprSel.isSubSlot&&exprSel.block&&exprSel.block._expectedExpr){"
        "      expectedType=exprSel.block._expectedExpr[exprSel.slotIdx]||null;}"
        "    exprSec.querySelectorAll('.block-btn').forEach(function(btn){"
        "      if(expectedType){"
        "        btn.classList[btn.getAttribute('data-type')===expectedType?'remove':'add']('hidden');"
        "      }else{"
        "        btn.classList.remove('hidden');"
        "      }});"
        "    return;"
        "  }"
        "  if(activePhantoml){"
        "    var ph=activePhantoml.phantom;"
        "    var step=PROGRESSION_MODE&&STEPS?STEPS[CURRENT_STEP]:null;"
        "    var guided=step?step.guidance==='guided':false;"
        "    ctx.className='has-sel';"
        "    ctx.textContent='place: '+ph.hint;"
        "    blockSec.style.display='flex';"
        "    exprTitle.style.display='';"
        "    blockSec.querySelectorAll('.block-btn').forEach(function(btn){"
        "      var type=btn.getAttribute('data-type');"
        "      if(ph.expects){"
        "        btn.classList[type===ph.expects?'remove':'add']('hidden');"
        "      }else if(!guided){"
        "        btn.classList.remove('hidden');"
        "      }else{"
        "        btn.classList.add('hidden');"
        "      }});"
        "    exprSec.querySelectorAll('.block-btn').forEach(function(btn){btn.classList.add('hidden');});"
        "    return;"
        "  }"
        "  blockSec.style.display='flex';"
        "  exprTitle.style.display='';"
        "  if(!sel){"
        "    ctx.className='';ctx.textContent='select a section';"
        "    blockSec.querySelectorAll('.block-btn').forEach(function(btn){btn.classList.add('hidden');});"
        "    exprSec.querySelectorAll('.block-btn').forEach(function(btn){btn.classList.add('hidden');});"
        "    return;"
        "  }"
        "  ctx.className='has-sel';"
        "  var parts=sel.pathStr.split(' \\u2192 ');"
        "  ctx.textContent='adding to: '+parts[parts.length-1];"
        "  var inNested=sel.pathStr.indexOf('\\u2192')!==-1;"
        "  blockSec.querySelectorAll('.block-btn').forEach(function(btn){"
        "    var type=btn.getAttribute('data-type');"
        "    var def=BLOCKS[type];if(!def){btn.classList.remove('hidden');return;}"
        "    var ok=inNested?(def.allowed.indexOf('if')!==-1||def.allowed.indexOf('for')!==-1||def.allowed.indexOf('while')!==-1)"
        "                   :(def.allowed.indexOf(sel.section)!==-1);"
        "    if(ok&&PALETTE_ALLOWED!==null)ok=PALETTE_ALLOWED.indexOf(type)!==-1;"
        "    if(ok){btn.classList.remove('hidden');}else{btn.classList.add('hidden');}});"
        "  exprSec.querySelectorAll('.block-btn').forEach(function(btn){btn.classList.add('hidden');});}"
        "function setSelection(section,targetArr,pathStr){"
        "  sel={section:section,targetArr:targetArr,pathStr:pathStr};"
        "  document.getElementById('statusbar').innerHTML='adding to: <span>'+pathStr+'</span>';"
        "  updatePalette();"
        "  render();}"
        "function clearSelection(){"
        "  sel=null;exprSel=null;"
        "  document.getElementById('statusbar').textContent='click a section or if body to select it';"
        "  updatePalette();"
        "  render();}"
        "document.addEventListener('click',function(e){"
        "  if(!e.target.closest('.section')&&!e.target.closest('.if-body')&&"
        "     !e.target.closest('.block-btn')&&!e.target.closest('#codepanel')&&!e.target.closest('button')&&"
        "     !e.target.closest('.expr-slot')&&!e.target.closest('.expr-block-inline')){"
        "    clearSelection();}});"
        "function expandSection(elId){"
        "  ['gs','ss','ls'].forEach(function(id){"
        "    document.getElementById(id).classList.toggle('expanded', id===elId);});}"
        "function setupSection(elId,sName,label){"
        "  var el=document.getElementById(elId);"
        "  var hdr=el.querySelector('.section-header');"
        "  var body=document.getElementById(elId+'-body');"
        "  hdr.addEventListener('click',function(e){"
        "    e.stopPropagation();"
        "    expandSection(elId);"
        "    setSelection(sName,SECTIONS[sName],label);"
        "  });"
        "  body.addEventListener('click',function(e){"
        "    if(e.target===body){e.stopPropagation();setSelection(sName,SECTIONS[sName],label);}});}"
        "setupSection('gs','global','Global');"
        "setupSection('ss','setup','setup()');"
        "setupSection('ls','loop','loop()');"
        "document.querySelectorAll('.block-btn').forEach(function(btn){"
        "  btn.addEventListener('click',function(e){"
        "    e.stopPropagation();"
        "    var type=btn.getAttribute('data-type');if(!type)return;"
        "    var def=BLOCKS[type];if(!def)return;"
        "    if(exprSel&&def.asExpr){"
        "      var newNode=makeExNode(type);"
        "      if(exprSel.condObj){"
        "        exprSel.condObj[exprSel.side]=newNode;"
        "      }else if(exprSel.isSubSlot){"
        "        if(!exprSel.exNode.children)exprSel.exNode.children=[];"
        "        exprSel.exNode.children[exprSel.slotIdx]=newNode;"
        "      }else{"
        "        if(!exprSel.block.exChildren)exprSel.block.exChildren=[];"
        "        exprSel.block.exChildren[exprSel.slotIdx]=newNode;"
        "      }"
        "      exprSel=null;updatePalette();render();return;"
        "    }"
        "    if(activePhantoml&&def.asStatement){"
        "      var ph=activePhantoml.phantom;"
        "      var arr=activePhantoml.arr;"
        "      var idx=activePhantoml.idx;"
        "      var newBlock;"
        "      if(type==='ifblock'){"
        "        var guided=PROGRESSION_MODE&&STEPS&&STEPS[CURRENT_STEP]&&STEPS[CURRENT_STEP].guidance==='guided';"
        "        var cond={leftExpr:null,op:'==',rightExpr:null,joiner:'none',leftExpr2:null,op2:'==',rightExpr2:null};"
        "        if(ph.condition&&guided){"
        "          cond.op=ph.condition.op||'==';"
        "          cond.joiner=ph.condition.joiner||'none';"
        "          cond.op2=ph.condition.op2||'==';"
        "          cond._expectedCond={"
        "            left:ph.condition.leftExpr?ph.condition.leftExpr.type:null,"
        "            right:ph.condition.rightExpr?ph.condition.rightExpr.type:null,"
        "            left2:ph.condition.leftExpr2?ph.condition.leftExpr2.type:null,"
        "            right2:ph.condition.rightExpr2?ph.condition.rightExpr2.type:null"
        "          };}"
        "        var ib=guided&&ph.ifbody?JSON.parse(JSON.stringify(ph.ifbody)):[];"
        "        var eifs=guided&&ph.elseifs?JSON.parse(JSON.stringify(ph.elseifs)):[];"
        "        var eb=guided&&ph.elsebody?JSON.parse(JSON.stringify(ph.elsebody)):null;"
        "        newBlock={id:(Date.now()+Math.random()).toString(),type:'ifblock',"
        "          condition:cond,ifbody:ib,elseifs:eifs,elsebody:eb};"
        "      }else if(type==='forloop'){"
        "        var b=guided&&ph.body?JSON.parse(JSON.stringify(ph.body)):[];"
        "        newBlock={id:(Date.now()+Math.random()).toString(),type:'forloop',"
        "          forinit:'int i = 0',forcond:'i < 10',forincr:'i++',"
        "          body:b};"
        "      }else if(type==='whileloop'){"
        "        var guidedW=PROGRESSION_MODE&&STEPS&&STEPS[CURRENT_STEP]&&STEPS[CURRENT_STEP].guidance==='guided';"
        "        var wcond={leftExpr:null,op:'!=',rightExpr:null,joiner:'none',leftExpr2:null,op2:'==',rightExpr2:null};"
        "        if(ph.condition&&guidedW){"
        "          wcond.op=ph.condition.op||'!=';"
        "          wcond._expectedCond={"
        "            left:ph.condition.leftExpr?ph.condition.leftExpr.type:null,"
        "            right:ph.condition.rightExpr?ph.condition.rightExpr.type:null"
        "          };}"
        "        var b=guided&&ph.body?JSON.parse(JSON.stringify(ph.body)):[];"
        "        newBlock={id:(Date.now()+Math.random()).toString(),type:'whileloop',condition:wcond,body:b};"
        "      }else{"
        "        var guided=PROGRESSION_MODE&&STEPS&&STEPS[CURRENT_STEP]&&STEPS[CURRENT_STEP].guidance==='guided';"
        "        var params=def.inputs.map(function(inp){"
        "          if(inp.t==='sel'){var f=inp.o[0];return typeof f==='object'?f.v:f;}return '';});"
        "        var exch=guided"
        "          ?def.inputs.map(function(){return null;})"
        "          :(def.defaults?def.defaults.map(function(d){return d?JSON.parse(JSON.stringify(d)):null;}):null)||[];"
        "        var expectedExpr=guided&&ph.exChildren"
        "          ?ph.exChildren.map(function(e){return e?e.type:null;})"
        "          :null;"
        "        newBlock={id:(Date.now()+Math.random()).toString(),type:type,params:params,exChildren:exch};"
        "        if(expectedExpr)newBlock._expectedExpr=expectedExpr;"
        "      }"
        "      arr.splice(idx,1,newBlock);"
        "      activePhantoml=null;"
        "      checkStepComplete();"
        "      updatePalette();render();return;"
        "    }"
        "    if(!def.asStatement){flash(type+' can only go in expression slots');return;}"
        "    if(!sel){flash('Select a section or if body first');return;}"
        "    var inIf=sel.pathStr.indexOf('\\u2192')!==-1;"
        "    if(inIf){if(def.allowed.indexOf('if')===-1&&def.allowed.indexOf('for')===-1&&def.allowed.indexOf('while')===-1){flash('\"'+type+'\" not allowed here');return;}}"
        "    else{if(def.allowed.indexOf(sel.section)===-1){flash('Goes in: '+def.allowed.filter(function(a){return a!=='if'&&a!=='for'&&a!=='while';}).join(' or '));return;}}"
        "    var block;"
        "    if(type==='ifblock'){"
        "      block={id:(Date.now()+Math.random()).toString(),type:'ifblock',"
        "        condition:{leftExpr:null,op:'==',rightExpr:null,joiner:'none',leftExpr2:null,op2:'==',rightExpr2:null},"
        "        ifbody:[],elseifs:[],elsebody:null};"
        "    }else if(type==='forloop'){"
        "      block={id:(Date.now()+Math.random()).toString(),type:'forloop',forinit:'int i = 0',forcond:'i < 10',forincr:'i++',body:[]};"
        "    }else if(type==='whileloop'){"
        "      block={id:(Date.now()+Math.random()).toString(),type:'whileloop',"
        "        condition:{leftExpr:null,op:'!=',rightExpr:null,joiner:'none',leftExpr2:null,op2:'==',rightExpr2:null},"
        "        body:[]};"
        "    }else{"
        "      var params=def.inputs.map(function(inp){"
        "        if(inp.t==='sel'){var f=inp.o[0];return typeof f==='object'?f.v:f;}return '';});"
        "      var exChildren=def.defaults?def.defaults.map(function(d){return d?JSON.parse(JSON.stringify(d)):null;}):[];"
        "      block={id:(Date.now()+Math.random()).toString(),type:type,params:params,exChildren:exChildren};"
        "    }"
        "    sel.targetArr.push(block);render();});});"
        "function render(){"
        "  console.log('render called', new Error().stack);"
        "  var anc=collectAncestorArrays();"
        "  renderSection('gs','global',anc);renderSection('ss','setup',anc);renderSection('ls','loop',anc);"
        "  ['gs','ss','ls'].forEach(function(id){"
        "    var el=document.getElementById(id);"
        "    var sn=id==='gs'?'global':id==='ss'?'setup':'loop';"
        "    var base='section s-'+(id==='gs'?'global':id==='ss'?'setup':'loop');"
        "    var isExpanded=el.classList.contains('expanded');"
        "    el.className=(sel&&sel.targetArr===SECTIONS[sn])?base+' active':base;"
        "    if(isExpanded)el.classList.add('expanded');});"
        "  console.log('[DEBUG] render() finishing. Re-applying highlights.'); genCode(); applySketchHighlights();"
        "  if (typeof READONLY_MODE !== 'undefined' && READONLY_MODE) {"
        "    document.querySelectorAll('.blk-input,.cond-input,.vartext-input,.cond-select,.cond-joiner').forEach(function(el) {"
        "      el.setAttribute('disabled', true);"
        "    });"
        "    document.querySelectorAll('.act').forEach(function(el) {"
        "      el.style.display = 'none';"
        "    });"
        "    document.querySelectorAll('.ws-block,.if-body,.for-body,.while-body,.if-block,.for-block,.while-block').forEach(function(el) {"
        "      el.style.pointerEvents = 'none';"
        "    });"
        "    document.querySelectorAll('.palette-block,.palette-item').forEach(function(el) {"
        "      el.style.display = 'none';"
        "    });"
        "  }"
        "}"
        "function collectAncestorArrays(){"
        "  var anc=[];if(!sel)return anc;"
        "  function walk(arr){for(var i=0;i<arr.length;i++){var b=arr[i];"
        "    if(b.type==='ifblock'){if(containsTarget(b))anc.push(b.id);"
        "      walk(b.ifbody);b.elseifs.forEach(function(ei){walk(ei.body);});if(b.elsebody)walk(b.elsebody);"
        "    }else if(b.type==='forloop'||b.type==='whileloop'){if(b.body&&isDescendantOf(b.body,sel.targetArr))anc.push(b.id);if(b.body)walk(b.body);}}}"
        "  walk(SECTIONS[sel.section]);return anc;}"
        "function containsTarget(ifBlock){"
        "  if(ifBlock.ifbody===sel.targetArr)return true;"
        "  for(var i=0;i<ifBlock.elseifs.length;i++)if(ifBlock.elseifs[i].body===sel.targetArr)return true;"
        "  if(ifBlock.elsebody===sel.targetArr)return true;"
        "  function walkDeep(arr){for(var j=0;j<arr.length;j++){var b=arr[j];"
        "    if(b.type==='ifblock'&&containsTarget(b))return true;"
        "    if((b.type==='forloop'||b.type==='whileloop')&&b.body&&isDescendantOf(b.body,sel.targetArr))return true;"
        "  }return false;}"
        "  return walkDeep(ifBlock.ifbody)||ifBlock.elseifs.some(function(ei){return walkDeep(ei.body);})||"
        "         (ifBlock.elsebody?walkDeep(ifBlock.elsebody):false);}"
        "function braceDepth(arr,idx){"
        "  var depth=0;"
        "  for(var i=0;i<idx;i++){"
        "    if(arr[i].type!=='codeblock')continue;"
        "    var c=(arr[i].params[0]||'').trim();"
        "    if(c.charAt(c.length-1)==='{')depth++;"
        "    if(c==='}'||c.match(/^\\}/))depth=Math.max(0,depth-1);"
        "  }"
        "  return depth;"
        "}"
        "function renderSection(elId,sName,anc){"
        "  var body=document.getElementById(elId+'-body');"
        "  body.querySelectorAll('.ws-block,.if-block').forEach(function(e){e.remove();});"
        "  SECTIONS[sName].forEach(function(block,idx){body.appendChild(renderBlock(block,idx,SECTIONS[sName],sName,sName,anc));});}"
        "function renderBlock(block,idx,parentArr,section,pathStr,anc){"
        "  if(block.type==='ifblock')return renderIfBlock(block,idx,parentArr,section,pathStr,anc);"
        "  if(block.type==='forloop')return renderForBlock(block,idx,parentArr,section,pathStr,anc);"
        "  if(block.type==='whileloop')return renderWhileBlock(block,idx,parentArr,section,pathStr,anc);"
        "  if(block.type==='phantom')return renderPhantomBlock(block,idx,parentArr);"
        "  if(block.type==='phantom_resolved')return renderPhantomResolved(block);"
        "  return renderActionBlock(block,idx,parentArr);}"
        "function renderPhantomBlock(block,idx,parentArr){"
        "  var d=document.createElement('div');"
        "  d.className='ws-block phantom-block';"
        "  var depth=braceDepth(parentArr,idx);"
        "  if(depth>0)d.style.marginLeft=(depth*18)+'px';"
        "  var isActive=activePhantoml&&activePhantoml.arr===parentArr&&activePhantoml.idx===idx;"
        "  if(isActive)d.classList.add('active');"
        "  var icon=document.createElement('span');icon.className='phantom-icon';icon.textContent='+';"
        "  var hint=document.createElement('span');hint.className='phantom-hint';hint.textContent=block.hint||'Place a block here';"
        "  var exp=document.createElement('span');exp.className='phantom-expects';exp.textContent=block.expects||'';"
        "  d.appendChild(icon);d.appendChild(hint);d.appendChild(exp);"
        "  d.addEventListener('click',function(e){"
        "    e.stopPropagation();"
        "    if(activePhantoml&&activePhantoml.arr===parentArr&&activePhantoml.idx===idx){"
        "      activePhantoml=null;"
        "    }else{"
        "      activePhantoml={arr:parentArr,idx:idx,phantom:block};"
        "      sel=null;exprSel=null;"
        "    }"
        "    updatePalette();render();});"
        "  return d;}"
        "function renderPhantomResolved(block){"
        "  var d=document.createElement('div');"
        "  d.className='ws-block phantom-block';d.style.opacity='0.45';d.style.cursor='default';"
        "  d.style.background='#f6f8fa';d.style.borderColor='#d0d7de';"
        "  var icon=document.createElement('span');icon.className='phantom-icon';icon.textContent='\\u2713';"
        "  var hint=document.createElement('span');hint.className='phantom-hint';"
        "  hint.style.color='#57606a';hint.textContent=block.hint||'';"
        "  d.appendChild(icon);d.appendChild(hint);"
        "  return d;}"
        "function renderActionBlock(block,idx,parentArr){"
        "  var def=B[block.type],d=document.createElement('div');d.className='ws-block';"
        "  d.setAttribute('data-id', block.id);"
        "  if(block.type==='codeblock'){"
        "    d.classList.add('codeblock-block');"
        "    var depth=braceDepth(parentArr,idx);"
        "    var c=(block.params[0]||'').trim();"
        "    if(c==='}'||c.match(/^\\}/))depth=Math.max(0,depth-1);"
        "    if(depth>0)d.style.marginLeft=(depth*18)+'px';"
        "    var icon=document.createElement('span');d.appendChild(icon);"
        "    var code=document.createElement('span');code.className='codeblock-code';"
        "    code.textContent=block.params[0]||'';d.appendChild(code);"
        "    function mkb2(ic,fn){var bt=document.createElement('button');bt.className='act';bt.textContent=ic;"
        "      bt.addEventListener('click',function(e){e.stopPropagation();fn();});return bt;}"
        "    d.appendChild(mkb2('\\u2191',function(){if(idx>0){var t=parentArr[idx-1];parentArr[idx-1]=parentArr[idx];parentArr[idx]=t;render();}}));"
        "    d.appendChild(mkb2('\\u2193',function(){if(idx<parentArr.length-1){var t=parentArr[idx+1];parentArr[idx+1]=parentArr[idx];parentArr[idx]=t;render();}}));"
        "    d.appendChild(mkb2('\\u00D7',function(){parentArr.splice(idx,1);render();}));"
        "    return d;}"
        "  var nm=document.createElement('span');nm.className='blk-name';nm.textContent=block.type;d.appendChild(nm);"
        "  var bdepth=braceDepth(parentArr,idx);if(bdepth>0)d.style.marginLeft=(bdepth*18)+'px';"
        "  def.inputs.forEach(function(inp,j){"
        "    if(inp.t==='expr'){"
        "      d.appendChild(renderExprSlot(block,j,inp.l));return;}"
        "    if(inp.t==='vartext'){"
        "      (function(capturedJ,capturedInpO){"
        "        var f=document.createElement('div');f.className='blk-field';"
        "        var lb=document.createElement('label');lb.textContent=inp.l;f.appendChild(lb);"
        "        var wrap=document.createElement('span');wrap.className='vartext-wrap';"
        "        var ei=document.createElement('input');ei.type='text';ei.className='vartext-input';"
        "        ei.value=block.params[capturedJ]||'';ei.placeholder='name';"
        "        var drop=null;"
        "        function closeDrop(){if(drop){drop.remove();drop=null;}}"
        "        function openDrop(filter){"
        "          closeDrop();"
        "          var vars=capturedInpO?getPinSuggestions(capturedInpO):getVarSuggestions();"
        "          var filtered=filter?vars.filter(function(v){return v.toLowerCase().indexOf(filter.toLowerCase())===0;}):vars;"
        "          if(filtered.length===0&&filter){return;}"
        "          drop=document.createElement('div');drop.className='vartext-drop';"
        "          if(filtered.length===0){"
        "            var empty=document.createElement('div');empty.className='vartext-drop-empty';"
        "            empty.textContent='no options yet';drop.appendChild(empty);"
        "          }else{"
        "            filtered.forEach(function(v){"
        "              var item=document.createElement('div');item.className='vartext-drop-item';"
        "              item.textContent=v;"
        "              item.addEventListener('mousedown',function(e){"
        "                e.preventDefault();e.stopPropagation();"
        "                ei.value=v;block.params[capturedJ]=v;genCode();"
        "                closeDrop();});"
        "              drop.appendChild(item);});"
        "          }"
        "          wrap.appendChild(drop);}"
        "        ei.addEventListener('click',function(e){e.stopPropagation();openDrop('');});"
        "        ei.addEventListener('focus',function(){openDrop('');});"
        "        ei.addEventListener('input',function(e){"
        "          e.stopPropagation();"
        "          block.params[capturedJ]=e.target.value;genCode();"
        "          e.target.value===''?openDrop(''):openDrop(e.target.value);});"
        "        ei.addEventListener('blur',function(){setTimeout(closeDrop,150);});"
        "        ei.addEventListener('keydown',function(e){"
        "          e.stopPropagation();"
        "          if(e.key==='Escape'||e.key==='Enter'){closeDrop();}"
        "          if(e.key==='Enter'){ei.blur();}});"
        "        wrap.appendChild(ei);f.appendChild(wrap);d.appendChild(f);"
        "      })(j,inp.o||null);return;}"
        "    var f=document.createElement('div');f.className='blk-field';"
        "    var lb=document.createElement('label');lb.textContent=inp.l;f.appendChild(lb);"
        "    var el;"
        "    if(inp.t==='sel'){el=document.createElement('select');"
        "      var opts=inp.o; if(typeof opts==='string'){opts=getOptions(opts);}"
        "      if(!block.params[j]){var op=document.createElement('option');op.value='';op.textContent='\\u2014';el.appendChild(op);}"
        "      opts.forEach(function(opt){var o=document.createElement('option');"
        "        if(typeof opt==='object'){o.value=opt.v;o.textContent=opt.lb;}else{o.value=opt;o.textContent=opt;}"
        "        el.appendChild(o);});el.value=block.params[j];"
        "    }else{el=document.createElement('input');el.type=inp.t==='number'?'number':'text';el.value=block.params[j];}"
        "    el.className='blk-input';"
        "    if(block.type==='increment'&&inp.l==='By'){"
        "      var op=block.params[1]||'++';f.style.display=(op==='++'||op==='--')?'none':'';}"
        "    el.addEventListener('click',function(e){e.stopPropagation();});"
        "    el.addEventListener('input',function(e){e.stopPropagation();block.params[j]=e.target.value;genCode();"
        "      if(block.type==='increment'&&inp.l==='Op'){"
        "        var byF=d.querySelector('.by-field');"
        "        if(byF)byF.style.display=(e.target.value==='++'||e.target.value==='--')?'none':'';}});"
        "    if(block.type==='increment'&&inp.l==='By')f.className+=' by-field';"
        "    f.appendChild(el);d.appendChild(f);});"
        "  function mkb(ic,fn){var bt=document.createElement('button');bt.className='act';bt.textContent=ic;"
        "    bt.addEventListener('click',function(e){e.stopPropagation();fn();});return bt;}"
        "  d.appendChild(mkb('\\u2191',function(){if(idx>0){var t=parentArr[idx-1];parentArr[idx-1]=parentArr[idx];parentArr[idx]=t;render();}}));"
        "  d.appendChild(mkb('\\u2193',function(){if(idx<parentArr.length-1){var t=parentArr[idx+1];parentArr[idx+1]=parentArr[idx];parentArr[idx]=t;render();}}));"
        "  d.appendChild(mkb('\\u00D7',function(){parentArr.splice(idx,1);render();}));"
        "  return d;}"
        "function renderIfBlock(block,idx,parentArr,section,parentPathStr,anc){"
        "  var wrap=document.createElement('div');"
        "  wrap.className='if-block'+(anc.indexOf(block.id)!==-1?' ancestor':'');"
        "  wrap.setAttribute('data-id', block.id);"
        "  var hdr=document.createElement('div');hdr.className='if-header';"
        "  hdr.appendChild(kw('if ('));appendCondFields(hdr,block.condition);hdr.appendChild(kw(')'));"
        "  hdr.appendChild(mkact('+ else if',function(){"
        "    block.elseifs.push({condition:{leftExpr:null,op:'==',rightExpr:null,joiner:'none',leftExpr2:null,op2:'==',rightExpr2:null},body:[]});render();}));"
        "  if(block.elsebody===null)hdr.appendChild(mkact('+ else',function(){block.elsebody=[];render();}));"
        "  hdr.appendChild(mkact('\\u00D7',function(){"
        "    parentArr.splice(idx,1);"
        "    if(sel&&(sel.targetArr===block.ifbody||isDescendant(block,sel.targetArr)))clearSelection();else render();}));"
        "  wrap.appendChild(hdr);"
        "  var ifPathStr=parentPathStr+' \\u2192 if';"
        "  var isOnlyBody=block.elseifs.length===0&&block.elsebody===null;"
        "  wrap.appendChild(makeBodyZone(block.ifbody,section,ifPathStr,isOnlyBody,anc));"
        "  block.elseifs.forEach(function(ei,eiIdx){"
        "    var eiHdr=document.createElement('div');eiHdr.className='elseif-header';"
        "    eiHdr.appendChild(kw('else if ('));appendCondFields(eiHdr,ei.condition);eiHdr.appendChild(kw(')'));"
        "    eiHdr.appendChild(mkact('\\u00D7',function(){block.elseifs.splice(eiIdx,1);render();}));"
        "    wrap.appendChild(eiHdr);"
        "    var eiPathStr=parentPathStr+' \\u2192 else if';"
        "    var eiIsLast=eiIdx===block.elseifs.length-1&&block.elsebody===null;"
        "    wrap.appendChild(makeBodyZone(ei.body,section,eiPathStr,eiIsLast,anc));});"
        "  if(block.elsebody!==null){"
        "    var elHdr=document.createElement('div');elHdr.className='else-header';"
        "    elHdr.appendChild(kw('else'));"
        "    elHdr.appendChild(mkact('\\u00D7',function(){block.elsebody=null;render();}));"
        "    wrap.appendChild(elHdr);"
        "    wrap.appendChild(makeBodyZone(block.elsebody,section,parentPathStr+' \\u2192 else',true,anc));}"
        "  return wrap;}"
        "function renderForBlock(block,idx,parentArr,section,parentPathStr,anc){"
        "  var wrap=document.createElement('div');wrap.className='for-block';"
        "  wrap.setAttribute('data-id', block.id);"
        "  var hdr=document.createElement('div');hdr.className='for-header';"
        "  var fkw=document.createElement('span');fkw.className='for-keyword';fkw.textContent='for (';hdr.appendChild(fkw);"
        "  var fields=[{key:'init',label:'init',ph:'int i=0'},{key:'cond',label:'cond',ph:'i<10'},{key:'incr',label:'incr',ph:'i++'}];"
        "  if(!block.forinit&&block.forinit!=='')block.forinit='int i = 0';"
        "  if(!block.forcond&&block.forcond!=='')block.forcond='i < 10';"
        "  if(!block.forincr&&block.forincr!=='')block.forincr='i++';"
        "  var keys=['forinit','forcond','forincr'],labels=['init','cond','incr'],phs=['int i=0','i<10','i++'];"
        "  for(var fi=0;fi<3;fi++){(function(ki,la,ph){"
        "    var fw=document.createElement('div');fw.style.cssText='display:flex;flex-direction:column;font-size:8px;';"
        "    var fl=document.createElement('label');fl.textContent=la;fl.style.color='#57606a';fw.appendChild(fl);"
        "    var fe=document.createElement('input');fe.type='text';fe.className='cond-input';fe.value=block[ki]||'';"
        "    fe.placeholder=ph;"
        "    fe.addEventListener('click',function(e){e.stopPropagation();});"
        "    fe.addEventListener('input',function(e){e.stopPropagation();block[ki]=e.target.value;genCode();});"
        "    fw.appendChild(fe);hdr.appendChild(fw);"
        "    if(fi<2){var sep=document.createElement('span');sep.className='for-keyword';sep.textContent=';';hdr.appendChild(sep);}"
        "  })(keys[fi],labels[fi],phs[fi]);}"
        "  var ekw=document.createElement('span');ekw.className='for-keyword';ekw.textContent=') {';hdr.appendChild(ekw);"
        "  hdr.appendChild(mkact('\\u00D7',function(){parentArr.splice(idx,1);"
        "    if(sel&&(sel.targetArr===block.body||isDescendantOf(block.body,sel.targetArr)))clearSelection();else render();}));"
        "  wrap.appendChild(hdr);"
        "  if(!block.body)block.body=[];"
        "  var bodyPath=parentPathStr+' \\u2192 for';"
        "  var bz=document.createElement('div');bz.className='for-body';"
        "  if(sel&&sel.targetArr===block.body)bz.classList.add('selected');"
        "  block.body.forEach(function(b,bi){bz.appendChild(renderBlock(b,bi,block.body,section,bodyPath,anc));});"
        "  if(block.body.length===0){var hint=document.createElement('div');hint.className='body-hint';"
        "    hint.textContent='click to select, then add blocks';bz.appendChild(hint);}"
        "  bz.addEventListener('click',function(e){"
        "    if(e.target===bz||e.target.classList.contains('body-hint')){e.stopPropagation();setSelection(section,block.body,bodyPath);}});"
        "  wrap.appendChild(bz);"
        "  var cz=document.createElement('div');cz.style.cssText='border-left:1px dashed #2e7d32;border-right:1px dashed #2e7d32;border-bottom:1px dashed #2e7d32;border-radius:0 0 5px 5px;padding:2px 6px;font-size:10px;color:#2e7d32;';"
        "  cz.textContent='} // end for';wrap.appendChild(cz);"
        "  return wrap;}"
        "function renderWhileBlock(block,idx,parentArr,section,parentPathStr,anc){"
        "  var wrap=document.createElement('div');wrap.className='while-block';"
        "  wrap.setAttribute('data-id', block.id);"
        "  var hdr=document.createElement('div');hdr.className='while-header';"
        "  var wkw=document.createElement('span');wkw.className='while-keyword';wkw.textContent='while (';hdr.appendChild(wkw);"
        "  if(!block.condition)block.condition={leftExpr:null,op:'!=',rightExpr:null,joiner:'none',leftExpr2:null,op2:'==',rightExpr2:null};"
        "  appendCondFields(hdr,block.condition);"
        "  var ewkw=document.createElement('span');ewkw.className='while-keyword';ewkw.textContent=') {';hdr.appendChild(ewkw);"
        "  hdr.appendChild(mkact('\\u00D7',function(){parentArr.splice(idx,1);"
        "    if(sel&&(sel.targetArr===block.body||isDescendantOf(block.body,sel.targetArr)))clearSelection();else render();}));"
        "  wrap.appendChild(hdr);"
        "  if(!block.body)block.body=[];"
        "  var bodyPath=parentPathStr+' \\u2192 while';"
        "  var bz=document.createElement('div');bz.className='while-body';"
        "  if(sel&&sel.targetArr===block.body)bz.classList.add('selected');"
        "  block.body.forEach(function(b,bi){bz.appendChild(renderBlock(b,bi,block.body,section,bodyPath,anc));});"
        "  if(block.body.length===0){var hint=document.createElement('div');hint.className='body-hint';"
        "    hint.textContent='click to select, then add blocks';bz.appendChild(hint);}"
        "  bz.addEventListener('click',function(e){"
        "    if(e.target===bz||e.target.classList.contains('body-hint')){e.stopPropagation();setSelection(section,block.body,bodyPath);}});"
        "  wrap.appendChild(bz);"
        "  var cz=document.createElement('div');cz.style.cssText='border-left:1px dashed #6a1b9a;border-right:1px dashed #6a1b9a;border-bottom:1px dashed #6a1b9a;border-radius:0 0 5px 5px;padding:2px 6px;font-size:10px;color:#6a1b9a;';"
        "  cz.textContent='} // end while';wrap.appendChild(cz);"
        "  return wrap;}"
        "function isDescendantOf(body,targetArr){"
        "  if(body===targetArr)return true;"
        "  for(var i=0;i<body.length;i++){var b=body[i];"
        "    if(b.type==='ifblock'){if(isDescendantOf(b.ifbody,targetArr))return true;"
        "      for(var j=0;j<b.elseifs.length;j++)if(isDescendantOf(b.elseifs[j].body,targetArr))return true;"
        "      if(b.elsebody&&isDescendantOf(b.elsebody,targetArr))return true;"
        "    }else if(b.type==='forloop'||b.type==='whileloop'){if(isDescendantOf(b.body,targetArr))return true;}}"
        "  return false;}"
        "function makeBodyZone(arr,section,pathStr,isLast,anc){"
        "  var div=document.createElement('div');"
        "  div.className='if-body'+(isLast?' last':'');"
        "  if(sel&&sel.targetArr===arr)div.classList.add('selected');"
        "  arr.forEach(function(block,idx){div.appendChild(renderBlock(block,idx,arr,section,pathStr,anc));});"
        "  if(arr.length===0){var hint=document.createElement('div');hint.className='body-hint';"
        "    hint.textContent='click to select, then add blocks';div.appendChild(hint);}"
        "  div.addEventListener('click',function(e){"
        "    if(e.target===div||e.target.classList.contains('body-hint')){"
        "      e.stopPropagation();setSelection(section,arr,pathStr);}});"
        "  return div;}"
        "function isDescendant(ifBlock,targetArr){"
        "  if(ifBlock.ifbody===targetArr)return true;"
        "  for(var i=0;i<ifBlock.elseifs.length;i++)if(ifBlock.elseifs[i].body===targetArr)return true;"
        "  if(ifBlock.elsebody===targetArr)return true;"
        "  function walkDeep(arr){for(var j=0;j<arr.length;j++){var b=arr[j];"
        "    if(b.type==='ifblock'&&isDescendant(b,targetArr))return true;"
        "    if((b.type==='forloop'||b.type==='whileloop')&&b.body&&isDescendantOf(b.body,targetArr))return true;"
        "  }return false;}"
        "  return walkDeep(ifBlock.ifbody)||ifBlock.elseifs.some(function(ei){return walkDeep(ei.body);})||"
        "         (ifBlock.elsebody?walkDeep(ifBlock.elsebody):false);}"
        "function kw(text){var s=document.createElement('span');s.className='if-keyword';s.textContent=text;return s;}"
        "function mkact(text,fn){var b=document.createElement('button');b.className='act';b.textContent=text;"
        "  b.addEventListener('click',function(e){e.stopPropagation();fn();});return b;}"
        "function getConditionSuggestions(){"
        "  var seen={},out=[];"
        "  function add(v){if(!v)return;if(seen[v])return;seen[v]=true;out.push(v);}"
        "  ['global','setup','loop'].forEach(function(sec){"
        "    SECTIONS[sec].forEach(function(b){"
        "      if(b.type==='pinmode'){"
        "        var pin=b.params[0],mode=b.params[1];"
        "        if(mode==='INPUT'||mode==='INPUT_PULLUP')add('digitalRead('+pin+')');"
        "      }else if(b.type==='analogread'){"
        "        var ap=b.params[0],vn=b.params[1]||'val';"
        "        add('analogRead('+ap+')');"
        "        add(vn);"
        "      }else if(b.type==='intvar'||b.type==='stringvar'){"
        "        add(b.params[0]);"
        "      }"
        "    });"
        "  });"
        "  ['HIGH','LOW'].forEach(add);"
        "  return out;"
        "}"
        "function getVarSuggestions(){"
        "  var seen={},out=[];"
        "  function add(v){if(!v)return;if(seen[v])return;seen[v]=true;out.push(v);}"
        "  ['global','setup','loop'].forEach(function(sec){"
        "    SECTIONS[sec].forEach(function(b){"
        "      if(b.type==='intvar'||b.type==='longvar'||b.type==='stringvar'){add(b.params[0]);}"
        "    });"
        "    function walkBody(arr){arr.forEach(function(b){"
        "      if(b.type==='intvar'||b.type==='longvar'){add(b.params[0]);}"
        "      if(b.ifbody)walkBody(b.ifbody);"
        "      if(b.elseifs)b.elseifs.forEach(function(ei){walkBody(ei.body);});"
        "      if(b.elsebody)walkBody(b.elsebody);"
        "      if(b.body)walkBody(b.body);"
        "    });}"
        "    walkBody(SECTIONS[sec]);"
        "  });"
        "  return out;"
        "}"
        "function getPinSuggestions(optKey){"
        "  var seen={},out=[];"
        "  SECTIONS.global.forEach(function(b){"
        "    if(b.type==='intvar'&&b.params[0]&&!seen[b.params[0]]){seen[b.params[0]]=true;out.push(b.params[0]);}"
        "  });"
        "  getOptions(optKey||'DIGITAL_PIN_OPTIONS').forEach(function(p){"
        "    if(!seen[p]){seen[p]=true;out.push(p);}"
        "  });"
        "  return out;"
        "}"
        "function renderCondExprSlot(cond,side,label){"
        "  var exNode=cond[side]||null;"
        "  var wrap=document.createElement('div');wrap.className='blk-field';"
        "  var lb=document.createElement('label');lb.textContent=label;wrap.appendChild(lb);"
        "  var slot=document.createElement('div');"
        "  slot.className='expr-slot'+(exNode?' has-expr':'');"
        "  var isActive=exprSel&&exprSel.condObj===cond&&exprSel.side===side;"
        "  if(isActive)slot.classList.add('active');"
        "  if(exNode){"
        "    slot.appendChild(renderExprBlock(exNode,function(){cond[side]=null;exprSel=null;updatePalette();render();}));"
        "  }else{"
        "    var ph=document.createElement('span');ph.textContent=isActive?'> drop expr':'+ expr';slot.appendChild(ph);"
        "  }"
        "  slot.addEventListener('click',function(e){"
        "    e.stopPropagation();"
        "    if(exprSel&&exprSel.condObj===cond&&exprSel.side===side){exprSel=null;updatePalette();render();return;}"
        "    exprSel={condObj:cond,side:side};sel=null;"
        "    document.getElementById('statusbar').innerHTML='<span style=\"color:#9a6700\">click an expression to fill the '+label+' slot</span>';"
        "    updatePalette();"
        "    render();});"
        "  wrap.appendChild(slot);return wrap;}"
        "function appendCondFields(parent,cond){"
        "  parent.appendChild(renderCondExprSlot(cond,'leftExpr','left'));"
        "  parent.appendChild(condField('op',cond,'opsel'));"
        "  parent.appendChild(renderCondExprSlot(cond,'rightExpr','right'));"
        "  parent.appendChild(condField('joiner',cond,'joinsel'));"
        "  var g2=document.createElement('span');"
        "  g2.style.display=cond.joiner!=='none'?'contents':'none';"
        "  g2.appendChild(renderCondExprSlot(cond,'leftExpr2','left2'));"
        "  g2.appendChild(condField('op2',cond,'opsel'));"
        "  g2.appendChild(renderCondExprSlot(cond,'rightExpr2','right2'));"
        "  parent.appendChild(g2);"
        "  var joinEl=parent.querySelector('.cond-joiner');"
        "  joinEl.addEventListener('change',function(){g2.style.display=joinEl.value!=='none'?'contents':'none';});}"
        "function condField(labelText,obj,type){"
        "  var f=document.createElement('div');f.className='cond-field';"
        "  var lb=document.createElement('label');lb.textContent=labelText;f.appendChild(lb);"
        "  var el;"
        "  if(type==='opsel'){el=document.createElement('select');el.className='cond-select';"
        "    [['==','equals'],['!=','not equals'],['>','greater than'],['<','less than'],['>=','greater or equal'],['<=','less than or equal']].forEach(function(o){"
        "      var opt=document.createElement('option');opt.value=o[0];opt.textContent=o[1];el.appendChild(opt);});"
        "    el.value=obj[labelText];"
        "  }else if(type==='joinsel'){el=document.createElement('select');el.className='cond-joiner';"
        "    [['none','\\u2014'],['and','and'],['or','or']].forEach(function(o){"
        "      var opt=document.createElement('option');opt.value=o[0];opt.textContent=o[1];el.appendChild(opt);});"
        "    el.value=obj[labelText];"
        "  }"
        "  el.addEventListener('click',function(e){e.stopPropagation();});"
        "  el.addEventListener('change',function(e){e.stopPropagation();obj[labelText]=e.target.value;genCode();});"
        "  f.appendChild(el);return f;}"
        "function genCond(c){"
        "  var left=c.leftExpr?genExpr(c.leftExpr,null,'x'):(c.left||'x');"
        "  var right=c.rightExpr?genExpr(c.rightExpr,null,'0'):(c.right||'0');"
        "  var base=left+' '+(c.op||'==')+' '+right;"
        "  if(c.joiner&&c.joiner!=='none'){"
        "    var left2=c.leftExpr2?genExpr(c.leftExpr2,null,'x'):(c.left2||'x');"
        "    var right2=c.rightExpr2?genExpr(c.rightExpr2,null,'0'):(c.right2||'0');"
        "    if(left2!=='x')base+=' '+(c.joiner==='and'?'&&':'||')+' '+left2+' '+(c.op2||'==')+' '+right2;"
        "  }"
        "  return base;}"
        "function genBlocks(arr,indent){"
        "  var lines=[],extra=0;"
        "  arr.forEach(function(b){"
        "    if(b.type==='phantom'||b.type==='phantom_resolved')return;"
        "    if(b.type==='codeblock'){"
        "      var c=(b.params[0]||'').trim();"
        "      if(c==='}'||c.match(/^\\}/))extra=Math.max(0,extra-1);"
        "      lines.push(genBlock(b,indent+extra));"
        "      if(c.charAt(c.length-1)==='{')extra++;"
        "    }else{lines.push(genBlock(b,indent+extra));}"
        "  });"
        "  return lines.join('\\n');}"
        "function genBlock(block,indent){"
        "  var pad='';for(var i=0;i<indent;i++)pad+='   ';"
        "  if(block.type==='ifblock'){"
        "    var lines=[pad+'if ('+genCond(block.condition)+') {'];"
        "    lines.push(genBlocks(block.ifbody,indent+1));"
        "    lines.push(pad+'}');"
        "    block.elseifs.forEach(function(ei){"
        "      lines.push(pad+'else if ('+genCond(ei.condition)+') {');"
        "      lines.push(genBlocks(ei.body,indent+1));"
        "      lines.push(pad+'}');});"
        "    if(block.elsebody!==null){"
        "      lines.push(pad+'else {');"
        "      lines.push(genBlocks(block.elsebody,indent+1));"
        "      lines.push(pad+'}');}"
        "    return lines.join('\\n');}"
        "  if(block.type==='forloop'){"
        "    var init=block.forinit||'int i = 0';"
        "    var cond=block.forcond||'i < 10';"
        "    var incr=block.forincr||'i++';"
        "    var lines=[pad+'for ('+init+'; '+cond+'; '+incr+') {'];"
        "    lines.push(genBlocks(block.body||[],indent+1));"
        "    lines.push(pad+'}');"
        "    return lines.join('\\n');}"
        "  if(block.type==='whileloop'){"
        "    var cond=block.condition?genCond(block.condition):(block.whilecond||'true');"
        "    var lines=[pad+'while ('+cond+') {'];"
        "    lines.push(genBlocks(block.body||[],indent+1));"
        "    lines.push(pad+'}');"
        "    return lines.join('\\n');}"
        "  return pad+BLOCKS[block.type].genStmt(block.params,block.exChildren||[]);}"
        "function genCode(){"
        "  var co=document.getElementById('codeout');"
        "  var gv=genBlocks(SECTIONS.global,0);"
        "  var sc=genBlocks(SECTIONS.setup,1);"
        "  var lc=genBlocks(SECTIONS.loop,1);"
        "  co.textContent='// Arduino Sketch\\n// Block Builder\\n// ------------\\n\\n'"
        "    +(gv?gv+'\\n\\n':'')"
        "    +'void setup() {\\n'+(sc?sc+'\\n':'')+'}'+"
        "    '\\n\\nvoid loop() {\\n'+(lc?lc+'\\n':'')+'}';checkStepComplete();}"
        "function findBlockById(id){"
        "  var found=null;"
        "  function walk(arr){"
        "    if(!arr)return;"
        "    for(var i=0;i<arr.length;i++){"
        "      if(arr[i].id==id){found=arr[i];return;}"
        "      if(arr[i].ifbody)walk(arr[i].ifbody);"
        "      if(arr[i].elseifs)arr[i].elseifs.forEach(function(ei){walk(ei.body);});"
        "      if(arr[i].elsebody)walk(arr[i].elsebody);"
        "      if(arr[i].body)walk(arr[i].body);}}"
        "  ['global','setup','loop'].forEach(function(s){walk(SECTIONS[s]);});"
        "  return found;}"
        "window.getBlockCode=function(id){"
        "  var b=findBlockById(id);if(!b)return null;"
        "  var code=genBlock(b,0);return code.split('\\n')[0].trim();};"
        "window.getGeneratedCode = function() { return document.getElementById('codeout').textContent; };"
        "window.isProgressionMode = function() { return PROGRESSION_MODE; };"
        "window.setBlockData = function(data) {"
        "  if (!data) return;"
        "  SECTIONS.global = data.global || [];"
        "  SECTIONS.setup = data.setup || [];"
        "  SECTIONS.loop = data.loop || [];"
        "  clearSelection();"
        "  if (typeof MASTER_SKETCH !== 'undefined' && MASTER_SKETCH) validateSketch();"
        "};"
        "function flash(txt){"
        "  var mb=document.getElementById('msg');mb.textContent=txt;mb.classList.add('show');"
        "  setTimeout(function(){mb.classList.remove('show');},2500);}"
        "document.getElementById('copybtn').addEventListener('click',function(){"
        "  var txt=document.getElementById('codeout').textContent;"
        "  if(navigator.clipboard&&navigator.clipboard.writeText)"
        "    navigator.clipboard.writeText(txt).then(function(){flash('Copied!');}).catch(function(){fbCopy(txt);});"
        "  else fbCopy(txt);});"
        "window.copyCode = function(){"
        "  var txt=document.getElementById('codeout').textContent;"
        "  if(navigator.clipboard&&navigator.clipboard.writeText)"
        "    navigator.clipboard.writeText(txt).then(function(){flash('Copied!');}).catch(function(){fbCopy(txt);});"
        "  else fbCopy(txt);};"
        "function fbCopy(txt){"
        "  var ta=document.createElement('textarea');ta.value=txt;"
        "  ta.style.cssText='position:fixed;opacity:0;';document.body.appendChild(ta);ta.select();"
        "  try{document.execCommand('copy');flash('Copied!');}catch(e){flash('Select manually');}"
        "  document.body.removeChild(ta);}"
        "document.getElementById('clrbtn').addEventListener('click',function(){"
        "  SECTIONS.global=[];SECTIONS.setup=[];SECTIONS.loop=[];clearSelection();});"
        "function saveBlocks(){"
        "  if(!USERNAME||!PAGE)return;"
        "  var state;"
        "  if(PROGRESSION_MODE){"
        "    state = {current_step: CURRENT_STEP, student_saves: STUDENT_SAVES};"
        "  } else {"
        "    state = {global: SECTIONS.global, setup: SECTIONS.setup, loop: SECTIONS.loop};"
        "  }"
        "  fetch(SUPABASE_URL+'/rest/v1/block_saves?on_conflict=username,page',"
        "    {method:'POST',"
        "     headers:{'apikey':SUPABASE_KEY,'Authorization':'Bearer '+SUPABASE_KEY,"
        "       'Content-Type':'application/json','Prefer':'resolution=merge-duplicates,return=minimal'},"
        "     body:JSON.stringify({username:USERNAME,page:PAGE,blocks_json:JSON.stringify(state),updated_at:new Date().toISOString()})"
        "    }).then(function(r){if(r.ok)flash('Saved!');else flash('Save failed');});}"
        "window.saveBlocks = saveBlocks;"
        "function loadBlocks(){"
        "  if(!USERNAME||!PAGE||PAGE==='null'||PAGE==='undefined')return;"
        "  fetch(SUPABASE_URL+'/rest/v1/block_saves?username=eq.'+USERNAME+'&page=eq.'+PAGE,"
        "    {headers:{'apikey':SUPABASE_KEY,'Authorization':'Bearer '+SUPABASE_KEY}})"
        "  .then(function(r){return r.json();})"
        "  .then(function(data){"
        "    if(data&&data.length>0){"
        "      var saved=JSON.parse(data[0].blocks_json);"
        "      if(PROGRESSION_MODE&&saved.current_step!==undefined){"
        "        CURRENT_STEP=saved.current_step;"
        "        STUDENT_SAVES=saved.student_saves||[];"
        "        var allSaves={global:[],setup:[],loop:[]};"
        "        STUDENT_SAVES.forEach(function(sv){"
        "          allSaves.global=allSaves.global.concat(sv.global||[]);"
        "          allSaves.setup=allSaves.setup.concat(sv.setup||[]);"
        "          allSaves.loop=allSaves.loop.concat(sv.loop||[]);});"
        "        buildWorkspace(CURRENT_STEP,allSaves);"
        "        clearSelection();render();genCode();if(typeof checkStepComplete==='function')checkStepComplete();"
        "      }else{"
        "        SECTIONS.global=saved.global;"
        "        SECTIONS.setup=saved.setup;"
        "        SECTIONS.loop=saved.loop;}"
        "      clearSelection();render();genCode();"
        "      flash('Loaded!');}})"
        "  .catch(function(){flash('Load failed');});}"
        "document.getElementById('savebtn').addEventListener('click',function(){saveBlocks();});"
        "document.getElementById('resetbtn').addEventListener('click',function(){"
        "  if(!confirm('Reset to original? Your saved progress will be lost.'))return;"
        "  STUDENT_SAVES=[];CURRENT_STEP=0;"
        + initial_js +
        "  clearSelection();render();genCode();"
        "  flash('Reset!');});"
        "function countPhantoms(arr){"
        "  var n=0;"
        "  arr.forEach(function(b){"
        "    if(b.type==='phantom')n++;"
        "    if(b.type==='ifblock'){n+=countPhantoms(b.ifbody);b.elseifs.forEach(function(ei){n+=countPhantoms(ei.body);});if(b.elsebody)n+=countPhantoms(b.elsebody);}"
        "    if((b.type==='forloop'||b.type==='whileloop')&&b.body)n+=countPhantoms(b.body);"
        "  });"
        "  return n;}"
        "function countIncomplete(arr){"
        "  var n=0;"
        "  arr.forEach(function(b){"
        "    if(b.type==='phantom'||b.type==='phantom_resolved'||b.type==='codeblock')return;"
        "    if(b.type==='ifblock'){"
        "      var c=b.condition;"
        "      if(c){if(!c.leftExpr)n++;if(!c.rightExpr)n++;"
        "        if(c.joiner!=='none'){if(!c.leftExpr2)n++;if(!c.rightExpr2)n++;}}"
        "      n+=countIncomplete(b.ifbody);"
        "      b.elseifs.forEach(function(ei){"
        "        var ec=ei.condition;"
        "        if(ec){if(!ec.leftExpr)n++;if(!ec.rightExpr)n++;}"
        "        n+=countIncomplete(ei.body);});"
        "      if(b.elsebody)n+=countIncomplete(b.elsebody);"
        "      return;}"
        "    if(b.type==='whileloop'){"
        "      var c=b.condition;"
        "      if(c){if(!c.leftExpr)n++;if(!c.rightExpr)n++;}"
        "      if(b.body)n+=countIncomplete(b.body);return;}"
        "    if(b.type==='forloop'){"
        "      if(b.body)n+=countIncomplete(b.body);return;}"
        "    var def=BLOCKS[b.type];if(!def)return;"
        "    def.inputs.forEach(function(inp,j){"
        "      if(inp.t==='expr'){"
        "        if(!b.exChildren||!b.exChildren[j])n++;"
        "      }else if(inp.t==='text'||inp.t==='number'||inp.t==='vartext'){"
        "        if(!b.params||!b.params[j]||b.params[j]==='')n++;"
        "      }"
        "    });"
        "  });"
        "  return n;}"
        "function compareExpr(u,t){"
        "  if(!u&&!t)return true;if(!u||!t)return false;"
        "  if(u.type!==t.type)return false;"
        "  if(u.type==='value'){return (u.params[0]||'').trim()===(t.params[0]||'').trim();}"
        "  for(var i=0;i<(u.params||[]).length;i++)if((u.params[i]||'').trim()!==(t.params[i]||'').trim())return false;"
        "  var uc=u.children||[],tc=t.children||[];"
        "  if(uc.length!==tc.length)return false;"
        "  for(var i=0;i<uc.length;i++)if(!compareExpr(uc[i],tc[i]))return false;"
        "  return true;}"
        "function compareCondition(u,t){"
        "  if(!u&&!t)return true;if(!u||!t)return false;"
        "  if(u.op!==t.op)return false;"
        "  if(!compareExpr(u.leftExpr,t.leftExpr))return false;"
        "  if(!compareExpr(u.rightExpr,t.rightExpr))return false;"
        "  if(u.joiner!==t.joiner)return false;"
        "  if(u.joiner!=='none'){"
        "    if(u.op2!==t.op2)return false;"
        "    if(!compareExpr(u.leftExpr2,t.leftExpr2))return false;"
        "    if(!compareExpr(u.rightExpr2,t.rightExpr2))return false;"
        "  }"
        "  return true;}"
        "function generateExprHint(u,t,tier){"
        "  if(!u&&!t)return null;if(!u)return 'Missing value';"
        "  if(u.type!==t.type)return 'Wrong type: use '+t.type;"
        "  var def=BLOCKS[u.type];"
        "  if(u.type==='value'){"
        "    var uv=(u.params[0]||'').trim(),tv=(t.params[0]||'').trim();"
        "    if(uv!==tv)return tier===3?'Value should be '+tv:'Check value';"
        "  }"
        "  for(var i=0;i<(u.params||[]).length;i++){"
        "    if((u.params[i]||'').trim()!==(t.params[i]||'').trim()){"
        "       var lbl=(def&&def.inputs[i])?def.inputs[i].l:'setting';"
        "       return tier===3?lbl+' should be '+t.params[i]:'Check '+lbl;"
        "    }"
        "  }"
        "  var uc=u.children||[],tc=t.children||[];"
        "  if(uc.length!==tc.length)return 'Structure mismatch';"
        "  for(var i=0;i<uc.length;i++){"
        "    var h=generateExprHint(uc[i],tc[i],tier);"
        "    if(h){"
        "       var lbl=(def&&def.inputs[i])?def.inputs[i].l:'slot';"
        "       return lbl+': '+h;"
        "    }"
        "  }"
        "  return null;}"
        "function generateCondHint(u,t,tier){"
        "  if(!u&&!t)return null;if(!u||!t)return 'Condition missing';"
        "  var h=generateExprHint(u.leftExpr,t.leftExpr,tier);if(h)return 'Left side: '+h;"
        "  if(u.op!==t.op)return tier===3?'Operator should be '+t.op:'Check operator';"
        "  h=generateExprHint(u.rightExpr,t.rightExpr,tier);if(h)return 'Right side: '+h;"
        "  if(t.joiner!=='none'){"
        "    if(u.joiner!==t.joiner)return 'Check joiner (and/or)';"
        "    h=generateExprHint(u.leftExpr2,t.leftExpr2,tier);if(h)return '2nd Left: '+h;"
        "    if(u.op2!==t.op2)return tier===3?'2nd Op should be '+t.op2:'Check 2nd operator';"
        "    h=generateExprHint(u.rightExpr2,t.rightExpr2,tier);if(h)return '2nd Right: '+h;"
        "  }"
        "  return null;}"
        "function generateHint(u,t,tier){"
        "  if(tier<2)return '';"
        "  if(u.type!==t.expects)return 'Wrong block. Should be '+t.expects;"
        "  var def=BLOCKS[u.type];"
        "  if(!def)return '';"
        "  for(var i=0;i<(t.params||[]).length;i++){"
        "    if(!def.inputs[i])continue;"
        "    var up=u.params[i]||'',tp=t.params[i]||'';"
        "    if(up.trim()!==tp.trim()){"
        "      var lbl=(def&&def.inputs[i])?def.inputs[i].l:'field';"
        "      return tier===3?'Check '+lbl+': expected \"'+tp+'\"':'Check '+lbl;"
        "    }"
        "  }"
        "  if(t.expects==='ifblock'||t.expects==='whileloop'){"
        "    var h=generateCondHint(u.condition,t.condition,tier);if(h)return h;"
        "  }"
        "  if(t.expects==='forloop'){"
        "    if((u.forinit||'')!==(t.forinit||''))return tier===3?'Init: '+t.forinit:'Check init';"
        "    if((u.forcond||'')!==(t.forcond||''))return tier===3?'Cond: '+t.forcond:'Check condition';"
        "    if((u.forincr||'')!==(t.forincr||''))return tier===3?'Incr: '+t.forincr:'Check increment';"
        "  }"
        "  var uex=u.exChildren||[],tex=t.exChildren||[];"
        "  for(var i=0;i<tex.length;i++){"
        "    var h=generateExprHint(uex[i],tex[i],tier);"
        "    if(h){"
        "       var lbl=(def&&def.inputs[i])?def.inputs[i].l:'slot';"
        "       return lbl+': '+h;"
        "    }"
        "  }"
        "  return '';}"
        "function collectBadIds(uList,tList,tier,badIds){"
        "  if(!uList||!tList)return;"
        "  uList.forEach(function(ub,i){"
        "    var tb=tList[i];if(!tb)return;"
        "    if(tb.type==='phantom'){"
        "      if(!compareBlock(ub,tb))badIds.push({id:ub.id,hint:generateHint(ub,tb,tier)});"
        "      var tc=null;"
        "      if(tb.expects==='ifblock')tc={ifbody:tb.ifbody,elseifs:tb.elseifs,elsebody:tb.elsebody};"
        "      else if(tb.expects==='forloop'||tb.expects==='whileloop')tc={body:tb.body};"
        "      if(tc){"
        "        if(ub.type==='ifblock'){collectBadIds(ub.ifbody,tc.ifbody,tier,badIds);"
        "          if(ub.elseifs&&tc.elseifs)ub.elseifs.forEach(function(ei,k){if(tc.elseifs[k])collectBadIds(ei.body,tc.elseifs[k].body,tier,badIds);});"
        "          if(ub.elsebody&&tc.elsebody)collectBadIds(ub.elsebody,tc.elsebody,tier,badIds);}"
        "        else if(ub.type==='forloop'||ub.type==='whileloop'){collectBadIds(ub.body,tc.body,tier,badIds);}"
        "      }"
        "    }"
        "  });}"
        "function compareBlock(u,t){"
        "  if(!u)return false;"
        "  if(t.type==='phantom'){"
        "    if(u.type!==t.expects)return false;"
        "    if(t.expects==='ifblock'||t.expects==='whileloop'){"
        "       if(!compareCondition(u.condition,t.condition))return false;"
        "    }"
        "    if(t.expects==='forloop'){"
        "       if((u.forinit||'')!==(t.forinit||''))return false;"
        "       if((u.forcond||'')!==(t.forcond||''))return false;"
        "       if((u.forincr||'')!==(t.forincr||''))return false;"
        "    }"
        "    for(var i=0;i<(t.params||[]).length;i++){"
        "       var up=u.params[i]||'',tp=t.params[i]||'';"
        "       if(up.trim()!==tp.trim())return false;"
        "    }"
        "    var uex=u.exChildren||[],tex=t.exChildren||[];"
        "    for(var i=0;i<tex.length;i++){"
        "       if(!compareExpr(uex[i],tex[i]))return false;"
        "    }"
        "    return true;"
        "  }"
        "  return true;}"
        "function validateStep(){"
        "  if(!STEPS||!STEPS[CURRENT_STEP])return true;"
        "  var tmpl=STEPS[CURRENT_STEP];"
        "  var valid=true;var tier=1;if(CHECK_FAIL_COUNT>=2)tier=2;if(CHECK_FAIL_COUNT>=4)tier=3;"
        "  var badIds=[];"
        "  ['global','setup','loop'].forEach(function(sec){"
        "    var uArr=SECTIONS[sec],tArr=tmpl[sec];"
        "    collectBadIds(uArr,tArr,tier,badIds);"
        "  });"
        "  if(badIds.length>0)valid=false;"
        "  document.querySelectorAll('.ws-block,.if-block,.for-block,.while-block').forEach(function(el){el.classList.remove('error-block');});"
        "  document.querySelectorAll('.block-hint').forEach(function(el){el.remove();});"
        "  if(!valid){"
        "    CHECK_FAIL_COUNT++;"
        "    badIds.forEach(function(bid){"
        "      var el=document.querySelector('[data-id=\"'+bid.id+'\"]');"
        "      if(el){"
        "        el.classList.add('error-block');"
        "        if(bid.hint){var hd=document.createElement('div');hd.className='block-hint';hd.textContent=bid.hint;el.appendChild(hd);}"
        "      }"
        "    });"
        "  }"
        "  return valid;}"
        "function checkSketchFields(uList, mList, badIds, path = [], section = ''){"
        "  if(!uList||!mList)return;"
        "  for(var i=0;i<uList.length&&i<mList.length;i++){"
        "    var ub=uList[i],mb=mList[i];"
        "    if(!ub||!mb)continue;"
        "    if(ub.type!==mb.type)continue;"
        "    var bad=false;"
        "    if(mb.params){"
        "      for(var j=0;j<mb.params.length;j++){"
        "        var mv=mb.params[j],uv=(ub.params&&ub.params[j]!==undefined)?ub.params[j]:'';"
        "        if(typeof mv==='string'&&mv.trim()!==''&&(!uv||(typeof uv==='string'&&uv.trim()===''))){"
        "          badIds.push({id: ub.id, section: section, path: path.concat([i]), hint: 'Fill in all the fields for this block'});"
        "          bad=true;break;}}}"
        "    if(!bad&&mb.exChildren){"
        "      for(var j=0;j<mb.exChildren.length;j++){"
        "        var me=mb.exChildren[j],ue=ub.exChildren?ub.exChildren[j]:null;"
        "        if(me&&me.params&&me.params[0]&&me.params[0].trim()!==''&&(!ue||!ue.params||!ue.params[0]||ue.params[0].trim()==='')){"
        "          badIds.push({id: ub.id, section: section, path: path.concat([i]), hint: 'Fill in all the fields for this block'});"
        "          bad=true;break;}}}"
        "    if(ub.type==='ifblock'){"
        "      checkSketchFields(ub.ifbody, mb.ifbody, badIds, path.concat([i, 'ifbody']), section);"
        "      if(ub.elseifs && mb.elseifs) {"
        "        ub.elseifs.forEach(function(ei, k) {"
        "          if(mb.elseifs[k]) checkSketchFields(ei.body, mb.elseifs[k].body, badIds, path.concat([i, 'elseifs', k, 'body']), section);"
        "        });"
        "      }"
        "      if(mb.elsebody)checkSketchFields(ub.elsebody||[], mb.elsebody, badIds, path.concat([i, 'elsebody']), section);"
        "    }else if(ub.type==='forloop'||ub.type==='whileloop'){"
        "      checkSketchFields(ub.body, mb.body, badIds, path.concat([i, 'body']), section);}}}"
        "function applySketchHighlights(){"
        "  document.querySelectorAll('.ws-block,.if-block,.for-block,.while-block').forEach(function(el){el.classList.remove('error-block');});"
        "  document.querySelectorAll('.block-hint').forEach(function(el){el.remove();});"
        "  if (SKETCH_ERROR_PATHS.length > 0) {"
        "    var sb = document.getElementById('statusbar');"
        "    if(sb) { sb.style.transition='background 0.2s'; sb.style.background='#ffebe9'; setTimeout(function(){sb.style.background='';}, 400); }"
        "  }"
        "  SKETCH_ERROR_PATHS.forEach(function(entry){"
        "    var res = SECTIONS[entry.section];"
        "    if(!res) return;"
        "    for(var i=0; i<entry.path.length; i++){"
        "      res = res[entry.path[i]];"
        "      if(!res) break;"
        "    }"
        "    if(res && res.id){"
        "      var el = document.querySelector('[data-id=\"'+res.id+'\"]');"
        "      if(el){"
        "        el.classList.add('error-block');"
        "        if(entry.hint){"
        "          var hd=document.createElement('div');hd.className='block-hint';hd.textContent=entry.hint;"
        "          var target = el.querySelector('.if-header, .for-header, .while-header') || el;"
        "          target.appendChild(hd);"
        "        }"
        "      }"
        "    }"
        "  });"
        "}"
        "function validateSketch(){"
        "  console.log('[DEBUG] validateSketch() invoked.');"
        "  if(!MASTER_SKETCH)return {valid:true};"
        "  var badIds=[];"
        "  ['global','setup','loop'].forEach(function(sec){"
        "    checkSketchFields(SECTIONS[sec], MASTER_SKETCH[sec], badIds, [], sec);"
        "  });"
        "  SKETCH_ERROR_PATHS=badIds;"
        "  applySketchHighlights();"
        "  return {valid: badIds.length===0, errorCount: badIds.length, errors: badIds};}"
        "window.validateSketch = validateSketch;"
        "window.dumpDebug = function() {"
        "  console.log('--- BLOCK BUILDER DEBUG DUMP ---');"
        "  console.log('MASTER_SKETCH:', MASTER_SKETCH);"
        "  console.log('SECTIONS:', SECTIONS);"
        "  console.log('SKETCH_ERROR_PATHS:', SKETCH_ERROR_PATHS);"
        "  console.log('--------------------------------');"
        "};"
        "function checkStepComplete(){"
        "  if(!PROGRESSION_MODE)return;"
        "  var phantoms=countPhantoms(SECTIONS.global)+countPhantoms(SECTIONS.setup)+countPhantoms(SECTIONS.loop);"
        "  var incomplete=countIncomplete(SECTIONS.global)+countIncomplete(SECTIONS.setup)+countIncomplete(SECTIONS.loop);"
        "  var total=phantoms+incomplete;"
        "  var btn=document.getElementById('nextbtn');"
        "  if(btn.classList.contains('next-mode'))return;"
        "  var curGuidance = STEPS&&STEPS[CURRENT_STEP]?STEPS[CURRENT_STEP].guidance:'guided';"
        "  if(curGuidance==='free'){"
        "    btn.classList.add('ready');"
        "    btn.classList.remove('check-mode');"
        "    btn.textContent='Next Step \\u2192';"
        "    btn.classList.add('next-mode');"
        "    return;"
        "  }"
        "  if(btn.classList.contains('check-mode')){"
        "     if(total>0){btn.classList.remove('ready');btn.textContent='Complete Step';btn.classList.remove('check-mode');}"
        "     return;"
        "  }"
        "  var prog=document.getElementById('step-progress');"
        "  if(prog){"
        "    if(phantoms>0)prog.textContent=phantoms+' block'+(phantoms===1?'':'s')+' to place';"
        "    else if(incomplete>0)prog.textContent=incomplete+' field'+(incomplete===1?'':'s')+' to fill';"
        "    else prog.textContent='complete';}"
        "  if(total===0){btn.classList.add('ready');btn.textContent='Check Code';btn.classList.add('check-mode');}"
        "  else{btn.classList.remove('ready');btn.textContent='Complete Step';btn.classList.remove('check-mode');}}"
        "function buildWorkspace(stepIdx,saves){"
        "  if(!PROGRESSION_MODE||!STEPS||stepIdx>=STEPS.length)return;"
        "  var step=STEPS[stepIdx];"
        "  function mergeSaved(templateArr,savedArr){"
        "    if(!savedArr||!savedArr.length)return templateArr.slice();"
        "    var STRUCTURAL=['ifblock','forloop','whileloop'];"
        "    var out=[];"
        "    var si=0;"
        "    templateArr.forEach(function(b){"
        "      if(b.type==='phantom_resolved'){"
        "        if(si<savedArr.length){"
        "          var sb=savedArr[si];"
        "          var code=genBlock(sb,0).trim();"
        "          out.push({id:sb.id,type:'codeblock',params:[code]});"
        "          si++;}"
        "      }else{out.push(b);}"
        "    });"
        "    return out;"
        "  }"
        "  var savedG=saves?saves.global:null;"
        "  var savedS=saves?saves.setup:null;"
        "  var savedL=saves?saves.loop:null;"
        "  SECTIONS.global=mergeSaved(step.global,savedG);"
        "  SECTIONS.setup=mergeSaved(step.setup,savedS);"
        "  SECTIONS.loop=mergeSaved(step.loop,savedL);"
        "  PALETTE_ALLOWED = (step.palette !== undefined && step.palette !== null) ? step.palette : null;"
        "  var lbl=document.getElementById('step-label');"
        "  var bar=document.getElementById('step-bar');"
        "  if(lbl)lbl.textContent=step.label;"
        "  if(bar)bar.style.display='flex';"
        "  window.CURRENT_STEP_META = {guidance: step.guidance, view: step.view};"
        "  window.dispatchEvent(new CustomEvent('stepchange', {detail: window.CURRENT_STEP_META}));"
        "  var activeId='ls';"
        "  if(step.active==='global')activeId='gs';"
        "  else if(step.active==='setup')activeId='ss';"
        "  expandSection(activeId);"
        "  var nbtn=document.getElementById('nextbtn');"
        "  if(nbtn)nbtn.style.display=(step.guidance==='open'||stepIdx>=STEPS.length-1)?'none':'';"
        "  var pbtn=document.getElementById('prevbtn');"
        "  if(pbtn)pbtn.style.display=stepIdx>0?'':'none';"
        "  if(window.updateDrawer) window.updateDrawer(stepIdx);"
        "  checkStepComplete();}"
        "document.getElementById('nextbtn').addEventListener('click',function(){"
        "  if(!document.getElementById('nextbtn').classList.contains('ready'))return;"
        "  var btn=document.getElementById('nextbtn');"
        "  var meta=window.CURRENT_STEP_META || {};"
        "  if(btn.classList.contains('check-mode')){"
        "    if(meta.view==='editor'){"
        "      btn.textContent='Compiling...'; btn.disabled=true;"
        "      var code=window.getEditorCode?window.getEditorCode():'';"
        "      fetch('http://127.0.0.1:3210/compile',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({code:code})})"
        "      .then(function(r){return r.json();})"
        "      .then(function(data){"
        "        btn.disabled=false;"
        "        if(data.success){"
        "          btn.textContent='Next Step \\u2192'; btn.classList.remove('check-mode'); btn.classList.add('next-mode'); flash('Correct!');"
        "        }else{"
        "          btn.textContent='Check Code'; flash('Compile failed: '+(data.message||'check your code syntax'));"
        "        }"
        "      }).catch(function(){ btn.disabled=false; btn.textContent='Check Code'; flash('Compiler Agent offline'); });"
        "      return;"
        "    }"
        "    if(validateStep()){"
        "      btn.textContent='Next Step \\u2192';"
        "      btn.classList.remove('check-mode');"
        "      btn.classList.add('next-mode');"
        "      flash('Correct!');"
        "      CHECK_FAIL_COUNT=0;"
        "    }else{"
        "      flash('Incorrect - check highlighted blocks');"
        "    }"
        "    return;"
        "  }"
        "  try{"
        "    var STRUCTURAL=['ifblock','forloop','whileloop'];"
        "    var saves={global:SECTIONS.global.filter(function(b){return b.type!=='phantom'&&b.type!=='phantom_resolved';}),"
        "               setup:SECTIONS.setup.filter(function(b){return b.type!=='phantom'&&b.type!=='phantom_resolved';}),"
        "               loop:SECTIONS.loop.filter(function(b){return b.type!=='phantom'&&b.type!=='phantom_resolved';}) };"
        "    STUDENT_SAVES.push(JSON.parse(JSON.stringify(saves)));"
        "    CURRENT_STEP++;"
        "    flash('advancing to step '+CURRENT_STEP);"
        "    var allSaves={global:[],setup:[],loop:[]};"
        "    STUDENT_SAVES.forEach(function(sv){"
        "      allSaves.global=allSaves.global.concat(sv.global||[]);"
        "      allSaves.setup=allSaves.setup.concat(sv.setup||[]);"
        "      allSaves.loop=allSaves.loop.concat(sv.loop||[]);"
        "    });"
        "    buildWorkspace(CURRENT_STEP,allSaves);"
        "    flash('built step '+CURRENT_STEP);"
        "    btn.classList.remove('next-mode');"
        "    clearSelection();render();genCode();"
        "    flash('Step '+(CURRENT_STEP+1)+'!');"
        "    saveBlocks();"
        "    if(window.openDrawer) window.openDrawer();"
        "  }catch(e){flash('ERR: '+e.message);console.error(e);}});"
        "document.getElementById('prevbtn').addEventListener('click',function(){"
        "  if(!PROGRESSION_MODE||CURRENT_STEP<=0)return;"
        "  if(!confirm('Go back to previous step? Your progress on the current step will be discarded.'))return;"
        "  CURRENT_STEP--;"
        "  STUDENT_SAVES.pop();"
        "  var allSaves={global:[],setup:[],loop:[]};"
        "  STUDENT_SAVES.forEach(function(sv){"
        "    allSaves.global=allSaves.global.concat(sv.global);allSaves.setup=allSaves.setup.concat(sv.setup);allSaves.loop=allSaves.loop.concat(sv.loop);});"
        "  buildWorkspace(CURRENT_STEP,allSaves);"
        "  flash('Returned to step '+CURRENT_STEP);"
        "  clearSelection();render();genCode();});"
        "if(USERNAME){loadBlocks();}"
        "updatePalette();"
        "render();"
        "if(PROGRESSION_MODE)checkStepComplete();" +
        overlay_js +
        "})();"
    )

    html = (
        "<div id='block-builder-ui'>"
        "<link href='https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;800&display=swap' rel='stylesheet'>"
        "<style>" + css + "</style>"
        + body +
        "<script>" + js + "</script>"
        "</div>"
    )

    if return_html:
        return html