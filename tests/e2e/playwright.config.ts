import { defineConfig, devices } from "@playwright/test";

const API_PORT = Number(process.env.E2E_API_PORT ?? 8000);
const WEB_PORT = Number(process.env.E2E_WEB_PORT ?? 3000);

export default defineConfig({
  testDir: ".",
  timeout: 60_000,
  fullyParallel: false,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? [["github"], ["html", { open: "never" }]] : "list",
  use: {
    baseURL: `http://localhost:${WEB_PORT}`,
    trace: "retain-on-failure",
    ...(process.env.PLAYWRIGHT_CHROMIUM_PATH
      ? { launchOptions: { executablePath: process.env.PLAYWRIGHT_CHROMIUM_PATH } }
      : {}),
  },
  projects: [
    { name: "desktop", use: { ...devices["Desktop Chrome"] } },
    { name: "mobile", use: { ...devices["Pixel 7"] }, testMatch: /smoke/ },
  ],
  webServer: [
    {
      command: `uv run uvicorn docmorph_api.main:create_app --factory --port ${API_PORT}`,
      cwd: "../..",
      url: `http://localhost:${API_PORT}/health`,
      reuseExistingServer: !process.env.CI,
      env: {
        DOCMORPH_ENV: "test",
        DOCMORPH_DATABASE_URL: "sqlite:///./var/e2e.db",
        DOCMORPH_STORAGE_LOCAL_PATH: "./var/e2e-storage",
      },
    },
    {
      command: `pnpm --filter @docmorph/web exec next start --port ${WEB_PORT}`,
      cwd: "../..",
      url: `http://localhost:${WEB_PORT}`,
      reuseExistingServer: !process.env.CI,
      env: { DOCMORPH_API_URL: `http://localhost:${API_PORT}` },
    },
  ],
});
