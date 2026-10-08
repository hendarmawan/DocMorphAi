import { expect, test } from "@playwright/test";

test("home page loads and the API is reachable through the web app", async ({ page, request }) => {
  const health = await request.get("/api/health");
  expect(health.ok()).toBeTruthy();
  expect((await health.json()).status).toBe("ok");

  await page.goto("/");
  await expect(page.getByRole("heading", { level: 1 })).toContainText("Intelligent documents");
  await expect(page.getByRole("button", { name: "Choose file" })).toBeVisible();
  await expect(page.locator(".error")).toHaveCount(0);
});
