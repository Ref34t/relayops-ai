const { test, expect } = require("@playwright/test");

test("dashboard supports session login and workflow creation", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByText("Session login")).toBeVisible();
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page.getByText("Signed in.")).toBeVisible();
  await expect(page.locator("#workspace-mode")).toContainText("Session");
  await page.getByRole("button", { name: "Run workflow" }).click();
  await expect(page.getByText("Workflow created. Scroll updated to the latest runs.")).toBeVisible();
  await expect(page.getByText("AI analysis").first()).toBeVisible();
});

test("settings page can run connector diagnostics", async ({ page }) => {
  await page.goto("/settings");
  await page.getByRole("button", { name: "Run connector checks" }).click();
  await expect(page.getByText("Connector checks completed. Review any misconfigured providers below.")).toBeVisible();
  await expect(page.locator("#settings-integrations .metric-card").first()).toContainText("OpenAI");
});
