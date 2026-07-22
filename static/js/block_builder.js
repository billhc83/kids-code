// block_builder.js — Entry point: reads BB_CONFIG, code generation, persistence, window exports, and initialization
// Load order: bb-blocks.js → bb-render.js → bb-validation.js → block_builder.js (this file)
(function () {
  // console.log('[BB] block_builder.js: Execution started.');
  var CFG = window.BB_CONFIG;
  if (!CFG) { /* console.error('[BB] block_builder.js: BB_CONFIG is missing!'); */ return; }
  // console.log('[BB] Config loaded. mode=' + CFG.mode + ' steps=' + (CFG.steps ? CFG.steps.length : 'undefined') + ' force_preset=' + CFG.force_preset);

  var BB = window._BB;

  // ── Populate config into shared state ─────────────────────────────────────
  BB.USERNAME     = CFG.username;
  BB.PAGE         = CFG.page;
  BB.MASTER_SKETCH = CFG.master || null;

  BB.DEFAULT_VIEW  = CFG.default_view;
  BB.LOCK_VIEW     = CFG.lock_view;
  BB.READONLY_MODE = CFG.readonly_mode;
  BB.LOCK_MODE     = CFG.lock_mode;
  BB.AUTHORING_MODE = !!CFG.authoring_mode;
  BB.PALETTE_ALLOWED = CFG.palette || null;

  // ── Code generation ────────────────────────────────────────────────────────
  BB.genBlocks = function (arr, indent) {
    var lines = [], extra = 0;
    arr.forEach(function (b) {
      var blockToGen = b;
      if (b.type === 'slot') {
        if (b.content === null) return;
        blockToGen = b.content;
      }
      if (blockToGen.type === 'codeblock') {
        var c = (blockToGen.params[0] || '').trim();
        var cForIndent = c.replace(/\/\/.*$/, '').trim();
        if (cForIndent === '}' || cForIndent.match(/^\}/)) extra = Math.max(0, extra - 1);
        lines.push(BB.genBlock(blockToGen, indent + extra));
        if (cForIndent.charAt(cForIndent.length - 1) === '{') extra++;
      } else { lines.push(BB.genBlock(blockToGen, indent + extra)); }
    });
    return lines.join('\n');
  };

  BB.genBlock = function (block, indent) {
    var pad = ''; for (var i = 0; i < indent; i++) pad += '   ';
    var blockToGen = block;
    if (block.type === 'slot') {
      if (block.content === null) return '';
      blockToGen = block.content;
    }
    if (blockToGen.type === 'ifblock') {
      var lines = [pad + 'if (' + BB.genCond(blockToGen.condition) + ') {'];
      lines.push(BB.genBlocks(blockToGen.ifbody, indent + 1));
      lines.push(pad + '}');
      blockToGen.elseifs.forEach(function (ei) {
        lines.push(pad + 'else if (' + BB.genCond(ei.condition) + ') {');
        lines.push(BB.genBlocks(ei.body, indent + 1));
        lines.push(pad + '}');
      });
      if (blockToGen.elsebody !== null) {
        lines.push(pad + 'else {');
        lines.push(BB.genBlocks(blockToGen.elsebody.body, indent + 1));
        lines.push(pad + '}');
      }
      return lines.join('\n');
    }
    if (blockToGen.type === 'elseifclause') {
      var lines = [pad + 'else if (' + BB.genCond(blockToGen.condition) + ') {'];
      lines.push(BB.genBlocks(blockToGen.body || [], indent + 1));
      lines.push(pad + '}');
      return lines.join('\n');
    }
    if (blockToGen.type === 'elseclause') {
      var lines = [pad + 'else {'];
      lines.push(BB.genBlocks(blockToGen.body || [], indent + 1));
      lines.push(pad + '}');
      return lines.join('\n');
    }
    if (blockToGen.type === 'forloop') {
      var init = blockToGen.forinit || 'int i = 0';
      var cond = blockToGen.forcond || 'i < 10';
      var incr = blockToGen.forincr || 'i++';
      var lines = [pad + 'for (' + init + '; ' + cond + '; ' + incr + ') {'];
      lines.push(BB.genBlocks(blockToGen.body || [], indent + 1));
      lines.push(pad + '}');
      return lines.join('\n');
    }
    if (blockToGen.type === 'whileloop') {
      var cond = blockToGen.condition ? BB.genCond(blockToGen.condition) : (blockToGen.whilecond || 'true');
      var lines = [pad + 'while (' + cond + ') {'];
      lines.push(BB.genBlocks(blockToGen.body || [], indent + 1));
      lines.push(pad + '}');
      return lines.join('\n');
    }
    return pad + BB.BLOCKS[blockToGen.type].genStmt(blockToGen.params, blockToGen.exChildren || []);
  };

  function hasServoBlocks() {
    function walkArr(arr) {
      if (!arr) return false;
      for (var i = 0; i < arr.length; i++) {
        var b = arr[i].type === 'slot' ? arr[i].content : arr[i];
        if (!b) continue;
        if (b.type && b.type.indexOf('servo') === 0) return true;
        if (b.ifbody && walkArr(b.ifbody)) return true;
        if (b.elseifs) for (var j = 0; j < b.elseifs.length; j++) { if (walkArr(b.elseifs[j].body)) return true; }
        if (b.elsebody && walkArr(b.elsebody.body)) return true;
        if (b.body && walkArr(b.body)) return true;
      }
      return false;
    }
    return walkArr(BB.SECTIONS.global) || walkArr(BB.SECTIONS.setup) || walkArr(BB.SECTIONS.loop);
  }

  BB.genCode = function () {
    var co = document.getElementById('codeout');
    var gv = BB.genBlocks(BB.SECTIONS.global, 0);
    var sc = BB.genBlocks(BB.SECTIONS.setup, 1);
    var lc = BB.genBlocks(BB.SECTIONS.loop, 1);
    var includes = hasServoBlocks() ? '#include <Servo.h>\n\n' : '';
    co.textContent = '// Arduino Sketch\n// Block Builder\n// ------------\n\n'
      + includes
      + (gv ? gv + '\n\n' : '')
      + 'void setup() {\n' + (sc ? sc + '\n' : '') + '}'
      + '\n\nvoid loop() {\n' + (lc ? lc + '\n' : '') + '}';
    BB.checkStepComplete();
  };
  window.genCode = BB.genCode;

  BB.findBlockById = function (id) {
    var found = null;
    function walk(arr) {
      if (!arr) return;
      for (var i = 0; i < arr.length; i++) {
        var b = arr[i];
        var blockToCheck = b.type === 'slot' ? b.content : b;
        if (blockToCheck && blockToCheck.id == id) { found = blockToCheck; return; }
        if (b.type === 'slot' && b.content) {
          if (b.content.type === 'ifblock') {
            if (b.content.ifbody) walk(b.content.ifbody);
            if (b.content.elseifs) b.content.elseifs.forEach(function (ei) { walk(ei.body); });
            if (b.content.elsebody) walk(b.content.elsebody.body);
          } else if (b.content.type === 'forloop' || b.content.type === 'whileloop') { if (b.content.body) walk(b.content.body); }
          else if ((b.content.type === 'elseifclause' || b.content.type === 'elseclause') && b.content.body) walk(b.content.body);
        } else if (b.type !== 'slot') {
          if (b.type === 'ifblock') {
            if (b.ifbody) walk(b.ifbody);
            if (b.elseifs) b.elseifs.forEach(function (ei) { walk(ei.body); });
            if (b.elsebody) walk(b.elsebody.body);
          } else if ((b.type === 'forloop' || b.type === 'whileloop') && b.body) walk(b.body);
          else if ((b.type === 'elseifclause' || b.type === 'elseclause') && b.body) walk(b.body);
        }
      }
    }
    ['global', 'setup', 'loop'].forEach(function (s) { walk(BB.SECTIONS[s]); });
    return found;
  };

  // ── Window exports ─────────────────────────────────────────────────────────
  window.getBlockCode = function (id) {
    var b = BB.findBlockById(id); if (!b) return null;
    var code = BB.genBlock(b, 0); return code.split('\n')[0].trim();
  };
  window.getGeneratedCode = function () { return document.getElementById('codeout').textContent; };
  window.isProgressionMode = function () { return BB.PROGRESSION_MODE; };
  window.setBlockData = function (data) {
    if (!data) return;
    BB.SECTIONS.global = data.global || [];
    BB.SECTIONS.setup  = data.setup  || [];
    BB.SECTIONS.loop   = data.loop   || [];
    BB.clearSelection();
    // Without these, an editor->blocks sync (see setMode() in the IDE
    // templates) silently updates BB.SECTIONS but never re-renders the
    // workspace, never re-runs step validation (the Next/Check button's
    // ready state goes stale), and never refreshes #codeout — which is
    // also what the sim tab's code-driven mode reads via
    // getGeneratedCode(). Same render+genCode pairing resetBlocks() already
    // uses elsewhere in this file after any other BB.SECTIONS mutation.
    BB.render();
    BB.genCode();
    if (BB.MASTER_SKETCH) BB.validateSketch();
  };

  // ── Persistence ─────────────────────────────────────────────────────────────
  BB.flash = function (txt) {
    var mb = document.getElementById('msg'); mb.textContent = txt; mb.classList.add('show');
    setTimeout(function () { mb.classList.remove('show'); }, 2500);
  };

  window.copyCode = function () {
    var txt = document.getElementById('codeout').textContent;
    if (navigator.clipboard && navigator.clipboard.writeText)
      navigator.clipboard.writeText(txt).then(function () { BB.flash('Copied!'); }).catch(function () { BB.fbCopy(txt); });
    else BB.fbCopy(txt);
  };

  BB.fbCopy = function (txt) {
    var ta = document.createElement('textarea'); ta.value = txt;
    ta.style.cssText = 'position:fixed;opacity:0;'; document.body.appendChild(ta); ta.select();
    try { document.execCommand('copy'); BB.flash('Copied!'); } catch (e) { BB.flash('Select manually'); }
    document.body.removeChild(ta);
  };

  BB.saveBlocks = function () {
    if (!BB.USERNAME || !BB.PAGE) return;
    var state;
    if (BB.PROGRESSION_MODE) {
      // Snapshot the current in-progress step so it survives a page reload
      var saves = BB.STUDENT_SAVES.slice();
      saves[BB.CURRENT_STEP] = { global: BB.SECTIONS.global, setup: BB.SECTIONS.setup, loop: BB.SECTIONS.loop };
      state = { current_step: BB.CURRENT_STEP, student_saves: saves };
    } else {
      state = { global: BB.SECTIONS.global, setup: BB.SECTIONS.setup, loop: BB.SECTIONS.loop };
    }
    fetch('/api/blocks/save', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ page: BB.PAGE, blocks_json: JSON.stringify(state) })
    }).then(function (r) { if (r.ok) BB.flash('Saved!'); else BB.flash('Save failed'); });
  };
  window.saveBlocks = BB.saveBlocks;

  BB.loadBlocks = function () {
    if (!BB.USERNAME || !BB.PAGE || BB.PAGE === 'null' || BB.PAGE === 'undefined') return;
    fetch('/api/blocks/load?page=' + encodeURIComponent(BB.PAGE))
      .then(function (r) { return r.json(); })
      .then(function (resp) {
        var data = resp.data;
        // console.log('[BB:loadBlocks] response rows=' + (data ? data.length : 'null'));
        if (data && data.length > 0) {
          var saved = JSON.parse(data[0].blocks_json);
          // console.log('[BB:loadBlocks] found save: current_step=' + saved.current_step + ' student_saves len=' + (saved.student_saves ? saved.student_saves.length : 'none'));
          if (BB.PROGRESSION_MODE) {
            // console.log('[BB:loadBlocks] saved.student_saves:', JSON.stringify(saved.student_saves));
            if (saved.current_step !== undefined) {
              var savedStep = saved.current_step;
              if (savedStep >= BB.STEPS.length) {
                // console.log('[loadBlocks] saved step ' + savedStep + ' out of bounds (len=' + BB.STEPS.length + '), resetting to 0');
                savedStep = 0;
              }
              BB.CURRENT_STEP   = savedStep;
              BB.STUDENT_SAVES  = saved.student_saves || [];
            } else if (saved.global || saved.setup || saved.loop) {
              // Fallback: migrate old free-mode save into progression format
              BB.STUDENT_SAVES[BB.CURRENT_STEP] = { global: saved.global || [], setup: saved.setup || [], loop: saved.loop || [] };
            }
            BB.buildWorkspace(BB.CURRENT_STEP);
          } else {
            BB.SECTIONS.global = saved.global || [];
            BB.SECTIONS.setup  = saved.setup  || [];
            BB.SECTIONS.loop   = saved.loop   || [];
          }
          BB.clearSelection(); BB.render(); BB.genCode();
          if (BB.PROGRESSION_MODE) BB.checkStepComplete();
          BB.flash('Loaded!');
        }
      })
      .catch(function () { BB.flash('Load failed'); });
  };

  window.resetBlocks = function () {
    if (!confirm('Reset this step? Your progress on this step will be cleared.')) return false;
    if (BB.PROGRESSION_MODE) {
      delete BB.STUDENT_SAVES[BB.CURRENT_STEP];
      BB.buildWorkspace(BB.CURRENT_STEP);
    } else {
      BB.SECTIONS.global = CFG.blocks ? JSON.parse(JSON.stringify(CFG.blocks.global)) : [];
      BB.SECTIONS.setup  = CFG.blocks ? JSON.parse(JSON.stringify(CFG.blocks.setup))  : [];
      BB.SECTIONS.loop   = CFG.blocks ? JSON.parse(JSON.stringify(CFG.blocks.loop))   : [];
    }
    BB.saveBlocks();
    BB.clearSelection(); BB.render(); BB.genCode();
    BB.flash('Reset!');
    return true;
  };

  // ── Auto-save ──────────────────────────────────────────────────────────────
  BB._dirty = false;
  BB._autoSaveReady = false;  // only track changes after initial load

  BB.saveBlocksAuto = function () {
    if (!BB.USERNAME || !BB.PAGE) return;
    var state;
    if (BB.PROGRESSION_MODE) {
      // Snapshot the current in-progress step so it survives a page reload
      var saves = BB.STUDENT_SAVES.slice();
      saves[BB.CURRENT_STEP] = { global: BB.SECTIONS.global, setup: BB.SECTIONS.setup, loop: BB.SECTIONS.loop };
      state = { current_step: BB.CURRENT_STEP, student_saves: saves };
    } else {
      state = { global: BB.SECTIONS.global, setup: BB.SECTIONS.setup, loop: BB.SECTIONS.loop };
    }
    fetch('/api/blocks/save', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ page: BB.PAGE, blocks_json: JSON.stringify(state) })
    }).then(function (r) { if (r.ok) BB.flash('Auto-saved'); });
  };

  // Wrap BB.render so any user-driven render marks the state as dirty
  var _origRender = BB.render;
  BB.render = function () {
    _origRender.apply(this, arguments);
    if (BB.PROGRESSION_MODE) BB.applyStepHighlights();
    else BB.applySketchHighlights();
    if (BB._autoSaveReady) BB._dirty = true;
  };
  window.render = BB.render;

  setInterval(function () {
    if (BB._dirty && BB._autoSaveReady) {
      BB._dirty = false;
      BB.saveBlocksAuto();
    }
  }, 7000);

  // ── Overlay message listener ───────────────────────────────────────────────
  if (CFG.is_overlay) {
    window.addEventListener('message', function (e) {
      if (e.data && e.data.type === 'bb_save_request') {
        BB.saveBlocks();
        setTimeout(function () { window.parent.postMessage({ type: 'bb_close' }, '*'); }, 600);
      }
    });
  }

  // ── Initialization ─────────────────────────────────────────────────────────
  // console.log('[BB] Initializing workspace. mode=' + CFG.mode + ' USERNAME=' + BB.USERNAME + ' PAGE=' + BB.PAGE);
  if (CFG.mode === 'progression') {
    BB.PROGRESSION_MODE = true;
    BB.STEPS = CFG.steps;
    BB.CURRENT_STEP = 0;
    BB.STUDENT_SAVES = [];
    // console.log('[BB] Progression mode: ' + (BB.STEPS ? BB.STEPS.length : 'NO STEPS') + ' steps. Step[0]:', BB.STEPS && BB.STEPS[0] ? BB.STEPS[0].label : 'MISSING');
    BB.buildWorkspace(0, null);
  } else {
    BB.SECTIONS.global = CFG.blocks ? CFG.blocks.global : [];
    BB.SECTIONS.setup  = CFG.blocks ? CFG.blocks.setup  : [];
    BB.SECTIONS.loop   = CFG.blocks ? CFG.blocks.loop   : [];
    BB.render();
    BB.genCode();
  }
  // console.log('[BB] loadBlocks check: USERNAME=' + !!BB.USERNAME + ' PROGRESSION_MODE=' + !!BB.PROGRESSION_MODE + ' force_preset=' + CFG.force_preset + ' → will load=' + !!(BB.USERNAME && (BB.PROGRESSION_MODE || !CFG.force_preset)));
  if (BB.USERNAME && (BB.PROGRESSION_MODE || !CFG.force_preset)) BB.loadBlocks();
  BB.updatePalette();
  BB.render();
  if (BB.PROGRESSION_MODE) BB.checkStepComplete();

  // Enable dirty tracking after initial load settles (500 ms grace period)
  setTimeout(function () { BB._autoSaveReady = true; }, 500);
})();
