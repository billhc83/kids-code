// bb-validation.js — Validation, hint generation, sketch checking, and tutorial/progression
// Requires: bb-blocks.js and bb-render.js loaded first
(function () {
  ('[DEBUG] bb-validation.js: start');
  var BB = window._BB;

  BB.SKETCH_ERROR_PATHS = [];
  BB.STEP_ERROR_IDS = [];

  // ── Phantom / incomplete counters ─────────────────────────────────────────
  BB.countPhantoms = function (arr) {
    var n = 0;
    arr.forEach(function (b) {
      if (b.type === 'slot') {
        if (b.content === null) n++;
        else {
          if (b.content.type === 'ifblock') { n += BB.countPhantoms(b.content.ifbody); b.content.elseifs.forEach(function (ei) { n += BB.countPhantoms(ei.body); }); if (b.content.elsebody) n += BB.countPhantoms(b.content.elsebody); }
          if ((b.content.type === 'forloop' || b.content.type === 'whileloop') && b.content.body) n += BB.countPhantoms(b.content.body);
        }
      } else if (b.type === 'ifblock') { n += BB.countPhantoms(b.ifbody); b.elseifs.forEach(function (ei) { n += BB.countPhantoms(ei.body); }); if (b.elsebody) n += BB.countPhantoms(b.elsebody); }
      else if ((b.type === 'forloop' || b.type === 'whileloop') && b.body) n += BB.countPhantoms(b.body);
      else if ((b.type === 'elseifclause' || b.type === 'elseclause') && b.body) n += BB.countPhantoms(b.body);
    });
    return n;
  };

  BB.countIncomplete = function (arr) {
    var n = 0;
    arr.forEach(function (b) {
      var currentBlock = b;
      if (b.type === 'slot') { if (b.content === null) return; currentBlock = b.content; }
      if (currentBlock.type === 'codeblock') return;
      if (currentBlock.type === 'ifblock') {
        var c = currentBlock.condition;
        if (c) {
          if (!c.leftExpr) n++; if (!c.rightExpr) n++;
          if (c.joiner !== 'none') { if (!c.leftExpr2) n++; if (!c.rightExpr2) n++; }
        }
        n += BB.countIncomplete(currentBlock.ifbody);
        currentBlock.elseifs.forEach(function (ei) {
          var ec = ei.condition;
          if (ec) { if (!ec.leftExpr) n++; if (!ec.rightExpr) n++; }
          n += BB.countIncomplete(ei.body);
        });
        if (currentBlock.elsebody) n += BB.countIncomplete(currentBlock.elsebody);
        return;
      }
      if (currentBlock.type === 'whileloop') {
        var c = currentBlock.condition;
        if (c) { if (!c.leftExpr) n++; if (!c.rightExpr) n++; }
        if (currentBlock.body) n += BB.countIncomplete(currentBlock.body); return;
      }
      if (currentBlock.type === 'forloop') {
        if (currentBlock.body) n += BB.countIncomplete(currentBlock.body); return;
      }
      if (currentBlock.type === 'elseifclause') {
        var c = currentBlock.condition;
        if (c) { if (!c.leftExpr) n++; if (!c.rightExpr) n++; }
        if (currentBlock.body) n += BB.countIncomplete(currentBlock.body); return;
      }
      if (currentBlock.type === 'elseclause') {
        if (currentBlock.body) n += BB.countIncomplete(currentBlock.body); return;
      }
      var def = BB.BLOCKS[currentBlock.type]; if (!def) return;
      def.inputs.forEach(function (inp, j) {
        if (inp.t === 'expr') {
          if (!currentBlock.exChildren || !currentBlock.exChildren[j]) n++;
        } else if (inp.t === 'text' || inp.t === 'number' || inp.t === 'vartext') {
          if (currentBlock.type === 'tone' && j === 2) return; // Duration is optional
          if (!currentBlock.params || !currentBlock.params[j] || currentBlock.params[j] === '') n++;
        }
      });
    });
    return n;
  };

  // ── Comparison helpers ────────────────────────────────────────────────────
  BB.compareExpr = function (u, t) {
    if (!u && !t) return true; if (!u || !t) return false;
    if (u.type !== t.type) return false;
    if (u.type === 'value') { return (u.params[0] || '').trim() === (t.params[0] || '').trim(); }
    for (var i = 0; i < (u.params || []).length; i++) if ((u.params[i] || '').trim() !== (t.params[i] || '').trim()) return false;
    var uc = u.children || [], tc = t.children || [];
    if (uc.length !== tc.length) return false;
    for (var i = 0; i < uc.length; i++) if (!BB.compareExpr(uc[i], tc[i])) return false;
    return true;
  };

  BB.compareCondition = function (u, t) {
    if (!u && !t) return true; if (!u || !t) return false;
    if (u.op !== t.op) return false;
    if (!BB.compareExpr(u.leftExpr, t.leftExpr)) return false;
    if (!BB.compareExpr(u.rightExpr, t.rightExpr)) return false;
    if (u.joiner !== t.joiner) return false;
    if (u.joiner !== 'none') {
      if (u.op2 !== t.op2) return false;
      if (!BB.compareExpr(u.leftExpr2, t.leftExpr2)) return false;
      if (!BB.compareExpr(u.rightExpr2, t.rightExpr2)) return false;
    }
    return true;
  };

  // ── Hint generators ───────────────────────────────────────────────────────
  BB.generateExprHint = function (u, t, tier) {
    if (!u && !t) return null; if (!u) return 'Missing value';
    if (!t) return 'Unexpected value';
    if (u.type !== t.type) return 'Wrong type: use ' + t.type;
    var def = BB.BLOCKS[u.type];
    if (u.type === 'value') {
      var uv = (u.params[0] || '').trim(), tv = (t.params[0] || '').trim();
      if (uv !== tv) return tier === 3 ? 'Value should be ' + tv : 'Check value';
    }
    for (var i = 0; i < (u.params || []).length; i++) {
      if ((u.params[i] || '').trim() !== (t.params[i] || '').trim()) {
        var lbl = (def && def.inputs[i]) ? def.inputs[i].l : 'setting';
        return tier === 3 ? lbl + ' should be ' + t.params[i] : 'Check ' + lbl;
      }
    }
    var uc = u.children || [], tc = t.children || [];
    if (uc.length !== tc.length) return 'Structure mismatch';
    for (var i = 0; i < uc.length; i++) {
      var h = BB.generateExprHint(uc[i], tc[i], tier);
      if (h) {
        var lbl = (def && def.inputs[i]) ? def.inputs[i].l : 'slot';
        return lbl + ': ' + h;
      }
    }
    return null;
  };

  BB.generateCondHint = function (u, t, tier) {
    if (!u && !t) return null; if (!u || !t) return 'Condition missing';
    var h = BB.generateExprHint(u.leftExpr, t.leftExpr, tier); if (h) return 'Left side: ' + h;
    if (u.op !== t.op) return tier === 3 ? 'Operator should be ' + t.op : 'Check operator';
    h = BB.generateExprHint(u.rightExpr, t.rightExpr, tier); if (h) return 'Right side: ' + h;
    if (t.joiner !== 'none') {
      if (u.joiner !== t.joiner) return 'Check joiner (and/or)';
      h = BB.generateExprHint(u.leftExpr2, t.leftExpr2, tier); if (h) return '2nd Left: ' + h;
      if (u.op2 !== t.op2) return tier === 3 ? '2nd Op should be ' + t.op2 : 'Check 2nd operator';
      h = BB.generateExprHint(u.rightExpr2, t.rightExpr2, tier); if (h) return '2nd Right: ' + h;
    }
    return null;
  };

  BB.generateHint = function (u, t, tier) {
    if (tier < 2) return '';
    var pm = t.type === 'slot' ? t.phantom_meta : t;
    var tm = t.type === 'slot' ? t.master : t;
    if (u.type !== pm.expects) return 'Wrong block. Should be ' + pm.expects;
    var def = BB.BLOCKS[u.type];
    if (!def) return '';
    var masterParams = (tm && tm.params) || pm.params || [];
    for (var i = 0; i < masterParams.length; i++) {
      if (!def.inputs[i]) continue;
      var up = u.params[i] || '', tp = masterParams[i] || '';
      if (u.type === 'tone' && i === 2 && tp.trim() === '') continue; // Ignore duration mismatch if master is empty
      if (up.trim() !== tp.trim()) {
        var lbl = def.inputs[i].l || 'field';
        return tier === 3 ? 'Check ' + lbl + ': expected "' + tp + '"' : 'Check ' + lbl;
      }
    }
    if (pm.expects === 'ifblock' || pm.expects === 'whileloop' || pm.expects === 'elseifclause') {
      var h = BB.generateCondHint(u.condition, pm.condition, tier); if (h) return h;
    }
    if (pm.expects === 'forloop') {
      if ((u.forinit || '') !== (pm.forinit || '')) return tier === 3 ? 'Init: ' + pm.forinit : 'Check init';
      if ((u.forcond || '') !== (pm.forcond || '')) return tier === 3 ? 'Cond: ' + pm.forcond : 'Check condition';
      if ((u.forincr || '') !== (pm.forincr || '')) return tier === 3 ? 'Incr: ' + pm.forincr : 'Check increment';
    }
    var uex = u.exChildren || [];
    var tex = (tm && tm.exChildren) || pm.exChildren || [];
    for (var i = 0; i < tex.length; i++) {
      var h = BB.generateExprHint(uex[i], tex[i], tier);
      if (h) {
        var lbl = (def && def.inputs[i]) ? def.inputs[i].l : 'slot';
        return lbl + ': ' + h;
      }
    }
    return '';
  };

  BB.collectBadIds = function (uList, tList, tier, badIds) {
    if (!uList || !tList) return;
    tList.forEach(function (tb, i) {
      var ub = uList[i];
      var tb = tList[i]; if (!tb) return;
      if (tb.type === 'slot') {
        if (ub === undefined || ub.type !== 'slot' || ub.content === null) {
          badIds.push({ id: tb.id, hint: 'Missing block' });
        } else {
          if (!BB.compareBlock(ub.content, tb)) badIds.push({ id: ub.content.id, hint: BB.generateHint(ub.content, tb, tier) });
          var pm = tb.phantom_meta;
          var uc = ub.content;
          if (pm.expects === 'ifblock') {
            BB.collectBadIds(uc.ifbody, pm.ifbody, tier, badIds);
            if (uc.elseifs && pm.elseifs) uc.elseifs.forEach(function (ei, k) { if (pm.elseifs[k]) BB.collectBadIds(ei.body, pm.elseifs[k].body, tier, badIds); });
            if (uc.elsebody && pm.elsebody) BB.collectBadIds(uc.elsebody, pm.elsebody, tier, badIds);
          } else if (pm.expects === 'forloop' || pm.expects === 'whileloop') { BB.collectBadIds(uc.body, pm.body, tier, badIds); }
          else if (pm.expects === 'elseifclause' || pm.expects === 'elseclause') { BB.collectBadIds(uc.body, pm.body, tier, badIds); }
        }
      } else if (tb.type === 'codeblock') {
        // No comparison needed for codeblocks
      }
    });
  };

  BB.compareBlock = function (u, t) {
    if (!u) return false;
    if (t.type === 'slot') {
      var pm = t.phantom_meta;
      if (u.type !== pm.expects) return false;
      var mc = t.master || pm;
      if (pm.expects === 'ifblock' || pm.expects === 'whileloop' || pm.expects === 'elseifclause') { if (!BB.compareCondition(u.condition, mc.condition)) return false; }
      if (pm.expects === 'forloop') {
        if ((u.forinit || '') !== (mc.forinit || '')) return false;
        if ((u.forcond || '') !== (mc.forcond || '')) return false; if ((u.forincr || '') !== (mc.forincr || '')) return false;
      }
      var masterParams = (t.master && t.master.params) || pm.params || [];
      for (var i = 0; i < masterParams.length; i++) {
        var up = u.params[i] || '', tp = masterParams[i] || '';
        if (u.type === 'tone' && i === 2 && tp.trim() === '') continue; // Ignore duration mismatch if master is empty
        if (up.trim() !== tp.trim()) return false;
      }
      var uex = u.exChildren || [];
      var tex = (t.master && t.master.exChildren) || pm.exChildren || [];
      for (var i = 0; i < tex.length; i++) {
        if (!BB.compareExpr(uex[i], tex[i])) return false;
      }
      return true;
    }
    return true;
  };

  // ── Sketch field validation ───────────────────────────────────────────────
  BB.checkSketchFields = function (uList, mList, badIds, path, section) {
    path = path || []; section = section || '';
    if (!uList || !mList) return;
    for (var i = 0; i < uList.length && i < mList.length; i++) {
      var ub = uList[i], mb = mList[i];
      if (!ub || !mb) continue;
      if (ub.type !== mb.type) continue;
      var bad = false;
      if (mb.params) {
        for (var j = 0; j < mb.params.length; j++) {
          var mv = mb.params[j], uv = (ub.params && ub.params[j] !== undefined) ? ub.params[j] : '';
          if (typeof mv === 'string' && mv.trim() !== '' && (!uv || (typeof uv === 'string' && uv.trim() === ''))) {
            badIds.push({ id: ub.id, section: section, path: path.concat([i]), hint: 'Fill in all the fields for this block' });
            bad = true; break;
          }
        }
      }
      if (!bad && mb.exChildren) {
        for (var j = 0; j < mb.exChildren.length; j++) {
          var me = mb.exChildren[j], ue = ub.exChildren ? ub.exChildren[j] : null;
          if (me && me.params && me.params[0] && me.params[0].trim() !== '' && (!ue || !ue.params || !ue.params[0] || ue.params[0].trim() === '')) {
            badIds.push({ id: ub.id, section: section, path: path.concat([i]), hint: 'Fill in all the fields for this block' });
            bad = true; break;
          }
        }
      }
      if (ub.type === 'ifblock') {
        BB.checkSketchFields(ub.ifbody, mb.ifbody, badIds, path.concat([i, 'ifbody']), section);
        if (ub.elseifs && mb.elseifs) {
          ub.elseifs.forEach(function (ei, k) {
            if (mb.elseifs[k]) BB.checkSketchFields(ei.body, mb.elseifs[k].body, badIds, path.concat([i, 'elseifs', k, 'body']), section);
          });
        }
        if (mb.elsebody) BB.checkSketchFields(ub.elsebody || [], mb.elsebody, badIds, path.concat([i, 'elsebody']), section);
      } else if (ub.type === 'forloop' || ub.type === 'whileloop') {
        BB.checkSketchFields(ub.body, mb.body, badIds, path.concat([i, 'body']), section);
      } else if (ub.type === 'elseifclause' || ub.type === 'elseclause') {
        BB.checkSketchFields(ub.body, mb.body, badIds, path.concat([i, 'body']), section);
      }
    }
  };

  BB.applySketchHighlights = function () {
    document.querySelectorAll('.ws-block,.if-block,.for-block,.while-block,.phantom-block').forEach(function (el) { el.classList.remove('error-block'); });
    document.querySelectorAll('.block-hint').forEach(function (el) { el.remove(); });
    (BB.SKETCH_ERROR_PATHS || []).forEach(function (entry) {
      var res = BB.SECTIONS[entry.section];
      if (!res) return;
      for (var i = 0; i < entry.path.length; i++) {
        res = res[entry.path[i]];
        if (!res) break;
      }
      if (res && res.id) {
        var el = document.querySelector('[data-id="' + res.id + '"]');
        if (el) {
          el.classList.add('error-block');
          if (entry.hint) {
            var hd = document.createElement('div'); hd.className = 'block-hint'; hd.textContent = entry.hint;
            hd.style.display = 'block';
            var target = el.querySelector('.if-header, .for-header, .while-header') || el;
            target.appendChild(hd);
          }
        }
      }
    });
  };

  BB.validateSketch = function () {
    ('[DEBUG] validateSketch() invoked.');
    if (!BB.MASTER_SKETCH) return { valid: true };
    var badIds = [];
    ['global', 'setup', 'loop'].forEach(function (sec) {
      BB.checkSketchFields(BB.SECTIONS[sec], BB.MASTER_SKETCH[sec], badIds, [], sec);
    });
    BB.SKETCH_ERROR_PATHS = badIds;
    if (badIds.length > 0) {
      var sb = document.getElementById('statusbar');
      if (sb) { sb.style.transition = 'background 0.2s'; sb.style.background = '#ffebe9'; setTimeout(function () { sb.style.background = ''; }, 400); }
    }
    BB.applySketchHighlights();
    return { valid: badIds.length === 0, errorCount: badIds.length, errors: badIds };
  };
  window.validateSketch = BB.validateSketch;

  window.dumpDebug = function () {
    ('--- BLOCK BUILDER DEBUG DUMP ---');
    ('MASTER_SKETCH:', BB.MASTER_SKETCH);
    ('SECTIONS (Current State):', BB.SECTIONS);
    ('SKETCH_ERROR_PATHS:', BB.SKETCH_ERROR_PATHS);
    ('--------------------------------');
  };

  // ── Step completion check ─────────────────────────────────────────────────
  BB.checkStepComplete = function () {
    ('[DEBUG] checkStepComplete called, PROGRESSION_MODE:', BB.PROGRESSION_MODE);
    if (!BB.PROGRESSION_MODE) return;
    ('[DEBUG] checkStepComplete past guard');
    var phantoms = BB.countPhantoms(BB.SECTIONS.global) + BB.countPhantoms(BB.SECTIONS.setup) + BB.countPhantoms(BB.SECTIONS.loop);
    ('[DEBUG] phantoms:', phantoms);
    var incomplete = BB.countIncomplete(BB.SECTIONS.global) + BB.countIncomplete(BB.SECTIONS.setup) + BB.countIncomplete(BB.SECTIONS.loop);
    var total = phantoms + incomplete;
    var step = BB.STEPS && BB.STEPS[BB.CURRENT_STEP] ? BB.STEPS[BB.CURRENT_STEP] : null;
    var curGuidance = step && step.config && step.config.guidance ? step.config.guidance : 'guided';

    if (curGuidance === 'open' || curGuidance === 'free') {
      BB.nextBtnState.ready = true;
      BB.nextBtnState.mode = 'next-mode';
      BB.nextBtnState.text = 'Next Step \u2192';
      BB.nextBtnState.visible = true;
      window.dispatchEvent(new CustomEvent('bb_next_state', {
        detail: {
          state: {
            ready: true, 'check-mode': false, 'next-mode': true, hidden: false, text: BB.nextBtnState.text, prevVisible: BB.nextBtnState.prevVisible
          }
        }
      }));
      return;
    }
    if (BB.nextBtnState.mode === 'next-mode') return;
    if (BB.nextBtnState.mode === 'check-mode') {
      if (total > 0) {
        BB.nextBtnState.ready = false;
        BB.nextBtnState.text = 'Complete Step';
        BB.nextBtnState.mode = '';
        window.dispatchEvent(new CustomEvent('bb_next_state', {
          detail: {
            state: {
              ready: false, 'check-mode': false, 'next-mode': false, hidden: !BB.nextBtnState.visible, text: BB.nextBtnState.text, prevVisible: BB.nextBtnState.prevVisible
            }
          }
        }));
      }
      return;
    }

    if (phantoms > 0) BB.stepProgress = phantoms + ' block' + (phantoms === 1 ? '' : 's') + ' to place';
    else if (incomplete > 0) BB.stepProgress = incomplete + ' field' + (incomplete === 1 ? '' : 's') + ' to fill';
    else BB.stepProgress = 'Click Check Code when Finished';

    if (total === 0) {
      BB.nextBtnState.ready = true;
      BB.nextBtnState.text = 'Check Code';
      BB.nextBtnState.mode = 'check-mode';
    } else {
      BB.nextBtnState.ready = false;
      BB.nextBtnState.text = 'Complete Step';
      BB.nextBtnState.mode = '';
    }

    window.dispatchEvent(new CustomEvent('bb_step_update', { detail: { label: BB.stepLabel, progress: BB.stepProgress } }));
    window.dispatchEvent(new CustomEvent('bb_next_state', {
      detail: {
        state: {
          ready: BB.nextBtnState.ready,
          'check-mode': BB.nextBtnState.mode === 'check-mode',
          'next-mode': BB.nextBtnState.mode === 'next-mode',
          hidden: !BB.nextBtnState.visible,
          text: BB.nextBtnState.text,
          prevVisible: BB.nextBtnState.prevVisible
        }
      }
    }));
    return true;
  };

  // ── Step highlights (called by render() on every redraw) ─────────────────
  BB.applyStepHighlights = function () {
    document.querySelectorAll('.ws-block,.if-block,.for-block,.while-block,.phantom-block').forEach(function (el) { el.classList.remove('error-block'); });
    document.querySelectorAll('.block-hint').forEach(function (el) { el.remove(); });
    (BB.STEP_ERROR_IDS || []).forEach(function (bid) {
      var el = document.querySelector('[data-id="' + bid.id + '"]');
      if (el) {
        el.classList.add('error-block');
        if (bid.hint) { 
          var hd = document.createElement('div'); hd.className = 'block-hint'; hd.textContent = bid.hint; 
          hd.style.display = 'block';
          var target = el.querySelector('.if-header, .for-header, .while-header') || el;
          target.appendChild(hd);
        }
      }
    });
  };

  // ── Step validation ───────────────────────────────────────────────────────
  BB.validateStep = function () {
    if (!BB.STEPS || !BB.STEPS[BB.CURRENT_STEP]) return true;
    var tmpl = BB.STEPS[BB.CURRENT_STEP];
    var valid = true; var tier = 2; if (BB.CHECK_FAIL_COUNT >= 3) tier = 3;
    var badIds = [];
    ['global', 'setup', 'loop'].forEach(function (sec) { BB.collectBadIds(BB.SECTIONS[sec], tmpl[sec], tier, badIds); });
    if (badIds.length > 0) valid = false;
    if (!valid) {
      BB.CHECK_FAIL_COUNT++;
      BB.STEP_ERROR_IDS = badIds;
    } else {
      BB.STEP_ERROR_IDS = [];
    }
    BB.applyStepHighlights();
    return valid;
  };

  // ── Workspace builder ─────────────────────────────────────────────────────
  BB.buildWorkspace = function (stepIdx, saves) {
    if (!BB.PROGRESSION_MODE || !BB.STEPS || stepIdx >= BB.STEPS.length) return;
    var step = BB.STEPS[stepIdx];
    if (BB.STUDENT_SAVES[stepIdx]) {
      var savedState = BB.STUDENT_SAVES[stepIdx];
      BB.SECTIONS.global = JSON.parse(JSON.stringify(savedState.global));
      BB.SECTIONS.setup  = JSON.parse(JSON.stringify(savedState.setup));
      BB.SECTIONS.loop   = JSON.parse(JSON.stringify(savedState.loop));
    } else {
      BB.SECTIONS.global = JSON.parse(JSON.stringify(step.global));
      BB.SECTIONS.setup  = JSON.parse(JSON.stringify(step.setup));
      BB.SECTIONS.loop   = JSON.parse(JSON.stringify(step.loop));
    }
    BB.PALETTE_ALLOWED = (step.palette !== undefined && step.palette !== null) ? step.palette : null;
    BB.stepLabel = step.label;
    window.dispatchEvent(new CustomEvent('bb_step_update', { detail: { label: BB.stepLabel, progress: '' } }));
    var curGuidance = step && step.config && step.config.guidance ? step.config.guidance : (step.config.structure === 'none' ? 'open' : 'guided');
    window.CURRENT_STEP_META = { guidance: curGuidance, view: step.config.interface, readOnly: !!step.config.readonly };
    window.dispatchEvent(new CustomEvent('stepchange', { detail: window.CURRENT_STEP_META }));
    var activeId = (step.active === 'global') ? 'gs' : (step.active === 'setup' ? 'ss' : 'ls');
    BB.expandSection(activeId);
    BB.STEP_ERROR_IDS = [];
    BB.CHECK_FAIL_COUNT = 0;
    BB.nextBtnState.visible  = !(stepIdx >= BB.STEPS.length - 1);
    BB.nextBtnState.ready    = false; BB.nextBtnState.mode = ''; BB.nextBtnState.text = 'Complete Step'; BB.nextBtnState.prevVisible = stepIdx > 0;
    window.dispatchEvent(new CustomEvent('bb_next_state', { detail: { state: { ready: false, 'check-mode': false, 'next-mode': false, hidden: !BB.nextBtnState.visible, text: BB.nextBtnState.text, prevVisible: BB.nextBtnState.prevVisible } } }));
    window.dispatchEvent(new CustomEvent('bb_next_state', { detail: { state: { ready: false, 'check-mode': false, 'next-mode': false, hidden: !BB.nextBtnState.visible, text: BB.nextBtnState.text, prevVisible: BB.nextBtnState.prevVisible, feedback: null } } }));
    if (window.updateDrawer) window.updateDrawer(stepIdx);
    BB.checkStepComplete(); BB.render(); BB.genCode();
  };

  // ── bbNext / bbPrev ───────────────────────────────────────────────────────
  window.bbNext = function () {
    if (!BB.nextBtnState.ready) return;
    if (BB.nextBtnState.mode === 'check-mode') {
      if (BB.validateStep()) {
        BB.nextBtnState.text = 'Next Step \u2192';
        BB.nextBtnState.mode = 'next-mode';
        window.dispatchEvent(new CustomEvent('bb_next_state', {
          detail: {
            state: {
              ready: true, 'check-mode': false, 'next-mode': true, hidden: false,
              text: BB.nextBtnState.text, prevVisible: BB.nextBtnState.prevVisible,
              feedback: { text: 'Correct!', type: 'success' }
            }
          }
        }));
        BB.CHECK_FAIL_COUNT = 0;
      } else {
        window.dispatchEvent(new CustomEvent('bb_next_state', {
          detail: {
            state: {
              ready: true, 'check-mode': true, 'next-mode': false, hidden: false,
              text: BB.nextBtnState.text, prevVisible: BB.nextBtnState.prevVisible,
              feedback: { text: 'Try again - check highlighted blocks', type: 'error' }
            }
          }
        }));
      }
      return;
    }
    try {
      BB.STUDENT_SAVES[BB.CURRENT_STEP] = JSON.parse(JSON.stringify(BB.SECTIONS));
      BB.CURRENT_STEP++; BB.buildWorkspace(BB.CURRENT_STEP); BB.saveBlocks();
      if (window.openDrawer) window.openDrawer();
    } catch (e) { BB.flash('ERR: ' + e.message); console.error(e); }
  };

  window.bbPrev = function () {
    if (!BB.PROGRESSION_MODE || BB.CURRENT_STEP <= 0) return;
    BB.CURRENT_STEP--; BB.STUDENT_SAVES.pop(); BB.buildWorkspace(BB.CURRENT_STEP);
  };

  window.getCurrentStepMeta = function () { return window.CURRENT_STEP_META || {}; };

  ('[DEBUG] bb-validation.js: done');
})();
