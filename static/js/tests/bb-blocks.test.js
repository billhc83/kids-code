import { describe, it, expect, beforeEach } from 'vitest';
import { loadScript } from './helpers/loadScript.js';

// bb-blocks.js is fully DOM-free (confirmed by grep — no `document.*` calls
// anywhere in the file, see plans/JS_TEST_SCOPING.md §2), so no fixture DOM
// or BB_CONFIG stub is needed here — just load it and call its functions.
let BB;
beforeEach(() => {
  delete window._BB;
  loadScript('bb-blocks.js');
  BB = window._BB;
});

describe('BB.genExpr (via BB.makeExNode + BB.BLOCKS[type].genExpr)', () => {
  it('falls back to the literal param when the exNode has no type', () => {
    expect(BB.genExpr(null, '42', '0')).toBe('42');
    expect(BB.genExpr(undefined, '', '0')).toBe('0');
  });

  it('generates a value expr verbatim', () => {
    var node = { type: 'value', params: ['7'], children: [] };
    expect(BB.genExpr(node)).toBe('7');
  });

  it('generates a nested math expr recursively', () => {
    // math is the one variadic block — its operands live in terms/ops on the
    // exNode itself, not the generic params/children arrays (see BB.makeExNode).
    var node = { type: 'math', terms: ['1', 'analogRead(A0)'], ops: ['+'] };
    expect(BB.genExpr(node)).toBe('(1 + analogRead(A0))');
  });

  it('generates analogRead/digitalRead/millis/micros', () => {
    expect(BB.genExpr({ type: 'analogread', params: ['A2'], children: [] })).toBe('analogRead(A2)');
    expect(BB.genExpr({ type: 'digitalread', params: ['7'], children: [] })).toBe('digitalRead(7)');
    expect(BB.genExpr({ type: 'millis', params: [], children: [] })).toBe('millis()');
    expect(BB.genExpr({ type: 'micros', params: [], children: [] })).toBe('micros()');
  });

  it('returns the string fallback when a block type is unknown', () => {
    expect(BB.genExpr({ type: 'not_a_real_block', params: [], children: [] }, 'x', 'y')).toBe('x');
  });
});

describe('BB.makeExNode', () => {
  it('returns null for a block type that is not an expression', () => {
    expect(BB.makeExNode('pinmode')).toBeNull();
    expect(BB.makeExNode('nonexistent')).toBeNull();
  });

  it('builds a default exNode for the variadic math block', () => {
    var node = BB.makeExNode('math');
    expect(node.type).toBe('math');
    // math is variadic — its default shape is terms/ops, not the generic params/children.
    expect(node.terms).toEqual(['0', '0']);
    expect(node.ops).toEqual(['+']);
  });

  it('builds a default exNode for a no-input expr block (millis)', () => {
    var node = BB.makeExNode('millis');
    expect(node.type).toBe('millis');
    expect(node.params).toEqual([]);
    expect(node.children).toEqual([]);
  });

  it('defaults a vartext input to "0"', () => {
    var node = BB.makeExNode('servoread');
    expect(node.params).toEqual(['0']);
  });
});

describe('BB.genCond', () => {
  it('generates a simple condition with defaults when fields are missing', () => {
    expect(BB.genCond({})).toBe('x == 0');
  });

  it('generates a simple condition from plain left/right/op strings', () => {
    expect(BB.genCond({ left: 'val', op: '>', right: '100' })).toBe('val > 100');
  });

  it('ignores legacy leftExpr/rightExpr fields and always reads left/right', () => {
    // Pre-block-expression-slot-simplification saves may still carry the old
    // tree-shaped leftExpr/rightExpr fields alongside the current flat ones —
    // genCond must not fall back to them (see BB._savedStateIsStale, which is
    // what's responsible for discarding saves shaped like this).
    var cond = {
      left: 'analogRead(A0)',
      leftExpr: { type: 'analogread', params: ['A0'], children: [] },
      op: '<',
      right: '512',
      rightExpr: { type: 'value', params: ['512'], children: [] },
    };
    expect(BB.genCond(cond)).toBe('analogRead(A0) < 512');
  });

  it('joins a second clause with && for joiner "and"', () => {
    var cond = { left: 'a', op: '==', right: '1', joiner: 'and', left2: 'b', op2: '==', right2: '2' };
    expect(BB.genCond(cond)).toBe('a == 1 && b == 2');
  });

  it('joins a second clause with || for joiner "or"', () => {
    var cond = { left: 'a', op: '==', right: '1', joiner: 'or', left2: 'b', op2: '!=', right2: '2' };
    expect(BB.genCond(cond)).toBe('a == 1 || b != 2');
  });

  it('omits the second clause entirely when joiner is "none"', () => {
    var cond = { left: 'a', op: '==', right: '1', joiner: 'none', left2: 'b', op2: '==', right2: '2' };
    expect(BB.genCond(cond)).toBe('a == 1');
  });

  it('omits the second clause when left2 defaults to the unset placeholder "x"', () => {
    // genCond's own guard: `if (left2 !== 'x')` — an unset left2 (no left2,
    // no leftExpr2) resolves to the literal string 'x' and must not be
    // appended, even when joiner is set.
    var cond = { left: 'a', op: '==', right: '1', joiner: 'and' };
    expect(BB.genCond(cond)).toBe('a == 1');
  });
});

describe('BB.getOptions', () => {
  it('returns the base digital pin list plus any declared globals named as intvars', () => {
    BB.SECTIONS.global.push({ type: 'intvar', params: ['buzzerPin', '9'] });
    var opts = BB.getOptions('DIGITAL_PIN_OPTIONS');
    expect(opts).toContain('9');
    expect(opts).toContain('buzzerPin');
    expect(opts.indexOf('buzzerPin')).toBe(opts.length - 1);
  });

  it('does not duplicate a global name already present in the base list', () => {
    // Base digital pins are string numerals ('0'..'13'); a global literally
    // named '7' should not be appended twice.
    BB.SECTIONS.global.push({ type: 'intvar', params: ['7', '0'] });
    var opts = BB.getOptions('DIGITAL_PIN_OPTIONS');
    expect(opts.filter(function (o) { return o === '7'; }).length).toBe(1);
  });

  it('returns an empty array for an unrecognized option key', () => {
    expect(BB.getOptions('NOT_A_KEY')).toEqual([]);
  });

  it('returns the analog pins for ANALOG_PIN_OPTIONS and PWM pins for PWM_PIN_OPTIONS', () => {
    expect(BB.getOptions('ANALOG_PIN_OPTIONS')).toEqual(['A0', 'A1', 'A2', 'A3', 'A4', 'A5']);
    expect(BB.getOptions('PWM_PIN_OPTIONS')).toEqual(['3', '5', '6', '9', '10', '11']);
  });
});

describe('BB.getVarSuggestions', () => {
  it('collects intvar/longvar/stringvar names from all three top-level sections', () => {
    BB.SECTIONS.global.push({ type: 'intvar', params: ['ledPin'] });
    BB.SECTIONS.setup.push({ type: 'longvar', params: ['startTime'] });
    BB.SECTIONS.loop.push({ type: 'stringvar', params: ['msg'] });
    expect(BB.getVarSuggestions()).toEqual(['ledPin', 'startTime', 'msg']);
  });

  it('de-duplicates repeated names, keeping first-seen order', () => {
    BB.SECTIONS.global.push({ type: 'intvar', params: ['x'] });
    BB.SECTIONS.loop.push({ type: 'intvar', params: ['x'] });
    expect(BB.getVarSuggestions()).toEqual(['x']);
  });

  it('walks into an ifblock body, elseifs, and elsebody to find nested var declarations', () => {
    BB.SECTIONS.loop.push({
      type: 'ifblock',
      condition: {},
      ifbody: [{ type: 'intvar', params: ['ifVar'] }],
      elseifs: [{ condition: {}, body: [{ type: 'intvar', params: ['elseIfVar'] }] }],
      elsebody: { body: [{ type: 'intvar', params: ['elseVar'] }] },
    });
    var vars = BB.getVarSuggestions();
    expect(vars).toEqual(['ifVar', 'elseIfVar', 'elseVar']);
  });

  it('does not crash when elsebody is null (no else branch present)', () => {
    BB.SECTIONS.loop.push({
      type: 'ifblock',
      condition: {},
      ifbody: [{ type: 'intvar', params: ['onlyIfVar'] }],
      elseifs: [],
      elsebody: null,
    });
    expect(BB.getVarSuggestions()).toEqual(['onlyIfVar']);
  });

  it('extracts a var name declared inside a locked codeblock line', () => {
    BB.SECTIONS.global.push({ type: 'codeblock', params: ['int hiddenVar = 0;'] });
    expect(BB.getVarSuggestions()).toContain('hiddenVar');
  });
});

describe('BB.getConditionSuggestions', () => {
  it('suggests digitalRead(pin) for an INPUT/INPUT_PULLUP pinmode', () => {
    BB.SECTIONS.setup.push({ type: 'pinmode', params: ['2', 'INPUT_PULLUP'] });
    expect(BB.getConditionSuggestions()).toContain('digitalRead(2)');
  });

  it('does not suggest digitalRead for an OUTPUT pinmode', () => {
    BB.SECTIONS.setup.push({ type: 'pinmode', params: ['2', 'OUTPUT'] });
    expect(BB.getConditionSuggestions()).not.toContain('digitalRead(2)');
  });

  it('suggests analogRead(pin) and the assigned variable name', () => {
    BB.SECTIONS.loop.push({ type: 'analogread', params: ['A0', 'lightLevel'] });
    var suggestions = BB.getConditionSuggestions();
    expect(suggestions).toContain('analogRead(A0)');
    expect(suggestions).toContain('lightLevel');
  });

  it('always includes HIGH and LOW', () => {
    var suggestions = BB.getConditionSuggestions();
    expect(suggestions).toContain('HIGH');
    expect(suggestions).toContain('LOW');
  });
});

describe('BB.getPinSuggestions', () => {
  it('lists declared global intvars before the base pin options, de-duplicated', () => {
    BB.SECTIONS.global.push({ type: 'intvar', params: ['ledPin', '13'] });
    var suggestions = BB.getPinSuggestions('DIGITAL_PIN_OPTIONS');
    expect(suggestions[0]).toBe('ledPin');
    expect(suggestions).toContain('13');
    expect(suggestions.filter(function (s) { return s === '13'; }).length).toBe(1);
  });

  it('defaults to DIGITAL_PIN_OPTIONS when no option key is given', () => {
    var suggestions = BB.getPinSuggestions();
    expect(suggestions).toContain('A0');
  });
});
