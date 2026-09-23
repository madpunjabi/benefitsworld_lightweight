import { expect, test } from "@playwright/test";
import { LAB_BASE, loginToLabConsole, resetEnvironment } from "./helpers";

test.beforeEach(async ({ request }) => {
  await resetEnvironment(request);
});

test("header, description, badge, and static result cards are present", async ({ page }) => {
  await page.goto(`${LAB_BASE}/`);
  await loginToLabConsole(page);

  await expect(page.getByRole("heading", { name: "BenefitsWorld" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Lab Console" })).toBeVisible();
  await expect(page.getByTestId("lab-ground-truth-badge")).toContainText(
    "Researcher view — shows ground truth hidden from the benchmark agent",
  );
  await expect(page.getByTestId("lab-open-agent-view")).toBeVisible();

  const run1Card = page.getByTestId("lab-run1-result-card");
  await expect(run1Card).toContainText("BW-001 — Pilot Run 1");
  await expect(run1Card).toContainText("Fable 5.1");
  await expect(run1Card).toContainText("SUCCESS");
  await expect(run1Card).toContainText("196");
  await expect(run1Card).toContainText("16.78");
  await expect(run1Card).toContainText("Recorded experiment result");

  const bw002Note = page.getByTestId("lab-bw002-note");
  await expect(bw002Note).toContainText("Research iteration — evaluator ambiguity identified");
  await expect(bw002Note).not.toContainText("fail");
});

test("scenario dropdown switches the reset target to BW-002", async ({ page }) => {
  await page.goto(`${LAB_BASE}/`);
  await loginToLabConsole(page);
  await expect(page.getByTestId("lab-scenario-id")).toHaveText("BW-001");

  await page.getByTestId("lab-scenario-select").selectOption("BW-002");
  await page.getByTestId("lab-reset-button").click();
  await expect(page.getByTestId("lab-scenario-id")).toHaveText("BW-002");
  await expect(page.getByTestId("lab-case-status")).toHaveText("PENDING");

  // Switching back to BW-001 and resetting again must still work — this
  // is the existing shell_smoke assertion's exact scenario, now reachable
  // through the dropdown instead of only the implicit default.
  await page.getByTestId("lab-scenario-select").selectOption("BW-001");
  await page.getByTestId("lab-reset-button").click();
  await expect(page.getByTestId("lab-scenario-id")).toHaveText("BW-001");
});
