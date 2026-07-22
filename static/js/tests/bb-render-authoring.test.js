import { describe, it, expect, beforeEach } from 'vitest';
import { loadFullStack } from './helpers/loadFullStack.js';
import { installBlockBuilderFixture } from './helpers/domFixture.js';
import { loadScript } from './helpers/loadScript.js';

// Teacher-authoring toggle (plans/TEACHER_AUTHORING_LIVE_BUILDER_UI_SPEC.md
// §2, build order step 2): every renderable block gets a phantom/locked
// toggle when BB.AUTHORING_MODE is on, and nothing changes when it's off
// (students never see this — it's off by default and only flipped on for
// the teacher-authoring workspace).

function click(el) {
  el.dispatchEvent(new window.MouseEvent('click', { bubbles: true }));
}

function pushBareIfBlock(id) {
  var node = {
    id: id,
    type: 'ifblock',
    flag: 'locked',
    hint: null,
    condition: { left: '', op: '==', right: '', joiner: 'none', left2: '', op2: '==', right2: '' },
    ifbody: [],
    elseifs: [{ id: id + '-ei', flag: 'locked', hint: null, condition: { left: '', op: '==', right: '', joiner: 'none', left2: '', op2: '==', right2: '' }, body: [] }],
    elsebody: { id: id + '-el', flag: 'locked', hint: null, body: [] },
  };
  return node;
}

describe('authoring toggle — hidden when AUTHORING_MODE is off', () => {
  it('renders no .authoring-toggle anywhere, even with an if/elseif/else tree present', () => {
    var BB = loadFullStack({ authoring_mode: false });
    BB.SECTIONS.loop.push({ id: 'a1', type: 'digitalwrite', flag: 'locked', hint: null, params: ['13', 'HIGH'], exChildren: [undefined, undefined] });
    BB.SECTIONS.loop.push(pushBareIfBlock('if-1'));
    BB.render();
    expect(document.querySelectorAll('.authoring-toggle').length).toBe(0);
  });
});

describe('authoring toggle — visible when AUTHORING_MODE is on', () => {
  let BB;
  beforeEach(() => {
    BB = loadFullStack({ authoring_mode: true });
  });

  it('renders exactly one toggle on a plain action block', () => {
    BB.SECTIONS.loop.push({ id: 'a1', type: 'digitalwrite', flag: 'locked', hint: null, params: ['13', 'HIGH'], exChildren: [undefined, undefined] });
    BB.render();
    var block = document.querySelector('[data-id="a1"]');
    expect(block.querySelectorAll('.authoring-toggle').length).toBe(1);
  });

  it('renders exactly one toggle on a codeblock action block', () => {
    BB.SECTIONS.loop.push({ id: 'cb1', type: 'codeblock', flag: 'locked', hint: null, params: ['digitalWrite(13, HIGH);'] });
    BB.render();
    var block = document.querySelector('[data-id="cb1"]');
    expect(block.querySelectorAll('.authoring-toggle').length).toBe(1);
  });

  it('renders one toggle each on the if-header, elseif-header, and else-header', () => {
    var node = pushBareIfBlock('if-2');
    BB.SECTIONS.loop.push(node);
    BB.render();
    var wrap = document.querySelector('[data-id="if-2"]');
    expect(wrap.querySelector('.if-header').querySelectorAll('.authoring-toggle').length).toBe(1);
    expect(wrap.querySelector('.elseif-header').querySelectorAll('.authoring-toggle').length).toBe(1);
    expect(wrap.querySelector('.else-header').querySelectorAll('.authoring-toggle').length).toBe(1);
  });

  it('renders one toggle on for-header and while-header', () => {
    BB.SECTIONS.loop.push({ id: 'for-1', type: 'forloop', flag: 'locked', hint: null, forinit: 'int i = 0', forcond: 'i < 10', forincr: 'i++', body: [] });
    BB.SECTIONS.loop.push({ id: 'while-1', type: 'whileloop', flag: 'locked', hint: null, condition: { left: '', op: '!=', right: '', joiner: 'none', left2: '', op2: '==', right2: '' }, body: [] });
    BB.render();
    expect(document.querySelector('[data-id="for-1"] .for-header').querySelectorAll('.authoring-toggle').length).toBe(1);
    expect(document.querySelector('[data-id="while-1"] .while-header').querySelectorAll('.authoring-toggle').length).toBe(1);
  });

  it('clicking the toggle flips block.flag between locked and phantom, and the label updates', () => {
    var node = { id: 'a2', type: 'digitalwrite', flag: 'locked', hint: null, params: ['13', 'HIGH'], exChildren: [undefined, undefined] };
    BB.SECTIONS.loop.push(node);
    BB.render();
    var btn = document.querySelector('[data-id="a2"] .authoring-toggle');
    expect(btn.textContent).toContain('locked');

    click(btn);
    expect(node.flag).toBe('phantom');
    var btnAfter = document.querySelector('[data-id="a2"] .authoring-toggle');
    expect(btnAfter.textContent).toContain('phantom');

    click(btnAfter);
    expect(node.flag).toBe('locked');
  });

  it('shows the hint input only when flag is phantom, and typing into it updates block.hint', () => {
    var node = { id: 'a3', type: 'digitalwrite', flag: 'locked', hint: null, params: ['13', 'HIGH'], exChildren: [undefined, undefined] };
    BB.SECTIONS.loop.push(node);
    BB.render();
    expect(document.querySelector('[data-id="a3"] .authoring-hint-input')).toBeNull();

    click(document.querySelector('[data-id="a3"] .authoring-toggle'));
    var hintInput = document.querySelector('[data-id="a3"] .authoring-hint-input');
    expect(hintInput).toBeTruthy();

    hintInput.value = 'Turn the LED on';
    hintInput.dispatchEvent(new window.Event('input', { bubbles: true }));
    expect(node.hint).toBe('Turn the LED on');

    // Flip back to locked — hint input should disappear again, without losing the stored hint.
    click(document.querySelector('[data-id="a3"] .authoring-toggle'));
    expect(document.querySelector('[data-id="a3"] .authoring-hint-input')).toBeNull();
    expect(node.hint).toBe('Turn the LED on');
  });

  it('newly created blocks default to flag: locked so the toggle starts in a well-defined state', () => {
    // bb-render.js's palette-button click listener is bound once, at script
    // load time, over whatever `.block-btn` elements already exist in the
    // DOM — the real palette markup lives in server-rendered
    // templates/block_builder_fragment.html, not the minimal test fixture.
    // Rebuild the stack here with that one button present *before* bb-render.js
    // loads, so the real listener attaches to it, same as a live click.
    installBlockBuilderFixture();
    var btn = document.createElement('button');
    btn.className = 'block-btn'; btn.setAttribute('data-type', 'digitalwrite');
    document.getElementById('pal-blocks-section').appendChild(btn);

    delete window._BB;
    window.BB_CONFIG = {
      mode: 'freeform', username: null, page: null,
      blocks: { global: [], setup: [], loop: [] }, master: null,
      default_view: 'blocks', lock_view: false, readonly_mode: false,
      lock_mode: false, palette: null, is_overlay: false, force_preset: false,
      authoring_mode: true,
    };
    loadScript('bb-blocks.js');
    loadScript('bb-render.js');
    loadScript('bb-validation.js');
    loadScript('block_builder.js');
    var localBB = window._BB;

    localBB.sel = { section: 'loop', targetArr: localBB.SECTIONS.loop, pathStr: 'loop()' };
    localBB.updatePalette();
    click(btn);
    expect(localBB.SECTIONS.loop.length).toBe(1);
    expect(localBB.SECTIONS.loop[0].flag).toBe('locked');
    expect(localBB.SECTIONS.loop[0].hint).toBeNull();
  });
});
