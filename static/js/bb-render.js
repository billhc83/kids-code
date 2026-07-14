// bb-render.js — All rendering, UI interaction, palette, and selection functions
// Requires: bb-blocks.js loaded first (window._BB must exist)
(function () {
  ('[DEBUG] bb-render.js: start');
  var BB = window._BB;

  // ── Expression slot rendering ─────────────────────────────────────────────
  // Producer Value-slot chooser (block-expression-slot-simplification spec, step 5).
  // After rules 1-4, this is the ONLY remaining `t: 'expr'` input in the whole
  // vocabulary (intvar/longvar/setvar/stringvar's Value) — everywhere else that used
  // to offer this slot type is now flat. One field, one interaction, every mode: click
  // it and a menu opens with "Value" (type a literal/variable) alongside the producer
  // categories (Sensor, Timer, Calculate, ...) — same as the old flat block palette did
  // before this simplification, just reached through this field instead of the sidebar.
  // In guided/full mode the menu is narrowed to the phantom's expectedExTypes (and
  // "Value" only appears if the master answer itself is a bare literal/variable); in
  // open/free/verify it's always the full, unfiltered menu.
  BB.renderExprSlot = function (block, slotIdx, label) {
    if (!block.exChildren) block.exChildren = [];
    var exNode = block.exChildren[slotIdx] || null;
    // A literal/variable answer is still structurally an exChild of type 'value' —
    // validation (bb-validation.js's compareBlock/compareExpr) and the parser both
    // compare/emit it that way, never `params`. Only a REAL producer call (anything
    // other than 'value') gets the placed-chip UI; 'value' (or empty) renders as the
    // plain flat field below, same data shape either way.
    var isPlacedCall = exNode && exNode.type !== 'value';
    var wrap = document.createElement('div'); wrap.className = 'blk-field';
    var lbl = document.createElement('label'); lbl.textContent = label; wrap.appendChild(lbl);

    if (isPlacedCall) {
      var placedSlot = document.createElement('div'); placedSlot.className = 'expr-slot has-expr';
      placedSlot.appendChild(BB.renderExprBlock(exNode, function () {
        block.exChildren[slotIdx] = null; updatePalette(); render();
      }));
      wrap.appendChild(placedSlot);
      return wrap;
    }

    var def = BB.BLOCKS[block.type];
    var fallback = (def.inputs[slotIdx] && def.inputs[slotIdx].fallback) || '0';
    function getFlat() { return (exNode && exNode.type === 'value') ? (exNode.params[0] || '') : ''; }
    function setFlat(v) { block.exChildren[slotIdx] = v === '' ? null : { type: 'value', params: [v], children: [] }; }

    var stepC = BB.PROGRESSION_MODE && BB.STEPS ? BB.STEPS[BB.CURRENT_STEP] : null;
    var config = stepC ? stepC.config : { structure: 'none' };
    var expectedType = (config.structure === 'partial' || config.structure === 'full')
      ? ((block._expectedExpr && block._expectedExpr[slotIdx]) || null)
      : null;

    wrap.appendChild(renderValueField(block, slotIdx, getFlat, setFlat, fallback, expectedType));
    return wrap;
  };

  // Click-to-open menu for the producer Value slot: one input that IS the literal/
  // variable field (typing it sets the value live, exactly like any other flat field)
  // and that also opens a panel listing "Value" plus the producer categories. Picking a
  // category overlays the panel with that category's blocks (a back-crumb returns to
  // categories); picking a block places it and swaps the field to the placed-chip UI;
  // picking "Value" (or just typing) just closes the panel and leaves you editing the
  // literal. `expectedType`, when set (guided/full mode), narrows the menu to the
  // phantom's expected answer — including hiding "Value" entirely when the master
  // answer is a real producer call, since typing a literal could never satisfy it. The
  // one structural exception is a producer kind with a single category and a single
  // block in it (stringvar's Typed Input) — that's not "filtered down to one," it never
  // had a second option to disambiguate, so a category step would be pure friction; its
  // one block sits directly in the top-level list.
  function renderValueField(block, slotIdx, getFlat, setFlat, fallback, expectedType) {
    var def = BB.BLOCKS[block.type];
    var categories = BB.PRODUCER_CATEGORIES[def.exprCategoryKind || 'numeric'] || [];
    var showValueOption = !expectedType || expectedType === 'value';
    var isTrivialKind = categories.length === 1 && categories[0].types.length === 1;
    var visibleCats = isTrivialKind ? null : categories
      .map(function (cat) { return { label: cat.label, types: cat.types.filter(function (t) { return !expectedType || t === expectedType; }) }; })
      .filter(function (cat) { return cat.types.length > 0; });

    function place(type) {
      var newNode = BB.makeExNode(type);
      if (!block.exChildren) block.exChildren = [];
      block.exChildren[slotIdx] = newNode;
      window.genCode();
      updatePalette(); render();
    }

    var wrap = document.createElement('span'); wrap.className = 'value-tree-wrap vartext-wrap';
    var input = document.createElement('input'); input.type = 'text'; input.className = 'value-tree-input vartext-input';
    input.value = getFlat(); input.placeholder = fallback; input.autocomplete = 'off';
    wrap.appendChild(input);

    var panel = null, view = 'categories', activeCat = null;
    function closePanel() { if (panel) { panel.remove(); panel = null; } }

    function topLevelItems() {
      var items = [];
      if (showValueOption) {
        items.push({ value: null, label: 'Value', kind: 'value' });
        // Already-declared variables are a real, common choice here (e.g. referencing
        // an existing sensor reading) — same suggestion source renderVartextChip uses
        // for every other flat field, surfaced here too so it's not lost behind the
        // category menu.
        BB.getVarSuggestions().forEach(function (v) { items.push({ value: v, label: v, kind: 'var' }); });
      }
      if (isTrivialKind) {
        categories[0].types.forEach(function (t) { items.push({ value: t, label: BB.getExprLabel(t), kind: 'call' }); });
      } else {
        visibleCats.forEach(function (c) { items.push({ value: c.label, label: c.label, kind: 'cat' }); });
      }
      return items;
    }

    function openPanel() {
      closePanel();
      panel = document.createElement('div'); panel.className = 'value-tree-panel';

      if (view === 'children') {
        var crumb = document.createElement('div'); crumb.className = 'value-tree-crumb';
        var backBtn = document.createElement('button'); backBtn.type = 'button'; backBtn.className = 'value-tree-crumb-back';
        backBtn.textContent = '‹ Back';
        backBtn.addEventListener('mousedown', function (e) {
          e.preventDefault(); e.stopPropagation();
          view = 'categories'; activeCat = null;
          openPanel(); input.focus();
        });
        crumb.appendChild(backBtn);
        var crumbLbl = document.createElement('span'); crumbLbl.className = 'value-tree-crumb-label'; crumbLbl.textContent = activeCat.label;
        crumb.appendChild(crumbLbl);
        panel.appendChild(crumb);
      }

      var items = view === 'children'
        ? activeCat.types.map(function (t) { return { value: t, label: BB.getExprLabel(t), kind: 'call' }; })
        : topLevelItems();
      // A typed literal (e.g. a number) naturally won't match any menu label — the list
      // just empties out, which is fine: typing IS the action at that point, the menu's
      // only job is to offer the alternative when you haven't started typing a literal.
      var q = input.value.toLowerCase();
      var filtered = items.filter(function (it) { return !q || it.label.toLowerCase().indexOf(q) !== -1; });
      if (filtered.length === 0) {
        var empty = document.createElement('div'); empty.className = 'value-tree-empty'; empty.textContent = 'no matches';
        panel.appendChild(empty);
      } else {
        filtered.forEach(function (it) {
          var row = document.createElement('div'); row.className = 'value-tree-item' + (it.kind === 'value' ? ' value-tree-item-literal' : '');
          row.textContent = it.label;
          row.addEventListener('mousedown', function (e) {
            e.preventDefault(); e.stopPropagation();
            if (it.kind === 'value') { closePanel(); input.focus(); return; }
            if (it.kind === 'var') { setFlat(it.value); input.value = it.value; window.genCode(); closePanel(); input.blur(); return; }
            if (it.kind === 'call') { place(it.value); return; }
            activeCat = visibleCats.filter(function (c) { return c.label === it.value; })[0];
            view = 'children';
            openPanel(); input.focus();
          });
          panel.appendChild(row);
        });
      }
      wrap.appendChild(panel);
    }

    input.addEventListener('click', function (e) { e.stopPropagation(); if (!panel) openPanel(); });
    input.addEventListener('focus', function () { if (!panel) openPanel(); });
    input.addEventListener('input', function (e) {
      setFlat(e.target.value); window.genCode();
      openPanel();
    });
    input.addEventListener('blur', function () { setTimeout(closePanel, 150); });
    input.addEventListener('keydown', function (e) {
      e.stopPropagation();
      if (e.key === 'Escape' || e.key === 'Enter') { input.blur(); closePanel(); }
    });

    return wrap;
  }

  // Inline literal/variable field with the shared variable-suggestion dropdown —
  // used by every flat `vartext` field, including each term of the math chain and
  // the producer Value slot's flat/open-mode default (rule 1's assignment convention).
  function renderVartextChip(getVal, setVal, placeholder) {
    var ph = placeholder || '0';
    var wrap = document.createElement('span'); wrap.className = 'vartext-wrap';
    var ei = document.createElement('input'); ei.type = 'text'; ei.className = 'vartext-input';
    ei.value = getVal() || ph;
    ei.placeholder = ph;
    var drop = null;
    function closeDrop() { if (drop) { drop.remove(); drop = null; } }
    function openDrop(filter) {
      closeDrop();
      var vars = BB.getVarSuggestions();
      var filtered = filter ? vars.filter(function (v) { return v.toLowerCase().indexOf(filter.toLowerCase()) === 0; }) : vars;
      if (filtered.length === 0 && filter) { return; }
      drop = document.createElement('div'); drop.className = 'vartext-drop';
      if (filtered.length === 0) {
        var empty = document.createElement('div'); empty.className = 'vartext-drop-empty';
        empty.textContent = 'no variables yet'; drop.appendChild(empty);
      } else {
        filtered.forEach(function (v) {
          var item = document.createElement('div'); item.className = 'vartext-drop-item';
          item.textContent = v;
          item.addEventListener('mousedown', function (e) {
            e.preventDefault(); e.stopPropagation();
            ei.value = v; setVal(v); window.genCode();
            closeDrop();
          });
          drop.appendChild(item);
        });
      }
      wrap.appendChild(drop);
    }
    ei.addEventListener('click', function (e) { e.stopPropagation(); });
    ei.addEventListener('input', function (e) {
      e.stopPropagation();
      setVal(e.target.value); window.genCode();
      var v = e.target.value;
      if (v === '') { openDrop(''); } else { openDrop(v); }
    });
    ei.addEventListener('blur', function () { setTimeout(closeDrop, 150); });
    ei.addEventListener('keydown', function (e) {
      e.stopPropagation();
      if (e.key === 'Escape' || e.key === 'Enter') { closeDrop(); }
      if (e.key === 'Enter') { ei.blur(); }
    });
    wrap.appendChild(ei);
    return wrap;
  }

  BB.renderExprBlock = function (exNode, onRemove) {
    var def = BB.BLOCKS[exNode.type]; if (!def || !def.asExpr) return document.createTextNode('?');
    var chip = document.createElement('span');
    chip.className = 'expr-block-inline';
    chip.style.background = BB.getExprColor(exNode.type);
    chip.style.color = '#fff';
    var lbl = document.createElement('span'); lbl.textContent = exNode.type; chip.appendChild(lbl);
    if (def.variadic) {
      if (!exNode.terms) exNode.terms = ['0', '0'];
      if (!exNode.ops) exNode.ops = ['+'];
      exNode.terms.forEach(function (term, ti) {
        chip.appendChild(renderVartextChip(
          function () { return exNode.terms[ti]; },
          function (v) { exNode.terms[ti] = v; }
        ));
        if (ti < exNode.ops.length) {
          (function (capturedOi) {
            var es = document.createElement('select'); es.className = 'expr-sel';
            def.opOptions.forEach(function (opt) {
              var o = document.createElement('option'); o.value = opt.v; o.textContent = opt.lb; es.appendChild(o);
            });
            es.value = exNode.ops[capturedOi] || '+';
            es.addEventListener('click', function (e) { e.stopPropagation(); });
            es.addEventListener('change', function (e) { e.stopPropagation(); exNode.ops[capturedOi] = e.target.value; window.genCode(); });
            chip.appendChild(es);
          })(ti);
        }
      });
      chip.appendChild(mkact('+ term', function () {
        exNode.terms.push('0'); exNode.ops.push('+'); render();
      }));
      if (onRemove) {
        var rxv = document.createElement('span'); rxv.className = 'expr-remove'; rxv.textContent = 'x';
        rxv.title = 'Remove expression';
        rxv.addEventListener('click', function (e) { e.stopPropagation(); onRemove(); }); chip.appendChild(rxv);
      }
      return chip;
    }
    def.inputs.forEach(function (inp, ji) {
      if (inp.t === 'expr') {
        (function (capturedJi, capturedExNode) {
          var subSlot = document.createElement('span');
          var isSubActive = BB.exprSel && BB.exprSel.isSubSlot && BB.exprSel.exNode === capturedExNode && BB.exprSel.slotIdx === capturedJi;
          subSlot.style.cssText = 'display:inline-flex;align-items:center;border-radius:5px;padding:2px 6px;cursor:pointer;font-size:11px;min-width:34px;border:2px ' + (isSubActive ? 'solid #fff' : 'dashed rgba(255,255,255,0.6)') + ';background:' + (isSubActive ? 'rgba(255,255,255,0.35)' : 'rgba(255,255,255,0.15)') + ';';
          var subNode = (capturedExNode.children && capturedExNode.children[capturedJi]) || null;
          if (subNode) {
            subSlot.appendChild(BB.renderExprBlock(subNode, function () { if (!capturedExNode.children) capturedExNode.children = []; capturedExNode.children[capturedJi] = null; BB.exprSel = null; render(); }));
          } else {
            var sph = document.createElement('span'); sph.textContent = inp.l || '?';
            sph.style.cssText = 'opacity:0.85;font-weight:700;color:#fff;pointer-events:none;'; subSlot.appendChild(sph);
          }
          subSlot.addEventListener('click', function (e) {
            e.stopPropagation();
            if (BB.exprSel && BB.exprSel.isSubSlot && BB.exprSel.exNode === capturedExNode && BB.exprSel.slotIdx === capturedJi) {
              BB.exprSel = null; updatePalette(); render(); return;
            }
            BB.exprSel = { exNode: capturedExNode, slotIdx: capturedJi, isSubSlot: true }; BB.sel = null;
            document.getElementById('statusbar').innerHTML = '<span style="color:#9a6700">slot ' + inp.l + ' selected - click an expression to fill it</span>';
            document.querySelectorAll('.sub-slot-active').forEach(function (el) { el.classList.remove('sub-slot-active'); });
            subSlot.style.border = '2px solid #fff'; subSlot.style.background = 'rgba(255,255,255,0.35)';
            updatePalette();
          });
          chip.appendChild(subSlot);
        })(ji, exNode);
      } else if (inp.t === 'sel') {
        var es = document.createElement('select'); es.className = 'expr-sel';
        var opts = inp.o; if (typeof opts === 'string') opts = BB.getOptions(opts);
        if (!exNode.params[ji]) { var op = document.createElement('option'); op.value = ''; op.textContent = '\u2014'; es.appendChild(op); }
        opts.forEach(function (opt) {
          var o = document.createElement('option');
          if (typeof opt === 'object') { o.value = opt.v; o.textContent = opt.lb; } else { o.value = opt; o.textContent = opt; }
          es.appendChild(o);
        }); es.value = exNode.params[ji] || '';
        es.addEventListener('click', function (e) { e.stopPropagation(); });
        es.addEventListener('change', function (e) { e.stopPropagation(); exNode.params[ji] = e.target.value; window.genCode(); });
        chip.appendChild(es);
      } else if (inp.t === 'vartext') {
        chip.appendChild(renderVartextChip(
          function () { return exNode.params[ji]; },
          function (v) { exNode.params[ji] = v; }
        ));
      } else {
        var ei = document.createElement('input'); ei.type = inp.t === 'number' ? 'number' : 'text';
        ei.className = 'expr-input'; ei.value = exNode.params[ji] || '';
        ei.style.width = (inp.t === 'number' ? '48px' : '60px');
        ei.addEventListener('click', function (e) { e.stopPropagation(); });
        ei.addEventListener('input', function (e) { e.stopPropagation(); exNode.params[ji] = e.target.value; window.genCode(); });
        chip.appendChild(ei);
      }
    });
    if (onRemove) {
      var rx = document.createElement('span'); rx.className = 'expr-remove'; rx.textContent = 'x';
      rx.title = 'Remove expression';
      rx.addEventListener('click', function (e) { e.stopPropagation(); onRemove(); }); chip.appendChild(rx);
    }
    return chip;
  };

  // ── Palette ───────────────────────────────────────────────────────────────
  function updatePalette() {
    var ctx = document.getElementById('pal-context');
    var blockSec = document.getElementById('pal-blocks-section');
    var exprSec = document.getElementById('pal-expr-section');
    var exprTitle = document.getElementById('pal-expr-title');
    if (BB.LOCK_VIEW) {
      blockSec.style.display = 'none';
      exprSec.querySelectorAll('.block-btn').forEach(function (btn) { btn.classList.add('hidden'); });
      return;
    }
    var step = BB.PROGRESSION_MODE && BB.STEPS ? BB.STEPS[BB.CURRENT_STEP] : null;
    var config = step ? step.config : { structure: 'none', filter: false, validation: 'none', fill: true };

    if (BB.exprSel) {
      // Only ever set by the producer Value slot's open-mode "+" escape hatch now —
      // the Category -> Block tree it opens renders inline at the slot itself (see
      // renderValueTree), not via this sidebar, so both palette sections stay hidden.
      BB.activePhantoml = null;
      ctx.className = 'has-expr';
      ctx.textContent = 'choose a value kind in the field below';
      blockSec.style.display = 'none';
      exprTitle.style.display = 'none';
      exprSec.querySelectorAll('.block-btn').forEach(function (btn) { btn.classList.add('hidden'); });
      return;
    }
    if (BB.activePhantoml) {
      var ph = BB.activePhantoml.slot.phantom_meta;
      var isPartial = config.structure === 'partial';
      ctx.className = 'has-sel';
      ctx.textContent = 'place: ' + ph.hint;
      blockSec.style.display = 'flex';
      exprTitle.style.display = '';
      blockSec.querySelectorAll('.block-btn').forEach(function (btn) {
        var type = btn.getAttribute('data-type');
        if (ph.expects) {
          btn.classList[type === ph.expects ? 'remove' : 'add']('hidden');
        } else if (!isPartial) {
          btn.classList.remove('hidden');
        } else {
          btn.classList.add('hidden');
        }
      });
      exprSec.querySelectorAll('.block-btn').forEach(function (btn) { btn.classList.add('hidden'); });
      return;
    }
    blockSec.style.display = 'flex';
    exprTitle.style.display = '';
    if (!BB.sel) {
      ctx.className = ''; ctx.textContent = 'select a section';
      blockSec.querySelectorAll('.block-btn').forEach(function (btn) { btn.classList.add('hidden'); });
      exprSec.querySelectorAll('.block-btn').forEach(function (btn) { btn.classList.add('hidden'); });
      return;
    }
    ctx.className = 'has-sel';
    var parts = BB.sel.pathStr.split(' \u2192 ');
    ctx.textContent = 'adding to: ' + parts[parts.length - 1];
    var inNested = BB.sel.pathStr.indexOf('\u2192') !== -1;
    blockSec.querySelectorAll('.block-btn').forEach(function (btn) {
      var type = btn.getAttribute('data-type');
      var def = BB.BLOCKS[type]; if (!def) { btn.classList.remove('hidden'); return; }
      var ok = inNested ? (def.allowed.indexOf('if') !== -1 || def.allowed.indexOf('for') !== -1 || def.allowed.indexOf('while') !== -1)
        : (def.allowed.indexOf(BB.sel.section) !== -1);
      if (ok && config.filter && BB.PALETTE_ALLOWED !== null) ok = BB.PALETTE_ALLOWED.indexOf(type) !== -1;
      if (ok) { btn.classList.remove('hidden'); } else { btn.classList.add('hidden'); }
    });
    exprSec.querySelectorAll('.block-btn').forEach(function (btn) { btn.classList.add('hidden'); });
  }
  BB.updatePalette = updatePalette;

  // ── Selection ─────────────────────────────────────────────────────────────
  function setSelection(section, targetArr, pathStr) {
    BB.sel = { section: section, targetArr: targetArr, pathStr: pathStr };
    document.getElementById('statusbar').innerHTML = 'adding to: <span>' + pathStr + '</span>';
    updatePalette();
    render();
  }
  BB.setSelection = setSelection;

  function clearSelection() {
    BB.sel = null; BB.exprSel = null;
    document.getElementById('statusbar').textContent = 'click a section or if body to select it';
    updatePalette();
    render();
  }
  BB.clearSelection = clearSelection;

  document.addEventListener('click', function (e) {
    if (!e.target.closest('.section') && !e.target.closest('.if-body') &&
      !e.target.closest('.block-btn') && !e.target.closest('#codepanel') && !e.target.closest('button') &&
      !e.target.closest('.expr-slot') && !e.target.closest('.expr-block-inline') &&
      !e.target.closest('.value-tree-wrap')) {
      clearSelection();
    }
  });

  function expandSection(elId) {
    ['gs', 'ss', 'ls'].forEach(function (id) {
      document.getElementById(id).classList.toggle('expanded', id === elId);
    });
  }
  BB.expandSection = expandSection;

  function setupSection(elId, sName, label) {
    var el = document.getElementById(elId);
    var hdr = el.querySelector('.section-header');
    var body = document.getElementById(elId + '-body');
    hdr.addEventListener('click', function (e) {
      e.stopPropagation();
      expandSection(elId);
      var step = BB.PROGRESSION_MODE && BB.STEPS ? BB.STEPS[BB.CURRENT_STEP] : null;
      var guidance = step && step.config ? step.config.guidance : 'open';
      if (BB.PROGRESSION_MODE && guidance !== 'open' && guidance !== 'verify') return;
      setSelection(sName, BB.SECTIONS[sName], label);
    });
    body.addEventListener('click', function (e) {
      if (e.target === body) {
        e.stopPropagation();
        var step = BB.PROGRESSION_MODE && BB.STEPS ? BB.STEPS[BB.CURRENT_STEP] : null;
        var guidance = step && step.config ? step.config.guidance : 'open';
        if (BB.PROGRESSION_MODE && guidance !== 'open' && guidance !== 'verify') return;
        setSelection(sName, BB.SECTIONS[sName], label);
      }
    });
  }
  BB.setupSection = setupSection;

  setupSection('gs', 'global', 'Global');
  setupSection('ss', 'setup', 'setup()');
  setupSection('ls', 'loop', 'loop()');

  // ── Block palette button listeners ────────────────────────────────────────
  document.querySelectorAll('.block-btn').forEach(function (btn) {
    btn.addEventListener('click', function (e) {
      e.stopPropagation();
      var type = btn.getAttribute('data-type'); if (!type) return;
      var def = BB.BLOCKS[type]; if (!def) return;
      var step = BB.PROGRESSION_MODE && BB.STEPS ? BB.STEPS[BB.CURRENT_STEP] : null;
      var config = step ? step.config : { structure: 'none' };

      if (BB.exprSel && def.asExpr) {
        var newNode = BB.makeExNode(type);
        if (BB.exprSel.isSubSlot) {
          var prevSubTemplate = BB.exprSel.exNode._childTemplates && BB.exprSel.exNode._childTemplates[BB.exprSel.slotIdx];
          if (!BB.exprSel.exNode.children) BB.exprSel.exNode.children = [];
          BB.exprSel.exNode.children[BB.exprSel.slotIdx] = newNode;
          if (prevSubTemplate && prevSubTemplate.children) {
            newNode._expectedChildren = prevSubTemplate.children.map(function (c) { return c ? c.type : null; });
            newNode._childTemplates = prevSubTemplate.children;
          }
        } else {
          var prevTemplate = BB.exprSel.block.exChildren && BB.exprSel.block.exChildren[BB.exprSel.slotIdx];
          if (!BB.exprSel.block.exChildren) BB.exprSel.block.exChildren = [];
          BB.exprSel.block.exChildren[BB.exprSel.slotIdx] = newNode;
          if (prevTemplate && prevTemplate.children) {
            newNode._expectedChildren = prevTemplate.children.map(function (c) { return c ? c.type : null; });
            newNode._childTemplates = prevTemplate.children;
          }
        }
        BB.exprSel = null; updatePalette(); render(); return;
      }
      if (BB.activePhantoml && def.asStatement) {
        var arr = BB.activePhantoml.arr;
        var idx = BB.activePhantoml.idx;
        var slot = BB.activePhantoml.slot;
        var ph = slot.phantom_meta;
        var newBlock;
        var step = BB.PROGRESSION_MODE && BB.STEPS ? BB.STEPS[BB.CURRENT_STEP] : null;
        var config = step ? step.config : { structure: 'none', fill: true };
        var isPartial = config.structure === 'partial';
        var isMatchingPhantom = ph && type === ph.expects;

        if (type === 'ifblock') {
          var cond = { left: '', op: '==', right: '', joiner: 'none', left2: '', op2: '==', right2: '' };
          if (ph.condition && (isPartial || (isMatchingPhantom && config.fill === false))) {
            cond.op = ph.condition.op || '==';
            cond.joiner = ph.condition.joiner || 'none';
            cond.op2 = ph.condition.op2 || '==';
          }
          var ib = isPartial && ph.ifbody ? JSON.parse(JSON.stringify(ph.ifbody)) : [];
          var eifs = isPartial && ph.elseifs ? JSON.parse(JSON.stringify(ph.elseifs)) : [];
          var eb = isPartial && ph.elsebody ? JSON.parse(JSON.stringify(ph.elsebody)) : null;
          newBlock = {
            id: (Date.now() + Math.random()).toString(), type: 'ifblock',
            condition: cond, ifbody: ib, elseifs: eifs, elsebody: eb
          };
        } else if (type === 'elseifclause') {
          var cond = { left: '', op: '==', right: '', joiner: 'none', left2: '', op2: '==', right2: '' };
          if (ph.condition && (isPartial || (isMatchingPhantom && config.fill === false))) {
            cond.op = ph.condition.op || '==';
            cond.joiner = ph.condition.joiner || 'none';
            cond.op2 = ph.condition.op2 || '==';
          }
          var bd = isPartial && ph.body ? JSON.parse(JSON.stringify(ph.body)) : [];
          newBlock = { id: (Date.now() + Math.random()).toString(), type: 'elseifclause', condition: cond, body: bd };
        } else if (type === 'elseclause') {
          var bd = isPartial && ph.body ? JSON.parse(JSON.stringify(ph.body)) : [];
          newBlock = { id: (Date.now() + Math.random()).toString(), type: 'elseclause', body: bd };
        } else if (type === 'forloop') {
          var ib = isPartial && ph.body ? JSON.parse(JSON.stringify(ph.body)) : [];
          var fi = isPartial ? (ph.forinit || 'int i = 0') : 'int i = 0';
          var fc = isPartial ? (ph.forcond || 'i < 10') : 'i < 10';
          var fr = isPartial ? (ph.forincr || 'i++') : 'i++';
          newBlock = { id: (Date.now() + Math.random()).toString(), type: 'forloop', forinit: fi, forcond: fc, forincr: fr, body: ib };
        } else if (type === 'whileloop') {
          var wcond = { left: '', op: '!=', right: '', joiner: 'none', left2: '', op2: '==', right2: '' };
          if (ph.condition && (isPartial || (isMatchingPhantom && config.fill === false))) {
            wcond.op = ph.condition.op || '!=';
          }
          var wb = isPartial && ph.body ? JSON.parse(JSON.stringify(ph.body)) : [];
          newBlock = { id: (Date.now() + Math.random()).toString(), type: 'whileloop', condition: wcond, body: wb };
        } else {
          var params = (isMatchingPhantom && ph.params)
            ? JSON.parse(JSON.stringify(ph.params))
            : def.inputs.map(function (inp) {
              if (inp.t === 'sel') return BB.selDefault(inp); return '';
            });
          var exch;
          if (isMatchingPhantom && ph.exChildren) {
            exch = JSON.parse(JSON.stringify(ph.exChildren));
            // Producer Value-slot chooser (step 5): don't auto-reveal which producer
            // type fills this slot just because the outer block type matched — that's
            // still an active choice the student makes via the Category -> Block tree,
            // same as every other phantom sub-structure (a phantom `pinmode` isn't
            // auto-placed just because the master is known either). expectedExpr below
            // still carries the master's expected type through for the tree's filter.
            def.inputs.forEach(function (inp, ii) { if (inp.t === 'expr') exch[ii] = null; });
          } else {
            exch = (isPartial || config.fill === false)
              ? def.inputs.map(function (inp) { return inp.t === 'expr' ? null : undefined; })
              : (def.defaults ? def.defaults.map(function (d) { return d ? JSON.parse(JSON.stringify(d)) : null; }) : []) || [];
          }
          var expectedExpr = (isPartial || isMatchingPhantom) ? (ph.expectedExTypes || (ph.exChildren ? ph.exChildren.map(function (e) { return e ? e.type : null; }) : null)) : null;
          newBlock = { id: (Date.now() + Math.random()).toString(), type: type, params: params, exChildren: exch };
          if (expectedExpr) newBlock._expectedExpr = expectedExpr;
        }
        slot.content = newBlock;
        BB.activePhantoml = null;
        BB.checkStepComplete();
        updatePalette(); render(); return;
      }
      if (!def.asStatement) { BB.flash(type + ' can only go in expression slots'); return; }
      if (!BB.sel) { BB.flash('Select a section or if body first'); return; }
      var inIf = BB.sel.pathStr.indexOf('\u2192') !== -1;
      if (inIf) { if (def.allowed.indexOf('if') === -1 && def.allowed.indexOf('for') === -1 && def.allowed.indexOf('while') === -1) { BB.flash('"' + type + '" not allowed here'); return; } }
      else { if (def.allowed.indexOf(BB.sel.section) === -1) { BB.flash('Goes in: ' + def.allowed.filter(function (a) { return a !== 'if' && a !== 'for' && a !== 'while'; }).join(' or ')); return; } }
      var block;
      if (type === 'ifblock') {
        block = {
          id: (Date.now() + Math.random()).toString(), type: 'ifblock',
          condition: { left: '', op: '==', right: '', joiner: 'none', left2: '', op2: '==', right2: '' },
          ifbody: [], elseifs: [], elsebody: null
        };
      } else if (type === 'forloop') {
        block = { id: (Date.now() + Math.random()).toString(), type: 'forloop', forinit: 'int i = 0', forcond: 'i < 10', forincr: 'i++', body: [] };
      } else if (type === 'whileloop') {
        block = {
          id: (Date.now() + Math.random()).toString(), type: 'whileloop',
          condition: { left: '', op: '!=', right: '', joiner: 'none', left2: '', op2: '==', right2: '' },
          body: []
        };
      } else {
        var params = def.inputs.map(function (inp) {
          if (inp.t === 'sel') return BB.selDefault(inp); return '';
        });
        var exChildren = def.defaults ? def.defaults.map(function (d) { return d ? JSON.parse(JSON.stringify(d)) : null; }) : [];
        block = { id: (Date.now() + Math.random()).toString(), type: type, params: params, exChildren: exChildren };
      }
      if (BB.sel.insertIdx !== null && BB.sel.insertIdx !== undefined) {
        BB.sel.targetArr.splice(BB.sel.insertIdx, 0, block);
        BB.sel.insertIdx = null;
      } else {
        BB.sel.targetArr.push(block);
      }
      render();
    });
  });

  // ── Main render ───────────────────────────────────────────────────────────
  function render() {
    ('render called', new Error().stack);
    var anc = collectAncestorArrays();
    renderSection('gs', 'global', anc); renderSection('ss', 'setup', anc); renderSection('ls', 'loop', anc);
    ['gs', 'ss', 'ls'].forEach(function (id) {
      var el = document.getElementById(id);
      var sn = id === 'gs' ? 'global' : id === 'ss' ? 'setup' : 'loop';
      var base = 'section s-' + (id === 'gs' ? 'global' : id === 'ss' ? 'setup' : 'loop');
      var isExpanded = el.classList.contains('expanded');
      el.className = (BB.sel && BB.sel.targetArr === BB.SECTIONS[sn]) ? base + ' active' : base;
      if (isExpanded) el.classList.add('expanded');
    });
    if (typeof BB.genCode === 'function') BB.genCode();
    if (typeof BB.applySketchHighlights === 'function') BB.applySketchHighlights();
    if (typeof BB.applyStepHighlights === 'function') BB.applyStepHighlights();
    if (BB.READONLY_MODE) {
      document.querySelectorAll('.blk-input,.cond-input,.vartext-input,.cond-select,.cond-joiner').forEach(function (el) {
        el.setAttribute('disabled', true);
      });
      document.querySelectorAll('.act').forEach(function (el) {
        el.style.display = 'none';
      });
      document.querySelectorAll('.ws-block,.if-body,.for-body,.while-body,.if-block,.for-block,.while-block').forEach(function (el) {
        el.style.pointerEvents = 'none';
      });
      document.querySelectorAll('.palette-block,.palette-item').forEach(function (el) {
        el.style.display = 'none';
      });
    }
  }
  BB.render = render;

  // ── Ancestor / depth helpers ──────────────────────────────────────────────
  function collectAncestorArrays() {
    var anc = []; if (!BB.sel) return anc;
    function walk(arr) {
      for (var i = 0; i < arr.length; i++) {
        var b = arr[i];
        if (b.type === 'ifblock') {
          if (containsTarget(b)) anc.push(b.id);
          walk(b.ifbody); b.elseifs.forEach(function (ei) { walk(ei.body); }); if (b.elsebody) walk(b.elsebody);
        } else if (b.type === 'forloop' || b.type === 'whileloop') { if (b.body && isDescendantOf(b.body, BB.sel.targetArr)) anc.push(b.id); if (b.body) walk(b.body); }
        else if ((b.type === 'elseifclause' || b.type === 'elseclause') && b.body) { if (isDescendantOf(b.body, BB.sel.targetArr)) anc.push(b.id); walk(b.body); }
      }
    }
    walk(BB.SECTIONS[BB.sel.section]); return anc;
  }
  BB.collectAncestorArrays = collectAncestorArrays;

  function containsTarget(ifBlock) {
    if (ifBlock.ifbody === BB.sel.targetArr) return true;
    for (var i = 0; i < ifBlock.elseifs.length; i++) if (ifBlock.elseifs[i].body === BB.sel.targetArr) return true;
    if (ifBlock.elsebody === BB.sel.targetArr) return true;
    function walkDeep(arr) {
      for (var j = 0; j < arr.length; j++) {
        var b = arr[j];
        if (b.type === 'ifblock' && containsTarget(b)) return true;
        if ((b.type === 'forloop' || b.type === 'whileloop') && b.body && isDescendantOf(b.body, BB.sel.targetArr)) return true;
      } return false;
    }
    return walkDeep(ifBlock.ifbody) || ifBlock.elseifs.some(function (ei) { return walkDeep(ei.body); }) ||
      (ifBlock.elsebody ? walkDeep(ifBlock.elsebody) : false);
  }
  BB.containsTarget = containsTarget;

  function braceDepth(arr, idx) {
    var depth = 0;
    for (var i = 0; i < idx; i++) {
      var block = arr[i];
      if (block.type === 'slot' && block.content) { block = block.content; }
      else if (block.type === 'slot' && block.content === null) { continue; }
      if (block.type !== 'codeblock') continue;
      var c = (block.params[0] || '').trim();
      if (c.charAt(c.length - 1) === '{') depth++;
      if (c === '}' || c.match(/^\}/)) depth = Math.max(0, depth - 1);
    }
    return depth;
  }
  BB.braceDepth = braceDepth;

  // ── Insert strip ──────────────────────────────────────────────────────────
  function makeInsertStrip(section, targetArr, pathStr, insertIdx) {
    var strip = document.createElement('div');
    strip.className = 'insert-strip';
    var isActive = BB.sel && BB.sel.targetArr === targetArr && BB.sel.insertIdx === insertIdx;
    if (isActive) strip.classList.add('active');
    strip.addEventListener('click', function (e) {
      e.stopPropagation();
      var step = BB.PROGRESSION_MODE && BB.STEPS ? BB.STEPS[BB.CURRENT_STEP] : null;
      var guidance = step && step.config ? step.config.guidance : 'open';
      if (BB.PROGRESSION_MODE && guidance !== 'open' && guidance !== 'verify') return;
      BB.sel = { section: section, targetArr: targetArr, pathStr: pathStr, insertIdx: insertIdx };
      document.getElementById('statusbar').innerHTML = 'inserting into: <span>' + pathStr + '</span>';
      updatePalette();
      render();
    });
    return strip;
  }
  BB.makeInsertStrip = makeInsertStrip;

  // ── Section / block rendering ─────────────────────────────────────────────
  function renderSection(elId, sName, anc) {
    var body = document.getElementById(elId + '-body');
    body.querySelectorAll('.ws-block,.if-block,.insert-strip').forEach(function (e) { e.remove(); });
    var arr = BB.SECTIONS[sName];
    var step = BB.PROGRESSION_MODE && BB.STEPS ? BB.STEPS[BB.CURRENT_STEP] : null;
    var guidance = step && step.config ? step.config.guidance : 'open';
    var canInsert = !BB.READONLY_MODE && (!BB.PROGRESSION_MODE || guidance === 'open' || guidance === 'verify') && arr.length > 0;
    if (canInsert) body.appendChild(makeInsertStrip(sName, arr, sName, 0));
    arr.forEach(function (block, idx) {
      body.appendChild(renderBlock(block, idx, arr, sName, sName, anc));
      if (canInsert) body.appendChild(makeInsertStrip(sName, arr, sName, idx + 1));
    });
  }
  BB.renderSection = renderSection;

  function renderBlock(block, idx, parentArr, section, pathStr, anc) {
    if (block.type === 'ifblock')      return renderIfBlock(block, idx, parentArr, section, pathStr, anc);
    if (block.type === 'elseifclause') return renderElseIfClause(block, idx, parentArr, section, pathStr, anc);
    if (block.type === 'elseclause')   return renderElseClause(block, idx, parentArr, section, pathStr, anc);
    if (block.type === 'forloop')      return renderForBlock(block, idx, parentArr, section, pathStr, anc);
    if (block.type === 'whileloop')    return renderWhileBlock(block, idx, parentArr, section, pathStr, anc);
    if (block.type === 'slot')         return renderSlot(block, idx, parentArr, section, pathStr, anc);
    return renderActionBlock(block, idx, parentArr);
  }
  BB.renderBlock = renderBlock;

  function renderSlot(slot, idx, parentArr, section, pathStr, anc) {
    if (slot.content === null) {
      var d = document.createElement('div');
      d.className = 'ws-block phantom-block';
      var depth = braceDepth(parentArr, idx);
      if (depth > 0) d.style.marginLeft = (depth * 18) + 'px';
      var isActive = BB.activePhantoml && BB.activePhantoml.slot === slot;
      if (isActive) d.classList.add('active');
      var icon = document.createElement('span'); icon.className = 'phantom-icon'; icon.textContent = '+';
      var hint = document.createElement('span'); hint.className = 'phantom-hint'; hint.textContent = slot.phantom_meta.hint || 'Place a block here';
      var exp = document.createElement('span'); exp.className = 'phantom-expects'; exp.textContent = slot.phantom_meta.expects || '';
      d.appendChild(icon); d.appendChild(hint); d.appendChild(exp);
      d.addEventListener('click', function (e) {
        e.stopPropagation();
        if (BB.activePhantoml && BB.activePhantoml.slot === slot) {
          BB.activePhantoml = null;
        } else {
          BB.activePhantoml = { arr: parentArr, idx: idx, slot: slot };
          BB.sel = null; BB.exprSel = null;
        }
        updatePalette(); render();
      });
      return d;
    } else {
      return renderBlock(slot.content, idx, parentArr, section, pathStr, anc);
    }
  }
  BB.renderSlot = renderSlot;

  function renderActionBlock(block, idx, parentArr) {
    var d = document.createElement('div');
    var def = BB.B[block.type];
    d.className = 'ws-block';
    d.setAttribute('data-id', block.id);
    if (block.type === 'codeblock') {
      d.classList.add('codeblock-block');
      var depth = braceDepth(parentArr, idx);
      var c = (block.params[0] || '').trim();
      if (c === '}' || c.match(/^\}/)) depth = Math.max(0, depth - 1);
      if (depth > 0) d.style.marginLeft = (depth * 18) + 'px';
      if (block.parser_error) d.classList.add('parser-error');
      var code = document.createElement('span'); code.className = 'codeblock-code';
      code.textContent = block.params[0] || ''; d.appendChild(code);
      function mkb2(ic, fn) {
        var bt = document.createElement('button'); bt.className = 'act'; bt.textContent = ic;
        bt.addEventListener('click', function (e) { e.stopPropagation(); fn(); }); return bt;
      }
      d.appendChild(mkb2('\u2191', function () { if (idx > 0) { var t = parentArr[idx - 1]; parentArr[idx - 1] = parentArr[idx]; parentArr[idx] = t; render(); } }));
      d.appendChild(mkb2('\u2193', function () { if (idx < parentArr.length - 1) { var t = parentArr[idx + 1]; parentArr[idx + 1] = parentArr[idx]; parentArr[idx] = t; render(); } }));
      d.appendChild(mkb2('\u00D7', function () { parentArr.splice(idx, 1); render(); }));
      return d;
    }
    var nm = document.createElement('span'); nm.className = 'blk-name'; nm.textContent = block.type; d.appendChild(nm);
    var bdepth = braceDepth(parentArr, idx); if (bdepth > 0) d.style.marginLeft = (bdepth * 18) + 'px';

    var actualParentArr = parentArr;
    var actualIdx = idx;

    def.inputs.forEach(function (inp, j) {
      if (inp.t === 'expr') {
        d.appendChild(BB.renderExprSlot(block, j, inp.l)); return;
      }
      if (inp.t === 'vartext') {
        (function (capturedJ, capturedInpO) {
          var f = document.createElement('div'); f.className = 'blk-field';
          var lb = document.createElement('label'); lb.textContent = inp.l; f.appendChild(lb);
          var wrap = document.createElement('span'); wrap.className = 'vartext-wrap';
          var ei = document.createElement('input'); ei.type = 'text'; ei.className = 'vartext-input';
          ei.value = block.params[capturedJ] || '';
          var drop = null;
          function closeDrop() { if (drop) { drop.remove(); drop = null; } }
          function openDrop(filter) {
            closeDrop();
            var vars = capturedInpO ? BB.getPinSuggestions(capturedInpO) : BB.getVarSuggestions();
            var filtered = filter ? vars.filter(function (v) { return v.toLowerCase().indexOf(filter.toLowerCase()) === 0; }) : vars;
            if (filtered.length === 0 && filter) { return; }
            drop = document.createElement('div'); drop.className = 'vartext-drop';
            if (filtered.length === 0) {
              var empty = document.createElement('div'); empty.className = 'vartext-drop-empty';
              empty.textContent = 'no options yet'; drop.appendChild(empty);
            } else {
              filtered.forEach(function (v) {
                var item = document.createElement('div'); item.className = 'vartext-drop-item';
                item.textContent = v;
                item.addEventListener('mousedown', function (e) {
                  e.preventDefault(); e.stopPropagation();
                  ei.value = v; block.params[capturedJ] = v; window.genCode();
                  closeDrop();
                });
                drop.appendChild(item);
              });
            }
            wrap.appendChild(drop);
          }
          ei.addEventListener('click', function (e) { e.stopPropagation(); });
          ei.addEventListener('input', function (e) {
            e.stopPropagation();
            block.params[capturedJ] = e.target.value; window.genCode();
            if (e.target.value === '') { openDrop(''); } else { openDrop(e.target.value); }
          });
          ei.addEventListener('blur', function () { setTimeout(closeDrop, 150); });
          ei.addEventListener('keydown', function (e) {
            e.stopPropagation();
            if (e.key === 'Escape' || e.key === 'Enter') { closeDrop(); }
            if (e.key === 'Enter') { ei.blur(); }
          });
          wrap.appendChild(ei); f.appendChild(wrap); d.appendChild(f);
        })(j, inp.o || null); return;
      }
      var f = document.createElement('div'); f.className = 'blk-field';
      var lb = document.createElement('label'); lb.textContent = inp.l; f.appendChild(lb);
      var el;
      if (inp.t === 'sel') {
        el = document.createElement('select');
        var opts = inp.o; if (typeof opts === 'string') { opts = BB.getOptions(opts); }
        if (!block.params[j]) { var op = document.createElement('option'); op.value = ''; op.textContent = '\u2014'; el.appendChild(op); }
        opts.forEach(function (opt) {
          var o = document.createElement('option');
          if (typeof opt === 'object') { o.value = opt.v; o.textContent = opt.lb; } else { o.value = opt; o.textContent = opt; }
          el.appendChild(o);
        }); el.value = block.params[j];
      } else { el = document.createElement('input'); el.type = inp.t === 'number' ? 'number' : 'text'; el.value = block.params[j]; }
      el.className = 'blk-input';
      if (block.type === 'increment' && inp.l === 'By') {
        var op = block.params[1] || '++'; f.style.display = (op === '++' || op === '--') ? 'none' : '';
      }
      el.addEventListener('click', function (e) { e.stopPropagation(); });
      el.addEventListener('input', function (e) {
        e.stopPropagation(); block.params[j] = e.target.value; window.genCode();
        if (block.type === 'increment' && inp.l === 'Op') {
          var byF = d.querySelector('.by-field');
          if (byF) byF.style.display = (e.target.value === '++' || e.target.value === '--') ? 'none' : '';
        }
      });
      if (block.type === 'increment' && inp.l === 'By') f.className += ' by-field';
      f.appendChild(el); d.appendChild(f);
    });

    function mkb(ic, fn) {
      var bt = document.createElement('button'); bt.className = 'act'; bt.textContent = ic;
      bt.addEventListener('click', function (e) { e.stopPropagation(); fn(actualParentArr, actualIdx); }); return bt;
    }

    var isLockedCodeblock = block.type === 'codeblock' && block.locked;
    if (!BB.READONLY_MODE && !isLockedCodeblock) {
      d.appendChild(mkb('\u2191', function (arr, i) { if (i > 0) { var t = arr[i - 1]; arr[i - 1] = arr[i]; arr[i] = t; render(); } }, parentArr, idx));
      d.appendChild(mkb('\u2193', function (arr, i) { if (i < arr.length - 1) { var t = arr[i + 1]; arr[i + 1] = arr[i]; arr[i] = t; render(); } }, parentArr, idx));
      d.appendChild(mkb('\u00D7', function (arr, i) {
        if (arr[i].type === 'slot') {
          arr[i].content = null;
        } else {
          arr.splice(i, 1);
        }
        render(); BB.checkStepComplete();
      }, parentArr, idx));
    }
    return d;
  }
  BB.renderActionBlock = renderActionBlock;

  function renderIfBlock(block, idx, parentArr, section, parentPathStr, anc) {
    var wrap = document.createElement('div');
    wrap.className = 'if-block' + (anc.indexOf(block.id) !== -1 ? ' ancestor' : '');
    wrap.setAttribute('data-id', block.id);
    var hdr = document.createElement('div'); hdr.className = 'if-header';
    hdr.appendChild(kw('if (')); appendCondFields(hdr, block.condition); hdr.appendChild(kw(')'));
    if (!BB.READONLY_MODE) {
      hdr.appendChild(mkact('+ else if', function () {
        block.elseifs.push({ condition: { left: '', op: '==', right: '', joiner: 'none', left2: '', op2: '==', right2: '' }, body: [] }); render();
      }));
      if (block.elsebody === null) hdr.appendChild(mkact('+ else', function () { block.elsebody = []; render(); }));
      hdr.appendChild(mkact('\u00D7', function () {
        if (parentArr[idx] && parentArr[idx].type === 'slot') {
          parentArr[idx].content = null;
        } else {
          parentArr.splice(idx, 1);
        }
        if (BB.sel && (BB.sel.targetArr === block.ifbody || isDescendant(block, BB.sel.targetArr))) clearSelection(); else render(); BB.checkStepComplete();
      }));
    }
    wrap.appendChild(hdr);
    var ifPathStr = parentPathStr + ' \u2192 if';
    var isOnlyBody = block.elseifs.length === 0 && block.elsebody === null;
    wrap.appendChild(makeBodyZone(block.ifbody, section, ifPathStr, isOnlyBody, anc));
    block.elseifs.forEach(function (ei, eiIdx) {
      var eiHdr = document.createElement('div'); eiHdr.className = 'elseif-header';
      eiHdr.appendChild(kw('else if (')); appendCondFields(eiHdr, ei.condition); eiHdr.appendChild(kw(')'));
      if (!BB.READONLY_MODE) {
        eiHdr.appendChild(mkact('\u00D7', function () { block.elseifs.splice(eiIdx, 1); render(); }));
      }
      wrap.appendChild(eiHdr);
      var eiPathStr = parentPathStr + ' \u2192 else if';
      var eiIsLast = eiIdx === block.elseifs.length - 1 && block.elsebody === null;
      wrap.appendChild(makeBodyZone(ei.body, section, eiPathStr, eiIsLast, anc));
    });
    if (block.elsebody !== null) {
      var elHdr = document.createElement('div'); elHdr.className = 'else-header';
      elHdr.appendChild(kw('else'));
      if (!BB.READONLY_MODE) {
        elHdr.appendChild(mkact('\u00D7', function () { block.elsebody = null; render(); }));
      }
      wrap.appendChild(elHdr);
      wrap.appendChild(makeBodyZone(block.elsebody, section, parentPathStr + ' \u2192 else', true, anc));
    }
    return wrap;
  }
  BB.renderIfBlock = renderIfBlock;

  function renderElseIfClause(block, idx, parentArr, section, parentPathStr, anc) {
    if (!block.body) block.body = [];
    if (!block.condition) block.condition = { left: '', op: '>', right: '', joiner: 'none', left2: '', op2: '==', right2: '' };
    var wrap = document.createElement('div');
    wrap.className = 'if-block' + (anc.indexOf(block.id) !== -1 ? ' ancestor' : '');
    wrap.setAttribute('data-id', block.id);
    var hdr = document.createElement('div'); hdr.className = 'elseif-header';
    hdr.appendChild(kw('else if (')); appendCondFields(hdr, block.condition); hdr.appendChild(kw(')'));
    if (!BB.READONLY_MODE) {
      hdr.appendChild(mkact('\u00D7', function () {
        if (parentArr[idx] && parentArr[idx].type === 'slot') { parentArr[idx].content = null; }
        else { parentArr.splice(idx, 1); }
        if (BB.sel && (BB.sel.targetArr === block.body || isDescendantOf(block.body, BB.sel.targetArr))) clearSelection(); else render();
        BB.checkStepComplete();
      }));
    }
    wrap.appendChild(hdr);
    wrap.appendChild(makeBodyZone(block.body, section, parentPathStr + ' \u2192 else if', true, anc));
    return wrap;
  }
  BB.renderElseIfClause = renderElseIfClause;

  function renderElseClause(block, idx, parentArr, section, parentPathStr, anc) {
    if (!block.body) block.body = [];
    var wrap = document.createElement('div');
    wrap.className = 'if-block' + (anc.indexOf(block.id) !== -1 ? ' ancestor' : '');
    wrap.setAttribute('data-id', block.id);
    var hdr = document.createElement('div'); hdr.className = 'else-header';
    hdr.appendChild(kw('else'));
    if (!BB.READONLY_MODE) {
      hdr.appendChild(mkact('\u00D7', function () {
        if (parentArr[idx] && parentArr[idx].type === 'slot') { parentArr[idx].content = null; }
        else { parentArr.splice(idx, 1); }
        if (BB.sel && (BB.sel.targetArr === block.body || isDescendantOf(block.body, BB.sel.targetArr))) clearSelection(); else render();
        BB.checkStepComplete();
      }));
    }
    wrap.appendChild(hdr);
    wrap.appendChild(makeBodyZone(block.body, section, parentPathStr + ' \u2192 else', true, anc));
    return wrap;
  }
  BB.renderElseClause = renderElseClause;

  function renderForBlock(block, idx, parentArr, section, parentPathStr, anc) {
    var wrap = document.createElement('div'); wrap.className = 'for-block';
    wrap.setAttribute('data-id', block.id);
    var hdr = document.createElement('div'); hdr.className = 'for-header';
    hdr.appendChild(kw('for ('));
    var fkw = document.createElement('span'); fkw.className = 'for-keyword'; fkw.textContent = 'for ('; hdr.appendChild(fkw);
    if (!block.forinit && block.forinit !== '') block.forinit = 'int i = 0';
    if (!block.forcond && block.forcond !== '') block.forcond = 'i < 10';
    if (!block.forincr && block.forincr !== '') block.forincr = 'i++';
    var keys = ['forinit', 'forcond', 'forincr'], labels = ['init', 'cond', 'incr'], phs = ['int i=0', 'i<10', 'i++'];
    for (var fi = 0; fi < 3; fi++) {
      (function (ki, la, ph) {
        var fw = document.createElement('div'); fw.style.cssText = 'display:flex;flex-direction:column;font-size:8px;';
        var fl = document.createElement('label'); fl.textContent = la; fl.style.color = '#57606a'; fw.appendChild(fl);
        var fe = document.createElement('input'); fe.type = 'text'; fe.className = 'cond-input'; fe.value = block[ki] || '';
        fe.placeholder = ph;
        fe.addEventListener('click', function (e) { e.stopPropagation(); });
        fe.addEventListener('input', function (e) { e.stopPropagation(); block[ki] = e.target.value; window.genCode(); });
        fw.appendChild(fe); hdr.appendChild(fw);
        if (fi < 2) { var sep = document.createElement('span'); sep.className = 'for-keyword'; sep.textContent = ';'; hdr.appendChild(sep); }
      })(keys[fi], labels[fi], phs[fi]);
    }
    var ekw = document.createElement('span'); ekw.className = 'for-keyword'; ekw.textContent = ') {'; hdr.appendChild(ekw);
    if (!BB.READONLY_MODE) {
      hdr.appendChild(mkact('\u00D7', function () {
        if (parentArr[idx] && parentArr[idx].type === 'slot') {
          parentArr[idx].content = null;
        } else {
          parentArr.splice(idx, 1);
        }
        if (BB.sel && (BB.sel.targetArr === block.body || isDescendantOf(block.body, BB.sel.targetArr))) clearSelection(); else render(); BB.checkStepComplete();
      }));
    }
    wrap.appendChild(hdr);
    if (!block.body) block.body = [];
    var bodyPath = parentPathStr + ' \u2192 for';
    var bz = document.createElement('div'); bz.className = 'for-body';
    if (BB.sel && BB.sel.targetArr === block.body) bz.classList.add('selected');
    block.body.forEach(function (b, bi) { bz.appendChild(renderBlock(b, bi, block.body, section, bodyPath, anc)); });
    var step = BB.PROGRESSION_MODE && BB.STEPS ? BB.STEPS[BB.CURRENT_STEP] : null;
    var guidance = step && step.config ? step.config.guidance : 'open';
    var canSelect = !BB.PROGRESSION_MODE || guidance === 'open' || guidance === 'verify';
    if (block.body.length === 0) {
      var hint = document.createElement('div'); hint.className = 'body-hint';
      hint.textContent = canSelect ? 'click to select, then add blocks' : ''; bz.appendChild(hint);
    }
    bz.addEventListener('click', function (e) {
      if (e.target === bz || e.target.classList.contains('body-hint')) {
        e.stopPropagation();
        if (!canSelect) return;
        setSelection(section, block.body, bodyPath);
      }
    });
    wrap.appendChild(bz);
    var cz = document.createElement('div'); cz.style.cssText = 'border-left:1px dashed #2e7d32;border-right:1px dashed #2e7d32;border-bottom:1px dashed #2e7d32;border-radius:0 0 5px 5px;padding:2px 6px;font-size:10px;color:#2e7d32;';
    cz.textContent = '} // end for'; wrap.appendChild(cz);
    return wrap;
  }
  BB.renderForBlock = renderForBlock;

  function renderWhileBlock(block, idx, parentArr, section, parentPathStr, anc) {
    var wrap = document.createElement('div'); wrap.className = 'while-block';
    wrap.setAttribute('data-id', block.id);
    var hdr = document.createElement('div'); hdr.className = 'while-header';
    var wkw = document.createElement('span'); wkw.className = 'while-keyword'; wkw.textContent = 'while ('; hdr.appendChild(wkw);
    if (!block.condition) block.condition = { left: '', op: '!=', right: '', joiner: 'none', left2: '', op2: '==', right2: '' };
    appendCondFields(hdr, block.condition);
    var ewkw = document.createElement('span'); ewkw.className = 'while-keyword'; ewkw.textContent = ') {'; hdr.appendChild(ewkw);
    if (!BB.READONLY_MODE) {
      hdr.appendChild(mkact('\u00D7', function () {
        if (parentArr[idx] && parentArr[idx].type === 'slot') {
          parentArr[idx].content = null;
        } else {
          parentArr.splice(idx, 1);
        }
        if (BB.sel && (BB.sel.targetArr === block.body || isDescendantOf(block.body, BB.sel.targetArr))) clearSelection(); else render(); BB.checkStepComplete();
      }));
    }
    wrap.appendChild(hdr);
    if (!block.body) block.body = [];
    var bodyPath = parentPathStr + ' \u2192 while';
    var bz = document.createElement('div'); bz.className = 'while-body';
    if (BB.sel && BB.sel.targetArr === block.body) bz.classList.add('selected');
    block.body.forEach(function (b, bi) { bz.appendChild(renderBlock(b, bi, block.body, section, bodyPath, anc)); });
    var step = BB.PROGRESSION_MODE && BB.STEPS ? BB.STEPS[BB.CURRENT_STEP] : null;
    var guidance = step && step.config ? step.config.guidance : 'open';
    var canSelect = !BB.PROGRESSION_MODE || guidance === 'open' || guidance === 'verify';
    if (block.body.length === 0) {
      var hint = document.createElement('div'); hint.className = 'body-hint';
      hint.textContent = canSelect ? 'click to select, then add blocks' : ''; bz.appendChild(hint);
    }
    bz.addEventListener('click', function (e) {
      if (e.target === bz || e.target.classList.contains('body-hint')) {
        e.stopPropagation();
        if (!canSelect) return;
        setSelection(section, block.body, bodyPath);
      }
    });
    wrap.appendChild(bz);
    var cz = document.createElement('div'); cz.style.cssText = 'border-left:1px dashed #6a1b9a;border-right:1px dashed #6a1b9a;border-bottom:1px dashed #6a1b9a;border-radius:0 0 5px 5px;padding:2px 6px;font-size:10px;color:#6a1b9a;';
    cz.textContent = '} // end while'; wrap.appendChild(cz);
    return wrap;
  }
  BB.renderWhileBlock = renderWhileBlock;

  // ── Descendant helpers ────────────────────────────────────────────────────
  function isDescendantOf(body, targetArr) {
    if (body === targetArr) return true;
    for (var i = 0; i < body.length; i++) {
      var b = body[i];
      var blockToCheck = b.type === 'slot' ? b.content : b;
      if (blockToCheck) {
        if (blockToCheck.type === 'ifblock') {
          if (isDescendantOf(blockToCheck.ifbody, targetArr)) return true;
          for (var j = 0; j < blockToCheck.elseifs.length; j++) if (isDescendantOf(blockToCheck.elseifs[j].body, targetArr)) return true;
          if (blockToCheck.elsebody && isDescendantOf(blockToCheck.elsebody, targetArr)) return true;
        } else if (blockToCheck.type === 'forloop' || blockToCheck.type === 'whileloop') { if (blockToCheck.body && isDescendantOf(blockToCheck.body, targetArr)) return true; }
      }
    }
    return false;
  }
  BB.isDescendantOf = isDescendantOf;

  function makeBodyZone(arr, section, pathStr, isLast, anc) {
    var div = document.createElement('div');
    div.className = 'if-body' + (isLast ? ' last' : '');
    if (BB.sel && BB.sel.targetArr === arr) div.classList.add('selected');
    var step = BB.PROGRESSION_MODE && BB.STEPS ? BB.STEPS[BB.CURRENT_STEP] : null;
    var guidance = step && step.config ? step.config.guidance : 'open';
    var canSelect = !BB.PROGRESSION_MODE || guidance === 'open' || guidance === 'verify';
    var canInsert = !BB.READONLY_MODE && canSelect && arr.length > 0;
    if (canInsert) div.appendChild(makeInsertStrip(section, arr, pathStr, 0));
    arr.forEach(function (block, idx) {
      div.appendChild(renderBlock(block, idx, arr, section, pathStr, anc));
      if (canInsert) div.appendChild(makeInsertStrip(section, arr, pathStr, idx + 1));
    });
    if (arr.length === 0) {
      var hint = document.createElement('div'); hint.className = 'body-hint';
      hint.textContent = canSelect ? 'click to select, then add blocks' : ''; div.appendChild(hint);
    }
    div.addEventListener('click', function (e) {
      if (e.target === div || e.target.classList.contains('body-hint')) {
        e.stopPropagation();
        if (!canSelect) return;
        setSelection(section, arr, pathStr);
      }
    });
    return div;
  }
  BB.makeBodyZone = makeBodyZone;

  function isDescendant(ifBlock, targetArr) {
    if (ifBlock.ifbody === targetArr) return true;
    for (var i = 0; i < ifBlock.elseifs.length; i++) if (ifBlock.elseifs[i].body === targetArr) return true;
    if (ifBlock.elsebody === targetArr) return true;
    function walkDeep(arr) {
      for (var j = 0; j < arr.length; j++) {
        var b = arr[j];
        var blockToCheck = b.type === 'slot' ? b.content : b;
        if (blockToCheck) {
          if (blockToCheck.type === 'ifblock' && isDescendant(blockToCheck, targetArr)) return true;
          if ((blockToCheck.type === 'forloop' || blockToCheck.type === 'whileloop') && blockToCheck.body && isDescendantOf(blockToCheck.body, targetArr)) return true;
        }
      } return false;
    }
    return walkDeep(ifBlock.ifbody) || ifBlock.elseifs.some(function (ei) { return walkDeep(ei.body); }) ||
      (ifBlock.elsebody ? walkDeep(ifBlock.elsebody) : false);
  }
  BB.isDescendant = isDescendant;

  // ── UI helpers ────────────────────────────────────────────────────────────
  function kw(text) { var s = document.createElement('span'); s.className = 'if-keyword'; s.textContent = text; return s; }
  BB.kw = kw;

  function mkact(text, fn) {
    var b = document.createElement('button'); b.className = 'act'; b.textContent = text;
    b.addEventListener('click', function (e) { e.stopPropagation(); fn(); }); return b;
  }
  BB.mkact = mkact;

  // ── Condition rendering ───────────────────────────────────────────────────
  function renderCondField(cond, key, label) {
    var f = document.createElement('div'); f.className = 'cond-field';
    var lb = document.createElement('label'); lb.textContent = label; f.appendChild(lb);
    var wrap = document.createElement('span'); wrap.className = 'vartext-wrap';
    var ei = document.createElement('input'); ei.type = 'text'; ei.className = 'cond-input';
    ei.value = cond[key] || ''; ei.placeholder = label;
    var drop = null;
    function closeDrop() { if (drop) { drop.remove(); drop = null; } }
    function openDrop(filter) {
      closeDrop();
      var vars = BB.getConditionSuggestions();
      var filtered = filter ? vars.filter(function (v) { return v.toLowerCase().indexOf(filter.toLowerCase()) === 0; }) : vars;
      if (filtered.length === 0 && filter) { return; }
      drop = document.createElement('div'); drop.className = 'vartext-drop';
      if (filtered.length === 0) {
        var empty = document.createElement('div'); empty.className = 'vartext-drop-empty';
        empty.textContent = 'no suggestions yet'; drop.appendChild(empty);
      } else {
        filtered.forEach(function (v) {
          var item = document.createElement('div'); item.className = 'vartext-drop-item';
          item.textContent = v;
          item.addEventListener('mousedown', function (e) {
            e.preventDefault(); e.stopPropagation();
            ei.value = v; cond[key] = v; window.genCode();
            closeDrop();
          });
          drop.appendChild(item);
        });
      }
      wrap.appendChild(drop);
    }
    ei.addEventListener('click', function (e) { e.stopPropagation(); });
    ei.addEventListener('input', function (e) {
      e.stopPropagation();
      cond[key] = e.target.value; window.genCode();
      openDrop(e.target.value);
    });
    ei.addEventListener('blur', function () { setTimeout(closeDrop, 150); });
    ei.addEventListener('keydown', function (e) {
      e.stopPropagation();
      if (e.key === 'Escape' || e.key === 'Enter') { closeDrop(); }
      if (e.key === 'Enter') { ei.blur(); }
    });
    wrap.appendChild(ei); f.appendChild(wrap); return f;
  }
  BB.renderCondField = renderCondField;

  function appendCondFields(parent, cond) {
    parent.appendChild(renderCondField(cond, 'left', 'left'));
    parent.appendChild(condField('op', cond, 'opsel'));
    parent.appendChild(renderCondField(cond, 'right', 'right'));
    parent.appendChild(condField('joiner', cond, 'joinsel'));
    var g2 = document.createElement('span');
    g2.style.display = cond.joiner !== 'none' ? 'contents' : 'none';
    g2.appendChild(renderCondField(cond, 'left2', 'left2'));
    g2.appendChild(condField('op2', cond, 'opsel'));
    g2.appendChild(renderCondField(cond, 'right2', 'right2'));
    parent.appendChild(g2);
    var joinEl = parent.querySelector('.cond-joiner');
    joinEl.addEventListener('change', function () { g2.style.display = joinEl.value !== 'none' ? 'contents' : 'none'; });
  }
  BB.appendCondFields = appendCondFields;

  function condField(labelText, obj, type) {
    var f = document.createElement('div'); f.className = 'cond-field';
    var lb = document.createElement('label'); lb.textContent = labelText; f.appendChild(lb);
    var el;
    if (type === 'opsel') {
      el = document.createElement('select'); el.className = 'cond-select';
      [['==', 'equals'], ['!=', 'not equals'], ['>', 'greater than'], ['<', 'less than'], ['>=', 'greater or equal'], ['<=', 'less than or equal']].forEach(function (o) {
        var opt = document.createElement('option'); opt.value = o[0]; opt.textContent = o[1]; el.appendChild(opt);
      });
      el.value = obj[labelText];
    } else if (type === 'joinsel') {
      el = document.createElement('select'); el.className = 'cond-joiner';
      [['none', '\u2014'], ['and', 'and'], ['or', 'or']].forEach(function (o) {
        var opt = document.createElement('option'); opt.value = o[0]; opt.textContent = o[1]; el.appendChild(opt);
      });
      el.value = obj[labelText];
    }
    el.addEventListener('click', function (e) { e.stopPropagation(); });
    el.addEventListener('change', function (e) { e.stopPropagation(); obj[labelText] = e.target.value; window.genCode(); });
    f.appendChild(el); return f;
  }
  BB.condField = condField;

  ('[DEBUG] bb-render.js: done');
})();
