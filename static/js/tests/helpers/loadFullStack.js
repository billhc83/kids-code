import { loadScript } from './loadScript.js';
import { installBlockBuilderFixture } from './domFixture.js';

// Loads the real bb-blocks -> bb-render -> bb-validation -> block_builder
// chain in the order templates/block_builder_fragment.html actually loads
// them, against the real fragment markup, with a minimal BB_CONFIG. This is
// the only way to exercise block_builder.js at all — its outer IIFE bails
// immediately without window.BB_CONFIG, and its init block runs BB.render()/
// BB.genCode() against real DOM elements as an unavoidable load-time side
// effect (see plans/JS_TEST_SCOPING.md §2).
export function loadFullStack(configOverrides = {}) {
  installBlockBuilderFixture();
  delete window._BB;
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
    ...configOverrides,
  };
  loadScript('bb-blocks.js');
  loadScript('bb-render.js');
  loadScript('bb-validation.js');
  loadScript('block_builder.js');
  return window._BB;
}
