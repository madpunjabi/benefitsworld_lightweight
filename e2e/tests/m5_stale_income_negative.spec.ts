import path from "node:path";
import { expect, test } from "@playwright/test";
import { AGENT_BASE, advanceTime, resetEnvironment } from "./helpers";

const SCREENSHOT_DIR = path.resolve(__dirname, "../screenshots");

test.beforeEach(async ({ request }) => {
  await resetEnvironment(request);
});

test("negative: re-uploading the once-current D-101 does not satisfy the Day-18 updated income requirement", async ({
  page,
  request,
}) => {
  await advanceTime(request, 18);

  await page.goto(`${AGENT_BASE}/portal`);
  await expect(page.getByTestId("requirement-updated_income_verification")).toBeVisible();

  // The agent (mistakenly) relies on the previously-correct D-101 instead
  // of the newer D-107.
  await page.getByTestId("requirement-select-updated_income_verification").selectOption("D-101");
  await page.getByTestId("requirement-upload-updated_income_verification").click();

  await page.reload();
  // D-101 is received (an ordinary, real document — this isn't the
  // silent-failure mechanic) but the requirement stays open: stale
  // evidence does not satisfy a request for current proof.
  await expect(page.getByTestId("received-doc-D-101")).toBeVisible();
  await expect(page.getByTestId("requirement-updated_income_verification")).toBeVisible();
  await page.screenshot({ path: path.join(SCREENSHOT_DIR, "m5-neg-01-stale-d101-insufficient.png") });
});
