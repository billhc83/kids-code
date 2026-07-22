import { describe, it, expect, beforeEach } from 'vitest';
import { loadFullStack } from './helpers/loadFullStack.js';

// Real DOM interaction tier (plans/JS_TEST_SCOPING.md §2/§3 item 4): the
// "+ else if"/"+ else" button handlers inside bb-render.js's renderIfBlock()
// are exactly the click-driven logic that silently produced the wrong
// elsebody shape during the refactor described in
// plans/TEACHER_AUTHORING_LIVE_BUILDER_UI_SPEC.md §4 — hand-clicking was
// the only way that bug was ever caught. These tests drive the real
// buttons via dispatched click events against the real fragment markup and
// assert on both the BB.SECTIONS mutation and the re-rendered DOM.
let BB;
beforeEach(() => {
  BB = loadFullStack();
});

function click(el) {
  el.dispatchEvent(new window.MouseEvent('click', { bubbles: true }));
}

function actButton(container, text) {
  return Array.from(container.querySelectorAll('.act')).find(function (b) { return b.textContent === text; });
}

function pushBareIfBlock(id) {
  var node = {
    id: id,
    type: 'ifblock',
    condition: { left: '', op: '==', right: '', joiner: 'none', left2: '', op2: '==', right2: '' },
    ifbody: [],
    elseifs: [],
    elsebody: null,
  };
  BB.SECTIONS.loop.push(node);
  return node;
}

describe('renderIfBlock — "+ else if" / "+ else" buttons', () => {
  it('appends a well-formed elseif clause to block.elseifs and renders an elseif-header', () => {
    var node = pushBareIfBlock('if-1');
    BB.render();
    var wrap = document.querySelector('[data-id="if-1"]');
    expect(wrap).toBeTruthy();
    expect(wrap.querySelectorAll('.elseif-header').length).toBe(0);

    click(actButton(wrap.querySelector('.if-header'), '+ else if'));

    expect(node.elseifs.length).toBe(1);
    expect(node.elseifs[0].body).toEqual([]);
    expect(node.elseifs[0].condition).toMatchObject({ op: '==', joiner: 'none' });

    var wrapAfter = document.querySelector('[data-id="if-1"]');
    expect(wrapAfter.querySelectorAll('.elseif-header').length).toBe(1);
  });

  it('supports adding more than one elseif clause, each with its own independent body', () => {
    var node = pushBareIfBlock('if-2');
    BB.render();
    var hdr = document.querySelector('[data-id="if-2"] .if-header');
    click(actButton(hdr, '+ else if'));
    click(actButton(document.querySelector('[data-id="if-2"] .if-header'), '+ else if'));

    expect(node.elseifs.length).toBe(2);
    expect(node.elseifs[0]).not.toBe(node.elseifs[1]);
    expect(node.elseifs[0].body).not.toBe(node.elseifs[1].body);
    expect(document.querySelectorAll('[data-id="if-2"] .elseif-header').length).toBe(2);
  });

  it('sets elsebody to a real {body: []} object, not just a truthy placeholder, on "+ else"', () => {
    var node = pushBareIfBlock('if-3');
    BB.render();
    var hdr = document.querySelector('[data-id="if-3"] .if-header');
    click(actButton(hdr, '+ else'));

    expect(node.elsebody).not.toBeNull();
    expect(Array.isArray(node.elsebody.body)).toBe(true);
    expect(node.elsebody.body).toEqual([]);

    var wrapAfter = document.querySelector('[data-id="if-3"]');
    expect(wrapAfter.querySelectorAll('.else-header').length).toBe(1);
  });

  it('hides the "+ else" button once an else branch already exists (only one else allowed)', () => {
    var node = pushBareIfBlock('if-4');
    BB.render();
    click(actButton(document.querySelector('[data-id="if-4"] .if-header'), '+ else'));
    var hdrAfter = document.querySelector('[data-id="if-4"] .if-header');
    expect(actButton(hdrAfter, '+ else')).toBeUndefined();
  });

  it('removing the else branch (its "×" button) sets elsebody back to null and restores "+ else"', () => {
    var node = pushBareIfBlock('if-5');
    BB.render();
    click(actButton(document.querySelector('[data-id="if-5"] .if-header'), '+ else'));
    expect(node.elsebody).not.toBeNull();

    var elseHdr = document.querySelector('[data-id="if-5"] .else-header');
    click(actButton(elseHdr, '×'));

    expect(node.elsebody).toBeNull();
    var ifHdrAfter = document.querySelector('[data-id="if-5"] .if-header');
    expect(actButton(ifHdrAfter, '+ else')).toBeTruthy();
    expect(document.querySelectorAll('[data-id="if-5"] .else-header').length).toBe(0);
  });

  it('removing one elseif clause (its "×" button) splices only that clause out', () => {
    var node = pushBareIfBlock('if-6');
    BB.render();
    var hdr = document.querySelector('[data-id="if-6"] .if-header');
    click(actButton(hdr, '+ else if'));
    click(actButton(document.querySelector('[data-id="if-6"] .if-header'), '+ else if'));
    expect(node.elseifs.length).toBe(2);
    var keptClauseId = node.elseifs[1].id;

    var firstElseIfHeader = document.querySelectorAll('[data-id="if-6"] .elseif-header')[0];
    click(actButton(firstElseIfHeader, '×'));

    expect(node.elseifs.length).toBe(1);
    expect(node.elseifs[0].id).toBe(keptClauseId);
  });

  it('the elsebody added via "+ else" round-trips through BB.genBlock as a real else branch', () => {
    var node = pushBareIfBlock('if-7');
    node.condition.left = 'x';
    node.condition.right = '1';
    node.ifbody.push({ type: 'digitalwrite', params: ['2', 'HIGH'] });
    BB.render();
    click(actButton(document.querySelector('[data-id="if-7"] .if-header'), '+ else'));
    node.elsebody.body.push({ type: 'digitalwrite', params: ['2', 'LOW'] });

    var code = BB.genBlock(node, 0);
    expect(code).toBe(['if (x == 1) {', '   digitalWrite(2, HIGH);', '}', 'else {', '   digitalWrite(2, LOW);', '}'].join('\n'));
  });
});
