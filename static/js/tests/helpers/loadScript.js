import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const JS_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..');

// Loads one of the plain (non-module) `static/js/*.js` files by evaluating
// its source in the global scope. These files are `(function(){...})()`
// IIFEs that hang everything off `window`/`document`, never `export` — an
// indirect eval is the only way to run them unmodified under Vitest's jsdom
// environment while still landing their side effects on the real globals.
export function loadScript(filename) {
  const src = fs.readFileSync(path.join(JS_ROOT, filename), 'utf8');
  (0, eval)(src);
}
