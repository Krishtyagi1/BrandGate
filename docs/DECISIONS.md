## 28 October 2026 — production branch correction

Latest user steering supersedes prior nonprod/main instructions: deploy from
`prod`, no GitHub environment, repository Actions secrets, consolidate/amend the
two setup commits and restore main with force-with-lease if branch rules allow.
Use native GitHub ARM runner, exact prod-branch OIDC trust and production target
tag on the same low-traffic server. No extra instance or increased hosting spec.
User will report Actions outcomes; stop all monitoring and do not claim hosted
production deployment succeeded without their report.

## 28 October 2026 — repository secrets instead of environments

User explicitly requested no GitHub environment, repository Actions secrets and
API setup when possible. Use main-only manual workflow and exact immutable
repository/branch OIDC trust. Runtime target remains nonprod, checked in code and
IAM. No admin requirement is worked around by broadening trust or adding static
credentials. Earlier environment-specific plan entries below are superseded.

## 28 October 2026 — manual nonprod CI deployment

User requested GitHub Actions, local `.env.deploy`, user-managed environment
setup and nonproduction deployment. After the low-traffic resize, their “do it”
is implemented as preparation for the existing demo host, with no extra staging
host/cost. Deployment is manual from main after CI, using environment `nonprod`
and repository/environment-bound OIDC. Runtime secrets stay on the host. Local
configuration is never sourced as shell or bundled. No production workflow or
long-lived AWS access key is created. User applies the documented role/tag/
environment setup; remote execution is pending. Container rollback preserves
records but cannot reverse migrations, so only expand-compatible migrations are
eligible. Public-only DNS/proxy failures fail the job without automatically
rolling back a healthy app.

## 28 October 2026 — smallest practical low-traffic host

User requested reduced system specifications. Selected `t4g.micro` (1 GiB),
retained 2 GiB swap, standard CPU credits, existing encrypted disk/IP and moved
container memory caps to 512/256/64 MiB. Nano's 512 MiB leaves insufficient
headroom for the measured stack. Builds belong off-host in future CI. Keep one
host, no autoscaling/paid commitments, and require another sizing check before
meaningful concurrent use. Database backup/retained-record and public write/file
smokes passed after resize. Earlier 2 GiB deployment entries below are historical.

## 25 October 2026 — user-selected North Mini Code

The user selected `cohere/north-mini-code:free` and explicitly approved running
it without a zero-data-retention guarantee, retaining the no-training filter,
disclosing possible provider retention and requiring fresh owner consent.
Only this exact model with `OPENROUTER_ALLOW_PROVIDER_RETENTION=true` drops ZDR.
Other routes retain the existing ZDR requirement; zero prices and no fallback
remain enforced. No paid-model adapter or credit purchase was needed for the
successful synthetic probes. Earlier paid-model design remains unimplemented.

North Mini advertises tools/tool_choice but no response_format. It receives one
`emit_result` function schema. The app never executes tools: exactly one matching
call with JSON arguments must pass the existing Pydantic validation, otherwise
the run fails after at most one schema repair. Reasoning is excluded and never
returned as review output. Text only; no North Mini vision capability is claimed.

## 25 October 2026 — real model budget and credentials

The user authorised installing the OpenRouter key server-side, then approved up
to USD 1 for a working model and elected to add the minimum USD 5 prepaid balance
personally in Safari. The prepaid purchase is separate from the inference cap.
Keep privacy routing and owner processing consent. Current free-only model code
is unchanged while payment/access is pending. An optional capped paid text-model
design is documented; it is not yet implemented or deployed.

## 25 October 2026 — deployment preparation and hosting budget

Latest user instruction replaces the GCP target with AWS EC2 and Cloudflare at
`buildgate.velox0.com`. Use a dedicated Mumbai `t4g.small`; leave existing
`main` untouched. The user approved deployment within a USD 20/month hosting
budget on 25 October, replacing the earlier credits-only restriction for this
AWS deployment. AWS credits remain unverified. Host data stays on encrypted EBS;
no inbound SSH or public DB.
Use IMDSv2 with hop limit 1: only host SSM/artifact retrieval needs AWS metadata;
the application containers require no AWS identity. Standard CPU credits avoid
surplus credit billing. No reserved instances, savings commitment or paid tier
upgrade. Source-only current code can be served for the AGPL source offer.

The user requests a public deployment and restricts hosting to free/trial credits,
with no paid upgrade. They asked for Railway, then reported their trial exhausted,
then asked to use GCP credits and are switching to a credited Google account.
Do not provision against an unverified billing account or claim a live link before
public checks pass. No Railway/Render/GCP resources have been provisioned.

The tested Docker package retains one Next.js public listener and a loopback API,
with a separate restricted database runtime role, private persistent uploads where
the host supports them, secure cookies and exact HTTPS origin checks. No production
authentication or full security-audit claim is added. Existing source remains in
this checkout; no fork, commit or push was made while platform access was changing.

## 25 October 2026 — portable, credential-independent verification

Continue the existing approved P0 plan in this checkout. Use platform-specific
virtual-environment paths in browser launchers, consistent with the app launchers.
Automated tests supply explicitly synthetic provider settings and block the default
provider HTTP client; provider contract tests opt into mock transports. The local
app retains its real key/consent gates. No test key is written into `.env`, no live
AI result is fabricated and no P1 expansion is claimed. The previously recorded
build-window authorization remains the basis for this maintenance work.

## 24 October 2026 — simplified source workflow (latest)

- User explicitly authorised committing/pushing source to Krishtyagi1/BrandGate.
  Preserve its initial README commit; publish only reviewed source, fictional
  samples and documentation. Keys, company data, database, local reports and
  generated dependencies/assets remain ignored. Use the existing local Git
  identity; do not invent development history or contributions. README/progress
  report previous verified results and live-provider failures without claiming
  a new test run or a hosted deployment.

- The user requested and authorised this simpler implementation after answering workflow questions. All writes stay in the current project. Build-window permission and AGPL-compatible licensing were already recorded.
- White interface, three primary tabs: Rules, New review, Tracking. Rules shows every setup section on one page; team/privacy settings are secondary. Product name: Brand Content Review.
- A visible version is an evolving collection. Confirmed additions/replacements append immutable internal snapshots; overlapping replacement needs explicit acknowledgement. Previous review evidence stays frozen. Explicit New version starts empty. This supersedes the earlier visible-version UX.
- Integrate sources across files. Missing guidance stays Source missing while supported checks continue. Zero supported checks never produces completion. Source-backed typed prices must match literal entity, amount, currency, unit and dates; manual guidance discloses its human provenance.
- Task and company-wide instructions are redacted review intent, never factual authority. Changing scope, content or confirmed sources requires a fresh review; backend permissions authorise decisions.
- The user's static-image request reprioritises this portion of P1 while the earlier live P0 gate remains open. Local dominant-palette evaluation and optional capability-checked free vision are implemented; do not claim the blocked live route succeeded. No image correction or video support. Assistant/recurrence analytics remain unimplemented.
- Contextual review sends 24 selected sources; omitted contextual guidance leaves that category incomplete. Exact code checks see all applicable rules. Vision supports four confirmed references and explicitly reports excess or invalid references.
- Tutorial creates an isolated fictional workspace with unconfirmed source proposals and deliberately incorrect text/ad. No precomputed AI result, processing consent or human approval is seeded.
- Latest real synthetic probes: intake blocked by 429; vision blocked by no free/ZDR/schema-compatible endpoint. No privacy downgrade or paid fallback.

## Earlier 24 October 2026 implementation decisions

- Extend the existing local foundation in place. The user already authorised implementation/build timing and AGPL-compatible licensing; no new permission gate. All writes stay inside the project; no outside worktree or parent Git changes.
- Use immutable content revisions and exact artifact hashes. The displayed editor base remains bound to its saved version. Concurrent dirty buffers cannot silently rebase; clean buffers load the new content and clear inspection acknowledgement. New reviews supersede pending approval requests, including when the new provider call later fails.
- Use a conservative extraction gate: unsupported DOCX text in drawings/extra parts and PDF pages with images/missing text are incomplete, even if some text was extracted. The prototype does not pretend to inspect omitted words. Verified image transcripts support text review; image pixels/layout remain manual.
- Exact price checks require bounded product/unit/currency mentions, effective dates and a single clear amount. Substring products and foreign-dollar symbols do not produce confirmed violations. Contextual claim/tone checks remain advisory/unverified; no invented factual certainty or score.
- OpenRouter free-only routing enforces zero price, ZDR, no collection, no fallback and schema support. One bounded schema repair, a ten-attempt per-process cap and ten-request reserve apply. Intermittent provider failures are genuine incomplete runs; no paid or weaker-privacy fallback. Real company materials were not used for validation.
- Keep the original WIN1252 database/config; copy and verify into UTF-8. Test database is separate. No destructive reset.
- Retain SuperDoc's AGPL notice and the separately proprietary DOCX Engine licence. The app's AGPL licence does not relicense dependencies. Preserve local worker assets and disable editor telemetry/proofing.
- The core live gate remains open after final 429 failures; P1 is held rather than claiming missing improvements. Offline fixtures prove integration/safety, not live model accuracy or human feedback. Documentation records actual evidence and remaining work.

# Decisions

## 2026-10-24 confirmed planning requirements

The user selected OpenRouter free models only, real company materials, full Word-style browser DOCX editing and compatible open-source application licensing. They prioritised a very clean interface with retained context and a submission tonight. The proposed design uses a self-hosted SuperDoc browser editor, approved-source hybrid review, strict zero-cost/policy-compatible OpenRouter routing and local outbound minimisation/redaction. Editor fidelity and eligible model availability are execution gates, not measured results or accepted confidentiality guarantees. The detailed design/implementation/test documents are under `docs/superpowers/` and `docs/AI_WORKFLOW_TEST_PLAN.md`. No application code was changed in this planning update.

## Prototype sign-in simplification (user requested)

The user requested removing the sign-in code step for the prototype. Accounts now register and sign in directly with email and password, including accounts created before this change. Removed the verification screen, verification endpoint, outbox writer and outbox-reading helper. This overrides the original plan's verified-email requirement for this prototype only. Invitation codes still restrict joining to the matching account email, but email ownership is not established. Password hashing, session expiry, CSRF protection and organisation roles still apply. Legacy database verification fields/tables and existing outbox files are retained as unused historical data; they do not gate sign-in and no new verification codes are generated.

## 2026-10-23: Foundation checkpoint and phase numbering

Follow the architecture and gates in the implementation plan, while stopping at the user's Phase 1 approval boundary. Include repository phases 0 and 1 as foundation prerequisites. No compliance results or AI approval are implemented in this checkpoint.

## Local development dependencies

Use Next.js/React/TypeScript, FastAPI/Pydantic, PostgreSQL and LangGraph. Use official AG-UI Python event models/encoder and the official TypeScript client directly; a CopilotKit runtime is unnecessary for this diagnostic panel. Reassess only if later interaction requirements benefit from it. Pin installed versions and retain lockfiles.

No PostgreSQL server or Docker was found. Use embedded-postgres as a project-local launcher for real PostgreSQL, with independent migration-owner and restricted runtime credentials. Its npm wrapper has a beta version; it is local development infrastructure, not a managed hosting promise. Do not substitute SQLite for PostgreSQL or disable RLS to make tests pass.

Use opaque expiring HttpOnly sessions, Argon2 password hashes, email verification, one-time hashed invitation tokens, server role checks, request-origin/CSRF controls and PostgreSQL RLS. Local email verification messages are private files in .local/mail; this is a development delivery adapter, not real email or production identity verification.

## Local skill installation

Verified https://github.com/anthropics/skills/tree/main/skills/frontend-design and installed via the Codex skill-installer helper with an explicit .agents/skills destination and a project-local temporary directory. This avoids the global writes of a default install. Read its full SKILL.md before frontend work; available to subsequent turns as a project-local skill.

## Frontend design plan

Audience: creators and brand owners preparing evidence for human review. Visual direction: an orderly brand operations workspace with a small woven ink mark, a restrained navigation rail, generous editorial headings and compact evidence tables.

Tokens: paper #F6F8FC, surface #FFFFFF, ink #162841, indigo #4546B8, teal #167569, line #E0E6EF. Typography: locally installed Segoe UI/Calibri for controls, Georgia only for the short onboarding headline; no font CDN. Left-aligned content, a stable 236px sidebar, a broad work surface, stacked forms on mobile. Use one accent for actions and explicit text badges for status.

Design critique: avoid a marketing hero and repeated statistic cards, because foundation users need to set up trusted rules. Lead with a practical setup checklist, one prominent action and real persisted version/member data. Limit the rail to five destinations plus account settings. Later pages show an honest phase notice rather than mock findings.

```text
Brand rail | Organisation / role                           Account
           | Page title                         Primary action
           | Setup checklist or guideline table | Context / evidence
```

## Official references checked

- AG-UI event semantics: https://docs.ag-ui.com/concepts/events
- Python event models: https://docs.ag-ui.com/sdk/python/core/events
- LangGraph persistence/interrupt boundary: https://docs.langchain.com/oss/python/langgraph/interrupts
- CopilotKit integration comparison: https://docs.copilotkit.ai/langgraph-python
- PostgreSQL RLS (including superuser bypass): https://www.postgresql.org/docs/current/ddl-rowsecurity.html
- Portable PostgreSQL API: https://github.com/leinelissen/embedded-postgres

## Verified refinements

Disable Next.js response compression for the local server: measured proxy buffering otherwise prevented incremental SSE progress and made cancellation unavailable before completion. Keep no-transform cache headers on API responses. Use official SDK types and safe state snapshots, with business writes outside the stream.

Use a separate `inkloom_test` database for backend tests, in the same project-local PostgreSQL cluster. Browser fixtures use uniquely named synthetic accounts in the running local app. Account email verification remains explicitly local development delivery; real production identity verification is unresolved.

Portable database initialization initially wrote a transient OS temp setup file, then deleted it; corrected launchers explicitly set TEMP/TMP/TMPDIR to `.cache/tmp`. This was disclosed to the user and is recorded as an exception to the requested folder boundary.
# 2026-10-24 approved AI build decisions

- Continue in the current project folder; no parent repository staging, global install or outside worktree. User restriction takes precedence over worktree helper guidance.
- Use SuperDoc 2.26.0. The editor is AGPLv3; its current DOCX Engine dependency has separate proprietary terms permitting the present evaluation/development use. Disclose both components; do not describe the engine as open source or production licensing as resolved.
- Server extraction and artifact hashes own saved revisions. DOCX stays OOXML, PDF is selectable-text review with original download, and image OCR requires explicit transcript verification. Transcript editing does not change image pixels. Machine visual certification is not claimed.
- Keep OpenRouter requests free-only, no-collection, ZDR, strict schema and no paid fallback. Phala/Xing4.0 produced a real zero-cost response but shared upstream limits are intermittent. Failed/incomplete work cannot become an approval-ready check. One bounded schema repair is allowed; no policy downgrade occurs.
- Keep contextual AI findings advisory/unverified. Resolvable evidence is not proof of substantive factual support. Exact comparisons use owner-approved typed facts; high-risk promotional wording can be flagged as unverified evidence requests.
- Retain the original WIN1252 database and switch to a verified UTF-8 copy rather than deleting existing user data. New setup/test databases explicitly use UTF-8.
- Account IDs enforce separate reviewer controls. Two automated accounts validate mechanics and are not independent human feedback or proof of two different people.
- Supersede pending requests after content edits, guideline activation or reviewer-role revocation. Historical decisions remain unchanged.
- Pin PDF.js 5.4.296 within the supported major version to avoid the reported vulnerable newer range. Four transitive AG-UI/Zod advisory entries remain; bounded server-generated stream data reduces exposure but does not remove the dependency advisory. Record the final audit rather than claim a clean audit.


