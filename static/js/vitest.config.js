import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    environment: 'jsdom',
    include: ['tests/**/*.test.js'],
    // The source files under test log verbosely (e.g. block_builder.js's
    // '[BB] ...' init trace) — real diagnostic output when debugging the
    // app in a browser, just noise in a test run.
    onConsoleLog: () => false,
  },
});
