## Final deployment contract: prod branch — 28 October 2026

User clarified production on branch `prod`, requested consolidating/amending the
setup commits and restoring main, and explicitly asked not to monitor Actions.
Final workflow deploys on pushes to `prod` after reusable CI, with optional manual
dispatch where available. There is no GitHub environment. Repository Actions
secrets match ignored mode-0600 `.env.deploy`; runtime credentials stay on-host.
AWS OIDC trust is the exact immutable repository subject with
`:ref:refs/heads/prod`, and the target is tagged `DeploymentEnvironment=production`.
Temporary nonprod IAM permissions/role were removed. Existing host/IP/data remain.

Use the native standard `ubuntu-24.04-arm` runner for this public repository,
avoiding the slow emulated first build. The prior nonprod run was cancelled on
user correction; hosted CI had passed, but no completed hosted rollout is claimed.
Production Actions will be observed by the user; no further polling/monitoring.
Current local deployment boundary tests: 7 passed. Prior hosted CI verified the
148 backend tests and checks before the production branch/name correction.

GitHub reported main unprotected and no applicable main/prod rules before the
history change. Only the two setup commits created during this task are being
consolidated on prod; the pre-setup commit b971351 is main's restoration target.
A local refs/codex/backups/before-prod-migration ref preserves the old tip.
Force-with-lease is used only for that explicit main restoration, so concurrent
remote changes prevent the rewrite. No unrelated commits are dropped.

## Repository Actions secrets configuration — 28 October 2026

The user explicitly changed setup to repository Actions secrets with no GitHub
environment. Removed the environment block, retained main-only manual deployment
and updated AWS trust to the exact immutable repository subject ending
`:ref:refs/heads/main`. The role remains scoped to the tagged nonprod demo target.
Five deployment settings were installed as repository Actions secrets through the
API. No static AWS/model/database credentials were sent. The local `.env.deploy`
contains matching settings with mode 0600. The earlier environment-admin 403 is
historical; no new environment was created or required. Workflow execution and
first hosted deployment verification follow below.

## Actions AWS activation — 28 October 2026

At the user's explicit request, configured AWS role `BuildGateActionsNonprod`
with the repository's actual immutable OIDC subject and `environment:nonprod`,
restricted upload/SSM target permissions, host `ReadNonprodReleases` policy and
`DeploymentEnvironment=nonprod` tag. Existing GitHub OIDC provider audience was
verified. Filled the role ARN in ignored mode-0600 `.env.deploy`; configuration
validation passes. No long-lived AWS keys were generated or uploaded.

GitHub now grants `velox0` push access, but environment creation/protection PUT
returned HTTP 403 “Must have admin rights to Repository”. Environment secrets
and the first deployment remain pending environment admin access. The protected
nonprod setup has not been bypassed by using repository-wide credentials.
Workflow publication/CI verification proceed independently of that restriction.

## Nonprod GitHub Actions preparation — 28 October 2026

Added reusable CI (PR/main/manual deploy dependency) and a manual main-only
`nonprod` deployment workflow. Deployment builds ARM images off-host, uses OIDC
rather than static AWS keys, uploads a private release and verifies SHA-256 on
the existing 1 GiB demo host through SSM. Host rollout backs up the database,
locks app replacement, preserves runtime credentials/uploads/database/proxy,
and restores the prior app container on new-app startup/internal-health failure.
It reports failure if rollback or public HTTPS verification fails. Database
migrations are not undone by container rollback; expand-compatible changes only.

Created local ignored `.env.deploy` with mode 0600, demo identifiers and blank
OIDC role ARN. Committed template contains no secrets. Added exact-scope IAM
examples and `docs/GITHUB_ACTIONS_NONPROD.md` for the user's manual setup. No AWS
trust/permission/tag changes or GitHub environment/secrets changes were applied.
No hosted Actions run or new deployment was attempted in this preparation task.
The existing manually deployed demo remains unchanged.

Fresh checks: backend **148 passed in 18.96s**, deployment boundary **7 passed**,
typecheck/production build/Ruff/Bash syntax/diff checks passed; actionlint 1.7.12
reported no workflow errors. Focused independent read-only review found no
important issues and reran the seven deployment tests successfully. The initial
backend attempt needed the local PostgreSQL launcher restarted; subsequent full
run passed. Initial deployment-test failures reflected missing implementation;
a Mac test runner also needed a substitute for Linux `flock`. Final tests execute
actual shell control flow with isolated external-command substitutes, not AWS.

Pending user setup: repository write access, OIDC trust/role, `nonprod` host tag,
host release-read policy and GitHub environment secrets. Configuration validation
correctly refuses the intentionally blank `AWS_DEPLOY_ROLE_ARN`. See the setup
guide before activating manual deployment. Local secrets are excluded from the
curated source ZIP and Docker context; a placeholder template is safe to commit.

## Low-traffic downsizing — 28 October 2026

Reduced the running dedicated BuildGate host from `t4g.small` (2 GiB) to
`t4g.micro` (1 GiB, 2 burstable ARM vCPUs). Standard CPU credits retained.
App/PostgreSQL/proxy memory caps are now 512/256/64 MiB, with bounded swap and
existing 2 GiB host swap. Updated on-host startup and launch-template default
version 6, so subsequent deployment/replacement retains the low-traffic profile.

Made a private `pg_dump -Fc` archive and verified its table of contents before
the stop/resize/start. Preserved original encrypted 30 GiB EBS, IP, database,
uploads and provider key. Verified old synthetic draft and source records remain.
The previous smoke cookie was expired (401); fresh login succeeded. Public
verification passed four grouped checks: HTTPS/login, new registration/session,
organisation/draft write/read, exact private DOCX upload/download and anonymous
denial. Ten sequential health checks returned 200 in 0.258–0.304 seconds. All
containers stayed running without OOM; available RAM after smoke 422 MiB, swap
2 MiB. This is a low-traffic smoke, not a concurrent-load benchmark or AI eval.

Fresh AWS Price List: micro USD 0.0056/hour, USD 4.09/month at 730 hours. With
previous disk/IPv4 rates, base estimate **USD 10.47/month** before artifact
storage/traffic/tax, versus the previous USD 14.56. No commitments or new
infrastructure. Retained disk avoids migration; no EBS shrink was attempted.

Evidence: `.local/test-results/micro-public-smoke.json`,
`micro-server-verification.json`, `micro-retained-data.json`. `bash -n
deploy/ec2/start.sh` and `git diff --check` passed. No application code changed.

## Verified North Mini deployment — 25 October 2026

Live at **https://buildgate.velox0.com** with explicit model
`cohere/north-mini-code:free`, provider Cohere. The corrected public real-provider
review **passed all five grouped checks**, completed with reported cost **0**,
and returned the seeded deterministic price/unsupported-claim findings plus an
AI tone advisory backed by an approved source. Current-policy consent was
required; the old ZDR consent was rejected. Existing session and draft survived
redeployment. No approval or publication was performed.

Full backend suite **148 passed in 18.05s**; typecheck, production web build,
Ruff, diff check and corrected ARM image build passed. The server's provider-file
SHA-256 matches the tested local file. Runtime env remains root-only 0600. Private
evidence: `north-public-review.json`, `north-rollout.json` and
`north-real-repair-probe.json` in `.local/test-results/`.

Artifact downloads initially received IAM propagation 403s; the bounded retry
succeeded, then verified the full image SHA-256 before loading it. Launch-template
default version **5** now fetches the corrected image and current source archive.
No secrets are embedded in the template or image. Existing private key and data
were preserved on the current host; a replacement host still needs key setup.

Owners must enable the new policy in AI processing settings. No-training routing
remains required; provider retention may apply, and ZDR is not claimed for North
Mini. This is one synthetic live review, not a model-accuracy benchmark. North
Mini is text-only; no real vision success is claimed. No paid model was enabled.

## North Mini schema repair follow-up — 25 October 2026

The first public real review safely remained incomplete: the model returned
invalid category enum values, then prose during schema repair. Preserved the
failed report as `north-public-review-initial.json`. Added explicit schema and
function-call instructions to North Mini requests and kept repair in function
transport. A new regression failed before the correction; full suite then
**148 passed in 18.05s**. A real probe using that synthetic draft's outbound
payload returned schema-valid claim/messaging findings through Cohere at cost 0.
The correction is packaged for deployment; final public review is pending.

## North Mini Code verification — 25 October 2026

Real synthetic function-result adapter smoke: passed, actual model
`cohere/north-mini-code:free`, provider Cohere, reported cost 0. Strict ZDR probe
returned 404; the user explicitly approved provider retention with disclosure.

Seven new regression tests failed before implementation and then passed. They
cover function-result schema/transport, wrong/multiple/invalid calls, retention
opt-in scope and rejection of old ZDR consent. Full API suite **147 passed in
20.02s**. Typecheck, production build, Ruff, diff check and ARM Docker build passed.
The scoped independent review found no important issues. Reports are private in
`.local/test-results/north-*`; provider reasoning and credentials are excluded
from app results. Public deployment verification is pending below.

## AI environment verification — 25 October 2026

- EC2 SSM command verified `runtime.env` mode 0600/root and presence of API key,
  model, database migration URL, restricted-role password, HTTPS origin and port.
- App restart succeeded; public health HTTP 200 with `ai_mode: configured`;
  existing authenticated session and draft still returned HTTP 200.
- Local key authentication HTTP 200; free quota 50 remaining. Real structured
  free model probes returned 429 (Xing4) or no eligible endpoint 404 (three other
  models). AWS Nova probes were blocked by zero daily inference quotas. These
  failures are not successful model evaluations.
- Paid-mode boundary test draft demonstrated current paid-model rejection:
  147 passed/2 expected failures while exploring the optional change. Draft moved
  to ignored local work pending funding/implementation; it is not shipped as a
  failing regression suite. No paid provider code was implemented.
- Fresh unchanged application suite: `npm run test:api` **140 passed in 21.40s**.
  `git diff --check` passed; credential scan found no key in tracked/nonignored files.
- Private evidence: `.local/test-results/deployed-ai-environment.json` and
  `.local/test-results/paid-provider-red.log`. No credentials are in either report.

# Fresh macOS verification — 25 October 2026

## Public AWS deployment verification

- `https://buildgate.velox0.com/api/health`: 200, `server: cloudflare`,
  `cf-cache-status: DYNAMIC`, `Cache-Control: no-store, no-transform`.
  Cloudflare is proxied with Full (strict) TLS; origin certificate validated
  before origin firewall restriction. No TLS verification bypass used.
- Public synthetic smoke: **10 checks passed**, including registration/login,
  secure HttpOnly session, confirmed rule activation, DOCX upload/exact download,
  draft save/read, non-disclosing cross-org 404, anonymous 401, hostile Origin 403,
  exact source-only ZIP and session/draft/file retained after app restart.
- First smoke expected cross-org 403 but the implementation deliberately returns
  404. Inspected the backend contract and corrected the test's expected status;
  the initial report is preserved. No permission check was loosened.
- PostgreSQL mounted volume initially failed because its 0700 root belonged to
  root. Assigning it to the image's database UID retained 0700 and restored startup.
  A nonempty-volume reproduction passed three assertions. An initial empty named
  volume probe did not reproduce because Docker populates its permissions; it is
  not counted as a passing regression. An in-place script edit interrupted the
  original bootstrap shell; the corrected script was rerun after it exited.
- Live DB role privilege flags are all false (superuser, bypass RLS, create DB,
  create role). Encrypted storage and restricted origin firewall are configured.
- Full backend suite previously passed **140 tests**; application behavior did not
  change during deployment. Caddy validation, Bash syntax, Ruff and diff checks pass.
- The Mac retained an earlier missing-host DNS result. Public DNS resolves to
  Cloudflare; smoke selected that published address explicitly and retained full
  HTTPS hostname verification. `curl --doh-url` also reached the public service.
- Reports remain ignored under `.local/test-results`. No live AI request was made;
  cloud health accurately reports `ai_mode: unavailable` until a key is configured.

## Hosted package verification

- AWS EC2 dry-run: expected `DryRunOperation`, no instance created.
  `deploy/ec2/start.sh` passes `bash -n`; Caddy configuration validates.
  Actual EC2/Cloudflare public verification remains pending budget resolution.

- Full backend suite including hosted startup: **140 passed in 22.59s**.
- `docker build -t brandgate-hosted .`: passed (Python 3.12 and Node 22).
- Actual container smoke on an isolated PostgreSQL database: secure HttpOnly
  cookie; organisation/draft creation; exact DOCX upload and authorised download;
  unauthenticated private download rejected; uploaded bytes unchanged after app
  restart with mounted private storage. Five smoke assertions passed.
- Internal API termination stopped the hosted container with exit status 1.
  Missing hosted credentials failed before serving a public port.
- Independent Docker-context probe found and then verified the fix for nested
  `.env` exclusion. Root/nested synthetic credentials are absent from context.
- API/startup Ruff and `git diff --check` passed. Docker logs/reports stay under
  ignored `.local/test-results`. These checks are local; cloud deployment and
  real-provider AI checks remain unverified.

## Requested rerun — 25 October 2026

- `npm run test:api`: **129 passed in 21.08s**.
- `npm run typecheck`, API Ruff and `npm run build`: passed.
- `npm run test:e2e:simple`: **17 passed**, synthetic provider.
- `npm run test:e2e:ai`: **17 passed**, including concurrent-save safeguards;
  both browser suites reported four clean selected axe scans and no runtime errors.
- DOCX probe initially saved the paragraph but missed the table edit; no browser
  runtime errors were reported. This first attempt overlapped the production
  build; the cause is not established. Unchanged rerun after the build:
  **4 editor checks and 9 fidelity assertions passed**. Keep this as an
  intermittent test failure, not proof that it was fixed.
- Offline evaluation: **23 passed, 0 failed, 27 not run** out of 50.
- Local provider key remains empty; API reports `ai_mode: unavailable`.
  The Safari-created key has not been saved locally. No live inference attempted.

## Earlier setup verification

- `npm ci` and Python 3.12 locked dependency installation succeeded.
- `npm run test:api`: initially 112 passed/17 failed (missing live key in synthetic
  fixtures); after test isolation fix, **129 passed in 19.82s**. Default provider
  transport is blocked; contract tests use explicit synthetic HTTP transports.
- `npm run typecheck`, `npm run build`, `.venv/bin/python -m ruff check services/api`
  and `git diff --check`: passed.
- `npm run test:e2e:simple`: initial Windows Python path failure, then missing
  fixture credential; corrected both. Final **17 checks passed**, four clean
  selected axe scans, zero runtime errors, synthetic provider only.
- `npm run test:editor`: **4 passed**, no external requests/runtime errors;
  `.venv/bin/python scripts/check-docx-roundtrip.py`: **9 passed**.
- `npm run test:e2e:ai`: **17 passed**, including comments/history, exact revision
  approval, dirty-buffer conflict protection, clean reviewer refresh and four
  clean selected axe scans; zero browser runtime errors, synthetic provider only.
- `npm run eval:ai -- --mode offline`: **23 passed, 0 failed, 27 not run**, 50 total.
  Executed subset only; no overall model-accuracy claim.
- Fresh local API `/api/health`: `ok`, `ai_mode: unavailable`; web `/login`: 200.
  No key is configured and no live provider inference was attempted.
- `npm audit --json`: four high entries (AG-UI client/encoder/proto and Zod),
  `fixAvailable: false`. Report saved under ignored `.local/test-results`.
- Playwright browser download completed but Node 26 extraction stalled; extracted
  the matching official headless archive using Python before the passing tests.

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
