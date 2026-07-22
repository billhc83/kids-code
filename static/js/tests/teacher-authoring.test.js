import { describe, it, expect, beforeEach } from 'vitest';
import { loadTeacherAuthoringStack } from './helpers/loadTeacherAuthoringStack.js';

// Step-tabs shell + client-side StepDraft extraction
// (plans/TEACHER_AUTHORING_LIVE_BUILDER_UI_SPEC.md §5/§6, build order step 3).
// TA.STEPS holds each step's block tree in the live BB.SECTIONS shape;
// extraction into the {id, kind, flag, hint, ...} Node shape
// utils/teacher_authoring_serializer.py's materialize() consumes happens on
// Save via extractStepDraft() — these tests assert both sides: the shell's
// in-memory step management, and that extraction produces exactly the shape
// materialize_step() expects.

function plainLeaf(id, type, params) {
  return { id: id, type: type, flag: 'locked', hint: null, params: params, exChildren: params.map(function () { return undefined; }) };
}

function bareCond() {
  return { left: '', op: '==', right: '', joiner: 'none', left2: '', op2: '==', right2: '' };
}

let TA, BB;
beforeEach(() => {
  var stack = loadTeacherAuthoringStack();
  BB = stack.BB; TA = stack.TA;
});

describe('TA.init', () => {
  it('bootstraps a single blank step and renders it', () => {
    TA.init();
    expect(TA.STEPS.length).toBe(1);
    expect(TA.STEPS[0].label).toBe('Step 1');
    expect(TA.STEPS[0].guidance).toBe('guided');
    expect(document.querySelectorAll('#ta-tabs .ta-tab').length).toBe(2); // "1. Step 1" + "+ Add Step"
    expect(document.querySelector('#ta-tabs .ta-tab.active').textContent).toBe('1. Step 1');
  });
});

describe('extractStepDraft — leaf nodes', () => {
  it('extracts a plain action block into {id, kind: leaf, flag, hint, line}', () => {
    var node = TA.extractNode(plainLeaf('a1', 'digitalwrite', ['13', 'HIGH']));
    expect(node).toEqual({ id: 'a1', kind: 'leaf', flag: 'locked', hint: null, line: 'digitalWrite(13, HIGH);' });
  });

  it('extracts a phantom leaf with its hint carried through', () => {
    TA.init();
    var leaf = plainLeaf('a2', 'digitalwrite', ['13', 'HIGH']);
    leaf.flag = 'phantom'; leaf.hint = 'Turn the LED on';
    var node = TA.extractNode(leaf);
    expect(node).toEqual({ id: 'a2', kind: 'leaf', flag: 'phantom', hint: 'Turn the LED on', line: 'digitalWrite(13, HIGH);' });
  });

  it('extracts a codeblock leaf using its raw text as the line', () => {
    var node = TA.extractNode({ id: 'cb1', type: 'codeblock', flag: 'locked', hint: null, params: ['int x = 5;'] });
    expect(node).toEqual({ id: 'cb1', kind: 'leaf', flag: 'locked', hint: null, line: 'int x = 5;' });
  });
});

describe('extractStepDraft — compound nodes', () => {
  it('extracts an ifblock with an elseif and an else into the CompoundNode shape', () => {
    var node = {
      id: 'if-1', type: 'ifblock', flag: 'locked', hint: null,
      condition: { left: 'x', op: '==', right: '1', joiner: 'none', left2: '', op2: '==', right2: '' },
      ifbody: [plainLeaf('a3', 'digitalwrite', ['13', 'HIGH'])],
      elseifs: [{ id: 'ei-1', flag: 'phantom', hint: 'add the elseif condition', condition: bareCond(), body: [] }],
      elsebody: { id: 'el-1', flag: 'locked', hint: null, body: [plainLeaf('a4', 'digitalwrite', ['13', 'LOW'])] },
    };
    var extracted = TA.extractNode(node);
    expect(extracted).toEqual({
      id: 'if-1', kind: 'compound', compound_type: 'ifblock', flag: 'locked', hint: null,
      header: 'x == 1',
      body: [{ id: 'a3', kind: 'leaf', flag: 'locked', hint: null, line: 'digitalWrite(13, HIGH);' }],
      elseifs: [{ id: 'ei-1', header: 'x == 0', flag: 'phantom', hint: 'add the elseif condition', body: [] }],
      elsebody: { id: 'el-1', flag: 'locked', hint: null, body: [{ id: 'a4', kind: 'leaf', flag: 'locked', hint: null, line: 'digitalWrite(13, LOW);' }] },
    });
  });

  it('extracts a forloop header as semicolon-joined init/cond/incr', () => {
    var node = { id: 'for-1', type: 'forloop', flag: 'locked', hint: null, forinit: 'int i = 0', forcond: 'i < 10', forincr: 'i++', body: [] };
    var extracted = TA.extractNode(node);
    expect(extracted.compound_type).toBe('forloop');
    expect(extracted.header).toBe('int i = 0; i < 10; i++');
    expect(extracted.elseifs).toEqual([]);
    expect(extracted.elsebody).toBeNull();
  });

  it('extracts a whileloop header from its condition', () => {
    var cond = bareCond(); cond.op = '!=';
    var node = { id: 'while-1', type: 'whileloop', flag: 'locked', hint: null, condition: cond, body: [] };
    var extracted = TA.extractNode(node);
    expect(extracted.compound_type).toBe('whileloop');
    expect(extracted.header).toBe('x != 0'); // bareCond() defaults left/right to fallback 'x'/'0' via BB.genCond
  });
});

describe('extractStepDraft — step-level shape', () => {
  it('non-open steps get {label, guidance, view, global, setup, loop} with no read_only key at the default', () => {
    var step = { label: 'Turn it on', guidance: 'guided', view: 'blocks', read_only: null, sections: { global: [], setup: [], loop: [] } };
    var draft = TA.extractStepDraft(step);
    expect(draft).toEqual({ label: 'Turn it on', guidance: 'guided', view: 'blocks', global: [], setup: [], loop: [] });
  });

  it('includes read_only only when it differs from the guidance default', () => {
    var stepDefault = { label: 'S', guidance: 'guided', view: 'blocks', read_only: true, sections: { global: [], setup: [], loop: [] } };
    expect(TA.extractStepDraft(stepDefault).read_only).toBeUndefined();

    var stepOverride = { label: 'S', guidance: 'guided', view: 'blocks', read_only: false, sections: { global: [], setup: [], loop: [] } };
    expect(TA.extractStepDraft(stepOverride).read_only).toBe(false);
  });

  it('open steps get {label, guidance: open, view, raw} with no global/setup/loop keys', () => {
    var step = { label: 'Aside', guidance: 'open', view: 'blocks', read_only: null, sections: { global: [], setup: [], loop: [] }, raw: '// free-form notes' };
    var draft = TA.extractStepDraft(step);
    expect(draft).toEqual({ label: 'Aside', guidance: 'open', view: 'blocks', raw: '// free-form notes' });
  });
});

describe('step-tabs shell — switching and adding', () => {
  it('addStep() carries forward the previous step\'s accumulated tree with the same ids', () => {
    TA.init();
    BB.SECTIONS.global.push(plainLeaf('g1', 'intvar', ['ledPin', '13']));
    BB.SECTIONS.setup.push(plainLeaf('s1', 'pinmode', ['13', 'OUTPUT']));
    TA.addStep();
    expect(TA.STEPS.length).toBe(2);
    expect(TA.STEPS[1].sections.global).toEqual(TA.STEPS[0].sections.global);
    expect(TA.STEPS[1].sections.setup).toEqual(TA.STEPS[0].sections.setup);
    // Same object *content* (deep-equal ids), but not the same reference —
    // later mutation of one step must never leak into another step's tree.
    expect(TA.STEPS[1].sections.global).not.toBe(TA.STEPS[0].sections.global);
  });

  it('carried-forward blocks render as forced-locked ("already introduced") in the new step, via BB.AUTHORING_SEEN_IDS', () => {
    TA.init();
    BB.SECTIONS.setup.push(plainLeaf('s2', 'pinmode', ['13', 'OUTPUT']));
    TA.addStep(); // now on step 2, s2 carried forward and already "seen"
    var toggle = document.querySelector('[data-id="s2"] .authoring-toggle-forced');
    expect(toggle).toBeTruthy();
    expect(toggle.textContent).toContain('already introduced');
  });

  it('a freshly-added block in the new step is not forced-locked (its id was never seen before)', () => {
    TA.init();
    TA.addStep();
    BB.SECTIONS.loop.push(plainLeaf('new1', 'digitalwrite', ['13', 'HIGH']));
    BB.render();
    var wrap = document.querySelector('[data-id="new1"]');
    expect(wrap.querySelectorAll('.authoring-toggle-forced').length).toBe(0);
    expect(wrap.querySelectorAll('.authoring-toggle').length).toBe(1);
  });

  it('switchToStep() round-trips edits: leaving a step preserves it, returning restores it', () => {
    TA.init();
    BB.SECTIONS.loop.push(plainLeaf('r1', 'digitalwrite', ['13', 'HIGH']));
    TA.addStep(); // step 2, carries r1 forward
    BB.SECTIONS.loop.push(plainLeaf('r2', 'digitalwrite', ['12', 'LOW']));
    TA.switchToStep(0);
    expect(BB.SECTIONS.loop.map(function (b) { return b.id; })).toEqual(['r1']);

    TA.switchToStep(1);
    expect(BB.SECTIONS.loop.map(function (b) { return b.id; })).toEqual(['r1', 'r2']);
  });

  it('open-guidance steps hide the block workspace and show the raw textarea, round-tripping .raw', () => {
    TA.init();
    var sel = document.getElementById('ta-settings').querySelectorAll('select')[0];
    // First select is guidance in renderSettingsPanel's field order.
    sel.value = 'open';
    sel.dispatchEvent(new window.Event('change', { bubbles: true }));

    expect(document.getElementById('block-builder-ui').style.display).toBe('none');
    var rawEl = document.getElementById('ta-open-raw');
    expect(rawEl.style.display).toBe('');

    rawEl.value = 'free-form aside text';
    rawEl.dispatchEvent(new window.Event('input', { bubbles: true }));

    TA.addStep();
    TA.switchToStep(0);
    expect(document.getElementById('ta-open-raw').value).toBe('free-form aside text');
  });
});

describe('TA.init — hydrating an existing draft (build order step 4)', () => {
  // window.BB_CONFIG.initial_steps mirrors
  // utils/teacher_authoring_serializer.py's hydrate_steps() output exactly —
  // TA.init() should adopt it directly instead of bootstrapping a blank
  // Step 1, the reverse of the extraction path covered above.
  function initialSteps() {
    return [
      {
        label: 'Turn it on', guidance: 'guided', view: 'blocks', read_only: null, raw: '',
        sections: {
          global: [],
          setup: [plainLeaf('s1', 'pinmode', ['13', 'OUTPUT'])],
          loop: [{ id: 'l1', type: 'digitalwrite', params: ['13', 'HIGH'], flag: 'phantom', hint: 'Turn it on' }],
        },
      },
      {
        label: 'Turn it off', guidance: 'guided', view: 'blocks', read_only: null, raw: '',
        sections: {
          global: [],
          setup: [plainLeaf('s1', 'pinmode', ['13', 'OUTPUT'])],
          loop: [
            { id: 'l1', type: 'digitalwrite', params: ['13', 'HIGH'], flag: 'locked', hint: null },
            { id: 'l2', type: 'digitalwrite', params: ['13', 'LOW'], flag: 'phantom', hint: 'Turn it off' },
          ],
        },
      },
    ];
  }

  it('bootstraps TA.STEPS from BB_CONFIG.initial_steps instead of a blank Step 1', () => {
    var stack = loadTeacherAuthoringStack({ initial_steps: initialSteps() });
    stack.TA.init();
    expect(stack.TA.STEPS.length).toBe(2);
    expect(stack.TA.STEPS[0].label).toBe('Turn it on');
    expect(stack.TA.STEPS[1].label).toBe('Turn it off');
    expect(document.querySelectorAll('#ta-tabs .ta-tab').length).toBe(3); // 2 steps + "+ Add Step"
  });

  it('loads step 0\'s hydrated blocks into BB.SECTIONS on init', () => {
    var stack = loadTeacherAuthoringStack({ initial_steps: initialSteps() });
    stack.TA.init();
    expect(stack.BB.SECTIONS.setup.map(function (b) { return b.id; })).toEqual(['s1']);
    expect(stack.BB.SECTIONS.loop[0]).toMatchObject({ id: 'l1', type: 'digitalwrite', flag: 'phantom', hint: 'Turn it on' });
  });

  it('a block carried into step 2 with the same id renders forced-locked, same as a freshly-authored carry-forward', () => {
    var stack = loadTeacherAuthoringStack({ initial_steps: initialSteps() });
    stack.TA.init();
    stack.TA.switchToStep(1);
    var toggle = document.querySelector('[data-id="l1"] .authoring-toggle-forced');
    expect(toggle).toBeTruthy();
  });

  it('extracting a hydrated step round-trips id/flag/hint back out unchanged', () => {
    var stack = loadTeacherAuthoringStack({ initial_steps: initialSteps() });
    stack.TA.init();
    var draft = stack.TA.extractStepDraft(stack.TA.STEPS[0]);
    expect(draft.loop).toEqual([{ id: 'l1', kind: 'leaf', flag: 'phantom', hint: 'Turn it on', line: 'digitalWrite(13, HIGH);' }]);
  });

  it('falls back to a blank Step 1 when initial_steps is absent', () => {
    var stack = loadTeacherAuthoringStack();
    stack.TA.init();
    expect(stack.TA.STEPS.length).toBe(1);
    expect(stack.TA.STEPS[0].label).toBe('Step 1');
  });
});

describe('TA.buildAllStepDrafts', () => {
  it('serializes every step including the currently-active one (not yet explicitly saved)', () => {
    TA.init();
    BB.SECTIONS.loop.push(plainLeaf('b1', 'digitalwrite', ['13', 'HIGH']));
    var drafts = TA.buildAllStepDrafts();
    expect(drafts.length).toBe(1);
    expect(drafts[0].loop).toEqual([{ id: 'b1', kind: 'leaf', flag: 'locked', hint: null, line: 'digitalWrite(13, HIGH);' }]);
  });

  it('populates the hidden #ta-steps-json input on form submit', () => {
    TA.init();
    BB.SECTIONS.loop.push(plainLeaf('b2', 'digitalwrite', ['13', 'HIGH']));
    document.getElementById('ta-form').dispatchEvent(new window.Event('submit', { bubbles: true, cancelable: true }));
    var hidden = document.getElementById('ta-steps-json');
    var parsed = JSON.parse(hidden.value);
    expect(parsed.length).toBe(1);
    expect(parsed[0].loop[0].id).toBe('b2');
  });
});
