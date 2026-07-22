// teacher-authoring.js — step-tabs/settings shell + client-side StepDraft
// extraction (plans/TEACHER_AUTHORING_LIVE_BUILDER_UI_SPEC.md §5/§6, build
// order step 3). Requires bb-blocks.js -> bb-render.js -> bb-validation.js
// -> block_builder.js to already be loaded (window._BB, BB.genCond,
// BB.genBlock) and BB.AUTHORING_MODE to be on.
//
// TA.STEPS is the in-memory list of step drafts the teacher is building.
// Each entry mirrors StepDraft (utils/teacher_authoring_serializer.py) but
// keeps its block tree in the live BB.SECTIONS shape (id/type/params/...)
// rather than the {id, kind, flag, hint, ...} Node shape materialize()
// consumes — extraction into that shape happens once, on Save, via
// extractStepDraft(). This module owns BB.SECTIONS while it's active: tab
// switches serialize the outgoing step, then load the incoming one in.
(function () {
  var BB = window._BB;
  window.TA = window.TA || {};
  var TA = window.TA;

  // Matches utils/teacher_authoring_serializer.py's _DEFAULT_READONLY.
  var TA_DEFAULT_READONLY = { open: false, guided: true, free: true, full: true };
  TA.DEFAULT_READONLY = TA_DEFAULT_READONLY;

  TA.STEPS = [];
  TA.currentIdx = 0;

  function newBlankStep(label) {
    return {
      label: label, guidance: 'guided', view: 'blocks', read_only: null,
      sections: { global: [], setup: [], loop: [] }, raw: '',
    };
  }
  TA.newBlankStep = newBlankStep;

  // ── StepDraft extraction (mirrors materialize()'s input contract) ────────
  function extractNode(block) {
    var flag = block.flag || 'locked';
    var hint = block.hint || null;
    if (block.type === 'ifblock') {
      return {
        id: block.id, kind: 'compound', compound_type: 'ifblock', flag: flag, hint: hint,
        header: BB.genCond(block.condition),
        body: block.ifbody.map(extractNode),
        elseifs: (block.elseifs || []).map(function (ei) {
          return { id: ei.id, header: BB.genCond(ei.condition), flag: ei.flag || 'locked', hint: ei.hint || null, body: ei.body.map(extractNode) };
        }),
        elsebody: block.elsebody ? { id: block.elsebody.id, flag: block.elsebody.flag || 'locked', hint: block.elsebody.hint || null, body: block.elsebody.body.map(extractNode) } : null,
      };
    }
    if (block.type === 'forloop') {
      return {
        id: block.id, kind: 'compound', compound_type: 'forloop', flag: flag, hint: hint,
        header: (block.forinit || 'int i = 0') + '; ' + (block.forcond || 'i < 10') + '; ' + (block.forincr || 'i++'),
        body: (block.body || []).map(extractNode), elseifs: [], elsebody: null,
      };
    }
    if (block.type === 'whileloop') {
      return {
        id: block.id, kind: 'compound', compound_type: 'whileloop', flag: flag, hint: hint,
        header: BB.genCond(block.condition),
        body: (block.body || []).map(extractNode), elseifs: [], elsebody: null,
      };
    }
    // Leaf (includes 'codeblock' — genBlock(block, 0) with indent 0 returns
    // its raw text unpadded, same as any other single-statement leaf).
    return { id: block.id, kind: 'leaf', flag: flag, hint: hint, line: BB.genBlock(block, 0) };
  }
  TA.extractNode = extractNode;

  function extractSection(arr) { return arr.map(extractNode); }
  TA.extractSection = extractSection;

  function extractStepDraft(step) {
    var draft = { label: step.label, guidance: step.guidance, view: step.view };
    var defaultReadonly = TA_DEFAULT_READONLY[step.guidance];
    var readOnly = (step.read_only === null || step.read_only === undefined) ? defaultReadonly : step.read_only;
    if (readOnly !== defaultReadonly) draft.read_only = readOnly;

    if (step.guidance === 'open') {
      draft.raw = step.raw || '';
      return draft;
    }
    draft.global = extractSection(step.sections.global);
    draft.setup = extractSection(step.sections.setup);
    draft.loop = extractSection(step.sections.loop);
    return draft;
  }
  TA.extractStepDraft = extractStepDraft;

  TA.buildAllStepDrafts = function () {
    serializeCurrentStepFromWorkspace();
    return TA.STEPS.map(extractStepDraft);
  };

  // ── Accumulation rule (spec §3) — mirrors utils/teacher_authoring_serializer.py's _walk() ──
  function walkIds(arr, out) {
    arr.forEach(function (node) {
      out[node.id] = true;
      if (node.type === 'ifblock') {
        walkIds(node.ifbody, out);
        (node.elseifs || []).forEach(function (ei) { out[ei.id] = true; walkIds(ei.body, out); });
        if (node.elsebody) { out[node.elsebody.id] = true; walkIds(node.elsebody.body, out); }
      } else if (node.type === 'forloop' || node.type === 'whileloop') {
        walkIds(node.body || [], out);
      }
    });
  }

  function computeSeenIds(uptoIdx) {
    var seen = {};
    for (var i = 0; i < uptoIdx; i++) {
      var step = TA.STEPS[i];
      if (step.guidance === 'open') continue;
      step.sections.global.forEach(function (n) { seen[n.id] = true; });
      walkIds(step.sections.setup, seen);
      walkIds(step.sections.loop, seen);
    }
    return seen;
  }
  TA.computeSeenIds = computeSeenIds;

  // ── Step-tabs shell ────────────────────────────────────────────────────────
  function serializeCurrentStepFromWorkspace() {
    var step = TA.STEPS[TA.currentIdx];
    if (!step) return;
    if (step.guidance === 'open') {
      var rawEl = document.getElementById('ta-open-raw');
      if (rawEl) step.raw = rawEl.value;
    } else {
      step.sections = {
        global: JSON.parse(JSON.stringify(BB.SECTIONS.global)),
        setup: JSON.parse(JSON.stringify(BB.SECTIONS.setup)),
        loop: JSON.parse(JSON.stringify(BB.SECTIONS.loop)),
      };
    }
  }
  TA.serializeCurrentStepFromWorkspace = serializeCurrentStepFromWorkspace;

  function loadStepIntoWorkspace(idx) {
    var step = TA.STEPS[idx];
    var wsEl = document.getElementById('block-builder-ui');
    var rawEl = document.getElementById('ta-open-raw');
    if (step.guidance === 'open') {
      if (wsEl) wsEl.style.display = 'none';
      if (rawEl) { rawEl.style.display = ''; rawEl.value = step.raw || ''; }
    } else {
      if (wsEl) wsEl.style.display = '';
      if (rawEl) rawEl.style.display = 'none';
      BB.SECTIONS.global = JSON.parse(JSON.stringify(step.sections.global));
      BB.SECTIONS.setup = JSON.parse(JSON.stringify(step.sections.setup));
      BB.SECTIONS.loop = JSON.parse(JSON.stringify(step.sections.loop));
      BB.AUTHORING_SEEN_IDS = computeSeenIds(idx);
      BB.clearSelection();
      BB.render();
    }
  }
  TA.loadStepIntoWorkspace = loadStepIntoWorkspace;

  function renderTabs() {
    var el = document.getElementById('ta-tabs');
    if (!el) return;
    el.innerHTML = '';
    TA.STEPS.forEach(function (step, i) {
      var btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'ta-tab' + (i === TA.currentIdx ? ' active' : '');
      btn.textContent = (i + 1) + '. ' + (step.label || 'Step ' + (i + 1));
      btn.addEventListener('click', function () { if (i !== TA.currentIdx) switchToStep(i); });
      el.appendChild(btn);
    });
    var add = document.createElement('button');
    add.type = 'button'; add.className = 'ta-tab ta-tab-add'; add.textContent = '+ Add Step';
    add.addEventListener('click', addStep);
    el.appendChild(add);
  }
  TA.renderTabs = renderTabs;

  function taField(label, control) {
    var wrap = document.createElement('div'); wrap.className = 'ta-field';
    var lb = document.createElement('label'); lb.textContent = label;
    wrap.appendChild(lb); wrap.appendChild(control); return wrap;
  }

  function renderSettingsPanel() {
    var el = document.getElementById('ta-settings');
    if (!el) return;
    el.innerHTML = '';
    var step = TA.STEPS[TA.currentIdx];

    var labelInput = document.createElement('input'); labelInput.type = 'text'; labelInput.value = step.label;
    labelInput.addEventListener('input', function (e) { step.label = e.target.value; renderTabs(); });
    el.appendChild(taField('Label', labelInput));

    // guided/free/open only — utils/teacher_authoring_serializer.py's
    // validate_step_shape() enforces this same set server-side. `full` has
    // zero precedent in any real, published lesson (2026-07-22 corpus
    // audit), and `editor` view has never safely paired with any guidance
    // this tool builds — its one real pairing is `verify`, which this tool
    // has no UI for. No per-step view choice at all; every step is 'blocks'.
    var guidanceSel = document.createElement('select');
    ['guided', 'free', 'open'].forEach(function (g) {
      var o = document.createElement('option'); o.value = g; o.textContent = g; guidanceSel.appendChild(o);
    });
    guidanceSel.value = step.guidance;
    guidanceSel.addEventListener('change', function (e) {
      step.guidance = e.target.value;
      loadStepIntoWorkspace(TA.currentIdx);
      renderSettingsPanel();
    });
    el.appendChild(taField('Guidance', guidanceSel));

    var readOnlyChk = document.createElement('input'); readOnlyChk.type = 'checkbox';
    var defaultReadonly = TA_DEFAULT_READONLY[step.guidance];
    readOnlyChk.checked = (step.read_only === null || step.read_only === undefined) ? defaultReadonly : step.read_only;
    readOnlyChk.addEventListener('change', function (e) { step.read_only = e.target.checked; });
    el.appendChild(taField('Read-only', readOnlyChk));
  }
  TA.renderSettingsPanel = renderSettingsPanel;

  function switchToStep(idx) {
    serializeCurrentStepFromWorkspace();
    TA.currentIdx = idx;
    loadStepIntoWorkspace(idx);
    renderTabs();
    renderSettingsPanel();
  }
  TA.switchToStep = switchToStep;

  function addStep() {
    // Globals carry forward automatically once declared, and setup()/loop()
    // must restate all previously-placed code at every step (see this
    // project's CLAUDE.md sketch-directive rules, and materialize_step()'s
    // seen-id dedup, which relies on later steps repeating the same node ids
    // rather than redeclaring fresh ones). So a new step starts as a copy of
    // the *last* step's accumulated tree (same ids preserved) — not blank —
    // and the teacher adds new blocks on top of it. Carrying from the last
    // step specifically (not whichever tab happens to be open) matches the
    // append-only tab order this shell supports (spec §7 — no reordering).
    serializeCurrentStepFromWorkspace();
    var lastStep = TA.STEPS[TA.STEPS.length - 1];
    var step = newBlankStep('Step ' + (TA.STEPS.length + 1));
    step.sections = JSON.parse(JSON.stringify(lastStep.sections));
    TA.STEPS.push(step);
    TA.currentIdx = TA.STEPS.length - 1;
    loadStepIntoWorkspace(TA.currentIdx);
    renderTabs();
    renderSettingsPanel();
  }
  TA.addStep = addStep;

  // ── Hydration (build order step 4 — reverse of extractStepDraft) ─────────
  // window.BB_CONFIG.initial_steps, when present, is a list already shaped
  // like TA.STEPS entries (utils/teacher_authoring_serializer.py's
  // hydrate_steps() output: {label, guidance, view, read_only, sections,
  // raw}) — no further transformation needed, just adopt it directly.
  // guided/free/open + 'blocks'-only, same set validate_step_shape() enforces
  // server-side — a draft saved before that restriction existed (or hand-
  // edited via the raw JSON view) could still have 'full' guidance or an
  // 'editor' view baked in. Normalize on load rather than surface a stale
  // choice the settings panel no longer offers a way to see or fix.
  var TA_ALLOWED_GUIDANCE = { guided: true, free: true, open: true };

  function hydrateStepsFromConfig() {
    var cfg = window.BB_CONFIG || {};
    var initial = cfg.initial_steps;
    if (!initial || !initial.length) return null;
    return initial.map(function (s) {
      return {
        label: s.label, guidance: TA_ALLOWED_GUIDANCE[s.guidance] ? s.guidance : 'guided', view: 'blocks',
        read_only: (s.read_only === undefined) ? null : s.read_only,
        sections: s.sections || { global: [], setup: [], loop: [] },
        raw: s.raw || '',
      };
    });
  }

  // ── Bootstrap ──────────────────────────────────────────────────────────────
  TA.init = function () {
    TA.STEPS = hydrateStepsFromConfig() || [newBlankStep('Step 1')];
    TA.currentIdx = 0;
    renderTabs();
    renderSettingsPanel();
    loadStepIntoWorkspace(0);

    var saveBtn = document.getElementById('ta-save-btn');
    if (saveBtn && saveBtn.form) {
      saveBtn.form.addEventListener('submit', function () {
        var hidden = document.getElementById('ta-steps-json');
        if (hidden) hidden.value = JSON.stringify(TA.buildAllStepDrafts());
      });
    }
  };
})();
