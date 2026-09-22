import { execSync } from "node:child_process";
import { existsSync, readFileSync, readdirSync } from "node:fs";
import path from "node:path";
import { expect, test } from "@playwright/test";
import type { Page } from "@playwright/test";
import { AGENT_BASE, advanceTime, resetEnvironment } from "./helpers";

const FRONTEND_AGENT_DIR = path.resolve(__dirname, "../../frontend-agent");
const DIST_DIR = path.join(FRONTEND_AGENT_DIR, "dist");
const ALLOWED_ORIGIN = "http://localhost:5173";

// Collects every rendered <a href> on the current page and asserts each one
// resolves (via the browser's own href resolution, so relative paths count
// too) to the agent frontend's own origin. Anything else — an external
// site, :5174, :8000, file:// — is a click away from leaving the sandboxed
// benchmark surface, which the runner's navigate-only hook cannot see or
// block (see BW-001-v1.0.1: the Policy Library source-link bypass).
async function assertNoOffOriginLinks(page: Page, where: string) {
  const hrefs: string[] = await page.evaluate(() =>
    Array.from(document.querySelectorAll("a[href]")).map((a) => (a as HTMLAnchorElement).href),
  );
  for (const href of hrefs) {
    const origin = new URL(href).origin;
    expect(origin, `off-origin link found on ${where}: ${href}`).toBe(ALLOWED_ORIGIN);
  }
}

async function clickEachAndCheck(page: Page, testIdPrefix: string, where: string) {
  const items = page.locator(`[data-testid^="${testIdPrefix}"]`);
  const count = await items.count();
  for (let i = 0; i < count; i++) {
    await items.nth(i).click();
    await assertNoOffOriginLinks(page, `${where} (item ${i})`);
  }
}

const FORBIDDEN_PATTERNS = [
  /5174/,
  /localhost:5174/,
  /\/lab\//,
  /X-Lab-Token/i,
  /lab-token/i,
  /LabConsole/,
  /frontend-lab/,
];

test.beforeAll(() => {
  if (!existsSync(DIST_DIR)) {
    execSync("npm run build", { cwd: FRONTEND_AGENT_DIR, stdio: "inherit" });
  }
});

test("frontend-agent production bundle contains no lab references", () => {
  const files: string[] = [];
  const walk = (dir: string) => {
    for (const entry of readdirSync(dir, { withFileTypes: true })) {
      const full = path.join(dir, entry.name);
      if (entry.isDirectory()) walk(full);
      else files.push(full);
    }
  };
  walk(DIST_DIR);

  expect(files.length).toBeGreaterThan(0);

  for (const file of files) {
    const content = readFileSync(file, "utf-8");
    for (const pattern of FORBIDDEN_PATTERNS) {
      expect(content, `${path.relative(DIST_DIR, file)} matched ${pattern}`).not.toMatch(pattern);
    }
  }
});

test.describe("no clickable link can leave the agent frontend origin", () => {
  test.beforeEach(async ({ request }) => {
    await resetEnvironment(request);
  });

  test("every page, at Day 0 and Day 18, exposes only same-origin links", async ({ page, request }) => {
    // Day 0: static environment. Visit every route and open every
    // selectable item so any per-item detail content (like a policy
    // item's source citation) actually renders before we scan for links.
    await page.goto(`${AGENT_BASE}/portal`);
    await assertNoOffOriginLinks(page, "/portal (day 0)");

    await page.goto(`${AGENT_BASE}/files`);
    await assertNoOffOriginLinks(page, "/files (day 0, list)");
    await clickEachAndCheck(page, "file-item-", "/files (day 0)");

    await page.goto(`${AGENT_BASE}/policy`);
    await assertNoOffOriginLinks(page, "/policy (day 0, list)");
    await clickEachAndCheck(page, "policy-item-", "/policy (day 0)");

    await page.goto(`${AGENT_BASE}/inbox`);
    await assertNoOffOriginLinks(page, "/inbox (day 0, list)");
    await clickEachAndCheck(page, "inbox-message-", "/inbox (day 0)");

    await page.goto(`${AGENT_BASE}/calendar`);
    await assertNoOffOriginLinks(page, "/calendar (day 0)");

    await page.goto(`${AGENT_BASE}/agent`);
    await assertNoOffOriginLinks(page, "/agent (day 0)");

    // Day 18: the furthest scripted point in BW-001, where the interview,
    // housing, and updated-income events have fired and the inbox,
    // calendar, and files pages carry the most content.
    await advanceTime(request, 18);

    await page.goto(`${AGENT_BASE}/portal`);
    await assertNoOffOriginLinks(page, "/portal (day 18)");

    await page.goto(`${AGENT_BASE}/files`);
    await clickEachAndCheck(page, "file-item-", "/files (day 18)");

    await page.goto(`${AGENT_BASE}/inbox`);
    await clickEachAndCheck(page, "inbox-message-", "/inbox (day 18)");

    await page.goto(`${AGENT_BASE}/calendar`);
    await assertNoOffOriginLinks(page, "/calendar (day 18)");

    await page.goto(`${AGENT_BASE}/agent`);
    await assertNoOffOriginLinks(page, "/agent (day 18)");
  });
});
