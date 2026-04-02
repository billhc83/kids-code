import re, json, random

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


def parse_steps(sketch_code):
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
        reset = parts[4].lower() == 'reset' if len(parts) > 4 else False

        raw_steps.append({
            'label': label,
            'guidance': guidance or 'guided',
            'view': view or 'blocks',
            'palette_filter': palette_filter or 'nofilter',
            'reset': reset,
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
        if step.get('reset'):
            cumulative_global = []
            cumulative_setup = []
            cumulative_loop = []

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
            'active': active_section,
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
