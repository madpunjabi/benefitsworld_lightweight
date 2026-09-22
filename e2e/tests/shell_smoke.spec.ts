import path from "node:path";
import { expect, test } from "@playwright/test";

const SCREENSHOT_DIR = path.resolve(__dirname, "../screenshots");

const AGENT_ROUTES: Array<[string, string]> = [
  ["/portal", "page-portal"],
  ["/inbox", "page-inbox"],
  ["/files", "page-files"],
  ["/calendar", "page-calendar"],
  ["/policy", "page-policy"],
  ["/agent", "page-agent"],
];

test.describe("Milestone 1 shell smoke test", () => {
  test("all six agent routes load on :5173", async ({ page }) => {
    for (const [route, testId] of AGENT_ROUTES) {
      await page.goto(`http://localhost:5173${route}`);
      await expect(page.getByTestId(testId)).toBeVisible();
      await page.screenshot({
        path: path.join(SCREENSHOT_DIR, `agent${route.replace("/", "-")}.png`),
      });
    }
  });

  test("Lab Console loads on :5174 and shows backend truth", async ({ page }) => {
    await page.goto("http://localhost:5174");
    await expect(page.getByTestId("page-lab-console")).toBeVisible();
    await expect(page.getByTestId("lab-scenario-id")).toHaveText("BW-001");
    await expect(page.getByTestId("lab-case-status")).toHaveText("PENDING");
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, "lab-console-initial.png") });
  });

  test("Lab Console can advance simulated time and reset", async ({ page }) => {
    await page.goto("http://localhost:5174");
    await expect(page.getByTestId("lab-sim-day")).toHaveText("0");

    await page.getByTestId("lab-advance-input").fill("18");
    await page.getByTestId("lab-advance-button").click();
    await expect(page.getByTestId("lab-sim-day")).toHaveText("18");
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, "lab-console-day18.png") });

    await page.getByTestId("lab-reset-button").click();
    await expect(page.getByTestId("lab-sim-day")).toHaveText("0");
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, "lab-console-after-reset.png") });
  });

  test("agent frontend cannot reach the lab origin from its own JS context", async ({ page }) => {
    await page.goto("http://localhost:5173/portal");
    const result = await page.evaluate(async () => {
      try {
        const res = await fetch("http://localhost:8000/lab/world_state");
        return { ok: res.ok, status: res.status, blocked: false };
      } catch (e) {
        return { blocked: true, message: String(e) };
      }
    });
    // Either the browser's CORS policy blocks the fetch outright (network
    // error, "blocked: true"), or — if it somehow reaches the server — the
    // response must be a 401 because no X-Lab-Token exists anywhere in
    // this page's JS context to send.
    if (!result.blocked) {
      expect(result.status).toBe(401);
    }
  });
});
