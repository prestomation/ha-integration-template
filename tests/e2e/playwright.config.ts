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
    {
      name: 'chromium',
      use: {
        ...devices['Desktop Chrome'],
        // In sandboxed environments the Playwright CDN is blocked, so `npx
        // playwright install` can't fetch Chromium. Point at a pre-installed binary
        // via CHROMIUM_EXEC instead (unset in CI, where the install succeeds).
        ...(process.env.CHROMIUM_EXEC
          ? { launchOptions: { executablePath: process.env.CHROMIUM_EXEC } }
          : {}),
      },
    },
  ],
});
