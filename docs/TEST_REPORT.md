# Simplified workflow verification — 24 October 2026

## Latest results

- Final `npm.cmd run test:api`: **129 passed in 197.30s**, synthetic completions/HTTP fixtures and a real separate PostgreSQL database. Covers source aggregation, evidence/price validation, editable proposals, explicit replacements, immutable snapshots, task binding, missing/omitted guidance, tutorial isolation, visual-only approval readiness without a transcript and existing revision/permission safeguards. Current full report: `.local/test-results/backend.xml`.
- `npm.cmd run typecheck`, `npm.cmd run build`, `.venv/Scripts/ruff.exe check services/api`: passed.
- `npm.cmd run test:e2e:simple`: **17 checks passed**, four selected WCAG A/AA scans with zero violations and zero browser runtime errors. Includes isolated example, source confirmation, cited findings, text correction/recheck, separate reviewer approval, Tracking, static-ad palette/no image correction, X help and 390px no overflow. `.local/test-results/simple-workflow-browser.json`. Provider is explicitly synthetic; palette code runs locally.
- `npm.cmd run test:e2e:ai`: **17 checks passed**, four scans with zero selected violations and zero runtime errors. Existing comment/history/approval workflow plus concurrent dirty-buffer protection and clean reviewer refresh reran against the simplified UI. `.local/test-results/ai-workflow-browser.json`.
- `npm.cmd run test:editor`: **4 passed**, zero runtime/console errors or external requests. Actual SuperDoc paragraph/table edit, save/download, immutable original, reopen. `scripts/check-docx-roundtrip.py`: **9 passed** on the resulting representative fixture; arbitrary Word parity is unproven.
- `scripts/live-simple-smoke.py`: real synthetic source-intake call **blocked by 429**; real vision **unavailable: no endpoint satisfying free pricing, ZDR and schema**. Report `.local/test-results/simple-live/report.json`. No real company materials used. No real extraction/vision success or complete live workflow claim.
- Independent final code review found contextual-source truncation could overstate coverage and saved company instructions were ignored. Fixed: affected omitted categories stay incomplete, validation accepts only previewed evidence, intent reaches intake/review and is redacted. Regression tests pass.
- Browser iterations found a tutorial remount losing example links, muted-text contrast, text-link distinction, an overflowing focused tooltip and a test racing correction reload. Fixed before the passing runs. Tooltip placement follows the viewport; Escape dismisses it. Editor probe now dismisses the welcome panel before interacting with Save.
- One preceding full backend run had 126 passed, one failing new test with a wrongly classified legacy fixture and one transient PostgreSQL connection timeout. Corrected the fixture; targeted rerun confirmed the timeout case, then complete 128-test and final 129-test runs passed. Final visual module targeted run also passed 25 tests after the reference-limit message refinement.

Historical results below describe the earlier core. Their P1 statements are superseded by the user's later static-image request: optional vision is now implemented but live unavailable; assistant and recurrence analytics are still unimplemented. Automated users and synthetic providers are not independent human feedback or AI-accuracy evidence.

# Earlier AI workflow verification — 24 October 2026

This is the current report. Foundation results retained below are historical. No real company materials were used in tests or sent to inference.

## Actual results

| Command/check | Outcome | Scope and evidence |
|---|---|---|
| `npm.cmd run test:api` | **79 passed in 123.55s**, including the final currency-boundary extension | Real separate UTF-8 PostgreSQL database; provider completions replaced by explicit test doubles/HTTP contract fixtures. `.local/test-results/backend.xml`. |
| `npm.cmd run typecheck` | Passed | Current editor/image/restore/revision-binding TypeScript; production build also reran type checking. |
| `npm.cmd run build` | Passed | Next.js production compilation, types and route generation after the final UI revision fix. |
| `.venv/Scripts/python.exe -m ruff check services/api` | Passed | Current API, ingestion, providers, graph/evaluators and tests. |
| `npm.cmd run test:e2e:ai` | **17 passed**, four axe scans, zero violations in selected rules | Isolated ports 3001/8001, synthetic provider only. Create → preview → review/evidence → correction → recheck → comments → distinct-account approval → history, 390px layout, stale dirty buffer protection and clean reviewer revision refresh. `.local/test-results/ai-workflow-browser.json`. |
| `npm.cmd run test:editor` | **4 passed**, zero browser runtime errors/external requests | Actual SuperDoc in the production local app: paragraph/table edit, save, immutable original, download/reopen. `.local/test-results/editor-probe.json`. One aborted navigation request was recorded; no editor error. |
| `scripts/check-docx-roundtrip.py` | **9 passed** | Header/footer, table shape/edited cell, paragraph, untouched bold/size/color, page size. `.local/test-results/docx-fidelity.json`. |
| `npm.cmd run eval:ai -- --mode offline` | **23 passed, 0 failed, 27 not run** out of 50 | Developer-labelled synthetic dataset. Eighteen executed issue cases and five rewrite guard cases; no overall AI accuracy. `.local/test-results/evaluation-offline-benchmark.json`. |
| Live synthetic review | Succeeded on two earlier calls | Actual `xingchen-agi/xing4.0-29b-a4b:free`, Phala, reported cost 0; valid persisted approved-rule evidence. No fake result substituted. |
| Final `scripts/live-workflow-test.py` | **Blocked**, two bounded review attempts returned 429 | Runs `61ff24b8-143e-4940-9c85-041d78163033`, `4a3843b9-6842-4ff8-a8b4-c45da3d7e5b1`; each remained incomplete. `.local/test-results/live-workflow.json` and archived attempts. No successful full live correction/recheck/approval claim. |

The main preview is http://127.0.0.1:3000/login, with API on 8000 and PostgreSQL 54329. Production web build is served locally. This is not public deployment.

## Failures found and corrected

- PostgreSQL WIN1252 prevented representative Unicode DOCX data. Non-destructive UTF-8 copy retained old data/config and verified table counts; regression covers emoji/currency/headers and immutable originals.
- Initial accessibility browser checks found an unassociated reviewer label. Explicit input association fixed it; four final scans passed.
- Independent final static review found five Important issues: stale displayed revision versus approval/save metadata; a recheck stranding pending approvals; ignored DOCX chart/diagram text; scanned PDF body plus selectable header receiving complete coverage; substring entity/currency matches causing false price violations. A single fix pass added regression tests and fixed all five. Pending approvals are superseded transactionally; incomplete coverage blocks submission. Browser tests reproduce both concurrent creator and clean reviewer refresh paths.
- The first added concurrency browser test attempted submission before its background check finished and got the expected 409. The test now waits for canonical completion; the rerun passed all 17 checks.
- Some free provider routes refused the required privacy policy. The eligible Phala route succeeded intermittently, then returned 429. One live rewrite failed structured validation before bounded repair was added; a real successful rewrite with the repair remains unproven. Errors remain visible and never authorise approval.
- PDF dependency advisory: pinned pdfjs-dist 5.4.296. Four transitive AG-UI/Zod advisory entries remain; no clean-audit claim.

## Coverage limits and release gate

The 118-row acceptance catalogue is broader than the executable suite. Unmapped/planned cases remain unproven. Fifty synthetic labels are developer-authored, not independently adjudicated; 27 contextual cases were not run. Selected accessibility scans and screenshots do not establish complete accessibility. The DOCX fixture does not prove universal Word fidelity, arbitrary tracked-change support, all fonts, complex sections or RTL. Image OCR is local and requires creator verification; appearance/logo consistency remains manual. PDF image pages remain incomplete.

A real-model whole workflow, a safe live rewrite, a clean live control and a distinct actual human decision have not been demonstrated together. Two automated accounts are not independent human feedback. **The P0 live acceptance gate is open. P1 visual AI, assistant and recurrence analytics remain unimplemented under the required P0-first gate.** No public repository/deployment or real participant study is claimed.

## Historical foundation report

# Foundation verification — 2026-10-23

## Latest follow-up: email/password sign-in

The user requested removing account verification codes for this prototype. Fresh backend results: **34 passed in 48.99 seconds**. Regression coverage confirms direct sign-in after registration, sign-in by previously unverified accounts, duplicate registration, incorrect passwords, session cookie protection, expiry and logout. TypeScript and Python lint passed. The updated browser workflow passed **17 checks**, including registration followed directly by email/password sign-in, absence of the code field/action, onboarding, role restrictions, streaming, logout and mobile layout. Five automated accessibility scans reported zero violations. An initial browser run hit connection refused while the services were restarting; restarting the combined development launcher restored the preview and the full rerun passed. No production build was rerun for this follow-up.

The sections below retain the original checkpoint results from before account verification was removed.

## Scope

Accounts, organisations, email-token delivery adapter, invitations, role enforcement, PostgreSQL row security, approved guideline version lifecycle, provenance validation, upload failure handling, and the authenticated AG-UI diagnostic. No model or compliance accuracy is evaluated in this phase.

## Results

- Backend: **32 passed**, 0 failures/errors/skips, in **83.50 seconds** using the separate `inkloom_test` PostgreSQL database. Prior run on the same implementation also passed 32 checks before test database isolation was added.
- Python lint: passed after formatting/fixes.
- TypeScript: passed.
- Next.js production build: **passed**, including the final build after the stream-compression correction.
- Browser workflow: **17 checks passed**, including registration, verification, onboarding, v1/v2 preservation, invitations and denied creator actions, real streamed progress, cancellation, disconnect/refresh recovery, mobile navigation, logout and protected routes. No browser runtime errors in the passing run.
- Accessibility: **5 scans**, **0 violations** reported for the selected WCAG 2 A/AA and 2.1 AA rules on sign-in, desktop overview/knowledge, and mobile overview/knowledge. Desktop and 390px mobile screenshots were visually inspected; the checked mobile pages had no horizontal overflow.

Raw results: `.local/test-results/backend.xml`, `.local/test-results/browser.json` and screenshots in the same directory. Synthetic fixtures only.

The combined `npm.cmd run dev` launcher was started successfully after stopping the individual development services. PostgreSQL, FastAPI and Next.js all started on their documented loopback ports. A proxied health request returned `ok` with `ai_mode: disabled`; the login page returned HTTP 200. PowerShell setup and outbox scripts passed syntax parsing. The setup script was not rerun against already-installed dependencies.

## Failures found and addressed

1. The first backend run passed 28 tests but hit two setup/teardown errors in one oversized-file case because pytest placed the entire 5 MB payload in its test ID, exceeding Windows environment-variable limits. Explicit short test IDs fixed the runner; the oversized upload check then passed.
2. The first accessibility scan found insufficient contrast on the small AI mark. Its foreground colour was darkened. Later sign-in and desktop scans passed.
3. Browser locators initially assumed helper text was excluded from label names. They now match the actual accessible labels. This was a test selector failure.
4. The cancellation test exposed proxy compression buffering all SSE events. A timed probe found the proxy delivering the first event only at completion (~2.9 seconds). Disabling Next.js compression produced the first proxied step at ~133 ms, with completion at ~3.5 seconds in that sample. This demonstrates incremental transport in this local run; it is not a latency benchmark.
5. The portable database dependency used an OS temporary setup file on first initialization and removed it in its `finally` block. The launcher now explicitly redirects all its temporary files to `.cache/tmp`. No outside project files were intentionally retained. This exception to the requested folder boundary was disclosed to the user.

## Test commands

```powershell
npm.cmd run test:api
npm.cmd run test:e2e
npm.cmd run typecheck
npm.cmd run build
.\.venv\Scripts\ruff.exe check services/api
```

Browser screenshots: `.local/test-results/desktop-overview-empty.png`, `desktop-overview-active.png`, `desktop-brand-knowledge.png`, `mobile-overview.png`, `mobile-brand-knowledge.png`.

## Limits

Tests exercise synthetic local scenarios. They do not prove production readiness, full accessibility conformance, exhaustive PDF parser safety or real email verification. No content draft/review/approval tables exist yet, so stale content approval, self-approval and review-version pinning remain later tests. Historical guideline immutability and cross-tenant evidence checks are covered here.



## Current source package verification

The local source repository was initialized inside this project on codex/inkloom-ai; no commits were fabricated, parent repository changed or public push made. scripts/package-source.py generated a 118-file ZIP and hash manifest inside .local/releases. It checks selected source against the configured OpenRouter key and key patterns, excludes private/runtime/generated paths, and retains licences. This is a curated source package, not a clean-machine installation test or exhaustive secret audit. No actual independent user-feedback session was recorded.
