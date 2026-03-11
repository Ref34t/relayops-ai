const { test, expect } = require("@playwright/test");

test("dashboard supports session login and workflow creation", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByText("Session login")).toBeVisible();
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page.getByText("Signed in.")).toBeVisible();
  await expect(page.getByText("Session workspace")).toBeVisible();
  await page.getByRole("button", { name: "Run workflow" }).click();
  await expect(page.getByText("Workflow accepted and queued.")).toBeVisible();
  await expect(page.getByText("Live workflow history with AI reasoning attached.")).toBeVisible();
  await expect(page.getByText("Risk:").first()).toBeVisible();
});

test("settings page can run connector diagnostics", async ({ page }) => {
  await page.goto("/settings");
  await page.getByRole("button", { name: "Run connector checks" }).click();
  await expect(page.getByText("Connector diagnostics completed.")).toBeVisible();
  await expect(page.getByText("OpenAI").first()).toBeVisible();
});

test("next proxy exposes backend account endpoint", async ({ request }) => {
  const response = await request.get("/api/account");
  expect(response.ok()).toBeTruthy();
  const payload = await response.json();
  expect(payload.account.email).toBe("demo@relayops.app");
});
