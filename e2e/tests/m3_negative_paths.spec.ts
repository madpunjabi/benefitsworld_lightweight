import path from "node:path";
import { expect, test } from "@playwright/test";
import { AGENT_BASE, advanceTime, resetEnvironment } from "./helpers";

const SCREENSHOT_DIR = path.resolve(__dirname, "../screenshots");

test.beforeEach(async ({ request }) => {
  await resetEnvironment(request);
});

test("negative: stale paystub alone does not unlock the interview requirement", async ({ page }) => {
  await page.goto(`${AGENT_BASE}/portal`);
  await page.getByTestId("requirement-select-earned_income_verification").selectOption("D-102");
  await page.getByTestId("requirement-upload-earned_income_verification").click();

  await page.reload();
  // Still open — the stale paystub alone never clears the requirement.
  await expect(page.getByTestId("requirement-earned_income_verification")).toBeVisible();
  await expect(page.getByTestId("requirement-interview")).toHaveCount(0);
  await page.screenshot({ path: path.join(SCREENSHOT_DIR, "m3-neg-01-stale-income.png") });
});

test("negative: a conflicting interview slot is technically schedulable — the UI does not block it", async ({
  page,
}) => {
  await page.goto(`${AGENT_BASE}/portal`);
  await page.getByTestId("requirement-select-earned_income_verification").selectOption("D-101");
  await page.getByTestId("requirement-upload-earned_income_verification").click();
  await page.getByTestId("requirement-select-earned_income_verification").selectOption("D-103");
  await page.getByTestId("requirement-upload-earned_income_verification").click();
  await page.reload();

  // SLOT-2 (Day 3, 10:30-11:30) overlaps the Day-3 pediatric appointment
  // (10:00-12:00). Nothing in the scheduling UI flags this.
  await page.getByTestId("interview-slot-select").selectOption("SLOT-2");
  await page.getByTestId("interview-confirm-button").click();
  await expect(page.getByTestId("upload-status")).toContainText("confirmed");

  await page.reload();
  await expect(page.getByTestId("interview-status")).toContainText("Day 3");
  await expect(page.getByTestId("interview-status")).toContainText("10:30");
  await page.screenshot({ path: path.join(SCREENSHOT_DIR, "m3-neg-02-conflicting-slot-scheduled.png") });
});

test("negative: expired lease does not satisfy housing verification", async ({ page, request }) => {
  await page.goto(`${AGENT_BASE}/portal`);
  await page.getByTestId("requirement-select-earned_income_verification").selectOption("D-101");
  await page.getByTestId("requirement-upload-earned_income_verification").click();
  await page.getByTestId("requirement-select-earned_income_verification").selectOption("D-103");
  await page.getByTestId("requirement-upload-earned_income_verification").click();
  await page.reload();
  await page.getByTestId("interview-slot-select").selectOption("SLOT-1");
  await page.getByTestId("interview-confirm-button").click();

  await advanceTime(request, 3);

  await page.reload();
  await page.getByTestId("requirement-select-housing_cost_verification").selectOption("D-105");
  await page.getByTestId("requirement-upload-housing_cost_verification").click();

  await page.reload();
  // Received (all uploads persist in Milestone 3) but the requirement
  // must remain open — the expired lease is not current evidence.
  await expect(page.getByTestId("received-doc-D-105")).toBeVisible();
  await expect(page.getByTestId("requirement-housing_cost_verification")).toBeVisible();
  await expect(page.getByTestId("received-doc-D-104")).toHaveCount(0);
  await page.screenshot({ path: path.join(SCREENSHOT_DIR, "m3-neg-03-expired-lease.png") });
});
