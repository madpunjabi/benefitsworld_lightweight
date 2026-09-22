import path from "node:path";
import { expect, test } from "@playwright/test";
import { AGENT_BASE, resetEnvironment } from "./helpers";

const SCREENSHOT_DIR = path.resolve(__dirname, "../screenshots");

test.beforeEach(async ({ request }) => {
  await resetEnvironment(request);
});

test("human golden path: correct Day-0 income evidence is uploaded and verified through the UI", async ({
  page,
}) => {
  // 1. Open the portal and observe the pending income-verification requirement.
  await page.goto(`${AGENT_BASE}/portal`);
  await expect(page.getByTestId("case-status")).toHaveText("PENDING");
  await expect(page.getByTestId("requirement-earned_income_verification")).toBeVisible();
  await page.screenshot({ path: path.join(SCREENSHOT_DIR, "day0-01-portal-pending.png") });

  // 2. Inspect the files, including the current paystub, the stale
  // paystub, and the termination letter, to determine which evidence is
  // current — purely from visible content, no hidden tags.
  await page.goto(`${AGENT_BASE}/files`);
  await page.getByTestId("file-item-D-101").click();
  await expect(page.getByTestId("file-preview-text")).toContainText("Harbor Home Care");
  await expect(page.getByTestId("file-preview-text")).toContainText("2,140");
  await page.screenshot({ path: path.join(SCREENSHOT_DIR, "day0-02-current-paystub.png") });

  await page.getByTestId("file-item-D-102").click();
  await expect(page.getByTestId("file-preview-text")).toContainText("Bayview Market");
  await expect(page.getByTestId("file-preview-text")).toContainText("3,100");
  await page.screenshot({ path: path.join(SCREENSHOT_DIR, "day0-03-stale-paystub.png") });

  await page.getByTestId("file-item-D-103").click();
  await expect(page.getByTestId("file-preview-text")).toContainText("employment ended");
  await page.screenshot({ path: path.join(SCREENSHOT_DIR, "day0-04-termination-letter.png") });

  // 3. Optionally consult the policy library (grounded in the real CDSS
  // SAR 7A (12/23) instructions — see data/policy_sources/).
  await page.goto(`${AGENT_BASE}/policy`);
  await page.getByTestId("policy-search-input").fill("earned income");
  await page.getByTestId("policy-search-button").click();
  await expect(page.getByTestId("policy-item-POL-003")).toBeVisible();
  await page.getByTestId("policy-item-POL-003").click();
  await expect(page.getByTestId("policy-detail-text")).toContainText("check stubs");
  await expect(page.getByTestId("policy-detail")).toContainText("California Department of Social Services");
  await page.screenshot({ path: path.join(SCREENSHOT_DIR, "day0-05-policy.png") });

  // 4. Upload the current paystub and the termination letter through the
  // portal's ordinary upload workflow.
  await page.goto(`${AGENT_BASE}/portal`);
  const requirement = "earned_income_verification";
  await page.getByTestId(`requirement-select-${requirement}`).selectOption("D-101");
  await page.getByTestId(`requirement-upload-${requirement}`).click();
  await expect(page.getByTestId("upload-status")).toContainText("paystub_sep_current.pdf");

  await page.getByTestId(`requirement-select-${requirement}`).selectOption("D-103");
  await page.getByTestId(`requirement-upload-${requirement}`).click();
  await expect(page.getByTestId("upload-status")).toContainText("termination_bayview.pdf");

  // 5. Revisit/refresh the portal and verify both persisted as received.
  await page.reload();
  await expect(page.getByTestId("received-doc-D-101")).toBeVisible();
  await expect(page.getByTestId("received-doc-D-103")).toBeVisible();
  await page.screenshot({ path: path.join(SCREENSHOT_DIR, "day0-06-both-received.png") });
});

test("negative: uploading only the stale paystub does not produce the correct received evidence", async ({
  page,
}) => {
  await page.goto(`${AGENT_BASE}/portal`);
  const requirement = "earned_income_verification";
  await page.getByTestId(`requirement-select-${requirement}`).selectOption("D-102");
  await page.getByTestId(`requirement-upload-${requirement}`).click();
  await expect(page.getByTestId("upload-status")).toContainText("paystub_old_bayview.pdf");

  await page.reload();
  // The stale paystub itself persists (uploads always succeed in this
  // milestone) — but it is not the current-paystub evidence the golden
  // path requires, and the termination letter was never provided either.
  await expect(page.getByTestId("received-doc-D-102")).toBeVisible();
  await expect(page.getByTestId("received-doc-D-101")).toHaveCount(0);
  await expect(page.getByTestId("received-doc-D-103")).toHaveCount(0);
  await page.screenshot({ path: path.join(SCREENSHOT_DIR, "day0-07-stale-only-negative.png") });
});
