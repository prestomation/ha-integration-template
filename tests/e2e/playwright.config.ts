import { defineConfig, devices } from '@playwright/test';

const HA_URL = process.env.HA_URL || 'http://localhost:8123';

export default defineConfig({
  testDir: './tests',
  timeout: 60_000,
  expect: { timeout: 15_000 },
  fullyParallel: false,
  workers: 1,
  reporter: process.env.CI ? [['html', { open: 'never' }], ['list']] : 'list',
  use: {
    baseURL: HA_URL,
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    // Auth state captured once by global-setup (a real HA login).
    storageState: './.auth/state.json',
  },
  globalSetup: require.resolve('./global-setup'),
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  ],
});
