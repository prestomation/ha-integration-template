import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    environment: 'jsdom',
    globals: true,
    include: [
      'tests/frontend/**/*.test.js',
      'custom_components/example_integration/frontend/test/**/*.test.js',
    ],
  },
});
