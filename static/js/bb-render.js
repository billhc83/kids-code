// bb-render.js — All rendering, UI interaction, palette, and selection functions
// Requires: bb-blocks.js loaded first (window._BB must exist)
(function () {
  console.log('[DEBUG] bb-render.js: start');
  var BB = window._BB;

  // ── Expression slot rendering ─────────────────────────────────────────────
  BB.renderExprSlot = function (block, slotIdx, label) {
    if (!block.exChildren) block.exChildren = [];
    var exNode = block.exChildren[slotIdx] || null;
    var wrap = document.createElement('div'); wrap.className = 'blk-field';
    var lbl = document.createElement('label'); lbl.textContent = label; wrap.appendChild(lbl);
    var slot = document.createElement('div');
    slot.className = 'expr-slot' + (exNode ? ' has-expr' : '');
    var isActive = BB.exprSel && BB.exprSel.block === block && BB.exprSel.slotIdx === slotIdx;
    if (isActive) slot.classList.add('active');
    if (exNode) {
      slot.appendChild(BB.renderExprBlock(exNode, function () { block.exChildren[slotIdx] = null; BB.exprSel = null; updatePalette(); render(); }));
    } else {
      var ph = document.createElement('span'); ph.textContent = isActive ? '> drop expr' : '+ expr'; slot.appendChild(ph);
    }
    slot.addEventListener('click', function (e) {
      e.stopPropagation();
      if (BB.exprSel && BB.exprSel.block === block && BB.exprSel.slotIdx === slotIdx) { BB.exprSel = null; updatePalette(); render(); return; }
      BB.exprSel = { block: block, slotIdx: slotIdx };
      document.getElementById('statusbar').innerHTML = '<span style="color:#9a6700">click an expression block to snap it in</span>';
      updatePalette();
      render();
    });
    wrap.appendChild(slot); return wrap;
  };

  BB.renderExprBlock = function (exNode, onRemove) {
    var def = BB.BLOCKS[exNode.type]; if (!def || !def.asExpr) return document.createTextNode('?');
    var chip = document.createElement('span');
    chip.className = 'expr-block-inline';
    chip.style.background = BB.getExprColor(exNode.type);
    chip.style.color = '#fff';
    var lbl = document.createElement('span'); lbl.textContent = exNode.type; chip.appendChild(lbl);
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
        (function (capturedJiVt, capturedExNodeVt) {
          var wrap = document.createElement('span'); wrap.className = 'vartext-wrap';
          var ei = document.createElement('input'); ei.type = 'text'; ei.className = 'vartext-input';
          ei.value = capturedExNodeVt.params[capturedJiVt] || '0';
          ei.placeholder = '0';
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
                  ei.value = v; capturedExNodeVt.params[capturedJiVt] = v; window.genCode();
                  closeDrop();
                });
                drop.appendChild(item);
              });
            }
            wrap.appendChild(drop);
          }
          ei.addEventListener('click', function (e) { e.stopPropagation(); openDrop(''); });
          ei.addEventListener('focus', function (e) { openDrop(''); });
          ei.addEventListener('input', function (e) {
            e.stopPropagation();
            capturedExNodeVt.params[capturedJiVt] = e.target.value; window.genCode();
            var v = e.target.value;
            if (v === '') { openDrop(''); } else { openDrop(v); }
          });
          ei.addEventListener('blur', function () { setTimeout(closeDrop, 150); });
          ei.addEventListener('keydown', function (e) {
            e.stopPropagation();
            if (e.key === 'Escape' || e.key === 'Enter') { closeDrop(); }
            if (e.key === 'Enter') { ei.blur(); }
          });
          wrap.appendChild(ei); chip.appendChild(wrap);
        })(ji, exNode);
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
      BB.activePhantoml = null;
      ctx.className = 'has-expr';
      ctx.textContent = BB.exprSel.isSubSlot ? 'fill sub-slot:' : (BB.exprSel.exSlot ? 'fill value slot: ' + BB.exprSel.exSlot.phantom_meta.hint : 'fill value slot:');
      blockSec.style.display = 'none';
      exprTitle.style.display = '';
      var expectedType = null;
      if (config.structure === 'partial') {
        if (BB.exprSel.condObj) {
          var ec = BB.exprSel.condObj._expectedCond;
          if (ec) {
            var sideKey = BB.exprSel.side === 'leftExpr' ? 'left' : BB.exprSel.side === 'rightExpr' ? 'right' : BB.exprSel.side === 'leftExpr2' ? 'left2' : 'right2';
            expectedType = ec[sideKey] || null;
          }
        } else if (BB.exprSel.exSlot && BB.exprSel.exSlot.phantom_meta && BB.exprSel.exSlot.phantom_meta.expectedExTypes) {
          expectedType = BB.exprSel.exSlot.phantom_meta.expectedExTypes[BB.exprSel.slotIdx] || null;
        } else if (!BB.exprSel.isSubSlot && BB.exprSel.block && BB.exprSel.block._expectedExpr) {
          expectedType = BB.exprSel.block._expectedExpr[BB.exprSel.slotIdx] || null;
        }
      }
      exprSec.querySelectorAll('.block-btn').forEach(function (btn) {
        var bType = btn.getAttribute('data-type');
        var visible = true;
        if (expectedType && bType !== expectedType) visible = false;
        if (visible && config.filter && BB.PALETTE_ALLOWED !== null && BB.PALETTE_ALLOWED.indexOf(bType) === -1) visible = false;
        btn.classList[visible ? 'remove' : 'add']('hidden');
      });
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
      !e.target.closest('.expr-slot') && !e.target.closest('.expr-block-inline')) {
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
      if (BB.PROGRESSION_MODE && guidance !== 'open') return;
      setSelection(sName, BB.SECTIONS[sName], label);
    });
    body.addEventListener('click', function (e) {
      if (e.target === body) {
        e.stopPropagation();
        var step = BB.PROGRESSION_MODE && BB.STEPS ? BB.STEPS[BB.CURRENT_STEP] : null;
        var guidance = step && step.config ? step.config.guidance : 'open';
        if (BB.PROGRESSION_MODE && guidance !== 'open') return;
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
        if (BB.exprSel.condObj) {
          BB.exprSel.condObj[BB.exprSel.side] = newNode;
        } else if (BB.exprSel.isSubSlot) {
          if (!BB.exprSel.exNode.children) BB.exprSel.exNode.children = [];
          BB.exprSel.exNode.children[BB.exprSel.slotIdx] = newNode;
        } else {
          if (!BB.exprSel.block.exChildren) BB.exprSel.block.exChildren = [];
          BB.exprSel.block.exChildren[BB.exprSel.slotIdx] = newNode;
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
          var cond = { leftExpr: null, op: '==', rightExpr: null, joiner: 'none', leftExpr2: null, op2: '==', rightExpr2: null };
          if (ph.condition && (isPartial || (isMatchingPhantom && config.fill === false))) {
            cond.op = ph.condition.op || '==';
            cond.joiner = ph.condition.joiner || 'none';
            cond.op2 = ph.condition.op2 || '==';
            cond._expectedCond = ph.expectedCondTypes || {
              left: ph.condition.leftExpr ? ph.condition.leftExpr.type : null,
              right: ph.condition.rightExpr ? ph.condition.rightExpr.type : null,
              left2: ph.condition.leftExpr2 ? ph.condition.leftExpr2.type : null,
              right2: ph.condition.rightExpr2 ? ph.condition.rightExpr2.type : null
            };
          }
          var ib = isPartial && ph.ifbody ? JSON.parse(JSON.stringify(ph.ifbody)) : [];
          var eifs = isPartial && ph.elseifs ? JSON.parse(JSON.stringify(ph.elseifs)) : [];
          var eb = isPartial && ph.elsebody ? JSON.parse(JSON.stringify(ph.elsebody)) : null;
          newBlock = {
            id: (Date.now() + Math.random()).toString(), type: 'ifblock',
            condition: cond, ifbody: ib, elseifs: eifs, elsebody: eb
          };
        } else if (type === 'forloop') {
          var ib = isPartial && ph.body ? JSON.parse(JSON.stringify(ph.body)) : [];
          var fi = isPartial ? (ph.forinit || 'int i = 0') : 'int i = 0';
          var fc = isPartial ? (ph.forcond || 'i < 10') : 'i < 10';
          var fr = isPartial ? (ph.forincr || 'i++') : 'i++';
          newBlock = { id: (Date.now() + Math.random()).toString(), type: 'forloop', forinit: fi, forcond: fc, forincr: fr, body: ib };
        } else if (type === 'whileloop') {
          var wcond = { leftExpr: null, op: '!=', rightExpr: null, joiner: 'none', leftExpr2: null, op2: '==', rightExpr2: null };
          if (ph.condition && (isPartial || (isMatchingPhantom && config.fill === false))) {
            wcond.op = ph.condition.op || '!=';
            wcond._expectedCond = ph.expectedCondTypes || {
              left: ph.condition.leftExpr ? ph.condition.leftExpr.type : null,
              right: ph.condition.rightExpr ? ph.condition.rightExpr.type : null
            };
          }
          var wb = isPartial && ph.body ? JSON.parse(JSON.stringify(ph.body)) : [];
          newBlock = { id: (Date.now() + Math.random()).toString(), type: 'whileloop', condition: wcond, body: wb };
        } else {
          var params = (isMatchingPhantom && ph.params)
            ? JSON.parse(JSON.stringify(ph.params))
            : def.inputs.map(function (inp) {
              if (inp.t === 'sel') { var f = inp.o[0]; return typeof f === 'object' ? f.v : f; } return '';
            });
          var exch;
          if (isMatchingPhantom && ph.exChildren) {
            exch = JSON.parse(JSON.stringify(ph.exChildren));
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
          condition: { leftExpr: null, op: '==', rightExpr: null, joiner: 'none', leftExpr2: null, op2: '==', rightExpr2: null },
          ifbody: [], elseifs: [], elsebody: null
        };
      } else if (type === 'forloop') {
        block = { id: (Date.now() + Math.random()).toString(), type: 'forloop', forinit: 'int i = 0', forcond: 'i < 10', forincr: 'i++', body: [] };
      } else if (type === 'whileloop') {
        block = {
          id: (Date.now() + Math.random()).toString(), type: 'whileloop',
          condition: { leftExpr: null, op: '!=', rightExpr: null, joiner: 'none', leftExpr2: null, op2: '==', rightExpr2: null },
          body: []
        };
      } else {
        var params = def.inputs.map(function (inp) {
          if (inp.t === 'sel') { var f = inp.o[0]; return typeof f === 'object' ? f.v : f; } return '';
        });
        var exChildren = def.defaults ? def.defaults.map(function (d) { return d ? JSON.parse(JSON.stringify(d)) : null; }) : [];
        block = { id: (Date.now() + Math.random()).toString(), type: type, params: params, exChildren: exChildren };
      }
      BB.sel.targetArr.push(block); render();
    });
  });

  // ── Main render ───────────────────────────────────────────────────────────
  function render() {
    console.log('render called', new Error().stack);
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

  // ── Section / block rendering ─────────────────────────────────────────────
  function renderSection(elId, sName, anc) {
    var body = document.getElementById(elId + '-body');
    body.querySelectorAll('.ws-block,.if-block').forEach(function (e) { e.remove(); });
    BB.SECTIONS[sName].forEach(function (block, idx) { body.appendChild(renderBlock(block, idx, BB.SECTIONS[sName], sName, sName, anc)); });
  }
  BB.renderSection = renderSection;

  function renderBlock(block, idx, parentArr, section, pathStr, anc) {
    if (block.type === 'ifblock')   return renderIfBlock(block, idx, parentArr, section, pathStr, anc);
    if (block.type === 'forloop')   return renderForBlock(block, idx, parentArr, section, pathStr, anc);
    if (block.type === 'whileloop') return renderWhileBlock(block, idx, parentArr, section, pathStr, anc);
    if (block.type === 'slot')      return renderSlot(block, idx, parentArr, section, pathStr, anc);
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
          ei.value = block.params[capturedJ] || ''; ei.placeholder = 'name';
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
          ei.addEventListener('click', function (e) { e.stopPropagation(); openDrop(''); });
          ei.addEventListener('focus', function () { openDrop(''); });
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
        block.elseifs.push({ condition: { leftExpr: null, op: '==', rightExpr: null, joiner: 'none', leftExpr2: null, op2: '==', rightExpr2: null }, body: [] }); render();
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
    var canSelect = !BB.PROGRESSION_MODE || guidance === 'open';
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
    if (!block.condition) block.condition = { leftExpr: null, op: '!=', rightExpr: null, joiner: 'none', leftExpr2: null, op2: '==', rightExpr2: null };
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
    var canSelect = !BB.PROGRESSION_MODE || guidance === 'open';
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
    arr.forEach(function (block, idx) { div.appendChild(renderBlock(block, idx, arr, section, pathStr, anc)); });
    var step = BB.PROGRESSION_MODE && BB.STEPS ? BB.STEPS[BB.CURRENT_STEP] : null;
    var guidance = step && step.config ? step.config.guidance : 'open';
    var canSelect = !BB.PROGRESSION_MODE || guidance === 'open';
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
  function renderCondExprSlot(cond, side, label) {
    var exNode = cond[side] || null;
    var wrap = document.createElement('div'); wrap.className = 'blk-field';
    var lb = document.createElement('label'); lb.textContent = label; wrap.appendChild(lb);
    var slot = document.createElement('div');
    slot.className = 'expr-slot' + (exNode ? ' has-expr' : '');
    var isActive = BB.exprSel && BB.exprSel.condObj === cond && BB.exprSel.side === side;
    if (isActive) slot.classList.add('active');
    if (exNode) {
      slot.appendChild(BB.renderExprBlock(exNode, function () { cond[side] = null; BB.exprSel = null; updatePalette(); render(); }));
    } else {
      var ph = document.createElement('span'); ph.textContent = isActive ? '> drop expr' : '+ expr'; slot.appendChild(ph);
    }
    slot.addEventListener('click', function (e) {
      e.stopPropagation();
      if (BB.exprSel && BB.exprSel.condObj === cond && BB.exprSel.side === side) { BB.exprSel = null; updatePalette(); render(); return; }
      BB.exprSel = { condObj: cond, side: side }; BB.sel = null;
      document.getElementById('statusbar').innerHTML = '<span style="color:#9a6700">click an expression to fill the ' + label + ' slot</span>';
      updatePalette();
      render();
    });
    wrap.appendChild(slot); return wrap;
  }
  BB.renderCondExprSlot = renderCondExprSlot;

  function appendCondFields(parent, cond) {
    parent.appendChild(renderCondExprSlot(cond, 'leftExpr', 'left'));
    parent.appendChild(condField('op', cond, 'opsel'));
    parent.appendChild(renderCondExprSlot(cond, 'rightExpr', 'right'));
    parent.appendChild(condField('joiner', cond, 'joinsel'));
    var g2 = document.createElement('span');
    g2.style.display = cond.joiner !== 'none' ? 'contents' : 'none';
    g2.appendChild(renderCondExprSlot(cond, 'leftExpr2', 'left2'));
    g2.appendChild(condField('op2', cond, 'opsel'));
    g2.appendChild(renderCondExprSlot(cond, 'rightExpr2', 'right2'));
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

  console.log('[DEBUG] bb-render.js: done');
})();
