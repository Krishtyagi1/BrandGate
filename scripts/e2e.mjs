import { resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { mkdirSync, writeFileSync } from "node:fs";
import assert from "node:assert/strict";

const root = resolve(fileURLToPath(new URL("..", import.meta.url)));
process.env.PLAYWRIGHT_BROWSERS_PATH = resolve(root, ".cache/playwright");
process.env.TEMP = resolve(root, ".cache/tmp");
process.env.TMP = process.env.TEMP;
const { chromium, expect } = await import("@playwright/test");
const { default: AxeBuilder } = await import("@axe-core/playwright");
const output = resolve(root, ".local/test-results");
mkdirSync(output, { recursive: true });
const report = {
  startedAt: new Date().toISOString(),
  checks: [],
  accessibility: [],
  screenshots: [],
};
const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({
  baseURL: "http://127.0.0.1:3000",
  viewport: { width: 1440, height: 1050 },
});
const page = await context.newPage();
page.setDefaultTimeout(20000);
const password = "Synthetic passphrase for local test 123!";
const suffix = Date.now();
const email = `browser-owner-${suffix}@example.com`;
const errors = [];
page.on("pageerror", (error) => errors.push(error.message));
function check(name) {
  report.checks.push({ name, status: "passed" });
  console.log(`PASS ${name}`);
}
async function json(request, path, method = "GET", data) {
  const response = await request.fetch(`/api${path}`, {
    method,
    data,
    headers: { "X-Inkloom-CSRF": "1" },
  });
  const body = await response.json();
  return { status: response.status(), body };
}
async function auditA11y(name) {
  const result = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
    .analyze();
  report.accessibility.push({ name, violations: result.violations });
  assert.deepEqual(
    result.violations.map(
      (v) => `${v.id}: ${v.nodes.map((n) => n.target).join(",")}`,
    ),
    [],
    `Accessibility violations on ${name}`,
  );
  check(`${name}: automated accessibility scan`);
}
async function screenshot(name) {
  const path = resolve(output, `${name}.png`);
  await page.screenshot({ path, fullPage: true });
  report.screenshots.push(path);
}
try {
  await page.goto("/login");
  await expect(
    page.getByRole("heading", { name: "Welcome back" }),
  ).toBeVisible();
  await auditA11y("Sign in");
  await page
    .getByRole("button", { name: "Create an account", exact: true })
    .click();
  await page.getByLabel("Your name").fill("Morgan Reed");
  await page.getByLabel("Email address").fill(email);
  await page.getByLabel(/^Password/).fill(password);
  await page
    .getByRole("button", { name: "Create account", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Welcome back" }),
  ).toBeVisible();
  await expect(page.getByLabel("Verification code")).toHaveCount(0);
  await expect(
    page.getByRole("button", { name: "Enter a verification code" }),
  ).toHaveCount(0);
  await page.getByLabel("Email address").fill(email);
  await page.getByLabel(/^Password/).fill(password);
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Give your brand a home." }),
  ).toBeVisible();
  check("Create an account and sign in directly with email and password");
  await page
    .getByLabel("Organisation name", { exact: true })
    .fill(`TechNova ${suffix}`);
  await page
    .getByRole("button", { name: "Create organisation", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Welcome, Morgan." }),
  ).toBeVisible();
  const orgId = new URL(page.url()).pathname.split("/")[2];
  const base = `/org/${orgId}`;
  await expect(
    page.getByText("No active guidelines yet", { exact: true }),
  ).toBeVisible();
  await screenshot("desktop-overview-empty");
  check("Owner onboarding and persisted overview");
  await auditA11y("Overview desktop");
  await page
    .getByRole("link", { name: "Brand knowledge", exact: true })
    .click();
  await page.getByRole("button", { name: "Create first version" }).click();
  await expect(
    page.getByText("Version 1 created.", { exact: false }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Add rule", exact: true }).click();
  await page.getByLabel(/^Rule key/).fill("monthly_price");
  await page
    .getByLabel("Approved wording or value")
    .fill("Rs 999/month, effective 23 October 2026");
  await page.getByRole("checkbox").check();
  await page.getByRole("button", { name: "Save rule", exact: true }).click();
  await expect(page.getByText("Rule saved.", { exact: true })).toBeVisible();
  page.on("dialog", (dialog) => dialog.accept());
  await page
    .getByRole("button", { name: "Activate version", exact: true })
    .click();
  await expect(
    page.getByText("Version 1 is active.", { exact: true }),
  ).toBeVisible();
  await expect(
    page.getByText("Active guidelines", { exact: true }),
  ).toBeVisible();
  check("Owner reviews and activates guideline v1");
  const v1 = (
    await json(context.request, `/organisations/${orgId}/guidelines/versions`)
  ).body[0].id;
  await screenshot("desktop-brand-knowledge");
  await auditA11y("Brand knowledge desktop");
  await page.getByRole("button", { name: "New version", exact: true }).click();
  await page.getByRole("button", { name: "Add rule", exact: true }).click();
  await page.getByLabel(/^Rule key/).fill("monthly_price");
  await page
    .getByLabel("Approved wording or value")
    .fill("Rs 1299/month, effective 24 October 2026");
  await page.getByRole("checkbox").check();
  await page.getByRole("button", { name: "Save rule", exact: true }).click();
  await expect(page.getByText("Rule saved.", { exact: true })).toBeVisible();
  await page
    .getByRole("button", { name: "Activate version", exact: true })
    .click();
  await expect(
    page.getByText("Version 2 is active.", { exact: true }),
  ).toBeVisible();
  const old = (
    await json(
      context.request,
      `/organisations/${orgId}/guidelines/versions/${v1}`,
    )
  ).body;
  assert.equal(old.status, "archived");
  assert.match(old.rules[0].value, /999/);
  check("Activate v2 while preserving v1 source records");
  await page.getByRole("tab", { name: "Version history", exact: true }).click();
  await expect(page.getByRole("button", { name: /Version 1/ })).toBeVisible();
  await page
    .getByRole("link", { name: "Team & settings", exact: true })
    .click();
  const inviteEmail = `browser-creator-${suffix}@example.com`;
  await page.getByLabel("Email address", { exact: true }).fill(inviteEmail);
  await page
    .getByRole("button", { name: "Create invitation", exact: true })
    .click();
  const token = await page
    .getByLabel("Invitation code", { exact: true })
    .inputValue();
  const creatorContext = await browser.newContext({
    baseURL: "http://127.0.0.1:3000",
  });
  assert.equal(
    (
      await json(creatorContext.request, "/auth/register", "POST", {
        email: inviteEmail,
        name: "Sam Creator",
        password,
      })
    ).status,
    201,
  );
  assert.equal(
    (
      await json(creatorContext.request, "/auth/login", "POST", {
        email: inviteEmail,
        password,
      })
    ).status,
    200,
  );
  assert.equal(
    (
      await json(creatorContext.request, "/invitations/accept", "POST", {
        token,
      })
    ).status,
    200,
  );
  assert.equal(
    (
      await json(
        creatorContext.request,
        `/organisations/${orgId}/guidelines/versions`,
        "POST",
      )
    ).status,
    403,
  );
  check(
    "Invitation accepted by matching account; creator owner actions denied",
  );
  await page
    .getByRole("button", { name: "Run connection check", exact: true })
    .click();
  await expect(page.getByText("Completed", { exact: true })).toBeVisible();
  await expect(
    page.getByText("Connection check complete", { exact: true }),
  ).toBeVisible();
  check("Official AG-UI client receives live LangGraph progress");
  await page.reload();
  await expect(
    page.getByText("Saved status: completed", { exact: true }),
  ).toBeVisible();
  check("Completed stream status survives refresh");
  await page
    .getByRole("button", { name: "Run connection check", exact: true })
    .click();
  await expect(page.locator(".diagnostic-status")).toHaveText(
    "Checking organisation access",
  );
  await page.getByRole("button", { name: "Cancel check", exact: true }).click();
  await expect(page.locator(".diagnostic-status")).toContainText(/cancelled/i);
  check("Stream cancellation persists without changing guidelines");
  await page
    .getByRole("button", { name: "Run connection check", exact: true })
    .click();
  await expect(page.locator(".diagnostic-status")).toHaveText(
    "Checking organisation access",
  );
  await page.reload();
  await expect(page.locator(".diagnostic-status")).toContainText(
    /cancelled|interrupted|completed/,
    { timeout: 20000 },
  );
  check("Disconnected stream recovers persisted status after refresh");
  await page.goto(`${base}/dashboard`);
  await expect(
    page.getByRole("heading", { name: "Welcome, Morgan." }),
  ).toBeVisible();
  await screenshot("desktop-overview-active");
  await page.setViewportSize({ width: 390, height: 844 });
  await expect(
    page.getByRole("heading", { name: "Welcome, Morgan." }),
  ).toBeVisible();
  assert.ok(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
    "Dashboard has horizontal overflow",
  );
  await auditA11y("Overview mobile");
  await screenshot("mobile-overview");
  await page
    .getByRole("button", { name: "Open navigation", exact: true })
    .click();
  await page
    .getByRole("link", { name: "Brand knowledge", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Brand knowledge", exact: true }),
  ).toBeVisible();
  assert.ok(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
    "Knowledge page has horizontal overflow",
  );
  await auditA11y("Brand knowledge mobile");
  await screenshot("mobile-brand-knowledge");
  check("Mobile navigation and 390px layout without horizontal overflow");
  await page
    .getByRole("button", { name: "Open navigation", exact: true })
    .click();
  await page.getByRole("button", { name: /Morgan Reed Sign out/ }).click();
  await expect(
    page.getByRole("heading", { name: "Welcome back" }),
  ).toBeVisible();
  await page.goto(`${base}/brand`);
  await expect(
    page.getByRole("heading", { name: "Welcome back" }),
  ).toBeVisible();
  check("Sign out revokes session and protects organisation route");
  assert.deepEqual(errors, [], "Browser runtime errors");
  check("No browser JavaScript runtime errors");
  await creatorContext.close();
  report.status = "passed";
} catch (error) {
  report.status = "failed";
  report.error = String(error.stack || error);
  await screenshot("failure");
  console.error(report.error);
  process.exitCode = 1;
} finally {
  report.finishedAt = new Date().toISOString();
  writeFileSync(
    resolve(output, "browser.json"),
    JSON.stringify(report, null, 2),
  );
  await browser.close();
}
