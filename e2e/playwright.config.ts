import { defineConfig } from "@playwright/test";

const ROOT = "..";

export default defineConfig({
  testDir: "./tests",
  timeout: 30_000,
  reporter: [["list"]],
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
