import { describe, it, expect, beforeEach } from 'vitest';
import { loadFullStack } from './helpers/loadFullStack.js';

// block_builder.js's genBlocks/genBlock are pure codegen (only read
// BB.BLOCKS/BB.genCond, no DOM — plans/JS_TEST_SCOPING.md §2), but the
// *file itself* can only be loaded through the real bb-blocks -> bb-render
// -> bb-validation -> block_builder chain against real DOM, since its
// outer IIFE requires window.BB_CONFIG and unconditionally calls
// BB.render()/BB.genCode() at load time. loadFullStack() (backed by the
// real block_builder_fragment.html markup) handles that; the tests below
// only exercise the exported genBlocks/genBlock functions afterward.
let BB;
beforeEach(() => {
  BB = loadFullStack();
});

function digitalWrite(pin, value) {
  return { type: 'digitalwrite', params: [pin, value] };
}

describe('BB.genBlocks / BB.genBlock — plain statements', () => {
  it('generates a single digitalWrite statement with indentation', () => {
    expect(BB.genBlocks([digitalWrite('13', 'HIGH')], 1)).toBe('   digitalWrite(13, HIGH);');
  });

  it('joins multiple statements with newlines', () => {
    var code = BB.genBlocks([digitalWrite('13', 'HIGH'), { type: 'delay', params: ['1000'], exChildren: [] }], 1);
    expect(code).toBe('   digitalWrite(13, HIGH);\n   delay(1000);');
  });

  it('unwraps a slot before generating its content', () => {
    var slotBlock = { type: 'slot', content: digitalWrite('7', 'LOW') };
    expect(BB.genBlocks([slotBlock], 0)).toBe('digitalWrite(7, LOW);');
  });

  it('skips an unplaced slot (content === null) entirely', () => {
    var slotBlock = { type: 'slot', content: null };
    expect(BB.genBlocks([digitalWrite('2', 'HIGH'), slotBlock], 0)).toBe('digitalWrite(2, HIGH);');
  });
});

describe('BB.genBlocks / BB.genBlock — if/else-if/else with a real elsebody', () => {
  it('generates if + else, with no else-if branches', () => {
    var ifNode = {
      type: 'ifblock',
      condition: { left: 'x', op: '==', right: '1' },
      ifbody: [digitalWrite('2', 'HIGH')],
      elseifs: [],
      elsebody: { body: [digitalWrite('2', 'LOW')] },
    };
    var expected = [
      'if (x == 1) {',
      '   digitalWrite(2, HIGH);',
      '}',
      'else {',
      '   digitalWrite(2, LOW);',
      '}',
    ].join('\n');
    expect(BB.genBlock(ifNode, 0)).toBe(expected);
  });

  it('generates if + else-if + else together, in that order', () => {
    var ifNode = {
      type: 'ifblock',
      condition: { left: 'temp', op: '>', right: '80' },
      ifbody: [digitalWrite('9', 'HIGH')],
      elseifs: [
        { condition: { left: 'temp', op: '>', right: '50' }, body: [digitalWrite('9', 'LOW'), digitalWrite('10', 'HIGH')] },
      ],
      elsebody: { body: [digitalWrite('10', 'LOW')] },
    };
    var expected = [
      'if (temp > 80) {',
      '   digitalWrite(9, HIGH);',
      '}',
      'else if (temp > 50) {',
      '   digitalWrite(9, LOW);',
      '   digitalWrite(10, HIGH);',
      '}',
      'else {',
      '   digitalWrite(10, LOW);',
      '}',
    ].join('\n');
    expect(BB.genBlock(ifNode, 0)).toBe(expected);
  });

  it('omits the else branch entirely when elsebody is null', () => {
    var ifNode = {
      type: 'ifblock',
      condition: { left: 'x', op: '==', right: '1' },
      ifbody: [digitalWrite('2', 'HIGH')],
      elseifs: [],
      elsebody: null,
    };
    var expected = ['if (x == 1) {', '   digitalWrite(2, HIGH);', '}'].join('\n');
    expect(BB.genBlock(ifNode, 0)).toBe(expected);
  });

  it('generates multiple else-if branches in order before the final else', () => {
    var ifNode = {
      type: 'ifblock',
      condition: { left: 'a', op: '==', right: '1' },
      ifbody: [],
      elseifs: [
        { condition: { left: 'a', op: '==', right: '2' }, body: [digitalWrite('2', 'HIGH')] },
        { condition: { left: 'a', op: '==', right: '3' }, body: [digitalWrite('3', 'HIGH')] },
      ],
      elsebody: { body: [] },
    };
    var expected = [
      'if (a == 1) {',
      '',
      '}',
      'else if (a == 2) {',
      '   digitalWrite(2, HIGH);',
      '}',
      'else if (a == 3) {',
      '   digitalWrite(3, HIGH);',
      '}',
      'else {',
      '',
      '}',
    ].join('\n');
    expect(BB.genBlock(ifNode, 0)).toBe(expected);
  });

  it('applies correct nested indentation inside an elsebody', () => {
    var ifNode = {
      type: 'ifblock',
      condition: { left: 'x', op: '==', right: '1' },
      ifbody: [],
      elseifs: [],
      elsebody: { body: [digitalWrite('4', 'LOW')] },
    };
    var code = BB.genBlock(ifNode, 1);
    expect(code).toContain('   else {\n      digitalWrite(4, LOW);\n   }');
  });
});

describe('BB.genBlocks / BB.genBlock — for/while loops', () => {
  it('generates a for loop with defaults when forinit/forcond/forincr are blank', () => {
    var forNode = { type: 'forloop', forinit: '', forcond: '', forincr: '', body: [digitalWrite('2', 'HIGH')] };
    var expected = ['for (int i = 0; i < 10; i++) {', '   digitalWrite(2, HIGH);', '}'].join('\n');
    expect(BB.genBlock(forNode, 0)).toBe(expected);
  });

  it('generates a while loop from a structured condition', () => {
    var whileNode = { type: 'whileloop', condition: { left: 'x', op: '<', right: '10' }, body: [digitalWrite('2', 'HIGH')] };
    var expected = ['while (x < 10) {', '   digitalWrite(2, HIGH);', '}'].join('\n');
    expect(BB.genBlock(whileNode, 0)).toBe(expected);
  });
});

describe('BB.genBlocks — codeblock brace-tracking indentation', () => {
  it('dedents a lone closing brace and re-indents after an opening brace', () => {
    var arr = [
      { type: 'codeblock', params: ['for (int i = 0; i < 3; i++) {'] },
      { type: 'digitalwrite', params: ['2', 'HIGH'] },
      { type: 'codeblock', params: ['}'] },
    ];
    var code = BB.genBlocks(arr, 0);
    expect(code).toBe('for (int i = 0; i < 3; i++) {\n   digitalWrite(2, HIGH);\n}');
  });
});
