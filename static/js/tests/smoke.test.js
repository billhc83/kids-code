import { describe, it, expect, beforeEach } from 'vitest';
import { loadScript } from './helpers/loadScript.js';
import { loadFullStack } from './helpers/loadFullStack.js';

describe('loadScript smoke test', () => {
  beforeEach(() => {
    delete window._BB;
  });

  it('populates window._BB as a side effect of loading bb-blocks.js', () => {
    loadScript('bb-blocks.js');
    expect(window._BB).toBeDefined();
    expect(window._BB.BLOCKS).toBeDefined();
    expect(typeof window._BB.genCond).toBe('function');
  });
});

describe('loadFullStack smoke test', () => {
  it('loads all four scripts against the fixture DOM without throwing', () => {
    var BB = loadFullStack();
    expect(BB).toBeDefined();
    expect(typeof BB.genBlocks).toBe('function');
    expect(typeof BB.genBlock).toBe('function');
    expect(document.getElementById('codeout').textContent).toContain('void setup()');
  });
});
