# Demo runbook

Use fictional materials first. The root `Sample Company Brand Rules.docx` is a fictional sample. Do not copy real company documents, `.env`, `.local` or `.cache` into a submission.

## Start

From this project folder, run `npm.cmd run dev` only when no existing services occupy 3000/8000/54329. Open http://127.0.0.1:3000/login. Existing separate services can remain running; do not start a second launcher. Fresh setup: `powershell -ExecutionPolicy Bypass -File .\scripts\setup.ps1`. The ignored root `.env` needs `OPENROUTER_API_KEY`; never paste the key into chat/screenshots. Keep the default free-only route or configure an eligible explicit `:free` model.

Register a creator/owner account and a distinct reviewer account. Passwords need at least twelve characters. Use separate browser profiles/private windows for the two sessions. Invite the reviewer in Team & settings and accept its code while signed in with the matching email. These are prototype accounts; email ownership is not verified.

## Current three-tab walkthrough

1. **Help → Try the fictional example** creates a separate Northstar Botanics organisation with sources and deliberately incorrect text/ad, no AI results or approved rules.
2. **Rules** shows all setup sections. Inspect highlighted evidence, edit proposed fields, select rules, acknowledge and confirm. Manual missing guidance is labelled company-entered. Added sources update this visible version only after confirmation; price replacements need acknowledgement. New version starts empty.
3. **Tracking** opens the sample text. Choose checks/tasks, inspect the outbound preview and run. Missing guidance is visible per category; supported checks continue. Real contextual AI can be unavailable under free-provider limits. For a local demonstration during an outage, choose Products & prices, Language & terminology and Required wording only. Those exact checks run without inference and are labelled local checks; tone/claim interpretation and generated corrections still require an available AI route.
4. Apply a safe text correction if available, or edit manually. Save and recheck. Invite a separate reviewer through Settings and request a decision on the exact revision.
5. Open the sample ad in Tracking. Select **Colours & fonts** alone to demonstrate local dominant-palette observations against source colours. **Logos & visual examples** attempts optional vision, currently unavailable under the required free/privacy route. Images are evaluated only; video unsupported. Pure visual checks need no OCR transcript; printed text checks do.
6. Help can be dismissed/replayed. Channel information works on hover, keyboard focus and tap. Settings remains secondary to the three tabs.

Sources: ten uploads/version, 5 MB/file, 100 PDF pages and 200,000 extracted characters/file. Up to twenty embedded images/source; optional vision at most four confirmed references. AI intake resumes four chunks/run. Contextual review sends 24 sources and marks omitted guidance incomplete. Image pixels are unredacted; inspect all outbound images.

## Earlier detailed core checklist (previous navigation names)

1. Create an organisation. In Brand knowledge create a version with: approved fact `Cloudberry Daily Cleanser removes surface oil.`; tone `Use calm, precise language. Avoid exaggerated guarantees.`; prohibited term `miracle`; required disclaimer `Results vary.`. Add an approved price fact with entity `Cloudberry Daily Cleanser`, INR 799, unit `150ml`, effective from `2026-01-01`. Approve every rule and activate.
2. In settings inspect and enable the AI processing policy. Explain that only explicitly previewed content/approved excerpts leave the app, with local redaction, while confidential business wording may remain.
3. New review → text: `Cloudberry Daily Cleanser 150ml costs INR 499. A miracle cleanser guaranteed to cure acne. Results vary.` Save and inspect the outbound preview before sending.
4. Show the exact price/term mismatch and its approved source, plus the claim needing evidence. AI advisory results appear only if real inference succeeds. If the route fails, show the incomplete status and blocked approval; do not call it a completed AI check.
5. Request corrections. Compare the minimal/natural choices and explain code/model safety checks. Apply one safe choice if available; otherwise manually correct to `Cloudberry Daily Cleanser 150ml costs INR 799. It removes surface oil. Results vary.` Save and recheck. A failed rewrite must leave the original unchanged.
6. Send the fresh checked revision to the other reviewer. In that session inspect the exact content/evidence, add a comment and approve or request changes. The creator cannot approve. Approval never publishes content.
7. Return to creator: inspect history/download. Edit after approval and demonstrate the requirement to recheck. Start a new check while an approval is pending to demonstrate request supersession. Activate new guidelines and show stale checks.

## DOCX and image walkthroughs

Upload a fictional DOCX. Edit a paragraph and table cell using the native Word-style toolbar, save, download and reopen. Check headers/footer and formatting. Unsupported text-bearing parts, fields and unresolved tracked changes explicitly restrict submission. Do not promise arbitrary Word parity or simultaneous multiplayer editing.

Upload PNG/JPEG. Compare local OCR output against the displayed original and confirm the transcript before saving/reviewing. OCR may be unavailable; enter the transcript manually. Text rewrites do not modify image pixels. Visual logo/layout checks are manual exclusions. A PDF page with an image or missing extracted text remains incomplete and cannot be approved; use a verified text/DOCX source.

## Free-route failure

The key was genuinely exercised. Successful free inference and intermittent 429 failures are both recorded. Do not loosen privacy or switch to paid routes during the demo. Do not repeatedly retry a daily/shared capacity limit. A successful review does not prove rewrite availability. For an offline UI demonstration, run `npm.cmd run test:e2e:ai` and explicitly identify the synthetic provider fixture; this is test evidence, not real AI inference.

## Evidence commands

With the database running:

```powershell
npm.cmd run test:api
npm.cmd run typecheck
npm.cmd run build
.venv/Scripts/python.exe -m ruff check services/api
npm.cmd run test:e2e:ai
npm.cmd run test:e2e:simple
npm.cmd run test:editor
.venv/Scripts/python.exe scripts/check-docx-roundtrip.py
npm.cmd run eval:ai -- --mode offline
```

Install the local browser once if missing:

```powershell
$env:PLAYWRIGHT_BROWSERS_PATH = Join-Path $PWD '.cache/playwright'
$env:TEMP = Join-Path $PWD '.cache/tmp'
$env:TMP = $env:TEMP
node node_modules/@playwright/test/cli.js install chromium
```

Live synthetic workflow command: `.venv/Scripts/python.exe scripts/live-workflow-test.py`. It creates fictional materials and automated separate accounts, not actual human feedback. It has bounded retries and records provider failure. Reserve demo quota; do not launch multiple live evaluations concurrently. Reports and screenshots are private in `.local/test-results`.

## Before submission

Use `docs/IMPLEMENTATION_STATUS.md` and `docs/TEST_REPORT.md` for truthful delivery status. Optional static vision is implemented but live unavailable; assistant and recurrence analytics are not delivered. Do not present blocked/unimplemented capabilities as successful AI results.

The source repository and public deployment have not been published. Supply a judge-accessible repository, suitable private deployment or an organiser-approved installation/demo method. Include architecture, actual services/licences, AI/reuse disclosures, limitations, the event's required participant details and truthful contributions. A localhost link cannot be opened by remote judges.

Record actual feedback using `docs/USER_FEEDBACK.md`; leave unobserved tasks blank. Do not expose confidential screenshots, API keys or synthetic account passwords in a public recording.
