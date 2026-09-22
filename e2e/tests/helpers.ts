import { readFileSync } from "node:fs";
import path from "node:path";
import type { APIRequestContext } from "@playwright/test";

function readLabToken(): string {
  const envPath = path.resolve(__dirname, "../../.env");
  const content = readFileSync(envPath, "utf-8");
  const match = content.match(/^LAB_TOKEN=(.*)$/m);
  if (!match) throw new Error("LAB_TOKEN not found in repo-root .env");
  return match[1].trim();
}

export const LAB_TOKEN = readLabToken();
export const API_BASE = "http://localhost:8000";
export const AGENT_BASE = "http://localhost:5173";

// Every test starts from a clean, deterministic scenario state so tests
// are independent of run order and of each other's uploads.
export async function resetEnvironment(request: APIRequestContext) {
  const res = await request.post(`${API_BASE}/lab/reset`, {
    headers: { "X-Lab-Token": LAB_TOKEN },
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
