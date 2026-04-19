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


from lark import Lark, Transformer, v_args, UnexpectedToken, UnexpectedCharacters
import os

# Load grammar — one parser instance per start symbol to avoid Earley's
# "multiple start symbol items" bug when using a list of start symbols.
GRAMMAR_PATH = os.path.join(os.path.dirname(__file__), 'arduino.lark')
with open(GRAMMAR_PATH, 'r') as f:
    _grammar_text = f.read()

_EARLEY = dict(parser='earley', maybe_placeholders=False)
arduino_parser = Lark(_grammar_text, start='block_list', **_EARLEY)

class BlockTransformer(Transformer):
    def __init__(self, fill_conditions=False, fill_values=False):
        super().__init__()
        self.fill_conditions = fill_conditions
        self.fill_values = fill_values

    def block_list(self, items):
        # We return the list of raw items and handle phantoms in parse_blocks
        return [i for i in items if i is not None]

    def _make_phantom_meta(self, hint, tmpl):
        meta = {
            'hint': hint,
            'expects': tmpl['type'],
            'params': tmpl.get('params', []),
            'exChildren': tmpl.get('exChildren', []),
            'condition': tmpl.get('condition'),
        }
        for field in ['expectedExTypes', 'expectedCondTypes', 'ifbody', 'elseifs', 'elsebody', 'body', 'forinit', 'forcond', 'forincr']:
             if field in tmpl:
                 meta[field] = tmpl[field]
             elif field == 'expectedExTypes':
                 meta[field] = [e['type'] if e else None for e in tmpl.get('exChildren', [])]
        return meta

    def step(self, tokens):
        # //>> is handled in parse_steps, but we need to ignore it here or mark it
        return None

    def phantom(self, items):
        hint = str(items[0]).replace('//??', '').strip()
        return {'_is_phantom_dir': True, 'hint': hint}

    def locked(self, items):
        line = str(items[0]).replace('//##', '').strip()
        # Strip trailing inline C++ comments (e.g. `if (...) {   // Switch ON`)
        # but preserve lines that ARE comments (e.g. `// Serial.begin(9600);`)
        if not line.startswith('//'):
            comment_idx = line.find('//')
            if comment_idx != -1:
                line = line[:comment_idx].rstrip()
        return {'type': 'codeblock', 'params': [line], 'locked': True}

    def unknown_stmt(self, tokens):
        line = str(tokens[0]).strip()
        return {'type': 'codeblock', 'params': [line], 'locked': True}

    def unknown_raw(self, tokens):
        line = str(tokens[0]).strip()
        if not line: return None
        return {'type': 'codeblock', 'params': [line], 'locked': True}

    def if_block(self, items):
        cond = items[0]
        ifbody = items[1]
        
        # In Earley, items[2:] includes all subsequent clauses
        elseifs = [i for i in items[2:] if isinstance(i, dict) and i.get('_is_elseif')]
        elsebody = next((i for i in items[2:] if isinstance(i, list)), None)
        
        return {
            'type': 'ifblock',
            'condition': cond,
            'ifbody': ifbody,
            'elseifs': elseifs,
            'elsebody': elsebody
        }

    def else_if_clause(self, items):
        return {'type': 'elseifclause', '_is_elseif': True, 'condition': items[0], 'body': items[1]}

    def phantom_else_if(self, items):
        hint = str(items[0]).replace('//??', '').strip()
        condition = items[1]
        body = items[2] if len(items) > 2 else []
        return {'_is_phantom_elseif': True, 'hint': hint, 'condition': condition, 'body': body}

    def phantom_else_clause(self, items):
        hint = str(items[0]).replace('//??', '').strip()
        body = items[1] if len(items) > 1 else []
        return {'_is_phantom_elseclause': True, 'hint': hint, 'body': body}

    def else_clause(self, items):
        return items[0] # Returns the block_list (list)

    def while_loop(self, items):
        return {'type': 'whileloop', 'condition': items[0], 'body': items[1]}

    def for_loop(self, items):
        header = str(items[0]).strip()
        parts = [p.strip() for p in header.split(';')]
        return {
            'type': 'forloop',
            'forinit': parts[0] if len(parts) > 0 else '',
            'forcond': parts[1] if len(parts) > 1 else '',
            'forincr': parts[2] if len(parts) > 2 else '',
            'body': items[1]
        }

    def condition(self, items):
        res = {
            'leftExpr': items[0], 'op': str(items[1]) if len(items)>1 else '==', 'rightExpr': items[2] if len(items)>2 else None,
            'joiner': 'none', 'leftExpr2': None, 'op2': '==', 'rightExpr2': None
        }
        if len(items) > 3:
            res['joiner'] = 'and' if str(items[3]) == '&&' else 'or'
            res['leftExpr2'] = items[4]
            res['op2'] = str(items[5])
            res['rightExpr2'] = items[6]
        return res

    def stmt(self, items):
        return items[0]

    def empty_val(self, items):
        return {'type': 'value', 'params': [''], 'children': []}

    def var_decl(self, items):
        typ, name = str(items[0]), str(items[1])
        val = items[2] if len(items) > 2 else None
        vtype = 'intvar' if typ == 'int' else 'longvar' if 'long' in typ else 'boolvar' if typ == 'bool' else 'stringvar'
        if vtype == 'boolvar':
             return {'type': vtype, 'params': [name, str(val['params'][0]) if val else '']}
        return {'type': vtype, 'params': [name, ''], 'exChildren': [None, val]}

    def assignment(self, items):
        name = str(items[0])
        val = items[1]
        return {'type': 'setvar', 'params': [name, ''], 'exChildren': [None, val]}

    def crement(self, items): return {'type': 'increment', 'params': [str(items[0]), str(items[1]), '1']}
    def op_assign(self, items): return {'type': 'increment', 'params': [str(items[0]), str(items[1]), str(items[2]['params'][0])]}

    def func_call(self, items):
        from lark import Token as LarkToken
        if len(items) >= 2 and isinstance(items[1], LarkToken):
            prefix, name, args = str(items[0]), str(items[1]), (items[2] if len(items) > 2 else [])
        else:
            prefix, name, args = "", str(items[0]), (items[1] if len(items) > 1 else [])
        
        full_name = f"{prefix}.{name}" if prefix else name
        
        if full_name == "pinMode":
            return {'type': 'pinmode', 'params': [str(args[0]['params'][0]) if len(args) > 0 and 'params' in args[0] else '', str(args[1]['params'][0]) if len(args) > 1 and 'params' in args[1] else '']}
        if full_name == "digitalWrite":
            return {'type': 'digitalwrite', 'params': [str(args[0]['params'][0]) if len(args) > 0 and 'params' in args[0] else '', str(args[1]['params'][0]) if len(args) > 1 and 'params' in args[1] else '']}
        if full_name == "analogWrite":
            return {'type': 'analogwrite', 'params': [str(args[0]['params'][0]) if len(args) > 0 and 'params' in args[0] else '', ''], 'exChildren': [None, args[1] if len(args)>1 else None]}
        if full_name == "tone":
            p0 = str(args[0]['params'][0]) if args else ''
            p2 = str(args[2]['params'][0]) if len(args) > 2 else ''
            return {'type': 'tone', 'params': [p0, '', p2 or None], 'exChildren': [None, args[1] if len(args)>1 else None]}
        if full_name == "noTone":
            return {'type': 'notone', 'params': [''], 'exChildren': [args[0] if args else None]}
        if full_name == "delay":
            return {'type': 'delay', 'params': [''], 'exChildren': [args[0] if args else None]}
        if full_name == "delayMicroseconds":
            return {'type': 'delaymicroseconds', 'params': [''], 'exChildren': [args[0] if args else None]}
        if full_name == "Serial.begin":
             return {'type': 'serialbegin', 'params': [str(args[0]['params'][0]) if args else '']}
        if full_name in ["Serial.print", "Serial.println"]:
             return {'type': 'serialprint', 'params': ['', name], 'exChildren': [args[0] if args else None]}
        
        # Fallback for other func calls
        return {'type': 'codeblock', 'params': [f"{full_name}(...);"], 'locked': True}

    def arg_list(self, items): return items

    def add(self, items): return self._math('+', items)
    def sub(self, items): return self._math('-', items)
    def mul(self, items): return self._math('*', items)
    def div(self, items): return self._math('/', items)
    def mod(self, items): return self._math('%', items)

    def _math(self, op, items):
        return {
            'type': 'math',
            'params': ['', op, ''],
            'children': [items[0], None, items[1]]
        }

    def number(self, tokens): return {'type': 'value', 'params': [str(tokens[0])], 'children': []}
    def string(self, tokens): return {'type': 'value', 'params': [str(tokens[0])], 'children': []}
    def var(self, tokens): return {'type': 'value', 'params': [str(tokens[0])], 'children': []}
    
    def func_expr(self, items):
        from lark import Token as LarkToken
        if len(items) >= 2 and isinstance(items[1], LarkToken):
            prefix, name, args = str(items[0]), str(items[1]), (items[2] if len(items) > 2 else [])
        else:
            prefix, name, args = "", str(items[0]), (items[1] if len(items) > 1 else [])
        full_name = f"{prefix}.{name}" if prefix else name
        
        if full_name == "millis": return {'type': 'millis', 'params': [], 'children': []}
        if full_name == "Serial.available": return {'type': 'serialavailable', 'params': [], 'children': []}
        if full_name == "analogRead": return {'type': 'analogread', 'params': [str(args[0]['params'][0]) if args else ''], 'children': []}
        if full_name == "digitalRead": return {'type': 'digitalread', 'params': [str(args[0]['params'][0]) if args else ''], 'children': []}
        if full_name == "pulseIn":
            pin = str(args[0]['params'][0]) if args else ''
            val = str(args[1]['params'][0]) if len(args) > 1 else 'HIGH'
            return {'type': 'pulsein', 'params': [pin, val], 'children': []}
        if full_name == "random": return {'type': 'random', 'params': [str(a['params'][0]) if a else '' for a in args], 'children': []}
        if full_name == "map":
             return {
                 'type': 'map',
                 'params': ['', *[str(a['params'][0]) if a else '' for a in args[1:]]],
                 'children': [args[0] if args else None, None, None, None, None]
             }
        if full_name == "constrain":
             return {
                 'type': 'constrain',
                 'params': ['', *[str(a['params'][0]) if a else '' for a in args[1:]]],
                 'children': [args[0] if args else None, None, None]
             }
        return {'type': 'value', 'params': [f"{full_name}(...)"], 'children': []}


def parse_condition(cond_str, fill_conditions=False):
    # Wrap in a dummy sketch so it can be parsed via block_list, then extract the condition
    try:
        wrapped = f"if ({cond_str}) {{}}"
        tree = arduino_parser.parse(wrapped, start='block_list')
        blocks = BlockTransformer(fill_conditions=fill_conditions).transform(tree)
        if blocks and isinstance(blocks[0], dict) and 'condition' in blocks[0]:
            return blocks[0]['condition']
    except:
        pass
    return {'leftExpr': None, 'op': '==', 'rightExpr': None, 'joiner': 'none'}

def parse_expr(s):
    if not s: return {'type': 'value', 'params': [''], 'children': []}
    try:
        wrapped = f"int _x = {s};"
        tree = arduino_parser.parse(wrapped, start='block_list')
        blocks = BlockTransformer(fill_values=True).transform(tree)
        if blocks and isinstance(blocks[0], dict) and blocks[0].get('exChildren'):
            return blocks[0]['exChildren'][1] or {'type': 'value', 'params': [s], 'children': []}
    except:
        pass
    return {'type': 'value', 'params': [s], 'children': []}

def strip_expr_values(node):
    if node is None: return None
    t = node['type']
    if t == 'value': return None
    if t in ('millis', 'serialavailable', 'serialreadstring'): return node
    if t in ('analogread', 'digitalread'): return {'type': t, 'params': [''], 'children': []}
    if t == 'pulsein': return {'type': 'pulsein', 'params': ['', 'HIGH'], 'children': []}
    if t == 'random': return {'type': 'random', 'params': ['', ''], 'children': []}
    if t == 'math':
        op = node['params'][1] if len(node['params']) > 1 else '+'
        ch = node.get('children') or [None, None, None]
        return {
            'type': 'math',
            'params': ['', op, ''],
            'children': [strip_expr_values(ch[0]), None, strip_expr_values(ch[2])]
        }
    if t == 'map':
        ch = node.get('children') or [None]
        return {'type': 'map', 'params': ['', '', '', '', ''], 'children': [strip_expr_values(ch[0]), None, None, None, None]}
    if t == 'constrain':
        ch = node.get('children') or [None]
        return {'type': 'constrain', 'params': ['', '', ''], 'children': [strip_expr_values(ch[0]), None, None]}
    return node

def strip_block_values(block):
    """Deep copy a block and strip all numeric/variable values, keeping only structure."""
    if block is None: return None
    if isinstance(block, list):
         return [strip_block_values(b) for b in block]
    if not isinstance(block, dict):
         return block
    
    res = {k: v for k, v in block.items()}
    
    # Strip params for specific types
    if res.get('type') in ('pinmode', 'digitalwrite', 'analogwrite', 'tone', 'serialbegin', 'boolvar'):
         res['params'] = ["" for _ in res['params']]
    
    # Recurse into exChildren
    if res.get('exChildren'):
        res['exChildren'] = [strip_expr_values(c) for c in res['exChildren']]
    
    # Recurse into condition
    if res.get('condition'):
        cond = {k: v for k, v in res['condition'].items()}
        cond['leftExpr'] = strip_expr_values(cond['leftExpr'])
        cond['rightExpr'] = strip_expr_values(cond['rightExpr'])
        cond['leftExpr2'] = strip_expr_values(cond['leftExpr2'])
        cond['rightExpr2'] = strip_expr_values(cond['rightExpr2'])
        res['condition'] = cond
    
    # Recurse into bodies
    if res.get('ifbody'): res['ifbody'] = [strip_block_values(b) for b in res['ifbody']]
    if res.get('elseifs'): 
        for ei in res['elseifs']:
            ei['body'] = [strip_block_values(b) for b in ei['body']]
            if ei.get('condition'):
                c = {k: v for k, v in ei['condition'].items()}
                c['leftExpr'] = strip_expr_values(c['leftExpr'])
                c['rightExpr'] = strip_expr_values(c['rightExpr'])
                ei['condition'] = c
    if res.get('elsebody'): res['elsebody'] = [strip_block_values(b) for b in res['elsebody']]
    if res.get('body'): res['body'] = [strip_block_values(b) for b in res['body']]
    
    return res

def _make_slot(hint, master, initial_fill_content):
    """Build a phantom slot dict from a master block and hint string."""
    tmpl = strip_block_values(master)
    cond = master.get('condition') if isinstance(master, dict) else None
    return {
        'type': 'slot',
        'id': str(random.random() * 1000000000000000),
        'content': master if initial_fill_content else None,
        'master': master,
        'phantom_meta': {
            'hint': hint,
            'expects': master['type'] if isinstance(master, dict) else 'codeblock',
            'params': tmpl.get('params', []) if isinstance(tmpl, dict) else [],
            'exChildren': tmpl.get('exChildren', []) if isinstance(tmpl, dict) else [],
            'condition': tmpl.get('condition') if isinstance(tmpl, dict) else None,
            'expectedExTypes': [e['type'] if e else None for e in master.get('exChildren', [])] if isinstance(master, dict) and 'exChildren' in master else None,
            'expectedCondTypes': (lambda c: {
                'left':  c['leftExpr']['type']  if c.get('leftExpr')  else None,
                'right': c['rightExpr']['type'] if c.get('rightExpr') else None,
                'left2': c['leftExpr2']['type'] if c.get('leftExpr2') else None,
                'right2':c['rightExpr2']['type'] if c.get('rightExpr2') else None,
            })(cond) if cond else None,
            'ifbody': tmpl.get('ifbody', []) if isinstance(tmpl, dict) else [],
            'elseifs': tmpl.get('elseifs', []) if isinstance(tmpl, dict) else [],
            'elsebody': tmpl.get('elsebody') if isinstance(tmpl, dict) else None,
            'body': tmpl.get('body', []) if isinstance(tmpl, dict) else [],
            'forinit': tmpl.get('forinit') if isinstance(tmpl, dict) else '',
            'forcond': tmpl.get('forcond') if isinstance(tmpl, dict) else '',
            'forincr': tmpl.get('forincr') if isinstance(tmpl, dict) else '',
        }
    }


def _resolve_nested_bodies(item, fill_values=False, initial_fill_content=False):
    """
    Recursively resolve phantom directives inside the bodies of ifblock/whileloop/forloop items.
    Returns a new dict with resolved bodies; returns item unchanged for other types.
    """
    if not isinstance(item, dict):
        return item
    t = item.get('type')
    if t == 'ifblock':
        ifbody = resolve_phantom_items(item.get('ifbody') or [], fill_values, initial_fill_content)
        elseifs = []
        for ei in item.get('elseifs') or []:
            ei_copy = dict(ei)
            ei_copy['body'] = resolve_phantom_items(ei.get('body') or [], fill_values, initial_fill_content)
            elseifs.append(ei_copy)
        elsebody = item.get('elsebody')
        if elsebody:
            elsebody = resolve_phantom_items(elsebody, fill_values, initial_fill_content)
        return {**item, 'ifbody': ifbody, 'elseifs': elseifs, 'elsebody': elsebody}
    if t in ('whileloop', 'forloop'):
        body = resolve_phantom_items(item.get('body') or [], fill_values, initial_fill_content)
        return {**item, 'body': body}
    return item


def resolve_phantom_items(raw_items, fill_values=False, initial_fill_content=False):
    """
    Walk a list of raw BlockTransformer items and resolve //?? phantom directives
    into slot dicts. Handles phantom_else_if and phantom_else_clause by recursing
    into their bodies so nested phantoms inside else/else-if bodies are also resolved.
    """
    final_blocks = []
    current_phantom_hint = None

    for item in raw_items:
        if isinstance(item, dict) and item.get('_is_phantom_dir'):
            current_phantom_hint = item['hint']
            continue

        if isinstance(item, dict) and item.get('_is_phantom_elseif'):
            # phantom_else_if → elseifclause block
            resolved_body = resolve_phantom_items(item.get('body', []), fill_values, initial_fill_content)
            master = {
                'type': 'elseifclause',
                'condition': item.get('condition'),
                'body': resolved_body,
            }
            final_blocks.append(_make_slot(item['hint'], master, initial_fill_content))
            current_phantom_hint = None
            continue

        if isinstance(item, dict) and item.get('_is_phantom_elseclause'):
            # phantom_else_clause → elseclause block
            resolved_body = resolve_phantom_items(item.get('body', []), fill_values, initial_fill_content)
            master = {
                'type': 'elseclause',
                'body': resolved_body,
            }
            final_blocks.append(_make_slot(item['hint'], master, initial_fill_content))
            current_phantom_hint = None
            continue

        item = _resolve_nested_bodies(item, fill_values, initial_fill_content)

        if current_phantom_hint:
            final_blocks.append(_make_slot(current_phantom_hint, item, initial_fill_content))
            current_phantom_hint = None
        else:
            if not fill_values:
                final_blocks.append(strip_block_values(item))
            else:
                final_blocks.append(item)

    return final_blocks


def parse_blocks(code, fill_conditions=False, fill_values=False, initial_fill_content=False):
    code = code.strip()
    if not code: return []

    try:
        tree = arduino_parser.parse(code, start='block_list')
        raw_items = BlockTransformer().transform(tree)
        return resolve_phantom_items(raw_items, fill_values, initial_fill_content)
    except (UnexpectedToken, UnexpectedCharacters) as e:
        # Enhanced fallback: Include error column/line info if available
        error_meta = {'line': getattr(e, 'line', None), 'column': getattr(e, 'column', None)}
        result = []
        for i, line in enumerate(code.split('\n')):
            s = line.strip()
            if not s:
                continue
            # Skip directive lines — they are not real code
            if s.startswith('//??') or s.startswith('//>>'):
                continue
            if s.startswith('//##'):
                s = s.replace('//##', '', 1).strip()
                # Strip trailing inline comments
                if not s.startswith('//'):
                    comment_idx = s.find('//')
                    if comment_idx != -1:
                        s = s[:comment_idx].rstrip()
            if not s:
                continue
            result.append({
                'type': 'codeblock',
                'params': [s],
                'locked': True,
                'parser_error': error_meta if i == (getattr(e, 'line', 1) - 1) else None
            })
        return result

def parse_sketch(sketch_code, fill_conditions=False, fill_values=False, initial_fill_content=False):
    result = {'global': [], 'setup': [], 'loop': []}
    setup_start = re.search(r'void\s+setup\s*\(.*?\)', sketch_code)
    if setup_start:
        global_code = sketch_code[:setup_start.start()].strip()
    else:
        # No void setup() — could be a global-only chunk (no wrappers) or a
        # loop-only chunk.  Use everything before void loop() as globals; if
        # there is no loop either, the whole chunk is global declarations.
        loop_start = re.search(r'void\s+loop\s*\(.*?\)', sketch_code)
        global_code = sketch_code[:loop_start.start()].strip() if loop_start else sketch_code.strip()
    setup_m = re.search(r'void\s+setup\s*\(.*?\)\s*\{', sketch_code)
    loop_m  = re.search(r'void\s+loop\s*\(.*?\)\s*\{', sketch_code)
    setup_code = extract_brace_body(sketch_code, setup_m.end()-1)[0] if setup_m else ''
    loop_code  = extract_brace_body(sketch_code, loop_m.end()-1)[0]  if loop_m  else ''
    result['global'] = parse_blocks(global_code, fill_conditions, fill_values, initial_fill_content)
    result['setup']  = parse_blocks(setup_code,  fill_conditions, fill_values, initial_fill_content)
    result['loop']   = parse_blocks(loop_code,   fill_conditions, fill_values, initial_fill_content)
    return result


def collect_expr_types(nodes):
    types = set()
    if not nodes: return types
    for n in nodes:
        if not n: continue
        types.add(n['type'])
        if n.get('children'):
            types.update(collect_expr_types(n['children']))
    return types


def collect_types(blocks):
    """Walk a block tree and return the set of all block types used."""
    types = set()
    for b in blocks:
        if b['type'] == 'slot':
            pm = b['phantom_meta']
            types.add(pm['expects'])
            # Add 'value' whenever any expression slot exists — values are always needed
            # as leaf nodes. Specific expr types (math, pulsein, etc.) are NOT added to
            # PALETTE_ALLOWED; they are already constrained per-slot via expectedType.
            has_exprs = any(t for t in (pm.get('expectedExTypes') or []) if t)
            if not has_exprs and pm.get('exChildren'):
                has_exprs = bool(collect_expr_types(pm['exChildren']))
            if has_exprs:
                types.add('value')
            if pm.get('expectedCondTypes'):
                for val in pm['expectedCondTypes'].values():
                    if val: types.add(val)
            if pm.get('ifbody'): types.update(collect_types(pm['ifbody']))
            if pm.get('body'): types.update(collect_types(pm['body']))
            if b['content']:
                types.update(collect_types([b['content']]))
        else:
            types.add(b['type'])
            # Collect types from nested expression children
            if b.get('exChildren'):
                types.update(collect_expr_types(b['exChildren']))
            
            # Standard structural recursion
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
    step_pattern = re.compile(r'^\s*//>>(.+)$', re.MULTILINE)
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
        reset = any(p.lower() == 'reset' for p in parts)
        aside = any(p.lower() == 'aside' for p in parts)

        # 1. Base Mapping from Guidance Mode
        if guidance == 'open':
            structure = "none"
            validation = "none"
            fill = False
            is_filter = False
            is_readonly = False
        elif guidance == 'verify':
            structure = "none"
            validation = "verify"
            fill = True
            is_filter = True
            is_readonly = False
        elif guidance == 'free':
            structure = "none"
            validation = "none"
            fill = True
            is_filter = True
            is_readonly = True
        elif guidance == 'full':
            structure = "full"
            validation = "step"
            fill = True
            is_filter = True
            is_readonly = True
        else:  # default to guided
            structure = "partial"
            validation = "step"
            fill = False
            is_filter = True
            is_readonly = True

        # 2. Explicit Overrides (key:value)
        palette_override = None
        for p in parts:
            p_low = p.lower()
            if p_low.startswith('fill:'):
                fill = (p_low.split(':')[1] == 'true')
            if p_low.startswith('structure:'):
                structure = p_low.split(':')[1]
            if p_low.startswith('validation:'):
                validation = p_low.split(':')[1]
            if p_low.startswith('filter:'):
                is_filter = (p_low.split(':')[1] == 'true')
            if p_low.startswith('readonly:'):
                is_readonly = (p_low.split(':')[1] == 'true')
            if p.lower().startswith('palette:'):
                palette_override = [t.strip() for t in p.split(':', 1)[1].split(',') if t.strip()]
                is_filter = True

        step_config = {
            'flow': "progression",
            'guidance': guidance,
            'structure': structure,
            'fill': fill,
            'filter': is_filter,
            'readonly': is_readonly,
            'validation': validation,
            'interface': view if view in ['blocks', 'editor'] else 'blocks',
            'palette_override': palette_override,
        }
        print(f"[PARSE_STEPS]   fill_after_override={fill}  config.fill={step_config['fill']}")

        raw_steps.append({
            'label': label,
            'config': step_config,
            'reset': reset,
            'aside': aside,
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
        print(f"\n[PARSE_STEPS] ── processing '{step['label']}' | reset={step.get('reset')} | fill={step['config']['fill']} ──")
        print(f"[PARSE_STEPS]   cumulative_global len={len(cumulative_global)}  setup={len(cumulative_setup)}  loop={len(cumulative_loop)}")
        if step.get('reset'):
            cumulative_global = []
            cumulative_setup = []
            cumulative_loop = []
            print(f"[PARSE_STEPS]   *** RESET applied ***")

        # For verify mode, split chunk on //== to get initial workspace and correct answer
        verify_sep = re.compile(r'^\s*//==\s*$', re.MULTILINE)
        verify_global, verify_setup, verify_loop = [], [], []
        if step['config']['guidance'] == 'verify':
            halves = verify_sep.split(step['chunk'], maxsplit=1)
            initial_chunk = halves[0]
            correct_chunk = halves[1] if len(halves) == 2 else ''
            if correct_chunk:
                correct_parsed = parse_sketch(correct_chunk, fill_conditions=True, fill_values=True, initial_fill_content=True)
                verify_global = correct_parsed['global']
                verify_setup  = correct_parsed['setup']
                verify_loop   = correct_parsed['loop']
            step = dict(step, chunk=initial_chunk)

        # Parse this step's chunk as a sketch using the explicit fill control
        fill_val = step['config']['fill']
        print(f"[PARSE_STEPS]   fill_val={fill_val}  chunk[:80]={repr(step['chunk'][:80])}")
        parsed = parse_sketch(step['chunk'], fill_conditions=fill_val, fill_values=fill_val, initial_fill_content=fill_val)
        print(f"[PARSE_STEPS]   parsed → global={len(parsed['global'])} blocks, setup={len(parsed['setup'])} blocks, loop={len(parsed['loop'])} blocks")
        def _block_summary(blocks):
            return [(b.get('type'), b.get('params'), b.get('exChildren')) for b in blocks]
        print(f"[PARSE_STEPS]   parsed.global  : {_block_summary(parsed['global'])}")
        print(f"[PARSE_STEPS]   parsed.setup   : {_block_summary(parsed['setup'])}")
        print(f"[PARSE_STEPS]   parsed.loop    : {_block_summary(parsed['loop'])}")
        if step['config'].get('palette_override'):
            step['palette'] = step['config']['palette_override']
        elif step['config']['filter']:
            step_types = collect_types(
                parsed['global'] + parsed['setup'] + parsed['loop']
            )
            step['palette'] = list(step_types)
        else:
            step['palette'] = None

        # Determine active section based on where new blocks (phantoms) are located
        active_section = 'loop'
        if any(b['type'] == 'slot' and b['content'] is None for b in parsed['global']):
            active_section = 'global'
        elif any(b['type'] == 'slot' and b['content'] is None for b in parsed['setup']):
            active_section = 'setup'
        elif any(b['type'] == 'slot' and b['content'] is None for b in parsed['loop']):
            active_section = 'loop'
        elif parsed['setup']:
            active_section = 'setup'
        elif parsed['global']:
            active_section = 'global'

        # Build full workspace for this step:
        # global: cumulative phantom_resolved markers + this chunk's global blocks
        # setup/loop: use parsed content only if non-empty, otherwise carry cumulative forward.
        # An empty void setup() / void loop() in a step chunk is ignored.
        full = {
            'global': cumulative_global + parsed['global'],
            'setup': parsed['setup'] if parsed['setup'] else cumulative_setup,
            'loop': parsed['loop'] if parsed['loop'] else cumulative_loop,
        }
        print(f"[PARSE_STEPS]   full → global={len(full['global'])}  setup={len(full['setup'])}  loop={len(full['loop'])}")
        print(f"[PARSE_STEPS]   full.global: {_block_summary(full['global'])}")
        
        
        
        steps.append({
            'label':  step['label'],
            'config': step['config'],
            'palette': step['palette'],
            'active': active_section,
            'reset': step.get('reset', False),
            'global': full['global'],
            'setup':  full['setup'],
            'loop':   full['loop'],
            'verify_global': verify_global,
            'verify_setup':  verify_setup,
            'verify_loop':   verify_loop,
        })

        # Update cumulative storage: convert resolved slots to real codeblocks for next steps
        def resolve_slots(arr):
            resolved = []
            for b in arr:
                if b['type'] == 'slot':
                    # Carry the master solution forward as a locked block
                    sol = b.get('master')
                    if sol:
                        sol['locked'] = True
                        resolved.append(sol)
                else:
                    resolved.append(b)
            return resolved

        if not step.get('aside'):
            cumulative_global += resolve_slots(parsed['global'])
            if parsed['setup']: cumulative_setup = resolve_slots(parsed['setup'])
            if parsed['loop']: cumulative_loop = resolve_slots(parsed['loop'])

    return steps
