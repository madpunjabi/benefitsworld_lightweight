import { defineConfig } from "@playwright/test";

const ROOT = "..";

export default defineConfig({
  testDir: "./tests",
  timeout: 30_000,
  reporter: [["list"]],
  // All specs share ONE live backend/DB (there is no per-test database).
  // Any test that calls /lab/reset or /lab/clock/advance mutates global
  // state that every other running test can observe, so tests must not
  // run concurrently against each other.
  workers: 1,
  use: {
    screenshot: "off",
  },
  webServer: [
    {
      command: `${ROOT}/backend/.venv/bin/uvicorn app.main:app --port 8000`,
      cwd: `${ROOT}/backend`,
      url: "http://localhost:8000/health",
      reuseExistingServer: true,
      timeout: 30_000,
    },
    {
      command: "npm run dev",
      cwd: `${ROOT}/frontend-agent`,
      url: "http://localhost:5173",
      reuseExistingServer: true,
      timeout: 30_000,
    },
    {
      command: "npm run dev",
      cwd: `${ROOT}/frontend-lab`,
      url: "http://localhost:5174",
      reuseExistingServer: true,
      timeout: 30_000,
    },
  ],
});
