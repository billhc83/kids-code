// Mirrors templates/block_builder_fragment.html's #block-builder-ui markup
// (minus the <link>/<script> tags) — the real element ids/classes that
// bb-render.js's load-time setupSection('gs'|'ss'|'ls', ...) calls and
// block_builder.js's genCode()/render() require to exist, so the full
// script stack can be loaded in jsdom without a null-element crash.
export const BLOCK_BUILDER_FIXTURE_HTML = `
<div id="block-builder-ui">
  <div id="statusbar">click a section or if body to select it</div>
  <div id="app">
    <div id="palette">
      <div id="pal-context">select a section</div>
      <div id="pal-blocks-section"></div>
      <div id="pal-expr-section">
        <div class="pal-title-expr" id="pal-expr-title">Expressions</div>
      </div>
    </div>
    <div id="workspace">
      <div class="section s-global" id="gs">
        <div class="section-header"><h3>Global</h3><span class="toggle-arrow">&#9660;</span></div>
        <div class="section-body" id="gs-body"></div>
      </div>
      <div class="section s-setup expanded" id="ss">
        <div class="section-header"><h3>setup()</h3><span class="toggle-arrow">&#9660;</span></div>
        <div class="section-body" id="ss-body"></div>
      </div>
      <div class="section s-loop" id="ls">
        <div class="section-header"><h3>loop()</h3><span class="toggle-arrow">&#9660;</span></div>
        <div class="section-body" id="ls-body"></div>
      </div>
    </div>
    <div id="codepanel">
      <div id="msg"></div>
      <div id="codeout">// sketch\n// appears\n// here</div>
    </div>
  </div>
</div>
`;

export function installBlockBuilderFixture() {
  document.body.innerHTML = BLOCK_BUILDER_FIXTURE_HTML;
}
