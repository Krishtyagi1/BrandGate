## Vision preflight and measured local pixel checks — 30 October 2026

User requested pushing the completed Round 3 work and continuing. Signed commit `3d797a6` was pushed to `origin/prod`; its existing CI/deployment workflow is triggered by pushes. No Actions monitoring or hosted rollout success is claimed.

Continued with a metadata-only fail-closed vision preflight: model-level capabilities are insufficient; exact model/provider/tag identity must also appear in the published ZDR list and endpoint pricing/schema support must qualify. No image inference POST is issued when this cannot be verified. Runtime routing remains unchanged. Added an on-demand organisation-scoped status check in Settings. The 30 October read-only probe found no published qualifying ZDR endpoint for either free image/schema candidate. This is time-bound metadata evidence, not a guarantee about future availability.

Added a separately labelled deterministic pixel benchmark: 8 known contrast pairs +4 palette cases, including1 expected transparency rejection; actual **12/12 expected outcomes**. This does not measure model accuracy or independent human agreement. Model benchmark remains **0/12 evaluated**, with manual reference comparison as fallback.

Final continuation verification: **174 backend tests passed in20.17s**, **28 browser checks passed** including **9 selected axe scans with0 reported violations**; production build/TypeScript, Ruff and whitespace checks passed. Independent review identified two edge cases, reproduced and fixed with regressions, plus a passing metadata deadline regression. No deferred findings. Actual commands/outcomes are recorded in docs/ROUND3_PROGRESS.md. No credentials, company materials or actual-person photos included.

## Round 3 improvements — 29 October 2026

Implemented locally at the user's direction. The prior build authorisation remains recorded below; no official Round 3 calendar dates are inferred. No commit, push, deployment, hosting change or Actions monitoring was performed.

- **Visual review:** model findings now carry a bounded suspected-old-logo/placement/distortion/reference-difference type and normalised image regions. The review preview outlines those regions. A separate owner/reviewer can append a confirmed/not-an-issue/uncertain judgement with a note; the original finding remains advisory and no draft approval is created. Current approved logo images are available for manual comparison even when inference is unavailable.
- **Local contrast:** a member selects foreground/background pixels by clicking or entering coordinates. Server code verifies the saved revision/private file hash, rejects transparent samples and calculates luminance/contrast. Threshold comparison uses the unrounded ratio. This measures only those pixels, not text segmentation, font size or whole-image accessibility. EXIF orientation is applied to decoded images while original-byte hashes stay unchanged.
- **Finding assistant:** local extractive why/fix answers from the current finding's pinned approved rules. Exact citation IDs, excerpt, location and source identity must resolve before display. Missing/forged evidence and unsupported questions abstain. It has no provider call or edit/approve/activate tools. Answers use official AG-UI message events; questions/answers are privately persisted, bounded, rate-limited and idempotent. Current draft/source/scope/latest-run checks apply before answering and replaying streams. Supported phrasing is intentionally bounded; this is not a general conversational model.
- **Insights:** owner/reviewer view under Tracking, with 7/30/90-day UI periods (API 1–365 days), finding types by channel/creator/campaign and Unverified/assistant-abstention gaps. Counts retain historical findings across revisions in the period, one distinct draft per type/status, with corrected/dismissed observations retained and latest-check incompleteness disclosed. Campaign is optional current metadata; it does not change approved facts or review authority. Questions are a separate period-based denominator and can signal unsupported phrasing rather than a missing rule.

**Final verification:** `npm run test:api` → **163 passed in 25.74s**. `npm run test:e2e:simple` → **26 checks passed**, including **eight selected axe scans with zero reported violations**, desktop and 390px insights/visual-inspection/new-review coverage. `npm run build` passed production compilation and TypeScript; standalone typecheck and Ruff also passed. `git diff --check` passed. These are synthetic/offline workflow checks, not model accuracy or full accessibility certification. Independent read-only code review found one Important EXIF coordinate issue; the regression failed first (1:1 instead of21:1) and passed after orientation correction, followed by the full suite. No other Critical/Important findings or deferred minors were reported. See docs/ROUND3_PROGRESS.md for the evidence ledger.


**Live vision outcome:** `PYTHONPATH=services/api .venv/bin/python -m evals.visual_run --live --limit 4` selected `dots-studio/dots-3-note-preview:free`; the first inference returned HTTP 404/no endpoint meeting free/ZDR/schema requirements. No privacy downgrade or paid fallback. Twelve developer-labelled geometry-only image fixtures were generated; **0 evaluated / 12 unrun**, with agreement, precision and recall **null**, not zero accuracy or a pass. A second explicit synthetic probe of `nvidia/nemotron-3.5-super-vl:free` also returned HTTP 404. These were the two catalogue-compatible free image/schema candidates at probe time; the result is time-bound, not a claim that future/free routes can never work. See `evals/reports/visual-round3.json`. Manual reference comparison plus local palette/contrast is the documented fallback. Independent human labels and real-image agreement remain outstanding.

See docs/ROUND3_GUIDE.md for usage, reproducibility and limitations.

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

## North Mini Code redeployment — 25 October 2026

User-selected `cohere/north-mini-code:free` passed a real adapter smoke through
Cohere with reported cost 0. The user approved possible provider retention with
no-training routing retained. Added narrowly scoped server opt-in, a new
processing-policy version, fresh owner consent, settings/preview disclosure and
schema-validated function-result transport. Arbitrary/wrong/multiple function
calls and invalid arguments cannot become a pass; no model tools are executed.

Fresh verification: **147 API tests passed in 20.02s**; seven new transport/privacy
tests were first observed failing, then passed. Typecheck, production web build,
Ruff, diff check and ARM Docker build passed. Focused independent read-only review
reported no important findings. AWS image rollout and public live review follow.
No model accuracy percentage or complete real-AI approval workflow is claimed.

## AI environment follow-up — 25 October 2026

Installed the user-authorised OpenRouter key into the ignored local `.env` (0600)
and root-only EC2 `private/runtime.env` (0600). Transfer used a temporary SSM
SecureString with exact-parameter role permission; both parameter and permission
were removed after installation. No secret appeared in SSM command bodies,
reports, source archives or Docker builds. Recreated the app to load environment.
Verified all six required runtime fields present, public HTTPS health configured,
and existing session/draft still accessible after restart.

The key authenticates, has a USD 0 cap and expires 31 October 2026 UTC (1 November
in India). Free quota metadata reported 50 remaining. Real structured synthetic
requests: Xing4 returns HTTP 429 with upstream shared-pool throttling; Dots,
Nemotron VL and Liquid reject free/ZDR/schema routing with HTTP 404. Safari
credits shows an existing negative USD 0.20 account balance. No privacy filter
was weakened. AWS Nova Micro/Lite probes also rejected daily quota; Mumbai quota
inspection confirms zero inference quotas. No Bedrock integration was added.

User approved up to USD 1 for model use and chose to add the USD 5 minimum
OpenRouter credit balance in Safari. Payment and changing the key to a nonresetting
USD 1 total cap remain user actions. Retest free routing after the account is
funded before implementing the optional paid adapter design. That design is
pending; current application still rejects paid models. No real AI success is
claimed while provider access remains blocked.

## Public AWS deployment — 25 October 2026

Live URL: **https://buildgate.velox0.com** (Cloudflare proxy, Full strict TLS).

- Dedicated Mumbai ARM `t4g.small`, standard CPU credits, encrypted 30 GiB gp3,
  stable IPv4; existing unrelated instance unchanged. Management uses SSM.
  Origin ports 80/443 accept only Cloudflare's official IPv4 ranges; SSH, database
  and app ports are not public. Private runtime IDs stay in ignored deployment state.
- User approved a USD 20/month hosting budget. Queried base components estimate
  **USD 14.56/month** at 730 hours, before small S3 storage, traffic and taxes.
  This is a usage estimate, not an automatic AWS spend cap. No commitments bought.
- Actual public HTTPS smoke passed **10 checks**: health/noncached API, login page,
  registration/login/secure cookie, human-confirmed rule activation, exact DOCX
  upload/download, saved draft, cross-org/anonymous denial, cross-origin write
  denial, source ZIP, and session/draft/upload retention after app restart.
  TLS validation stayed enabled. The Mac cached the hostname's earlier NXDOMAIN;
  explicit public DNS/DoH checks confirmed the live Cloudflare endpoint.
- Initial PostgreSQL bootstrap hit a root-owned 0700 volume error. Fixed ownership
  to the image's actual database UID without widening permissions. A focused
  container reproduction passed three assertions; corrected startup was rerun
  successfully. Launch-template default version 3 includes the corrected startup.
- Restricted live DB role verified `NOSUPERUSER NOBYPASSRLS NOCREATEDB NOCREATEROLE`.
  Original files/accounts/data were not migrated. Public checks used synthetic data.
- **Updated configuration:** the OpenRouter key is installed in the private server
  environment (0600); explicit model `xingchen-agi/xing4.0-29b-a4b:free`.
  Public health reports configured. Current real probe returns upstream 429; no
  successful live inference, rewrite or complete live AI workflow is claimed.
  Current source is offered at `/source/buildgate-source.zip?release=aws-20261025`.

## Hosted deployment preparation — 25 October 2026

Latest steering: user switched to AWS and specified `buildgate.velox0.com` through
Cloudflare. Existing AWS CLI identity works in Mumbai; existing unrelated `main`
instance is untouched. Selected `t4g.small` (2 ARM vCPU, 2 GiB), standard CPU
credits, encrypted 30 GiB gp3 and stable IPv4. Official AWS Price List returned
USD 0.0112/hour (USD 8.18 for 730 hours), excluding storage/IPv4/traffic/taxes.
AWS account credit state could not be verified. User subsequently approved a
USD 20/month hosting budget. A dedicated instance launched with stable IPv4,
encrypted 30 GiB gp3 and no SSH ingress. SSM is online; runtime IDs are retained
only in the ignored local deployment state.
Private S3 release storage and a narrowly scoped artifact-read/SSM role were
created. DNS A record `buildgate` points to the host, initially DNS-only while
Caddy obtains its public certificate. Cloudflare zone mode is Full (strict).
Bootstrap/import and public verification are in progress; no live URL claim yet.

Official component prices yield USD 14.56/month at 730 hours for compute, 30 GiB
gp3 and one IPv4, before small S3 storage, traffic and taxes. Standard CPU credits
avoid surplus CPU billing. This is a usage estimate, not a hard AWS spending cap.

EC2 dry run returned expected `DryRunOperation` (launch permission confirmed).
Cloudflare access to `velox0.com` works and filtered DNS shows no `buildgate`
record. Tested ARM app/Postgres/Caddy images are packaged locally. Caddy config
validates; `deploy/ec2/start.sh` passes Bash syntax checking. Source-only archive
passes the existing credential/path scan; no local accounts or private files are
included. The public URL is not live yet.

User requested a public deployment, limited hosting to trial/free credits and no
paid upgrade, then selected GCP after reporting Railway trial was exhausted.
Render sign-in succeeded but no resources were provisioned. GCP's initially
selected account had no active billing account; user is switching to a credited
account. No public deployment or URL exists yet.

- Added Docker build and hosted supervisor for public Next.js plus loopback API,
  exact HTTPS origin/secure cookies and separately credentialled restricted DB role.
  No local accounts/files/database are copied. Cloud upload/Docker ignore rules
  exclude private state, including nested environment files.
- Full API suite: **140 passed in 22.59s** (11 new hosted-startup checks).
  API/startup Ruff and diff checks passed. Docker production build passed.
- Real container smoke: secure HttpOnly cookie, organisation/draft save,
  authenticated exact DOCX upload/download, unauthenticated source denial and
  exact upload retained after restart with a private mounted volume. Killing the
  internal API ended the container with status 1, stopping the public server.
  This local test is not a cloud deployment or a live AI result.
- Independent packaging review found nested `.env` files could enter the image;
  fixed recursive exclusions and reran a synthetic actual Docker context check.
  Both root and nested environment files are excluded. No leak observed.
- GCP CLI container is available locally; account/project/credit verification is
  required before provisioning. The OpenRouter key is still absent locally.

## macOS execution and test isolation — 25 October 2026

Requested verification rerun: backend **129 passed in 21.08s**, simplified browser
**17 passed**, build/typecheck/Ruff passed, offline evaluation **23 passed / 27
not run**. Editor's initial attempt missed the table change; unchanged rerun
passed **4 editor / 9 fidelity** checks. Cause remains unconfirmed; see test report.
Live key is still absent from `.env`, so genuine inference remains blocked.
Collaboration/concurrency browser rerun: **17 passed**; both browser suites
reported four clean selected axe scans and zero runtime errors.

- Installed locked npm/Python dependencies in this checkout using Python 3.12.13;
  started project-local PostgreSQL, FastAPI and the production web server.
  API health returned `ok` with `ai_mode: unavailable`; `/login` returned HTTP 200.
- Fixed both browser launchers to select the platform's virtual-environment Python.
  Original Mac command failed with Windows-path `ENOENT`.
- Fresh backend run initially had 112 passes/17 failures because synthetic review
  fixtures depended on an ignored developer key. Added synthetic environment
  configuration and a default blocked provider transport; HTTP contract tests
  still use explicit mock transports. Full rerun: **129 passed in 19.82s**.
  Browser fixture server now also supplies synthetic environment settings because
  the review API imports its settings function separately.
- `npm run typecheck`, `npm run build`, API Ruff and `git diff --check` passed.
  `npm run test:e2e:simple`: **17 passed**, including four clean selected axe scans.
  `npm run test:editor`: **4 passed**; DOCX roundtrip subset: **9 passed**.
  `npm run test:e2e:ai`: **17 passed**, four clean selected axe scans and zero
  runtime errors; includes concurrent saves and reviewer refresh.
- Offline benchmark: 23 passed, 0 failed, 27 not run out of 50. This does not
  establish contextual model accuracy. No live provider key is configured here;
  live P0 review/rewrite acceptance remains open and P1 expansion remains held.
- npm audit still reports four high-severity entries, with no automatic fix:
  AG-UI client/encoder/proto and Zod. No dependency upgrade was guessed.
- Playwright's Node 26 archive extraction stalled locally. Downloaded the official
  matching headless browser archive and extracted it with Python to the ignored
  project cache; the resulting browser ran the tests. README now includes Mac setup.

## Latest simplified workflow checkpoint — 24 October 2026

Source-publication preparation: expanded README with fresh-checkout instructions,
repository structure and recorded verification; strengthened .gitignore for
environment variants, private data, generated output and credentials; added
root progress.txt with the handoff, remaining work and live-provider limitations.
Target: https://github.com/Krishtyagi1/BrandGate. Preserved the remote initial
README commit as the base for the local source commit. Staged 146 source/sample/
documentation files; allowlist and configured-secret/pattern checks found no
findings. No application behavior changed or application tests rerun for this
documentation/publication task. Earlier no-public-push statements below describe
the historical checkpoints; consult Git history for publication state.

The user's follow-up requirements and answers are implemented in the existing project. Product name is Brand Content Review; white UI with Rules, New review and Tracking, one-page Rules setup, accessible category/platform help and replayable tutorial.

- Combined source collection with source-backed proposed fields, editable candidates/manual guidance, highlighted literal evidence and explicit human confirmation. Missing categories remain visible; supported checks continue.
- New uploads add to the same visible version. Confirmed overlap replacements append immutable snapshots and invalidate stale approvals. Explicit New version starts empty. Existing user data was retained.
- Review category/platform, selected checks, per-review tasks and company intent are saved and preview/hash bound. All current revision/role/evidence controls remain. Zero supported checks and omitted contextual sources never count as complete.
- Static images: local dominant-palette observations and optional capability-checked free vision, source references, unredacted pixel disclosure, no image corrections, video unsupported. Exact fonts and full accessibility certification unsupported.
- Isolated fictional tutorial workspace has unconfirmed sample sources, incorrect text/ad and no precomputed AI results or automatic processing consent. Human confirmation remains required.
- Final backend command `npm.cmd run test:api`: **129 passed in 197.30s**. TypeScript, Ruff and production build passed. Simplified browser **17 checks** and existing AI-workflow browser **17 checks** passed, each with four axe scans and zero selected violations/runtime errors. Real DOCX editor **4 checks**, representative roundtrip **9 checks** passed. Reports stay private under `.local/test-results`.
- Latest real synthetic intake probe blocked by free-model 429. Vision probe found no endpoint meeting free/ZDR/schema requirements. No paid fallback or privacy downgrade; neither was presented as successful AI.

Plans: `docs/superpowers/specs/2026-10-24-simple-source-review-design.md` and `docs/superpowers/plans/2026-10-24-simple-source-review.md`. All new files/caches/reports remain inside this project. Historical checkpoints below retain their original statements and counts.

## Previous core verification checkpoint — 24 October 2026

Authoritative current checkpoint; earlier sections below retain historical states.

- Core draft/review/rewrite/human-approval implementation is present, including text/DOCX/PDF/image content, local verified OCR transcripts, private files, current rule/revision pins, evidence validation, redacted preview, exact checks, real free OpenRouter adapter, comments, restore and history.
- Latest completed verification: 79 backend tests; 17 isolated browser checks; four axe scans with zero selected violations; four real DOCX browser checks and nine representative fidelity assertions; TypeScript, production build and full API Ruff passed. Offline evaluation: 23/50 passed, 27 contextual cases not run. The final full API rerun, including the extended currency-boundary cases, passed 79 tests in 123.55s.
- Independent final review identified five Important issues. Fixed displayed/base revision binding, recheck/pending-request supersession, DOCX drawing text coverage, mixed scanned PDF coverage and bounded price matching; regression evidence is in the test report. Review was static; it did not establish model accuracy.
- Actual free synthetic review succeeded twice with Xing4.0/Phala, reported cost 0. The final bounded full workflow attempt was blocked by two 429s. A live safe rewrite and full live acceptance remain unproven. No real company materials were transmitted.
- P1 visual AI, scoped assistant and recurrence insights are not delivered because the core live gate has not passed. No auto-publication. No actual independent user feedback.
- Current local preview uses the production web build at http://127.0.0.1:3000/login. A local project Git repository was initialized on codex/inkloom-ai inside this folder; no commit history was invented and no parent repository was changed. A curated local source archive was generated at .local/releases/inkloom-source.zip with 118 files, credential-pattern checks and a SHA-256 manifest; dependencies, private files and Git metadata are excluded. No public source push or public deployment.

See `docs/TEST_REPORT.md`, `docs/DEMO_RUNBOOK.md`, `docs/ARCHITECTURE.md` and `EXTERNAL_COMPONENTS.md` for exact commands, data flow and limitations. Application source uses AGPLv3; the separate proprietary DOCX Engine terms/notices are retained and disclosed.

# Inkloom implementation status

## 2026-10-24 approved build — current progress

The user approved implementation after reviewing the brief. The account/guideline foundation has now been extended with saved text/DOCX/PDF/image drafts, immutable revisions, stale-save protection, a browser Word-style editor, real OpenRouter review, code checks, approved-source retrieval, local redaction and explicit processing consent, evidence validation, correction jobs, comments, revision restore, a content library, approval queue and backend version/hash-bound decisions. Image OCR runs locally on Windows and requires creator verification; image appearance remains excluded and requires reviewer inspection. These are implemented features, subject to the checks and limits below.

- Real synthetic inference succeeded with `xingchen-agi/xing4.0-29b-a4b:free`, provider Phala, reported cost 0. Seeded pricing and tone findings were persisted with approved references. Free upstream capacity is intermittent: subsequent requests returned 429, and a live rewrite did not validate. Full live correction/recheck/approval validation remains in progress; no reliability claim is inferred from one successful inference.
- Isolated browser integration passed **15 checks**, including creating a draft, explicit outbound preview, evidence, correction/application/recheck, comments, separate-account approval, refresh/history, 390px layout and four accessibility scans. Its provider was an explicitly named synthetic test double, not a live-model accuracy test. Evidence: `.local/test-results/ai-workflow-browser.json`.
- DOCX browser probe passed actual paragraph and table editing, server save, immutable originals, export and reopen. A representative fidelity check passed headers, footers, table shape, edited cell, untouched bold/size/color and section page size. No external browser requests were observed. This proves that fixture, not arbitrary Word parity. Evidence: `editor-probe.json`, `docx-fidelity.json` and screenshots in `.local/test-results/`.
- Production build and TypeScript passed after the main text/DOCX workflow integration. New image/restore changes are receiving their follow-up checks.
- The 50-case developer-labelled synthetic evaluation dataset exists. Offline mode: **23 passed, 27 not run, 0 failed**; 18 issue-detection cases plus five rewrite safety cases. Contextual cases remain not run offline. No overall AI accuracy is claimed.
- PostgreSQL was discovered to use WIN1252. All application rows were copied and counted into `inkloom_utf8`; original database/config retained. Tests now use separate `inkloom_test_utf8`. Unicode/DOCX regression passed.

P1 visual model checks, scoped assistant and governance insights have not been implemented yet. The core live gate and final regression/review remain open. Earlier foundation-only descriptions below are historical checkpoints. See `docs/BUILD_LEDGER.md` for decisions and precise incremental outcomes.

Started: 2026-10-23 (Asia/Calcutta).

## 2026-10-24 AI workflow planning update

At the user's request, researched official Frontify/Adobe review patterns, OpenRouter routing/privacy/free limits and a self-hosted Word-style editor. New planning documents:

- `docs/superpowers/specs/2026-10-24-ai-review-workflow-design.md`
- `docs/superpowers/plans/2026-10-24-ai-review-workflow.md`
- `docs/AI_WORKFLOW_TEST_PLAN.md`

Confirmed: OpenRouter free models only, real company materials, full Word-style browser editing, compatible open-source licensing and a clean UI. Submission is tonight with a few hours available; exact cutoff is unspecified. The design enforces private local files, minimum/redacted outbound content and policy-compatible routes; no guaranteed confidentiality is inferred from a free model. New application functionality and new executable tests are not implemented by this documentation update, and no new test or AI accuracy result is claimed. Historical foundation results below remain historical.

## Authorisation and scope

The user confirmed: "implementation is permitted i am second round so do it" on 2026-10-23. This is the build-window confirmation for this session. Event name and exact official dates were not supplied; they are not invented here.

All created/modified files, downloads, virtual environments, caches, portable database data and test artifacts must remain under this project directory.

Initially present: AGENTS.md and INKLOOM_CODEX_IMPLEMENTATION_PLAN.md only. No app, dependencies, README or tests existed. Git discovery resolves to a parent outside this project; do not stage or change that parent repository.

## Phase mapping

The user's Phase 1 is the foundation checkpoint. The source-of-truth plan also requires a Phase 0 streaming spike and approved guideline versions in its Phase 1. This checkpoint includes those prerequisites; it does not start the full review editor, compliance engine, rewrites or human content approval work. Stop for user approval after the checkpoint.

- [x] Read both instruction files completely; inventory existing work.
- [x] Build permission confirmed by user.
- [x] Anthropic Frontend Design source verified; installed project-locally under .agents/skills/frontend-design.
- [x] Next.js + FastAPI + local PostgreSQL foundation.
- [x] Email/password accounts, sessions, organisations, invitations, roles, audit trail. Email verification was removed at the user's request for this prototype (see the update below).
- [x] Backend and PostgreSQL row security isolation.
- [x] PDF/DOCX extraction, owner-reviewed rules, immutable activated versions.
- [x] Authenticated LangGraph/AG-UI diagnostic stream, cancellation and disconnect handling.
- [x] Backend/security tests, browser flow, mobile checks, build/type checks.
- [x] Setup instructions and actual results recorded.

Later phases: review workspace, brand retrieval, real model adapter, runtime evaluations, 50 labelled offline cases, rewrites, draft approvals/history, other input modes, final reliability tests. All remain unimplemented until their respective checkpoints.

## Open decisions

Real AI provider/model, budget, external data processing disclosure and hosting are unresolved. This checkpoint sends no content to any model. The diagnostic stream is explicitly not an AI review. Prototype accounts sign in directly with email/password; production email verification and deployment configuration are future setup requirements.

## Commands and results

On 2026-10-23:

| Command                                                                   | Actual outcome                                                                                               |
| ------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| `npm.cmd install`                                                         | Installed local Node dependencies; audit reported 0 vulnerabilities at installation                          |
| `.venv/Scripts/python.exe -m pip install -r services/api/requirements.in` | Installed Python dependencies; full versions saved in `requirements.txt`                                     |
| `npm.cmd run test:api`                                                    | **32 passed**, 0 failures/errors/skips, **83.50 seconds**, using separate `inkloom_test` PostgreSQL database |
| `npm.cmd run test:e2e`                                                    | **17 checks passed**; **5** selected WCAG A/AA automated scans with **0 reported violations**                |
| `npm.cmd run typecheck`                                                   | Passed                                                                                                       |
| `.venv/Scripts/ruff.exe check services/api`                               | Passed                                                                                                       |
| `npm.cmd run build`                                                       | Passed, including the final build after streaming proxy correction                                           |

Browser cases include full registration/verification/onboarding, manual rule approval, v1/v2 activation and history, team invitation, creator permission denial, real streaming, cancellation, refresh recovery, 390px navigation/layout, logout and protected routes. No browser JavaScript runtime errors occurred in the passing run. Screenshots were visually inspected on desktop and mobile.

Backend cases include both PDF and DOCX extraction, parser timeout, no-text PDF failure, MIME/malformed/oversized files, chunked-body limits, citation scope/excerpt/location checks, verified identity, token expiry/reuse, role changes/disabled memberships, direct SQL RLS and audit immutability.

No real model evaluation was run. No AI accuracy, compliance, citation-support accuracy or rewrite-quality percentage is claimed. The historical guideline data is preserved; review-version pinning and content approval safety require the later review/approval implementation.

## Files contributed

- `apps/web/`: navigation, account/onboarding screens, overview, owner-reviewed brand knowledge, version history, member management, activity, connection diagnostic, responsive styles.
- `services/api/`: account/org/guideline/diagnostic APIs, validated inputs, restricted database access, baseline SQL/RLS, bounded parser worker and 32 foundation tests.
- `packages/contracts/index.ts`: shared TypeScript response view models; Python/Pydantic remains the server validation source.
- `scripts/`: portable database and application launchers, local setup, isolated backend test runner and Playwright/axe workflow.
- `README.md`, `.env.example`, `.gitignore`, `.npmrc`, lockfiles and this documentation: setup, decisions and actual limitations.

## Folder-boundary correction

During the first portable database initialization, its dependency used an OS temporary setup file and removed it during cleanup. This transient exception was disclosed to the user. The database launcher and web/API/test launchers now explicitly redirect temporary files to `.cache/tmp`. Application data, installed dependencies, browser binaries, mail, screenshots and reports remain under this folder.

## Checkpoint

Foundation complete; awaiting user approval before Phase 2. Next is the full UI workflow from the user's phase list. The implementation plan's later review/evaluation gates remain mandatory. No later-phase notice in the UI represents an implemented feature.

## Follow-up: direct prototype sign-in

At the user's request, removed the email verification code screen, API endpoint, outbox writer and helper script. Registration returns to sign-in, and both new accounts and previously unverified accounts can sign in with email/password. Duplicate registration reports that an account already exists. Team invitation codes remain separate from sign-in. Email ownership is not verified in this prototype; see `docs/DECISIONS.md` for the explicit departure from the original plan.

Fresh checks after this change: `npm.cmd run test:api` **34 passed in 48.99 seconds**; `npm.cmd run typecheck` passed; `.venv/Scripts/ruff.exe check services/api` passed; `npm.cmd run test:e2e` **17 checks passed**, including direct registration/sign-in with no verification field, five accessibility scans with no reported violations, team permissions, logout, streaming and mobile layouts. The first browser attempt encountered connection refused during the service restart; the full combined launcher was restarted and the subsequent complete browser run passed. The current app is running at `http://127.0.0.1:3000`. The historical checkpoint results above describe the earlier verification-code implementation.




## 24 October 2026 — user-requested fictional sample guidelines

Created samples/northstar-brand-guidelines.md, northstar-rules.json, review-with-issues.txt and review-clean.txt. Added 13 matching unapproved sample rules through the signed-in owner UI to the existing empty Version 1 draft of organisation newcomp. Includes typed INR 799/150ml price metadata, product name, claim limits, tone, three prohibited phrases, disclaimer, Instagram and manual accessibility/visual guidance. Kept owner review/activation pending. No AI calls, company data, application code changes or new test results in this sample-data task. Visible confirmation: .local/test-results/sample-guidelines.png.
