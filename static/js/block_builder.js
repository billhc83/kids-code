// block_builder.js — Entry point: reads BB_CONFIG, code generation, persistence, window exports, and initialization
// Load order: bb-blocks.js → bb-render.js → bb-validation.js → block_builder.js (this file)
(function () {
  ('[DEBUG] block_builder.js: Execution started.');
  var CFG = window.BB_CONFIG;
  if (!CFG) { console.error('[DEBUG] block_builder.js: BB_CONFIG is missing!'); return; }
  ('[DEBUG] block_builder.js: Config loaded.', CFG.mode);

  var BB = window._BB;

  // ── Populate config into shared state ─────────────────────────────────────
  BB.USERNAME     = CFG.username;
  BB.PAGE         = CFG.page;
  BB.MASTER_SKETCH = CFG.master || null;
  BB.SUPABASE_URL  = CFG.supabase_url;
  BB.SUPABASE_KEY  = CFG.supabase_key;
  BB.DEFAULT_VIEW  = CFG.default_view;
  BB.LOCK_VIEW     = CFG.lock_view;
  BB.READONLY_MODE = CFG.readonly_mode;
  BB.LOCK_MODE     = CFG.lock_mode;
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
        lines.push(BB.genBlocks(blockToGen.elsebody, indent + 1));
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

  BB.genCode = function () {
    var co = document.getElementById('codeout');
    var gv = BB.genBlocks(BB.SECTIONS.global, 0);
    var sc = BB.genBlocks(BB.SECTIONS.setup, 1);
    var lc = BB.genBlocks(BB.SECTIONS.loop, 1);
    co.textContent = '// Arduino Sketch\n// Block Builder\n// ------------\n\n'
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
            if (b.content.elsebody) walk(b.content.elsebody);
          } else if (b.content.type === 'forloop' || b.content.type === 'whileloop') { if (b.content.body) walk(b.content.body); }
          else if ((b.content.type === 'elseifclause' || b.content.type === 'elseclause') && b.content.body) walk(b.content.body);
        } else if (b.type !== 'slot') {
          if (b.type === 'ifblock') {
            if (b.ifbody) walk(b.ifbody);
            if (b.elseifs) b.elseifs.forEach(function (ei) { walk(ei.body); });
            if (b.elsebody) walk(b.elsebody);
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
    fetch(BB.SUPABASE_URL + '/rest/v1/block_saves?on_conflict=username,page', {
      method: 'POST',
      headers: {
        'apikey': BB.SUPABASE_KEY, 'Authorization': 'Bearer ' + BB.SUPABASE_KEY,
        'Content-Type': 'application/json', 'Prefer': 'resolution=merge-duplicates,return=minimal'
      },
      body: JSON.stringify({ username: BB.USERNAME, page: BB.PAGE, blocks_json: JSON.stringify(state), updated_at: new Date().toISOString() })
    }).then(function (r) { if (r.ok) BB.flash('Saved!'); else BB.flash('Save failed'); });
  };
  window.saveBlocks = BB.saveBlocks;

  BB.loadBlocks = function () {
    if (!BB.USERNAME || !BB.PAGE || BB.PAGE === 'null' || BB.PAGE === 'undefined') return;
    fetch(BB.SUPABASE_URL + '/rest/v1/block_saves?username=eq.' + BB.USERNAME + '&page=eq.' + BB.PAGE,
      { headers: { 'apikey': BB.SUPABASE_KEY, 'Authorization': 'Bearer ' + BB.SUPABASE_KEY } })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        if (data && data.length > 0) {
          var saved = JSON.parse(data[0].blocks_json);
          if (BB.PROGRESSION_MODE) {
            if (saved.current_step !== undefined) {
              BB.CURRENT_STEP   = saved.current_step;
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
    if (!confirm('Reset this step? Your progress on this step will be cleared.')) return;
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
    fetch(BB.SUPABASE_URL + '/rest/v1/block_saves?on_conflict=username,page', {
      method: 'POST',
      headers: {
        'apikey': BB.SUPABASE_KEY, 'Authorization': 'Bearer ' + BB.SUPABASE_KEY,
        'Content-Type': 'application/json', 'Prefer': 'resolution=merge-duplicates,return=minimal'
      },
      body: JSON.stringify({ username: BB.USERNAME, page: BB.PAGE, blocks_json: JSON.stringify(state), updated_at: new Date().toISOString() })
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
  ('[DEBUG] block_builder.js: Initializing workspace.');
  if (CFG.mode === 'progression') {
    BB.PROGRESSION_MODE = true;
    BB.STEPS = CFG.steps;
    BB.CURRENT_STEP = 0;
    BB.STUDENT_SAVES = [];
    BB.buildWorkspace(0, null);
  } else {
    BB.SECTIONS.global = CFG.blocks ? CFG.blocks.global : [];
    BB.SECTIONS.setup  = CFG.blocks ? CFG.blocks.setup  : [];
    BB.SECTIONS.loop   = CFG.blocks ? CFG.blocks.loop   : [];
    BB.render();
    BB.genCode();
  }
  if (BB.USERNAME && (BB.PROGRESSION_MODE || !CFG.force_preset)) BB.loadBlocks();
  BB.updatePalette();
  BB.render();
  if (BB.PROGRESSION_MODE) BB.checkStepComplete();

  // Enable dirty tracking after initial load settles (500 ms grace period)
  setTimeout(function () { BB._autoSaveReady = true; }, 500);
})();
