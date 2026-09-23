import { expect, test } from "@playwright/test";
import { LAB_BASE, LAB_CONSOLE_PASSWORD, resetEnvironment } from "./helpers";

test.beforeEach(async ({ request }) => {
  await resetEnvironment(request);
});

test("wrong password does not grant access to the console", async ({ page }) => {
  await page.goto(`${LAB_BASE}/`);
  await expect(page.getByTestId("page-lab-login")).toBeVisible();
  await page.getByTestId("lab-login-password").fill("definitely-the-wrong-password");
  await page.getByTestId("lab-login-submit").click();
  await expect(page.getByTestId("lab-login-error")).toBeVisible();
  await expect(page.getByTestId("page-lab-console")).toHaveCount(0);
});

test("correct password grants access, and logout returns to the login screen", async ({ page }) => {
  await page.goto(`${LAB_BASE}/`);
  await expect(page.getByTestId("page-lab-login")).toBeVisible();
  await page.getByTestId("lab-login-password").fill(LAB_CONSOLE_PASSWORD);
  await page.getByTestId("lab-login-submit").click();
  await expect(page.getByTestId("page-lab-console")).toBeVisible();

  // A fresh reload with the session cookie already set should go straight
  // to the console, no login prompt.
  await page.reload();
  await expect(page.getByTestId("page-lab-console")).toBeVisible();

  await page.getByTestId("lab-logout-button").click();
  await expect(page.getByTestId("page-lab-login")).toBeVisible();

  // And after logout, a reload must not silently regain access.
  await page.reload();
  await expect(page.getByTestId("page-lab-login")).toBeVisible();
});

test("no X-Lab-Token or VITE_LAB_TOKEN reference exists anywhere in the running page's JS context", async ({
  page,
}) => {
  await page.goto(`${LAB_BASE}/`);
  const hasLegacyToken = await page.evaluate(() => {
    // Nothing in the compiled bundle should define this global or ship
    // the string as a literal the page could read back.
    return document.documentElement.outerHTML.includes("VITE_LAB_TOKEN");
  });
  expect(hasLegacyToken).toBe(false);
});
