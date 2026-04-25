import { defineConfig, devices } from "@playwright/test";

/**
 * Playwright E2E config.
 *
 * Runs against a locally-started Next.js dev server. In CI the backend is
 * provided via GitHub Actions `services:` (Postgres + Redis) and the frontend
 * `webServer` is spun up here.
 */
export default defineConfig({
  testDir: "./e2e",
  timeout: 30_000,
  expect: { timeout: 5_000 },
  fullyParallel: true,
  reporter: process.env.CI ? "line" : "html",
  retries: process.env.CI ? 2 : 0,

  use: {
    baseURL: process.env.E2E_BASE_URL ?? "http://localhost:3000",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },

  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],

  webServer: process.env.CI
    ? {
        command: "pnpm build && pnpm start",
        url: "http://localhost:3000",
        reuseExistingServer: false,
        timeout: 120_000,
      }
    : undefined,
});
