import { expect, test } from "@playwright/test";
import { readFileSync } from "node:fs";
import { join } from "node:path";

const SAMPLE = join(__dirname, "..", "fixtures", "files", "quarterly-report.docx");

test("upload DOCX -> inspect -> template -> render -> prompt -> undo -> export", async ({ page }) => {
  await page.goto("/");
  await page.getByLabel("Upload document").setInputFiles(SAMPLE);

  // Studio opens with the inspected structure
  await expect(page).toHaveURL(/\/studio\/doc_/);
  const outline = page.getByRole("list", { name: "Outline" });
  await expect(outline).toContainText("Executive summary");
  await expect(outline).toContainText("Budget");
  await expect(page.locator(".analysis")).toContainText("business document");

  // Live preview renders the converted document
  const preview = page.frameLocator('iframe[title="Live document preview"]');
  await expect(preview.locator("h2, h1").filter({ hasText: "Executive summary" })).toBeVisible();
  await expect(preview.locator("table")).toContainText("$12,000");

  // Select a template
  await page.getByRole("button", { name: /^Academic/ }).click();
  await expect(page.getByRole("button", { name: /^Academic/ })).toHaveAttribute("aria-pressed", "true");
  await expect(preview.locator('meta[name="docmorph:template"]')).toHaveAttribute("content", "academic");

  // Change the design through a prompt
  await page.getByLabel("Describe changes…").fill("make it dark with a gold accent");
  await page.getByRole("button", { name: "Generate" }).click();
  await expect(page.getByRole("status")).toContainText("dark palette");
  await expect(preview.locator("body")).toHaveCSS("background-color", "rgb(15, 23, 42)");

  // Content edits are refused
  await page.getByLabel("Describe changes…").fill("rewrite the summary in French");
  await page.getByRole("button", { name: "Generate" }).click();
  await expect(page.getByRole("status")).toContainText("presentation only");

  // Undo restores the previous design
  await page.getByRole("button", { name: "Undo" }).click();
  await expect(preview.locator("body")).not.toHaveCSS("background-color", "rgb(15, 23, 42)");
  await page.getByRole("button", { name: "Redo" }).click();
  await expect(preview.locator("body")).toHaveCSS("background-color", "rgb(15, 23, 42)");

  // Export standalone HTML
  const downloadPromise = page.waitForEvent("download");
  await page.getByRole("link", { name: "Export HTML" }).click();
  const download = await downloadPromise;
  expect(download.suggestedFilename()).toBe("quarterly-strategy-report.html");
  const html = readFileSync((await download.path())!, "utf8");
  expect(html).toContain("Revenue grew");
  expect(html).toContain("#0f172a");
});
