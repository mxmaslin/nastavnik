import { defineConfig, devices } from '@playwright/test';

/**
 * E2E: поднимите backend (и зависимости), например `make up` в корне репозитория.
 * Next.js поднимает Playwright через webServer (в CI — всегда новый процесс; локально — переиспользует :3000).
 */
export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: process.env.CI ? 'github' : [['list'], ['html', { open: 'never' }]],
  timeout: 60_000,
  expect: { timeout: 15_000 },
  use: {
    baseURL: process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    // В CI порты свободны — поднимем Next здесь. Локально при `make up` переиспользуем frontend:3000.
    reuseExistingServer: true,
    timeout: 120_000,
  },
});
