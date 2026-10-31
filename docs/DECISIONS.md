## 31 October 2026 — public editable demo entry

The user requested a login-page button using credentials loaded from AWS and chose
editable documents plus AI checks/chat. Team management and rule activation stay
blocked. Reuse the prepared fictional Northstar account, but issue org-bound
creator-capability demo sessions rather than unrestricted owner sessions. Also
block consent changes, joining/creating organisations and human approvals. Shared
edits and chat are disclosed; only fictional sample data is appropriate.

Use SSM SecureString `/buildgate/production/demo-login` in ap-south-1, read by the
host's existing instance role with one exact parameter ARN. The startup/rollout
loader writes a private mode-0600 file atomically into the existing app volume;
the browser receives only a session cookie. No SDK/cloud credentials are added to
the app image. A retrieval failure removes the cached credential and disables
demo sign in while normal startup/deployment continues. Secrets refresh at
startup/deployment, not on every click.

Demo tokens have their own database registry and one-hour expiry, so older app
rollbacks cannot mistake them for normal owner sessions. Existing demo sessions
are not revoked merely by removing the AWS parameter. Normal authentication and
existing consent/approval/isolation checks remain in force.

Testing also exposed a pre-existing chat reliability issue: numeric portions of
server-generated UUID references could be redacted and then fail validation.
Exclude protocol identity fields from text redaction while still redacting
document text, questions and excerpts; a deterministic regression covers both.

## 31 October 2026 — release the verified UI refresh

The user's explicit “deploy” authorises committing/pushing the local UI refresh
to main/prod and deploying it to the existing host and both configured domains.
Use a signed commit and the existing checked Actions/SSM backup/rollback path.
This supersedes the prior local-only restriction for this refresh. No hosting
upgrade, provider/privacy change or new infrastructure is required.

Actions remained queued during release. Use the already established manual path
with a native ARM64 image of the exact clean signed commit, the same private
artifact checks and existing backup/rollback controls. The release passed public
browser verification on both domains. Keep the pending Actions run intact; it
contains the same application changes. The final docs-only verification commit
skips CI to avoid a redundant new application rollout.

## 31 October 2026 — compact local UI and transparent theme-aware art

The user asked for a less blocky/spaced UI, local-first execution and twisting
glowing red/blue glitter backgrounds. Their follow-up approved blurry transparent
backgrounds for both themes. Apply a compact shared layout with light/dark themes
and reusable alpha overlays rather than opaque dark artwork on every section.
Keep the three-tab workflow and all review/approval controls. Theme state is a
local browser preference, never organisation policy or workflow authority.

Generate/edit artwork only through the built-in image tool; keep original
variants and prompt provenance. Use static display blur and theme-specific
opacity, responsive local images and quiet reading surfaces. No people/photos,
remote font or new UI dependency. Keep DOCX paper light so the document's own
colours remain meaningful. The user has authorised local implementation/testing,
not committing, pushing or deploying this visual refresh.

## 30 October 2026 — additional BrandGate hostname

The user configured Cloudflare for `brandgate.velox0.com` and requested it alongside the existing hostname. Serve both hostnames directly from the same proxy/app/database. Keep the existing primary origin and deployment health target; add an exact HTTPS-only `WEB_ADDITIONAL_ORIGINS` allowlist for browser writes. Do not use wildcard origins, rewrite the browser's Origin header or weaken TLS. Host-only secure sessions stay separate across names. Add the hostname to fresh-host configuration and the existing host's private runtime, then deploy the backend support and gracefully reload the validated proxy. The user’s release authorisation covers the necessary signed main/prod update for this hostname change.

GitHub reported an Actions/Webhooks incident while this release was queued. Use the repository's existing manual deployment path with a locally built native ARM image of the clean signed commit, the same checked private release prefix/target and unchanged backup/rollback controls. No production-host build, extra server, policy downgrade or new credentials. A temporary new-host 302 preserved usability during deployment, followed by direct service after backend verification. Both-domain synthetic account/save/isolation checks passed. The final docs-only verification commit skips Actions to avoid another redundant app rollout; the pending original application workflow remains intact.

## 30 October 2026 — explicit production health-check identity

Diagnosing the user-supplied public-HTTPS failure reproduced HTTP 403 for Python's default user agent and 200 for a named deployment checker. Use a descriptive `BuildGate-DeployHealth/1.0` user agent, preserve exact health validation and bounded retries, and report the last status/error type. Do not weaken Cloudflare settings, assume every HTTPS failure is transient or automatically roll back an internally healthy app. No release/push was performed while diagnosing this failure.

## 30 October 2026 — document explanation chat and review overview

The user selected whole-document chat with cited follow-ups, added an overall findings dashboard, then approved both designs with “do both”. Implement in this checkout using the existing backend/provider/AG-UI controls. No new service or dependency. Preserve the three primary tabs: the dashboard appears above Tracking's existing saved-work list, with its own explicit filters and current counts; historical recurrence keeps its separate denominator. Creator visibility remains personal and owner/reviewer visibility remains organisation-scoped.

Add explicit outbound chat previews rather than silently sending questions/excerpts. Persist private per-user, exact-review request/answer history with immutable retry claims. Resolve citation IDs against approved snapshot evidence; keep unsupported evidence uncertain. The model is advisory and cannot authorise changes. Preserve the selected provider's existing free/pricing/privacy constraints, including the previously authorised North retention policy. No automatic commit, push or deployment is included in this feature request.

Execution stayed in this project according to the existing build ledger; no outside worktree. A fresh read-only reviewer checked the implementation. All six material findings received regression fixes. Synthetic browser doubles are distinguished from the successful real synthetic provider/end-to-end checks. Semantic answer quality beyond those narrow probes remains unmeasured; do not claim a general chatbot accuracy result.

## 30 October 2026 — endpoint preflight and separate local evaluation

Keep existing free-only, no-training and ZDR vision policy. Do not weaken it to make inference work. Add public metadata preflight before sending images: intersect exact model/provider/tag identities with the published ZDR list and validate endpoint prices/schema parameters. Unknown metadata fails closed. This can reject a technically working route when published metadata is incomplete; that conservative availability trade-off is intentional. Runtime request policy still enforces the same requirements and does not trust the preflight alone.

Expose a manual metadata-only Settings check, not recurring monitoring. Limit candidate count and response sizes; metadata contains no company records. Keep local contrast/palette benchmark results separate from unavailable vision-model agreement. Eight known contrast-pair labels and four palette cases are developer-authored synthetic expectations; never call 12/12 outcomes an overall visual-AI accuracy result.

## 29 October 2026 — Round 3 scope and conservative local assistant

The user asked to start implementing the improved three-feature scope. Extend the existing checkout/stack and keep the white Rules / New review / Tracking navigation. Insights is a secondary Tracking destination. No deploy, push or recurring monitoring is authorised by this request.

Use a **local extractive assistant** first: verified pinned excerpts with finite why/fix intents, no LLM/tools and no workflow authority. This makes the two named questions work independently of provider availability, at the cost of abstaining on other phrasings/questions. Persist bounded questions privately for owner/reviewer gap analysis and disclose that in the UI. Do not imply generic conversational reasoning or generated safe rewrites.

Contrast uses **human-selected opaque pixel samples**, server-side code and unrounded thresholds. No guessed text/background segmentation or image-level accessibility pass. Apply EXIF orientation to decoded images so measurements and region dimensions match browser coordinates; preserve original bytes and hashes.

Human visual judgements are append-only observations by a separate authorised person. They never replace advisory findings or create an approval. Manual comparison against owner-confirmed references is the fallback while strict free vision is unavailable. Both catalogue-compatible free vision candidates returned HTTP 404 under the unchanged policy in explicit synthetic probes. This time-bound result does not establish that future routes will be unavailable. Do not spend money, weaken privacy or infer model accuracy.

Analytics count distinct drafts by finding type/status across reviews started in the period, including corrected errors in earlier revisions. A latest-only summary was rejected during validation because it erased the recurrence history after a fix. Rechecks cannot inflate a type/status count. The incomplete denominator uses each draft’s latest check in the period; older successful checks cannot replace a newer failed check. Campaign labels use current metadata and do not invalidate factual checks; channel is taken from recorded review scope. Assistant questions have a separate period denominator; unsupported questions are explicitly not proof of missing guidelines.

User-supplied lead areas: Karan Verma (AI agents design) and Krish Tyagi (interface). These are planned ownership assignments, not claims that those people personally authored the AI-assisted changes in this session.

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


