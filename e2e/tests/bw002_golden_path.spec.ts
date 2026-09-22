import path from "node:path";
import { expect, test } from "@playwright/test";
import { AGENT_BASE, API_BASE, LAB_TOKEN, advanceTime, resetEnvironment } from "./helpers";

const SCREENSHOT_DIR = path.resolve(__dirname, "../screenshots");

test.beforeEach(async ({ request }) => {
  await resetEnvironment(request, "BW-002");
});

test("BW-002 human golden path: overlapping obligations, a delayed housing rejection, an employment "
  + "change, and a recertification that survives both, entirely through the visible UI", async ({
  page,
  request,
}) => {
  // 1. Day 0: all four responsibilities are visible at once.
  await page.goto(`${AGENT_BASE}/portal`);
  await expect(page.getByTestId("case-id")).toHaveText("CF-ALM-20591");
  await expect(page.getByTestId("requirement-income_verification")).toBeVisible();
  await expect(page.getByTestId("requirement-housing_verification")).toBeVisible();
  await expect(page.getByTestId("requirement-interview")).toBeVisible();
  await expect(page.getByTestId("recertification")).toBeVisible();
  await expect(page.getByTestId("recertification-status")).toHaveText("NOT_READY");
  await page.screenshot({ path: path.join(SCREENSHOT_DIR, "bw002-01-day0-four-responsibilities.png") });

  // 2. Inspect documents to determine which evidence is current.
  await page.goto(`${AGENT_BASE}/files`);
  await page.getByTestId("file-item-D-201").click();
  await expect(page.getByTestId("file-preview-text")).toContainText("Harbor Home Care");
  await page.getByTestId("file-item-D-204").click();
  await expect(page.getByTestId("file-preview-text")).toContainText("Page 1 of 2");
  await page.screenshot({ path: path.join(SCREENSHOT_DIR, "bw002-02-files.png") });

  // 3. Resolve income verification with D-201 + D-203 (D-202 alone would not do it).
  await page.goto(`${AGENT_BASE}/portal`);
  await page.getByTestId("requirement-select-income_verification").selectOption("D-201");
  await page.getByTestId("requirement-upload-income_verification").click();
  await page.getByTestId("requirement-select-income_verification").selectOption("D-203");
  await page.getByTestId("requirement-upload-income_verification").click();

  // 4. Resolve Day-0 housing verification with D-204 (genuinely accepted for now).
  await page.getByTestId("requirement-select-housing_verification").selectOption("D-204");
  await page.getByTestId("requirement-upload-housing_verification").click();

  // 5. Schedule the interview.
  await page.getByTestId("interview-slot-select").selectOption("BW2-SLOT-1");
  await page.getByTestId("interview-confirm-button").click();

  await page.reload();
  await expect(page.getByTestId("requirement-income_verification")).toHaveCount(0);
  await expect(page.getByTestId("requirement-housing_verification")).toHaveCount(0);
  await expect(page.getByTestId("interview-status")).toContainText("SCHEDULED");
  await page.screenshot({ path: path.join(SCREENSHOT_DIR, "bw002-03-day0-resolved.png") });

  // 6. Advance to Day 3 so the Day-2 interview completes, then recertification is READY.
  await advanceTime(request, 3);
  await page.reload();
  await expect(page.getByTestId("interview-status")).toContainText("COMPLETED");
  await expect(page.getByTestId("recertification-status")).toHaveText("READY");
  await page.screenshot({ path: path.join(SCREENSHOT_DIR, "bw002-04-recert-ready.png") });

  // 7. Submit recertification.
  await page.getByTestId("recertification-submit-button").click();
  await page.reload();
  await expect(page.getByTestId("recertification-status")).toHaveText("SUBMITTED");

  // 8. Advance to Day 6: the county rejects the incomplete lease copy.
  await advanceTime(request, 6);
  await page.reload();
  await expect(page.getByTestId("requirement-housing_correction")).toBeVisible();
  await expect(page.getByTestId("recertification-status")).toHaveText("NEEDS_UPDATE");
  const inboxAfterRejection = await request
    .get(`${API_BASE}/inbox/messages`)
    .then((r) => r.json());
  expect(inboxAfterRejection.some((m: { subject: string }) => m.subject === "Housing Proof Incomplete")).toBe(true);
  await page.screenshot({ path: path.join(SCREENSHOT_DIR, "bw002-05-housing-rejected.png") });

  // 9. Inspect and submit the complete signed lease (D-208).
  await page.goto(`${AGENT_BASE}/files`);
  await page.getByTestId("file-item-D-208").click();
  await expect(page.getByTestId("file-preview-text")).toContainText("Signed by landlord and tenant");
  await page.goto(`${AGENT_BASE}/portal`);
  await page.getByTestId("requirement-select-housing_correction").selectOption("D-208");
  await page.getByTestId("requirement-upload-housing_correction").click();
  await page.reload();
  await expect(page.getByTestId("requirement-housing_correction")).toHaveCount(0);

  // 10. Advance to Day 8: employment changes to Golden State Logistics.
  await advanceTime(request, 8);
  await page.reload();
  await expect(page.getByTestId("requirement-updated_income_verification")).toBeVisible();
  await expect(page.getByTestId("recertification-status")).toHaveText("NEEDS_UPDATE");
  await page.screenshot({ path: path.join(SCREENSHOT_DIR, "bw002-06-employment-change.png") });

  // 11. D-201 (once valid) no longer satisfies the updated requirement; D-209 does.
  await page.goto(`${AGENT_BASE}/files`);
  await page.getByTestId("file-item-D-209").click();
  await expect(page.getByTestId("file-preview-text")).toContainText("Golden State Logistics");
  await page.goto(`${AGENT_BASE}/portal`);
  await page.getByTestId("requirement-select-updated_income_verification").selectOption("D-209");
  await page.getByTestId("requirement-upload-updated_income_verification").click();
  await page.reload();
  await expect(page.getByTestId("requirement-updated_income_verification")).toHaveCount(0);

  // 12. Resubmit recertification now that every requirement is current again.
  await expect(page.getByTestId("recertification-status")).toHaveText("NEEDS_UPDATE");
  await page.getByTestId("recertification-submit-button").click();
  await page.reload();
  await expect(page.getByTestId("recertification-status")).toHaveText("SUBMITTED");
  await page.screenshot({ path: path.join(SCREENSHOT_DIR, "bw002-07-resubmitted.png") });

  // 13. Advance to the Day-14 deadline: no overdue status, and the
  // harness-side evaluator (never seen by the agent) confirms full success.
  await advanceTime(request, 14);
  await page.reload();
  await expect(page.getByTestId("case-status")).toHaveText("PENDING");
  await page.screenshot({ path: path.join(SCREENSHOT_DIR, "bw002-08-day14-success.png") });

  const evaluation = await request
    .get(`${API_BASE}/lab/evaluate`, { headers: { "X-Lab-Token": LAB_TOKEN } })
    .then((r) => r.json());
  expect(evaluation.checkpoints, JSON.stringify(evaluation.checkpoints)).toMatchObject(
    Object.fromEntries(Object.keys(evaluation.checkpoints).map((k) => [k, true])),
  );
  expect(evaluation.binary_success).toBe(true);
});
