# BrandGate

**Brand Content Review** is a pre-publication brand governance prototype: approved company sources → saved content → explainable findings → explicit corrections → fresh check → separate reviewer decision.

**Live prototype:** [buildgate.velox0.com](https://buildgate.velox0.com), deployed
25 October 2026 on a dedicated AWS host through Cloudflare. Public account/source/
draft and isolation smoke checks passed. Live AI currently needs a server-side
OpenRouter key; no real AI completion is claimed. See `docs/IMPLEMENTATION_STATUS.md`
and `deploy/ec2/README.md` for the deployment, cost estimate and prototype limits.
Current source: [download source ZIP](https://buildgate.velox0.com/source/buildgate-source.zip?release=aws-20261025).

## Quick start (Windows)

Requires Node.js 22+, Python 3.12 (available through `py -3.12`), npm and Git. The launcher supplies a project-local PostgreSQL database. The PowerShell setup and optional OCR target Windows; macOS setup and fresh test results are documented below and in `docs/TEST_REPORT.md`.

From a fresh checkout:

```powershell
git clone https://github.com/Krishtyagi1/BrandGate.git
cd BrandGate
powershell -ExecutionPolicy Bypass -File .\scripts\setup.ps1
Copy-Item .env.example .env
```

Edit the local `.env` and set `OPENROUTER_API_KEY`. Keep the key out of Git and chat. Then start the app:

```powershell
npm.cmd run dev
```

Open [Brand Content Review](http://127.0.0.1:3000/login). Web: `3000`; API: `8000`; local PostgreSQL: `54329`. Do not start duplicate launchers on occupied ports. Setup, caches, generated database credentials, company uploads and reports stay inside the project and are Git-ignored. The API reads the OpenRouter key server-side. Free routes must satisfy zero pricing, zero data retention (ZDR), denied data collection and structured output; incompatible/unavailable routes fail visibly. No paid fallback.

The repository contains source code and fictional examples, not the developer's installed dependencies, accounts, database, company materials or API keys. See [progress.txt](progress.txt) for the handoff, known gaps and remaining submission work.

## Local setup on macOS

With Node.js 22+ and [uv](https://docs.astral.sh/uv/) installed:

```sh
npm ci
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r services/api/requirements.txt
PLAYWRIGHT_BROWSERS_PATH="$PWD/.cache/playwright" npx playwright install chromium
npm run dev
```

The launcher starts PostgreSQL, the API and web app at the same loopback ports
listed above. Configure an ignored root `.env` for live AI; local accounts and
source setup work without a provider key. Automated backend and browser tests
use synthetic provider configuration and do not require your live key. Run
`npm run test:api`, `npm run test:e2e:simple` and `npm run test:e2e:ai`
sequentially because they share the isolated test database and browser-test ports.
Windows OCR is unavailable on macOS; image text needs a verified transcript.

## Project structure

| Path | Purpose |
|---|---|
| `apps/web` | Next.js interface, local Word-style editor and API proxy |
| `services/api` | FastAPI, PostgreSQL migrations, ingestion, AI providers and backend tests |
| `packages/contracts` | Shared frontend response contracts |
| `scripts` | Setup, launchers, browser checks and evaluation tools |
| `samples`, `evals` | Fictional examples and developer-labelled synthetic cases |
| `docs` | Architecture, design plans, test results, licences and demo guide |

## Try the workflow

1. Register and sign in with email/password. No verification code is required. Create an organisation.
2. In **Rules**, choose checks, upload PDF/DOCX and separate reference images, and inspect highlighted literal evidence. Edit proposed fields or add company guidance. Select proposals and explicitly confirm; overlapping replacements need separate acknowledgement. Updates stay in the same visible version, while immutable internal snapshots preserve old reviews. **New version** starts empty.
3. In **Team & settings**, inspect and enable the external AI processing policy. Invite another account as reviewer; that account accepts the invitation using its matching email. Prototype accounts do not verify email ownership.
4. Choose **New review**. Select Email, Social media (including LinkedIn/Instagram/X), Ads & visuals, Website, Documents or Other; select checks and describe the task. Paste text or upload DOCX, selectable-text PDF, PNG or JPEG (maximum 5 MB, 30,000 review characters). DOCX opens in the browser Word-style editor. Image text checks require a verified transcript; visual-only checks do not.
5. Save, choose **Check content**, inspect the redacted outbound payload, then explicitly send it. Findings distinguish exact mismatches, advisory interpretation and unverified claims, with approved references where available.
6. Request corrections, compare the two choices, and explicitly apply. Unsafe/ambiguous output is withheld. Save and recheck every changed revision.
7. Select a different reviewer and send for review. **Tracking** collects saved work and assigned approvals. The reviewer opens the exact saved version, inspects exclusions, and approves, requests changes or rejects. Nothing is auto-published.

Use **Help → Try the fictional example** for an isolated Northstar Botanics example. It supplies sources and deliberately incorrect content, with no precomputed AI results or automatic rule confirmation. The three primary tabs use a white minimal interface; settings remain secondary.

## What is implemented

- Accounts, organisations, roles, invitations, private sources, human-confirmed evolving guideline collections with immutable internal snapshots, and audit history.
- Saved text/DOCX/PDF/image content, immutable revision history, restore, comments, content library and approval queue.
- Local Word-style DOCX editing/export; exact saved artifact hashes; stale-save and concurrent editor safeguards.
- Approved-source retrieval, deterministic terms/disclaimer/typed-price checks, bounded LangGraph AI review, validated references and persisted AG-UI progress.
- OpenRouter free-only inference, outbound minimisation/redaction/preview, owner consent, quota reserve, bounded schema repair and safe failure.
- Two-option rewrite jobs, code guards plus a separate model check, explicit apply/recheck, backend role/revision/hash-bound approval.

## Checks

With project-local PostgreSQL running:

```powershell
npm.cmd run test:api
npm.cmd run typecheck
npm.cmd run build
.venv/Scripts/python.exe -m ruff check services/api
npm.cmd run test:e2e:ai
npm.cmd run test:e2e:simple
npm.cmd run test:editor
npm.cmd run eval:ai -- --mode offline
```

Backend tests use `inkloom_test_utf8`, separate from application data. The isolated AI browser test starts ports 3001/8001 and uses an explicitly labelled synthetic provider double. The editor probe uses the running app and fictional files. Tests never send company materials. Browser installation instructions are in `docs/DEMO_RUNBOOK.md`. Reports stay private under `.local/test-results`.

**Recorded verification:** 129 backend tests; 17 simplified-workflow browser checks; 17 collaboration/concurrency browser checks; four Word-editor checks and nine representative DOCX fidelity assertions passed at the latest implementation checkpoint. TypeScript, production build and Ruff passed. These are recorded local results, not fresh-install or deployed CI results. See the [test report](docs/TEST_REPORT.md) for exact commands, dates and limitations.

**Live AI limits:** Real synthetic OpenRouter text review previously succeeded with reported cost 0. The latest source-intake probe hit 429; vision found no endpoint satisfying free pricing, ZDR and schema requirements. Complete live AI reliability remains unproven. Synthetic provider tests establish workflow mechanics only. During a provider outage, select Products & prices, Language & terminology and Required wording for local exact checks; local palette evaluation is also available. Contextual tone/claim analysis and generated corrections still need an available AI route.

## Architecture and confidentiality

Next.js proxies same-origin requests to FastAPI. PostgreSQL enforces tenant isolation with a restricted runtime role and forced RLS; migrations use separate owner credentials. Backend records, permissions and hashes authorise changes. Agent events only present progress. No database transaction is held across inference.

Original files, redaction mappings, passwords and keys stay local. Previewed text and approved excerpts go to OpenRouter after deliberate dispatch. Visual requests also send the displayed original candidate and reference images: pixels are unredacted. Redaction cannot identify every business secret; routing settings are not a contractual confidentiality guarantee. OS account access, Windows/OneDrive sync, disk encryption and backups remain deployment concerns. No production identity verification, hosted encrypted storage, malware scanning or distributed job queue is claimed.

DOCX fidelity was checked on a representative fixture, not every Word feature. Unsupported text-bearing parts and unresolved tracked changes block submission. PDF image/missing-text pages are incomplete; PDF layout editing is not provided. Static image evaluation includes a local dominant-palette comparison and optional advisory free vision when an eligible route exists. Exact font identity and exhaustive accessibility certification are unsupported. Images are never corrected; videos are unsupported. Local OCR depends on Windows language support.

Source intake supports ten uploaded sources per collection, 5 MB/file, 100 PDF pages and 200,000 extracted characters/file. Up to twenty embedded images/source are extracted with provenance; static vision is bounded to four confirmed references. AI intake resumes four text chunks/run. Text review sends up to 24 selected sources and explicitly leaves omitted contextual guidance incomplete. Missing guidance is visible across the integrated collection; supported checks continue. A local extractive finding assistant and owner/reviewer recurrence insights are implemented; see `docs/ROUND3_GUIDE.md` for their bounded scope and the current vision fallback. The 50-case synthetic dataset exists; the earlier offline run passed 23 cases and left 27 contextual cases unrun. No overall AI-accuracy or user-study claim.

## Source, licences and submission

Application-authored source is offered under AGPLv3; third-party components retain their own terms. SuperDoc 2.26.0 is AGPLv3; its separate DOCX Engine 0.25.0 is proprietary. Notices and the engine licence are retained under `docs/licenses`; the dependency must not be described as wholly open source. See [external components](EXTERNAL_COMPONENTS.md), [architecture](docs/ARCHITECTURE.md), [demo runbook](docs/DEMO_RUNBOOK.md) and [implementation status](docs/IMPLEMENTATION_STATUS.md).

Source repository: [Krishtyagi1/BrandGate](https://github.com/Krishtyagi1/BrandGate). `.env*` (except `.env.example`), `.local`, `.cache`, dependencies, private data and generated test/build files are ignored. Source publication does not include a hosted app or the local database. Run `.venv/Scripts/python.exe scripts/package-source.py` for a curated source ZIP under `.local/releases`. A localhost preview is not a remote judge-accessible deployment. Required contribution details and actual feedback must be supplied truthfully before submission; no history or research evidence is fabricated.

## Production GitHub Actions

Production deployment runs from the `prod` branch after CI, using repository
Actions secrets and exact-branch AWS OIDC. No GitHub environment is required.
See [production setup](docs/GITHUB_ACTIONS_PRODUCTION.md). The ignored local
`.env.deploy` holds matching settings; runtime credentials stay on the host.
