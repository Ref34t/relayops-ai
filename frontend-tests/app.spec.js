const { test, expect } = require("@playwright/test");

test("landing routes unauthenticated users into sign-in and dashboard flow", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByText("Orchestrate operations across CRM, finance, and internal systems.")).toBeVisible();
  await page.getByRole("link", { name: "Sign in" }).click();
  await expect(page).toHaveURL(/\/signin$/);
  await expect(page.getByText("Access the workspace and continue where operations are happening.")).toBeVisible();
  await page.getByRole("button", { name: "Enter dashboard" }).click();
  await expect(page).toHaveURL(/\/dashboard$/);
  await expect(page.getByText("Operational workflows, integration status, and execution history in one workspace.")).toBeVisible();
  await page.getByRole("button", { name: "Submit workflow" }).click();
  await expect(page.getByText("Workflow queued.")).toBeVisible();
  await expect(page.getByText("Recent workflow runs.")).toBeVisible();
  await expect(page.getByText("Risk:").first()).toBeVisible();
});

test("settings page can run integration diagnostics", async ({ page }) => {
  await page.goto("/signin");
  await page.getByRole("button", { name: "Enter dashboard" }).click();
  await page.goto("/settings");
  await page.getByRole("button", { name: "Run diagnostics" }).click();
  await expect(page.getByText("Diagnostics complete.")).toBeVisible();
  await expect(page.getByText("OpenAI").first()).toBeVisible();
  await expect(page.getByText("Loaded credentials and environment values.")).toBeVisible();
});

test("protected routes redirect to sign-in when session is missing", async ({ page }) => {
  await page.goto("/dashboard");
  await expect(page).toHaveURL(/\/signin$/);
  await page.goto("/settings");
  await expect(page).toHaveURL(/\/signin$/);
});

test("next proxy exposes backend account endpoint", async ({ request }) => {
  const response = await request.get("/api/account");
  expect(response.ok()).toBeTruthy();
  const payload = await response.json();
  expect(payload.account.email).toBe("demo@relayops.app");
});
