import { loadScript } from './loadScript.js';
import { installBlockBuilderFixture } from './domFixture.js';

// Extra DOM the step-tabs shell (static/js/teacher-authoring.js) expects
// beyond the plain block-builder fixture: the tab strip, settings panel, the
// open-step raw textarea, and a form wrapping the "Save Draft" button +
// hidden steps_json input — mirrors what templates/teacher_authoring_build.html
// wires up around the included block_builder_fragment.html markup.
function installTeacherAuthoringFixture() {
  installBlockBuilderFixture();
  var wrap = document.createElement('div');
  wrap.innerHTML =
    '<div id="ta-tabs"></div>' +
    '<div id="ta-settings"></div>' +
    '<textarea id="ta-open-raw" style="display:none;"></textarea>' +
    '<form id="ta-form">' +
    '  <input type="hidden" name="steps_json" id="ta-steps-json">' +
    '  <button type="submit" id="ta-save-btn">Save Draft (Live)</button>' +
    '</form>';
  while (wrap.firstChild) document.body.appendChild(wrap.firstChild);
}

// Loads the real bb-blocks -> bb-render -> bb-validation -> block_builder ->
// teacher-authoring chain against the real fragment markup plus the extra TA
// shell elements above, with authoring_mode on by default (this module has
// no reason to load with it off).
export function loadTeacherAuthoringStack(configOverrides = {}) {
  installTeacherAuthoringFixture();
  delete window._BB;
  delete window.TA;
  window.BB_CONFIG = {
    mode: 'freeform',
    username: null,
    page: null,
    blocks: { global: [], setup: [], loop: [] },
    master: null,
    default_view: 'blocks',
    lock_view: false,
    readonly_mode: false,
    lock_mode: false,
    palette: null,
    is_overlay: false,
    force_preset: false,
    authoring_mode: true,
    ...configOverrides,
  };
  loadScript('bb-blocks.js');
  loadScript('bb-render.js');
  loadScript('bb-validation.js');
  loadScript('block_builder.js');
  loadScript('teacher-authoring.js');
  return { BB: window._BB, TA: window.TA };
}
