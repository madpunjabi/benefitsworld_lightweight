import path from "node:path";
import { expect, test } from "@playwright/test";
import { AGENT_BASE, advanceTime, resetEnvironment } from "./helpers";

const SCREENSHOT_DIR = path.resolve(__dirname, "../screenshots");

test.beforeEach(async ({ request }) => {
  await resetEnvironment(request);
});

test("human golden path: income -> interview -> housing, entirely through the visible UI", async ({
  page,
  request,
}) => {
  // 2. Observe the income requirement.
  await page.goto(`${AGENT_BASE}/portal`);
  await expect(page.getByTestId("requirement-earned_income_verification")).toBeVisible();

  // 3. Inspect documents.
  await page.goto(`${AGENT_BASE}/files`);
  await page.getByTestId("file-item-D-101").click();
  await expect(page.getByTestId("file-preview-text")).toContainText("Harbor Home Care");
  await page.getByTestId("file-item-D-102").click();
  await expect(page.getByTestId("file-preview-text")).toContainText("3,100");
  await page.getByTestId("file-item-D-103").click();
  await expect(page.getByTestId("file-preview-text")).toContainText("employment ended");
  await page.screenshot({ path: path.join(SCREENSHOT_DIR, "m3-01-files-income.png") });

  // 4-6. Upload D-101 and D-103 from the portal.
  await page.goto(`${AGENT_BASE}/portal`);
  await page.getByTestId("requirement-select-earned_income_verification").selectOption("D-101");
  await page.getByTestId("requirement-upload-earned_income_verification").click();
  await page.getByTestId("requirement-select-earned_income_verification").selectOption("D-103");
  await page.getByTestId("requirement-upload-earned_income_verification").click();

  // 7-8. Income requirement clears; interview requirement appears.
  await page.reload();
  await expect(page.getByTestId("requirement-earned_income_verification")).toHaveCount(0);
  await expect(page.getByTestId("requirement-interview")).toBeVisible();
  await page.screenshot({ path: path.join(SCREENSHOT_DIR, "m3-02-interview-required.png") });

  // 9-10. Open the calendar and observe the Day-3 pediatric appointment.
  await page.goto(`${AGENT_BASE}/calendar`);
  await expect(page.getByTestId("calendar-day-3")).toContainText("Pediatric appointment");
  await expect(page.getByTestId("calendar-day-3")).toContainText("10:00");
  await page.screenshot({ path: path.join(SCREENSHOT_DIR, "m3-03-calendar.png") });

  // 11-13. Return to the portal, inspect interview choices, and select a
  // NON-conflicting appointment (Day 3, 13:30-14:30 — same day as the
  // pediatric appointment but no time overlap).
  await page.goto(`${AGENT_BASE}/portal`);
  const slotSelect = page.getByTestId("interview-slot-select");
  await expect(slotSelect).toContainText("Day 2");
  await expect(slotSelect).toContainText("13:30");
  await slotSelect.selectOption("SLOT-3");
  await page.getByTestId("interview-confirm-button").click();
  await expect(page.getByTestId("upload-status")).toContainText("confirmed");

  // 14. Verify the scheduled appointment persisted.
  await page.reload();
  await expect(page.getByTestId("interview-status")).toContainText("Day 3");
  await expect(page.getByTestId("interview-status")).toContainText("13:30");
  await expect(page.getByTestId("interview-status")).toContainText("SCHEDULED");
  await page.screenshot({ path: path.join(SCREENSHOT_DIR, "m3-04-interview-scheduled.png") });

  // 15. Researcher/harness advances simulated time beyond the interview.
  await advanceTime(request, 4);

  // 16-17. Refresh the portal and notice the new housing request.
  await page.reload();
  await expect(page.getByTestId("interview-status")).toContainText("COMPLETED");
  await expect(page.getByTestId("requirement-housing_cost_verification")).toBeVisible();
  await page.screenshot({ path: path.join(SCREENSHOT_DIR, "m3-05-housing-required.png") });

  // 18. Open the inbox message.
  await page.goto(`${AGENT_BASE}/inbox`);
  const messageRow = page.locator('[data-testid^="inbox-message-"]').first();
  await messageRow.click();
  await expect(page.getByTestId("inbox-message-detail")).toContainText("Proof of Housing Costs Needed");
  await page.screenshot({ path: path.join(SCREENSHOT_DIR, "m3-06-inbox-message.png") });

  // 19. Inspect current and expired leases.
  await page.goto(`${AGENT_BASE}/files`);
  await page.getByTestId("file-item-D-104").click();
  await expect(page.getByTestId("file-preview-text")).toContainText("2026-08-01 through 2027-07-31");
  await page.getByTestId("file-item-D-105").click();
  await expect(page.getByTestId("file-preview-text")).toContainText("2025-08-01 through 2026-07-31");
  await page.screenshot({ path: path.join(SCREENSHOT_DIR, "m3-07-leases.png") });

  // 20. Upload the current lease (D-104).
  await page.goto(`${AGENT_BASE}/portal`);
  await page.getByTestId("requirement-select-housing_cost_verification").selectOption("D-104");
  await page.getByTestId("requirement-upload-housing_cost_verification").click();

  // 21-22. Housing evidence received; requirement clears.
  await page.reload();
  await expect(page.getByTestId("received-doc-D-104")).toBeVisible();
  await expect(page.getByTestId("requirement-housing_cost_verification")).toHaveCount(0);
  await page.screenshot({ path: path.join(SCREENSHOT_DIR, "m3-08-housing-cleared.png") });
});
