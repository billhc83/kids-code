import { describe, it, expect, beforeEach } from 'vitest';
import { loadScript } from './helpers/loadScript.js';

// bb-validation.js declares `var BB = window._BB;` at module scope, so
// bb-blocks.js must be loaded first (its header comment says the same).
// The functions under test here — countPhantoms/countIncomplete/
// compareExpr/compareCondition/collectBadIds/checkSketchFields — are all
// pure over BB.SECTIONS/block-tree data per plans/JS_TEST_SCOPING.md §2;
// none of them touch `document`.
let BB;
beforeEach(() => {
  delete window._BB;
  loadScript('bb-blocks.js');
  loadScript('bb-validation.js');
  BB = window._BB;
});

// A slot always wraps a `content` block (or null when unplaced) plus a
// `phantom_meta` describing what's expected — matching the shape
// utils/block_parser.py's `_make_slot()` produces (see elsebody trace in
// plans/TEACHER_AUTHORING_LIVE_BUILDER_UI_SPEC.md §4).
function slot(content, phantomMeta) {
  return { type: 'slot', id: 'slot-' + Math.random(), content: content, phantom_meta: phantomMeta };
}

function digitalWriteBlock(pin, value) {
  return { type: 'digitalwrite', id: 'dw-' + pin + '-' + value, params: [pin, value] };
}

// An if/elseif/else tree with a real elsebody — the exact shape the
// elsebody refactor touched (ifblock.elsebody = {body: [...]} | null).
function ifWithElseTree({ ifbody = [], elseifs = [], elsebody = null } = {}) {
  return {
    type: 'ifblock',
    id: 'if-1',
    condition: { left: 'x', op: '==', right: '1' },
    ifbody: ifbody,
    elseifs: elseifs,
    elsebody: elsebody,
  };
}

describe('BB.countPhantoms', () => {
  it('counts unplaced (content === null) slots at the top level', () => {
    var arr = [slot(null, {}), slot(digitalWriteBlock('2', 'HIGH'), {})];
    expect(BB.countPhantoms(arr)).toBe(1);
  });

  it('recurses into an ifblock elsebody to find phantoms', () => {
    var tree = ifWithElseTree({
      ifbody: [slot(digitalWriteBlock('2', 'HIGH'), {})],
      elsebody: { body: [slot(null, {})] },
    });
    expect(BB.countPhantoms([tree])).toBe(1);
  });

  it('does not crash and counts zero when elsebody is null', () => {
    var tree = ifWithElseTree({ ifbody: [slot(null, {})], elsebody: null });
    expect(BB.countPhantoms([tree])).toBe(1);
  });

  it('recurses into a slot whose content is an ifblock with an elsebody', () => {
    var ifNode = ifWithElseTree({ elsebody: { body: [slot(null, {})] } });
    var arr = [slot(ifNode, { expects: 'ifblock' })];
    expect(BB.countPhantoms(arr)).toBe(1);
  });

  it('counts phantoms across ifbody, every elseif, and elsebody together', () => {
    var tree = ifWithElseTree({
      ifbody: [slot(null, {})],
      elseifs: [{ condition: {}, body: [slot(null, {})] }],
      elsebody: { body: [slot(null, {}), slot(null, {})] },
    });
    expect(BB.countPhantoms([tree])).toBe(4);
  });
});

describe('BB.countIncomplete', () => {
  it('returns 0 for a fully-filled digitalwrite block', () => {
    expect(BB.countIncomplete([digitalWriteBlock('2', 'HIGH')])).toBe(0);
  });

  it('counts a missing required param', () => {
    expect(BB.countIncomplete([{ type: 'digitalwrite', params: ['', 'HIGH'] }])).toBe(1);
  });

  it('does not count a missing tone duration (documented optional field)', () => {
    // tone's Pin and Freq are both vartext (checked via params[j]); only
    // Duration (index 2) is exempted from the incomplete count.
    var toneBlock = { type: 'tone', params: ['9', '440', ''] };
    expect(BB.countIncomplete([toneBlock])).toBe(0);
  });

  it('counts an ifblock missing its condition sides, plus recurses into elsebody', () => {
    var tree = ifWithElseTree({
      ifbody: [],
      elsebody: { body: [{ type: 'digitalwrite', params: ['', 'HIGH'] }] },
    });
    tree.condition = { left: '', right: '', joiner: 'none' };
    // 2 for the missing condition sides + 1 for the incomplete elsebody block
    expect(BB.countIncomplete([tree])).toBe(3);
  });

  it('skips a slot whose content is null (nothing to validate yet)', () => {
    expect(BB.countIncomplete([slot(null, {})])).toBe(0);
  });

  it('validates the placed content of a slot, unwrapping it first', () => {
    expect(BB.countIncomplete([slot({ type: 'digitalwrite', params: ['', 'HIGH'] }, {})])).toBe(1);
  });
});

describe('BB.compareExpr', () => {
  it('treats two absent expressions as equal', () => {
    expect(BB.compareExpr(null, undefined)).toBe(true);
  });

  it('is false when only one side is present', () => {
    expect(BB.compareExpr({ type: 'value', params: ['1'], children: [] }, null)).toBe(false);
  });

  it('compares value exprs by trimmed param text', () => {
    var a = { type: 'value', params: [' 5 '], children: [] };
    var b = { type: 'value', params: ['5'], children: [] };
    expect(BB.compareExpr(a, b)).toBe(true);
  });

  it('recurses into terms for the variadic math expr', () => {
    var a = { type: 'math', terms: ['1', '2'], ops: ['+'] };
    var b = { type: 'math', terms: ['1', '9'], ops: ['+'] };
    expect(BB.compareExpr(a, b)).toBe(false);
  });
});

describe('BB.compareCondition', () => {
  it('compares op, both sides, and joiner', () => {
    var mk = function (op) { return { op: op, left: '', right: '', joiner: 'none' }; };
    expect(BB.compareCondition(mk('=='), mk('=='))).toBe(true);
    expect(BB.compareCondition(mk('=='), mk('!='))).toBe(false);
  });

  it('also compares the second clause when joiner is not none', () => {
    var a = { op: '==', left: '', right: '', joiner: 'and', op2: '==', left2: '', right2: '' };
    var b = { op: '==', left: '', right: '', joiner: 'and', op2: '!=', left2: '', right2: '' };
    expect(BB.compareCondition(a, b)).toBe(false);
  });
});

describe('BB.collectBadIds', () => {
  it('flags a top-level slot as "Missing block" when the target expects one but the student left it empty', () => {
    var uList = [slot(null, {})];
    var tList = [slot(null, { expects: 'digitalwrite', params: ['2', 'HIGH'] }, )];
    // give tList[0] an id to check against
    tList[0].id = 'target-slot-1';
    var badIds = [];
    BB.collectBadIds(uList, tList, 2, badIds);
    expect(badIds).toEqual([{ id: 'target-slot-1', hint: 'Missing block' }]);
  });

  it('recurses into an elsebody slot mismatch and reports the bad inner block id', () => {
    var studentElseDW = digitalWriteBlock('3', 'LOW');
    studentElseDW.id = 'student-else-dw';
    var uTree = ifWithElseTree({
      ifbody: [],
      elsebody: { body: [slot(studentElseDW, {})] },
    });
    uTree.condition = { op: '==', left: '', right: '', joiner: 'none' };

    var targetElseSlot = slot(null, {
      expects: 'digitalwrite',
      params: ['3', 'HIGH'], // target wants HIGH, student placed LOW
    });
    var tTree = ifWithElseTree({
      ifbody: [],
      elsebody: { body: [targetElseSlot] },
    });
    tTree.condition = uTree.condition;
    var uSlot = slot(uTree, { expects: 'ifblock', ifbody: [], elseifs: [], elsebody: tTree.elsebody, params: [] });
    var tSlot = slot(null, { expects: 'ifblock', ifbody: [], elseifs: [], elsebody: tTree.elsebody, params: [] });
    tSlot.master = tTree;
    tSlot.id = 'target-if-slot';

    var badIds = [];
    BB.collectBadIds([uSlot], [tSlot], 2, badIds);
    // The outer if slot itself compares OK (compareBlock only checks
    // params/condition/forinit, not nested bodies), but the recursive
    // descent into elsebody must still find the mismatched inner block.
    var innerHit = badIds.find(function (b) { return b.id === 'student-else-dw'; });
    expect(innerHit).toBeDefined();
  });

  it('does nothing when either list is missing', () => {
    var badIds = [];
    BB.collectBadIds(null, [slot(null, {})], 2, badIds);
    BB.collectBadIds([slot(null, {})], null, 2, badIds);
    expect(badIds).toEqual([]);
  });
});

describe('BB.checkSketchFields', () => {
  it('flags a block whose required param the student left blank', () => {
    var uList = [{ type: 'digitalwrite', id: 'u1', params: ['', 'HIGH'] }];
    var mList = [{ type: 'digitalwrite', id: 'm1', params: ['2', 'HIGH'] }];
    var badIds = [];
    BB.checkSketchFields(uList, mList, badIds, [], 'loop');
    expect(badIds).toEqual([{ id: 'u1', section: 'loop', path: [0], hint: 'Fill in all the fields for this block' }]);
  });

  it('does not flag a block whose type differs from the master (out of scope for this check)', () => {
    var uList = [{ type: 'delay', id: 'u1', params: [''] }];
    var mList = [{ type: 'digitalwrite', id: 'm1', params: ['2', 'HIGH'] }];
    var badIds = [];
    BB.checkSketchFields(uList, mList, badIds, [], 'loop');
    expect(badIds).toEqual([]);
  });

  it('recurses into elsebody using ((ub.elsebody && ub.elsebody.body) || []) when the student has no else branch yet', () => {
    var mTree = ifWithElseTree({
      elsebody: { body: [{ type: 'digitalwrite', id: 'm-else', params: ['2', 'HIGH'] }] },
    });
    var uTree = ifWithElseTree({ elsebody: null }); // student hasn't added an else branch at all
    uTree.id = 'u-if';
    mTree.id = 'm-if';
    var badIds = [];
    // Must not throw despite ub.elsebody being null while mb.elsebody exists.
    expect(function () {
      BB.checkSketchFields([uTree], [mTree], badIds, [], 'loop');
    }).not.toThrow();
  });

  it('recurses into a present elsebody and flags a blank field inside it', () => {
    var mTree = ifWithElseTree({
      elsebody: { body: [{ type: 'digitalwrite', id: 'm-else', params: ['2', 'HIGH'] }] },
    });
    var uTree = ifWithElseTree({
      elsebody: { body: [{ type: 'digitalwrite', id: 'u-else', params: ['', 'HIGH'] }] },
    });
    uTree.id = 'u-if'; mTree.id = 'm-if';
    var badIds = [];
    BB.checkSketchFields([uTree], [mTree], badIds, [], 'loop');
    var hit = badIds.find(function (b) { return b.id === 'u-else'; });
    expect(hit).toBeDefined();
    expect(hit.path).toEqual([0, 'elsebody', 'body', 0]);
  });

  it('recurses into every elseif branch by index', () => {
    var mTree = ifWithElseTree({
      elseifs: [{ condition: {}, body: [{ type: 'digitalwrite', id: 'm-ei', params: ['4', 'HIGH'] }] }],
    });
    var uTree = ifWithElseTree({
      elseifs: [{ condition: {}, body: [{ type: 'digitalwrite', id: 'u-ei', params: ['', 'HIGH'] }] }],
    });
    uTree.id = 'u-if'; mTree.id = 'm-if';
    var badIds = [];
    BB.checkSketchFields([uTree], [mTree], badIds, [], 'loop');
    var hit = badIds.find(function (b) { return b.id === 'u-ei'; });
    expect(hit).toBeDefined();
    expect(hit.path).toEqual([0, 'elseifs', 0, 'body', 0]);
  });
});
