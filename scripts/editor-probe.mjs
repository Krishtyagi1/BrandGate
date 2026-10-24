import { resolve } from "node:path";
import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import assert from "node:assert/strict";
const root = resolve(".");
process.env.PLAYWRIGHT_BROWSERS_PATH = resolve(root, ".cache/playwright");
process.env.TEMP = resolve(root, ".cache/tmp");
process.env.TMP = process.env.TEMP;
const { chromium, expect } = await import("@playwright/test");
const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({
  baseURL: "http://127.0.0.1:3000",
  viewport: { width: 1536, height: 1100 },
  acceptDownloads: true,
});
const page = await context.newPage();
page.setDefaultTimeout(60000);
const report = {
  kind: "synthetic DOCX editor probe",
  checks: [],
  errors: [],
  externalRequests: [],
};
report.consoleErrors = [];
report.failedRequests = [];
page.on("console", (m) => {
  if (m.type() === "error") report.consoleErrors.push(m.text().slice(0, 500));
});
page.on("requestfailed", (r) =>
  report.failedRequests.push({ url: r.url(), reason: r.failure()?.errorText }),
);
page.on("pageerror", (e) => report.errors.push(e.message));
page.on("request", (r) => {
  if (
    !r.url().startsWith("http://127.0.0.1:3000") &&
    !/^(blob|data):/.test(r.url())
  )
    report.externalRequests.push(r.url());
});
async function call(path, body) {
  const r = await context.request.post("/api" + path, {
    data: body,
    headers: { "X-Inkloom-CSRF": "1" },
  });
  assert.ok(r.ok(), `${path}: ${r.status()} ${await r.text()}`);
  return r.json();
}
try {
  const email = `editor-probe-${Date.now()}@example.com`,
    password = "Synthetic editor passphrase 123!";
  await call("/auth/register", {
    email,
    password,
    name: "Synthetic Editor Tester",
  });
  await call("/auth/login", { email, password });
  const org = await call("/organisations", { name: "Synthetic Editor Probe" });
  const upload = await context.request.post(
    `/api/organisations/${org.id}/drafts/upload`,
    {
      headers: { "X-Inkloom-CSRF": "1" },
      multipart: {
        title: "Synthetic launch document",
        channel: "general",
        file: {
          name: "editor-fixture.docx",
          mimeType:
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
          buffer: readFileSync(
            resolve(root, ".local/test-results/editor-fixture.docx"),
          ),
        },
      },
    },
  );
  assert.equal(upload.status(), 201, await upload.text());
  const draft = await upload.json();
  await page.goto(`/org/${org.id}/reviews/${draft.id}`, {
    waitUntil: "domcontentloaded",
    timeout: 120000,
  });
  await expect(
    page.getByRole("heading", { name: "Synthetic launch document" }),
  ).toBeVisible({ timeout: 120000 });
  const dismissTutorial = page.getByRole("button", {name:"Dismiss welcome tutorial"});
  if (await dismissTutorial.isVisible()) await dismissTutorial.click();
  await page.screenshot({
    path: resolve(root, ".local/test-results/editor-opening.png"),
    fullPage: true,
  });
  await expect(page.locator(".word-canvas")).toContainText(
    "Cloudberry Daily Cleanser",
    { timeout: 90000 },
  );
  report.checks.push("DOCX opens with extracted body text visible");
  const info = await page
    .locator(".word-canvas")
    .evaluate((el) => ({
      text: el.innerText.slice(0, 1000),
      editables: [
        ...el.querySelectorAll("[contenteditable],textarea,input"),
      ].map((e) => ({
        tag: e.tagName,
        role: e.getAttribute("role"),
        cls: e.className,
        editable: e.getAttribute("contenteditable"),
        "aria-label": e.getAttribute("aria-label"),
      })),
    }));
  report.editorInfo = info;
  await page.screenshot({
    path: resolve(root, ".local/test-results/editor-opened.png"),
    fullPage: true,
  });
  const paragraph = page
    .locator(".word-canvas")
    .getByText(
      "A document fixture for editor testing. No real company material.",
      { exact: true },
    )
    .first();
  await paragraph.click();
  await page.keyboard.press("End");
  await page.keyboard.insertText(" Tested edit.");
  await expect(
    page.getByRole("button", { name: "Save", exact: true }),
  ).toBeEnabled();
  const cell = page
    .locator(".word-canvas")
    .getByText("INR 799", { exact: true })
    .first();
  await cell.click();
  await page.keyboard.press("Home");
  await page.keyboard.press("Shift+End");
  await page.keyboard.insertText("INR 899");
  await page.getByRole("button", { name: "Save", exact: true }).click();
  await expect(page.getByText("Revision 2", { exact: true })).toBeVisible();
  const detail = await context.request.get(
    `/api/organisations/${org.id}/drafts/${draft.id}`,
  );
  const saved = await detail.json();
  assert.ok(
    saved.current_version.text.includes("Tested edit."),
    saved.current_version.text,
  );
  assert.ok(
    saved.current_version.text.includes("INR 899"),
    saved.current_version.text,
  );
  assert.ok(
    saved.current_version.text.includes(
      "Cloudberry Daily Cleanser costs INR 799 per 150ml.",
    ),
    saved.current_version.text,
  );
  report.checks.push(
    "Typed paragraph and table-cell edits saved into server-derived text",
  );
  const bytes = await context.request.get(
    `/api/organisations/${org.id}/drafts/${draft.id}/versions/${saved.current_version_id}/download`,
  );
  writeFileSync(
    resolve(root, ".local/test-results/editor-roundtrip.docx"),
    await bytes.body(),
  );
  assert.equal(saved.versions.length, 2);
  report.checks.push("Original retained and immutable revision created");
  await page.reload({ waitUntil: "domcontentloaded" });
  await expect(page.locator(".word-canvas")).toContainText("Tested edit.", {
    timeout: 90000,
  });
  await expect(page.locator(".word-canvas")).toContainText("INR 899");
  report.checks.push("Saved DOCX reopened with paragraph and table edits");
  await page.screenshot({
    path: resolve(root, ".local/test-results/editor-roundtrip.png"),
    fullPage: true,
  });
  assert.deepEqual(report.errors, []);
  assert.deepEqual(report.externalRequests, []);
  report.status = "passed";
} catch (e) {
  report.status = "failed";
  report.reason = e.message;
  await page
    .screenshot({
      path: resolve(root, ".local/test-results/editor-failed.png"),
      fullPage: true,
    })
    .catch(() => {});
  process.exitCode = 1;
} finally {
  writeFileSync(
    resolve(root, ".local/test-results/editor-probe.json"),
    JSON.stringify(report, null, 2),
  );
  console.log(JSON.stringify(report, null, 2));
  await browser.close();
}
