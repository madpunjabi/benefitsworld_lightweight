import { readFileSync } from "node:fs";
import path from "node:path";
import type { APIRequestContext, Page } from "@playwright/test";
import { expect } from "@playwright/test";

function readEnvVar(name: string): string {
  const envPath = path.resolve(__dirname, "../../.env");
  const content = readFileSync(envPath, "utf-8");
  const match = content.match(new RegExp(`^${name}=(.*)$`, "m"));
  if (!match) throw new Error(`${name} not found in repo-root .env`);
  return match[1].trim();
}

export const LAB_TOKEN = readEnvVar("LAB_TOKEN");
// Falls back to config.py's own local-dev default so this keeps working
// even if a developer's .env predates LAB_CONSOLE_PASSWORD.
export const LAB_CONSOLE_PASSWORD = (() => {
  try {
    return readEnvVar("LAB_CONSOLE_PASSWORD");
  } catch {
    return "dev-lab-password-benefitsworld-local-only";
  }
})();
export const API_BASE = "http://localhost:8000";
export const AGENT_BASE = "http://localhost:5173";
export const LAB_BASE = "http://localhost:5174";

// The Lab Console now sits behind a server-verified login (POST
// /lab/login) instead of an embedded token — every e2e test that visits
// it directly must log in first, exactly as a real researcher would.
//
// App.tsx shows "Loading…" while its own initial GET /lab/session check
// is in flight, then renders either the login form or the console. A
// synchronous isVisible() check taken immediately after goto() can win
// that race and see neither yet, so this waits for whichever of the two
// actually appears first instead of assuming one has already resolved.
export async function loginToLabConsole(page: Page) {
  const passwordField = page.getByTestId("lab-login-password");
  const labConsole = page.getByTestId("page-lab-console");
  await passwordField.or(labConsole).first().waitFor();

  if (await passwordField.isVisible()) {
    await passwordField.fill(LAB_CONSOLE_PASSWORD);
    await page.getByTestId("lab-login-submit").click();
  }
  await expect(labConsole).toBeVisible();
}

// Every test starts from a clean, deterministic scenario state so tests
// are independent of run order and of each other's uploads. Omitting
// scenarioId (every existing BW-001 test) always resets into BW-001,
// regardless of whatever scenario a previous test last loaded.
export async function resetEnvironment(request: APIRequestContext, scenarioId?: string) {
  const res = await request.post(`${API_BASE}/lab/reset`, {
    headers: { "X-Lab-Token": LAB_TOKEN },
    data: scenarioId ? { scenario_id: scenarioId } : {},
  });
  if (!res.ok()) {
    throw new Error(`environment reset failed: ${res.status()}`);
  }
}

// Stands in for the researcher/harness advancing simulated time — the
// benchmark agent has no equivalent tool (see IMPLEMENTATION_PLAN.md).
export async function advanceTime(request: APIRequestContext, toDay: number) {
  const res = await request.post(`${API_BASE}/lab/clock/advance`, {
    headers: { "X-Lab-Token": LAB_TOKEN, "Content-Type": "application/json" },
    data: { to_day: toDay },
  });
  if (!res.ok()) {
    throw new Error(`advance to day ${toDay} failed: ${res.status()}`);
  }
}
