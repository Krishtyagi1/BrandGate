import assert from "node:assert/strict";
import { mkdirSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";

process.env.PLAYWRIGHT_BROWSERS_PATH = resolve(".cache/playwright");
const { chromium, expect } = await import("@playwright/test");
const { default: AxeBuilder } = await import("@axe-core/playwright");
const output = resolve(".local/test-results");
mkdirSync(output, { recursive: true });
const report = { status: "running", checks: [], accessibility: [], errors: [] };
const browser = await chromium.launch({ headless: true });
let page;
const record = (name) => {
  report.checks.push(name);
  console.log("PASS " + name);
};
try {
  const context = await browser.newContext({
    baseURL: "http://127.0.0.1:3000",
    colorScheme: "light",
    viewport: { width: 1440, height: 960 },
  });
  page = await context.newPage();
  page.on("pageerror", (e) => report.errors.push(e.message));
  await page.goto("/login", { waitUntil: "networkidle", timeout: 120000 });
  await expect(
    page.getByRole("button", { name: "Switch to dark theme", exact: true }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Switch to dark theme", exact: true })
    .click();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  await page.reload({ waitUntil: "networkidle" });
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  record("Theme choice persists after reload");
  const otherPage = await context.newPage();
  await otherPage.goto("/login", { waitUntil: "networkidle" });
  await expect(
    otherPage.getByRole("button", {
      name: "Switch to light theme",
      exact: true,
    }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Switch to light theme", exact: true })
    .click();
  await expect(otherPage.locator("html")).toHaveAttribute(
    "data-theme",
    "light",
  );
  await page
    .getByRole("button", { name: "Switch to dark theme", exact: true })
    .click();
  await expect(otherPage.locator("html")).toHaveAttribute("data-theme", "dark");
  await otherPage.close();
  record("Appearance stays in sync across open tabs");
  for (const theme of ["dark", "light"]) {
    if (theme === "light")
      await page
        .getByRole("button", { name: "Switch to light theme", exact: true })
        .click();
    await expect(page.locator(".auth-art img")).toBeVisible();
    assert.ok(
      await page
        .locator(".auth-art img")
        .evaluate((im) => im.complete && im.naturalWidth > 0),
    );
    const scan = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
      .analyze();
    report.accessibility.push({
      theme,
      violations: scan.violations.map((v) => ({
        id: v.id,
        nodes: v.nodes.map((n) => n.target),
      })),
    });
    assert.equal(
      scan.violations.length,
      0,
      JSON.stringify(report.accessibility.at(-1)),
    );
    await page.screenshot({
      path: resolve(output, `refresh-login-${theme}.png`),
      fullPage: true,
    });
    await page.setViewportSize({ width: 390, height: 844 });
    assert.ok(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth + 2,
      ),
    );
    await expect(
      page.getByLabel("Email address", { exact: true }),
    ).toBeVisible();
    const mobileScan = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
      .analyze();
    report.accessibility.push({
      theme: `${theme}-mobile`,
      violations: mobileScan.violations.map((v) => ({
        id: v.id,
        nodes: v.nodes.map((n) => n.target),
      })),
    });
    assert.equal(
      mobileScan.violations.length,
      0,
      JSON.stringify(report.accessibility.at(-1)),
    );
    await page.screenshot({
      path: resolve(output, `refresh-login-${theme}-mobile.png`),
      fullPage: true,
    });
    await page.setViewportSize({ width: 1440, height: 960 });
    record(`${theme} artwork, login accessibility and mobile layout`);
  }
  await page
    .getByRole("button", { name: "Create an account", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Create your account", exact: true }),
  ).toBeVisible();
  await expect(page.getByLabel("Your name", { exact: true })).toBeVisible();
  record("Registration mode remains accessible");
  const system = await browser.newContext({
    baseURL: "http://127.0.0.1:3000",
    colorScheme: "dark",
  });
  const systemPage = await system.newPage();
  await systemPage.goto("/login", { waitUntil: "networkidle" });
  await expect(systemPage.locator("html")).toHaveAttribute(
    "data-theme",
    "dark",
  );
  await systemPage.emulateMedia({ colorScheme: "light" });
  await expect(systemPage.locator("html")).toHaveAttribute(
    "data-theme",
    "light",
  );
  record("Unselected theme follows system preference changes");
  const restricted = await browser.newContext({
    baseURL: "http://127.0.0.1:3000",
    colorScheme: "light",
  });
  await restricted.addInitScript(() => {
    Storage.prototype.getItem = () => {
      throw new Error("Synthetic unavailable storage");
    };
    Storage.prototype.setItem = () => {
      throw new Error("Synthetic unavailable storage");
    };
  });
  const restrictedPage = await restricted.newPage();
  restrictedPage.on("pageerror", (e) => report.errors.push(e.message));
  await restrictedPage.goto("/login", { waitUntil: "networkidle" });
  await restrictedPage
    .getByRole("button", { name: "Switch to dark theme", exact: true })
    .click();
  await expect(restrictedPage.locator("html")).toHaveAttribute(
    "data-theme",
    "dark",
  );
  assert.deepEqual(report.errors, []);
  const email = `theme-${Date.now()}@example.com`;
  const password = "Synthetic appearance verification 42!";
  const registered = await restricted.request.post("/api/auth/register", {
    headers: { "X-Inkloom-CSRF": "1" },
    data: { email, password, name: "Synthetic Theme Tester" },
  });
  assert.equal(registered.status(), 201);
  await restrictedPage.getByLabel("Email address", { exact: true }).fill(email);
  await restrictedPage.getByLabel("Password", { exact: true }).fill(password);
  await restrictedPage
    .getByRole("button", { name: "Sign in", exact: true })
    .click();
  await expect(
    restrictedPage.getByRole("heading", {
      name: "Give your brand a home.",
      exact: true,
    }),
  ).toBeVisible();
  await expect(restrictedPage.locator("html")).toHaveAttribute(
    "data-theme",
    "dark",
  );
  record("Theme choice survives sign-in when browser storage is unavailable");
  report.status = "passed";
} catch (error) {
  report.status = "failed";
  report.reason = error.message;
  process.exitCode = 1;
  if (page)
    await page
      .screenshot({
        path: resolve(output, "refresh-theme-failed.png"),
        fullPage: true,
      })
      .catch(() => {});
} finally {
  writeFileSync(
    resolve(output, "ui-refresh-theme.json"),
    JSON.stringify(report, null, 2),
  );
  console.log(
    JSON.stringify({
      status: report.status,
      checks: report.checks.length,
      reason: report.reason,
    }),
  );
  await browser.close();
}
