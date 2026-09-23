import path from "node:path";
import { expect, test } from "@playwright/test";
import { AGENT_BASE, LAB_BASE, advanceTime, loginToLabConsole, resetEnvironment } from "./helpers";

const SCREENSHOT_DIR = path.resolve(__dirname, "../screenshots");

test.beforeEach(async ({ request }) => {
  await resetEnvironment(request);
});

test("negative: an unrecovered silent failure leaves housing unresolved and evaluator shows progress, not success", async ({
  page,
  request,
}) => {
  await page.goto(`${AGENT_BASE}/portal`);
  await page.getByTestId("requirement-select-earned_income_verification").selectOption("D-101");
  await page.getByTestId("requirement-upload-earned_income_verification").click();
  await page.getByTestId("requirement-select-earned_income_verification").selectOption("D-103");
  await page.getByTestId("requirement-upload-earned_income_verification").click();
  await page.reload();
  await page.getByTestId("interview-slot-select").selectOption("SLOT-3");
  await page.getByTestId("interview-confirm-button").click();

  await advanceTime(request, 4);

  await page.reload();
  await page.getByTestId("requirement-select-housing_cost_verification").selectOption("D-104");
  await page.getByTestId("requirement-upload-housing_cost_verification").click();
  await expect(page.getByTestId("upload-status")).toContainText("Uploaded");

  // No retry. The benchmark permits this — nothing forces a second attempt.
  await page.reload();
  await expect(page.getByTestId("requirement-housing_cost_verification")).toBeVisible();
  await expect(page.getByTestId("received-doc-D-104")).toHaveCount(0);
  await page.screenshot({ path: path.join(SCREENSHOT_DIR, "m4-neg-01-unresolved-no-retry.png") });

  await page.goto(`${LAB_BASE}/`);
  await loginToLabConsole(page);
  await expect(page.getByTestId("lab-binary-success")).toHaveText("false");
  await expect(page.getByTestId("lab-checkpoint-silent_failure_occurred")).toHaveText("true");
  await expect(page.getByTestId("lab-checkpoint-d104_retried_successfully")).toHaveText("false");
  await expect(page.getByTestId("lab-checkpoint-housing_requirement_cleared")).toHaveText("false");
  // Earlier progress is still visible — this is progress tracking, not a
  // finalized-failure verdict (there is no benchmark-model runner yet).
  await expect(page.getByTestId("lab-checkpoint-income_evidence_completed")).toHaveText("true");
  await expect(page.getByTestId("lab-checkpoint-housing_request_reached")).toHaveText("true");
  await page.screenshot({ path: path.join(SCREENSHOT_DIR, "m4-neg-02-evaluator-not-success.png") });
});
