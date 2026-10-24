# Inkloom AI Review Workflow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking. Work stays in the existing project folder; no outside worktree or parent repository changes.

**Goal:** Deliver real free-model brand review, a Word-style DOCX editor, safe corrections, version-bound human approvals, the three named improvements and honest evaluation/submission evidence.

**Architecture:** Extend the existing Next.js/FastAPI/PostgreSQL application. A self-hosted browser DOCX editor keeps document structure, a bounded LangGraph workflow combines exact checks and approved-source retrieval with OpenRouter inference, and normal authenticated APIs own every saved revision and approval. Privacy and free-only routing are enforced before any external call.

**Tech stack:** Existing pinned stack and official AG-UI SDKs; proposed SuperDoc browser editor under a compatible open-source license; existing HTTPX client for OpenRouter; project-local extraction/OCR and private files. Verify and pin every new dependency before installing it.

**Spec:** `../specs/2026-10-24-ai-review-workflow-design.md`; root `INKLOOM_CODEX_IMPLEMENTATION_PLAN.md`; test specification `../../AI_WORKFLOW_TEST_PLAN.md`.

**Status (24 October 2026):** User approved implementation. Core tasks 1–10 have implemented paths with synthetic regression evidence; this is not a claim that every checkbox/gate below is complete. Real free review succeeded intermittently, but the full P0 live acceptance gate remains blocked by upstream 429s and an unproven live safe rewrite. P1 Tasks 11–12 are held. Task 13 has 79 passing backend tests, 17 browser checks, representative DOCX fidelity and 23/50 offline evaluation passes; 27 contextual cases remain not run. Task 14 has current architecture, notices, demo instructions and a local source repository/package, with public access and actual feedback still outstanding. The checklists below preserve the full acceptance targets; `docs/TEST_REPORT.md` and `docs/IMPLEMENTATION_STATUS.md` are authoritative for observed outcomes. Exact nightly submission cutoff remains unspecified.

## Global constraints

- Every created/modified file, cache, dependency, report and temporary file stays under this project directory.
- OpenRouter free models only. No paid fallback, paid plugins, credit purchase or automatic upgrade.
- Real files stay private; external payloads require approved policy, redaction/minimisation and deliberate user initiation. No confidentiality guarantee based solely on a free-model label.
- Keep email/password sign-in without a verification code.
- Never auto-approve or auto-publish. No self-approval; approvals bind exact saved artifact hashes and revisions.
- The source-of-truth spec defines P0 before the three P1 improvements. A limitation remains visible until its test/demo gate passes.
- Use official SDK contracts, Pydantic validation and backend permissions. No invented model capabilities or API methods.
- Reuse existing code and data. Do not run destructive migrations or include real materials in fixtures, logs, public source or screenshots.
- Proposed live invocation budget: 10 completion attempts, constrained by actual quota and a 10-request demo reserve. Rewrites have at most 2 repair passes; all subcalls and retries consume the action budget.

## Review focus

1. DOCX saves must retain untouched document parts; server extraction, anchors and hashes must match the saved bytes (Tasks 2 and 3).
2. A free model with no compatible private route must produce a clear unavailable state, never a paid or weaker-privacy fallback (Task 4).
3. Draft edits, role revocation and guideline activation racing a review/approval must not authorise an old version (Tasks 6 and 9).
4. Emoji, combining characters, repeated phrases and table cells must target the correct saved span (Tasks 2, 7 and 8).
5. No false completion when quota expires, a stream disconnects or an unreviewed document region remains (Tasks 6, 9, 10 and 13).

## Order and tonight's schedule

This is a prioritised build order, not a promise that broad Word compatibility and every improvement can be completed in a few hours. There is no basis for an exact finish estimate before the editor/free-route gates.

| Order | Outcome | Gate |
|---|---|---|
| First execution box, up to 25 minutes | Prove real free private inference and DOCX open/edit/save/export compatibility | Stop guessing if either fails; record the specific blocker and propose a concrete alternative before replacing the user's requirement. |
| Core build | Tasks 1–9: one real text/DOCX review, correction, recheck and separate-reviewer decision | One seeded price error, unsupported claim, tone advisory and clean control; authentic citations and immutable revisions. |
| Core hardening | Tasks 10 and 13: other formats, negative paths, quota recovery and release evidence | Supported formats/regions explicit, no silent file flattening or approval bypass. |
| Next available build time | Tasks 11–12: visual checks, follow-up and insights | Each improvement gets its own real demonstration and tests. |
| Final 20–30 minutes before the actual cutoff | Freeze features, rerun changed-path checks, record limitations and package the demo | No new risky feature integration during final packaging. |

If time runs out, report exactly which outcomes work. Never repeat the earlier mistake of calling a foundation-only application the finished AI MVP. Free-model availability and request ceilings can prevent completing the live benchmark tonight; preserve resumable evidence.

## File and module map

| Responsibility | Planned files |
|---|---|
| Revisioned persistence | `services/api/app/migrations.py`, `services/api/migrations/002_ai_workflow.sql`, existing `app/db.py`, `schema.sql` |
| Draft/file APIs | `services/api/app/drafts.py`, `services/api/app/review_models.py`, `services/api/ingestion/document_projection.py` |
| Browser editor | `apps/web/components/review-workspace.tsx`, `document-editor.tsx`, `finding-panel.tsx`, `rewrite-comparison.tsx`, `review-history.tsx`, `apps/web/lib/document-adapter.ts` |
| Shared data contracts | `packages/contracts/reviews.ts`, existing `index.ts`; schemas come from server models |
| AI/privacy configuration | `services/api/app/ai_config.py`, `services/api/providers/base.py`, `openrouter.py`, `services/api/privacy/redaction.py`, `app/ai_settings.py` |
| Rules/evidence | `services/api/evaluators/facts.py`, `evidence.py`, `rewrites.py`, `services/api/retrieval/approved_sources.py` |
| Workflow/transport | `services/api/agents/review_graph.py`, `services/api/app/reviews.py`, `run_executor.py`, `review_stream.py` |
| Human workflow | `services/api/app/approvals.py`, `review_comments.py`, `apps/web/components/approval-queue.tsx`, `content-library.tsx` |
| Improvements | `app/brand_assets.py`, `evaluators/visual.py`, `agents/followup.py`, `app/insights.py`, corresponding focused web components |
| Checks/evals | Focused pytest modules, `tests/e2e/*.mjs`, `evals/fixtures/*.jsonl`, `evals/run.py`, `evals/metrics.py`, bounded scripts under `scripts/` |
| Release evidence | `docs/AI_WORKFLOW_TEST_PLAN.md`, `docs/DEMO_RUNBOOK.md`, `docs/ARCHITECTURE.md`, `docs/EXTERNAL_COMPONENTS.md`, existing status/decisions/test report/README |

## Task 0 — Prove the two risky dependencies before the main build

**Files:** disposable synthetic probes under `.cache/spikes/`, findings in `docs/IMPLEMENTATION_STATUS.md`; no confidential files and no public upload.

- [ ] Inspect the selected SuperDoc package/release/licence without changing the global environment. In a project-local probe, open a synthetic representative DOCX, edit a styled paragraph/table, export and reopen it. Capture the preservation results and locally served worker/telemetry behaviour.
- [ ] With a locally configured key, make one synthetic schema request through a free route enforcing the proposed privacy/zero-cost controls. Verify real returned model/capability/route metadata; do not spend quota comparing many models before one eligible route works.
- [ ] If either probe fails, diagnose the concrete error and explain the smallest alternative. No replacing full browser editing with plain text, exposing company materials to a weaker route, or calling a mock live AI without user agreement.
- [ ] Once both gates pass, reuse the verified approach in Tasks 1–4; discard probe scaffolding or clearly separate it from product code. Probe results are feasibility evidence, not the 50-case evaluation.

## Task 1 — Versioned data and draft revision APIs

**Files:** migrations, `db.py`, `drafts.py`, `review_models.py`, `packages/contracts/reviews.ts`; tests `services/api/tests/test_drafts.py`, `test_ai_rls.py`.

**Interfaces:** `DraftCreate(title, channel, input_kind)`; `save_version(actor, org_id, draft_id, expected_current_version_id, file_bytes | text) -> DraftVersion`; `DraftVersion` exposes `id`, `version_no`, `text_sha256`, `artifact_sha256`, `coverage`, `created_at`, never private paths. All UUIDs are tenant-validated. `ReviewStatus` and document status are separate enums from the design.

- [ ] Add failing real-database tests for create/save/read, immutable prior versions, cross-tenant IDs and stale-save 409 preserving both versions.
- [ ] Introduce an applied-migrations ledger and additive migration inside the existing cluster; keep the separate `inkloom_test` database. Test applying it twice and to the existing baseline.
- [ ] Implement tenant-scoped revision APIs and private file storage; derive creator and hashes server-side, enforce limits and append audit entries transactionally.
- [ ] Generate/update TypeScript view contracts and register routers in `main.py`.
- [ ] Verify targeted pytest modules through `npm.cmd run test:api -- -k "draft or ai_rls"`, then typecheck. Record actual results.

## Task 2 — DOCX projection and document preservation gate

**Files:** `ingestion/document_projection.py`, `review_models.py`; tests `test_document_projection.py`; synthetic fixtures under `services/api/tests/fixtures/documents/`.

**Interfaces:** `project_document(file_bytes) -> DocumentProjection(text, blocks, coverage, unresolved_changes, exclusions)`; `DocumentAnchor(part, block_id, start, end, quote)` uses revision-scoped code-point ranges. Body paragraphs, ordered nested tables, headers and footers are required supported text regions; unsupported text parts are reported explicitly.

- [ ] Build synthetic DOCX fixtures covering split runs, headings/lists, hyperlinks, images, table cells, sections, headers/footers, Unicode, footnotes, fields, tracked changes, damaged ZIP and expanded ZIP limits.
- [ ] Write assertions for source order, exact content/anchors, preservation of original bytes and unresolved-review-markup detection; no `paragraph.text` rewrite that destroys formatting.
- [ ] Implement bounded package inspection and canonical projection. Do not fetch linked media or execute macros/fields.
- [ ] Document supported/unsupported regions and compare extraction after a saved round trip; ambiguous anchors must fail safely.
- [ ] Verify fixture extraction and package-part inventory before integrating AI.

## Task 3 — Word-style browser editor and authoritative save

**Files:** `document-editor.tsx`, `lib/document-adapter.ts`, `review-workspace.tsx`, relevant styles/package manifest; tests `tests/e2e/document-editor.mjs`.

**Interfaces:** application wrapper `DocumentEditorHandle.snapshot(): Promise<Blob>`, `reveal(anchor): Promise<void>`, `applyProposedEdit(anchor, expected_text, replacement): Promise<void>`, `hasUnsavedChanges(): boolean`. These are Inkloom-owned interfaces; map them to the pinned SuperDoc release's verified public API.

- [ ] Inspect/pin npm package version, actual licence, asset/worker loading and Next.js client-only requirements; retain licence notices and use compatible source terms.
- [ ] Prove open/type/format/table/edit/save/reopen/download for the representative DOCX fixture. Disable telemetry and network-linked document resources; serve assets locally.
- [ ] Add editor UI with compact formatting, zoom/find, visible save state and contextual side panel. No separate full-screen AI chat.
- [ ] Save exported DOCX bytes through Task 1, then reproject on the server through Task 2. Do not mark Saved until persistence succeeds.
- [ ] Test failed upload/export/save, stale concurrent save, refresh, original immutability, layout comparison, undo/redo and 390px use. Verify Word-style editing actually works; a document viewer is insufficient.
- [ ] Keep unsupported features visible and original download available; block destructive round trips. This compatibility result is a go/no-go gate.

## Task 4 — Real OpenRouter adapter, privacy and zero-cost enforcement

**Files:** `ai_config.py`, `providers/base.py`, `providers/openrouter.py`, `privacy/redaction.py`, `ai_settings.py`, `.env.example`, launchers, settings UI; tests `test_provider_policy.py`, `test_redaction.py`, `test_provider_contract.py`.

**Interfaces:** `ReviewProvider.evaluate(request: ProviderRequest) -> ProviderResponse`; `ProviderResponse` contains structured findings, actual model/provider identifiers, token usage and request ID. `prepare_payload(...) -> RedactedPayload(text, approved_excerpts, token_map_ref, policy_version)`. `GET /ai/status` reveals configured/eligible/connection-tested states separately, never key material.

- [ ] Before code, test that absent/paid/unknown-price model, noncompliant privacy route, missing key, unsupported schema and exhausted quota cannot dispatch an inference request.
- [ ] Explicitly load a root ignored `.env`; require free model validation and zero max prices, no paid tools/plugins, `data_collection=deny`, `zdr=true`, required schema parameters and a server-side key.
- [ ] Add local redaction and outbound preview with stable protected tokens; user-approved organisation processing policy is a prerequisite. Do not send real materials for connection tests; use a synthetic one-line schema check.
- [ ] Query current model capabilities and key limits; pin a free model for evals. Track all app/judge/eval attempts against a shared database quota budget, not one limiter per browser.
- [ ] Use bounded HTTP timeouts, response-size caps and at most one schema repair within the hard action budget. Handle 401/402/403/404/429/timeouts and provider capacity distinctly. Never relax privacy or cost after failure.
- [ ] Run offline HTTP contract checks; only after local key configuration run an explicit synthetic live smoke. Record model, route policy, observed usage and result. If no eligible free route exists, real-company AI use is blocked.

## Task 5 — Approved rule retrieval and deterministic facts

**Files:** `retrieval/approved_sources.py`, `evaluators/facts.py`, `evaluators/evidence.py`, guideline API/UI fields; tests `test_fact_checks.py`, `test_evidence.py`, `test_retrieval.py`.

**Interfaces:** `load_policy(org_id, guideline_version_id, channel, as_of) -> PolicySnapshot`; `retrieve(snapshot, text, limit=12) -> list[ApprovedEvidence]`; `check_facts(projection, policy) -> list[Finding]`; `verify_findings(proposed, projection, policy) -> VerifiedReview`.

- [ ] Add labelled rules and tests for price/currency/unit/date/entity scope, spelling/name, required disclaimers, prohibited terms, clean controls and ambiguous claims.
- [ ] Extend owner-confirmed structured facts additively. Do not automatically interpret existing ambiguous wording as a typed fact.
- [ ] Index only approved rule wording and approved supporting excerpts; constrain every retrieval query by organisation/version/approval/channel. Never index discarded source lines as trusted policy.
- [ ] Validate excerpt/location membership and substantive support; fabricate neither page labels nor references. Uncertain nuance becomes Unverified/Advisory rather than a confirmed fact.
- [ ] Measure retrieval recall against seeded expectations; use deterministic PostgreSQL retrieval first and preserve complete evidence IDs for historical runs.

## Task 6 — Persisted real review workflow and AG-UI stream

**Files:** `agents/review_graph.py`, `app/reviews.py`, `run_executor.py`, `review_stream.py`; tests `test_review_runs.py`, `test_review_stream.py`.

**Interfaces:** `start_review(actor, draft_id, version_id, idempotency_key) -> ReviewRun`; `execute_review(run_id) -> None`; `GET /review-runs/{id} -> ReviewView`; `POST /review-runs/{id}/stream` attaches an official AG-UI client to that authorised persisted run; `POST /review-runs/{id}/cancel` performs a conditional state change. Base path is `/api/organisations/{org_id}` for every endpoint.

- [ ] Test duplicate starts, unknown/cross-tenant IDs, cancellation races, interrupted process recovery, membership revocation and guideline activation while running.
- [ ] Pin draft/rules, run extraction/policy/retrieval/exact checks/model checks/verification/persistence as a bounded graph. Do not hold SQL locks across inference.
- [ ] Persist safe event sequence/snapshots with monotonically increasing per-run sequence. Reattach retrieves authoritative state and cannot start a second job.
- [ ] Stream named progress, verified finding view models and lifecycle using installed SDK models. Render no partial unvalidated JSON as a verified finding and expose no hidden reasoning.
- [ ] Treat failed/partial provider work as Incomplete/Failed; preserve useful deterministic results with a conspicuous coverage label. Late model responses cannot resurrect cancelled runs.
- [ ] Verify a real synthetic seeded error and clean control; reserve quota for user demo. Record actual live evidence separately from fake-provider integration tests.

## Task 7 — Review screen and evidence experience

**Files:** `review-workspace.tsx`, `finding-panel.tsx`, `review-history.tsx`, `lib/reviews.ts`, existing `workspace.tsx` and styles; tests `tests/e2e/review-workflow.mjs`.

**Interfaces:** `ReviewView` consumes Task 6; a finding includes type/status/severity/observed text/anchor/reason/evidence/coverage. Navigation resolves `/reviews/new` and `/reviews/{draftId}` explicitly rather than falling through to a phase notice.

- [ ] Render live step labels, source/version badges, clear stale/incomplete states and a real zero-findings state without a compliance percentage.
- [ ] Keep editor position/context when revealing cited text or a document finding. Test emoji, repeated text and table-cell anchors.
- [ ] Add keyboard focus handling, accessible announcements and mobile Document/Findings/History tabs.
- [ ] Test missing rules/key/eligible route, quota limit, permission denial, cancel, refresh and retry. UI never substitutes a mock result for an unavailable model.

## Task 8 — Safe rewrite comparison and document edits

**Files:** `evaluators/rewrites.py`, rewrite API section in `reviews.py`, `rewrite-comparison.tsx`, document adapter; tests `test_rewrites.py`, `tests/e2e/rewrite-document.mjs`.

**Interfaces:** `request_rewrites(parent_review_id, finding_id, version_id, idempotency_key) -> RewriteJob`; use the same persisted run infrastructure with `run_kind=rewrite`, and exclude those jobs from latest completed review selection. `validate_candidate(original, candidate, policy, protected_spans) -> CandidateValidation`; `apply_rewrite(...) -> DraftVersion` requires exact base/anchor/quoted text and explicit user action.

- [ ] Test changed protected URLs/email/hashtags/tokens, new claims, lost disclaimers, changed CTA, short/long length and factual-correction priority.
- [ ] Generate two options in one request where safe; validate independently with code and contextual support checks. At most 2 repair passes under quota; show a single safe option if only one qualifies.
- [ ] Preview changes inline and apply using public editor operations, preserving document structure. Save/reproject a new version and mark every previous finding stale.
- [ ] Reject applying a candidate to an edited revision or ambiguous repeated phrase; dismissing records a note without deleting history.
- [ ] Test applying, undoing, saving, exporting/reopening, redaction restoration and mandatory recheck before submission.

## Task 9 — Comments, separate-human approval and content library

**Files:** `approvals.py`, `review_comments.py`, `approval-queue.tsx`, `content-library.tsx`, dashboard changes; tests `test_approvals.py`, `test_comments.py`, `tests/e2e/approval-workflow.mjs`.

**Interfaces:** `request_approval(actor, draft_id, version_id, reviewer_id, idempotency_key) -> ApprovalRequest`; `decide(actor, request_id, expected_version_id, artifact_sha256, decision, comment, manual_visual_ack) -> ApprovalDecision`. Persist machine coverage, unchecked regions and human acknowledgement.

- [ ] Test self-approval, author/submitter role switching, wrong assignee, disabled member, stale text/file hashes, formatting-only edit, new guidelines and concurrent decisions.
- [ ] Require current complete supported-text review, no unresolved tracked changes and no unresolved confirmed high-severity issue. Let Unverified/Advisory findings remain visible for human judgement.
- [ ] For visual areas excluded from AI coverage, require explicit reviewer acknowledgement of personal inspection. Unknown/failed text extraction blocks submission.
- [ ] Lock and recheck all decision conditions in one transaction; duplicate idempotent decisions do not create duplicate audit writes. Keep superseded requests and prior approvals immutable.
- [ ] Add anchored/plain comments, resolve/reopen, Request changes/Reject with required comment, explicit Approve confirmation and revision comparison.
- [ ] Replace content/approval placeholders with real lists/filtering/search/pagination and persisted dashboard counts.
- [ ] Run two-account permission E2E, then request actual independent human feedback when available; distinguish the automated two-account test from real multi-person testing.

## Task 10 — PDF, images, OCR and original-preserving downloads

**Files:** `content_files` APIs, ingestion handlers, document workspace import controls, download endpoints; tests `test_content_uploads.py`, `test_exports.py`, `tests/e2e/content-formats.mjs`.

- [ ] Reuse bounded private upload checks; test MIME/content mismatch, oversized/empty/encrypted/scanned/corrupt files, zip bombs, malicious names and parser deadlines.
- [ ] PDF keeps page/region provenance and source preview. Editing extracted PDF text creates a new document with an explicit layout distinction.
- [ ] Add bounded local OCR only if an engine can be installed/run wholly under this project. Capture extraction coverage; unsupported OCR is an honest state, never a full text pass.
- [ ] Download the exact saved DOCX revision or original attachment. Mark draft vs approved artifact context; approved export checks the decision's version/file hash server-side.
- [ ] Reopen exported DOCX and inspect all representative pages/parts. Existing markup/comments and unsupported features follow the declared fidelity policy.

## Task 11 — Visual brand and accessibility improvement

**Files:** `brand_assets.py`, `evaluators/visual.py`, visual panel, asset fields; tests `test_visual_checks.py`, `tests/e2e/visual-review.mjs`.

- [ ] Store owner-approved logo references, palette/fonts and guideline version links; private downloads and RLS apply.
- [ ] Implement exact source-derived DOCX font checks, provided color/contrast calculations and image text/alt-text checks where data is available. Clearly identify regions these checks do not cover.
- [ ] Add optional image/crop payload preview, privacy redaction and capability-verified free vision analysis with source references. Never send confidential page images automatically.
- [ ] Use advisory findings for uncertain logo/layout judgements. Test approved/corrupt/missing logos, missing references, unreadable image, low contrast and no eligible free vision endpoint.
- [ ] Improvement is delivered only after one real representative visual check, evidence display and limitations record pass. OCR-only is not the visual improvement.

## Task 12 — Source-aware assistant and governance insights improvements

**Files:** `agents/followup.py`, assistant APIs/panel, `insights.py`, overview insights UI; tests `test_followup.py`, `test_insights.py` and E2E.

- [ ] Scope assistant threads to tenant/draft/revision/finding and approved evidence; stream answers with resolvable sources. Requests to publish/change roles/activate knowledge are refused as unavailable actions.
- [ ] A suggested edit uses the same explicit compare/apply/recheck path; chat cannot bypass Task 8 or 9. Test malicious instructions and guideline updates mid-thread.
- [ ] Compute actual issue recurrence, unsupported claims, unclear/conflicting rules and approval turnaround; specify whether counts are per draft/latest run or historical event. Prevent repeated rechecks from inflating headline counts.
- [ ] Add date range/denominators, small-sample/empty states and cross-tenant tests. Show measured usage/latency only where recorded.
- [ ] Demonstrate and test each improvement separately; record actual limitations and quota consumption.

## Task 13 — Regression suite, live evaluation and release evidence

**Files:** test modules and commands in `docs/AI_WORKFLOW_TEST_PLAN.md`, `evals/`, `scripts/test-ai.mjs`, `scripts/eval-ai.mjs`, `docs/TEST_REPORT.md`.

- [ ] Create the offline test harness and synthetic fixtures in parallel with each preceding task, not at the end. Every test names the contract failure it catches.
- [ ] Implement the 50-case labelled dataset, deterministic metrics and rubric-driven contextual judge. Ground truth is human-labelled and never the reviewed model's own answer.
- [ ] Keep default tests offline and network-blocked. Fake-provider tests establish wiring/safety, not model accuracy. Live eval requires explicit command, configured key, qualifying free route, request cap and synthetic cases only.
- [ ] Make live runs resumable by case/model/prompt/policy versions; classify pass/fail/error/not-run and report denominators. Reserve demo quota and do not retry daily limits in a loop.
- [ ] Run changed-path tests, full offline regression, typecheck, Ruff, production build, browser workflow and selected accessibility scans. Add visual inspection for editor/import/export fixtures.
- [ ] Run a live smoke and the affordable benchmark portion; record incomplete cases honestly. Do not claim the 50-case target has passed until actually measured.

## Task 14 — Submission packaging and documentation

- [ ] Create `docs/DEMO_RUNBOOK.md`: deterministic setup, company rules v1, seeded error, real review, cited explanation, rewrite, recheck, second-human workflow, rule v2/history, three improvement demos and negative cases.
- [ ] Create `docs/ARCHITECTURE.md` and `EXTERNAL_COMPONENTS.md` listing actual models/providers, dependencies/licences, source/template reuse, datasets and significant AI assistance.
- [ ] Update README, `.env.example`, status/decisions and test report with exact setup, commands, outcomes, privacy/data-flow limits, free-model availability and supported document features.
- [ ] Prepare a source repository inside this project and a secret/real-material exclusion review. Do not stage the parent repository, publish company documents or invent development history. Public push/hosting follows a named destination and user-authorised exposure.
- [ ] Prepare local installation/demo instructions; deployment remains optional until a private suitable host is chosen. A localhost URL is not a judge-accessible deployed link.
- [ ] Provide a structured user feedback form, record observed tasks/failures/changes, and distinguish actual feedback from planned studies. Participant/contribution details use truthful organiser-required information; no invented roles.
- [ ] Round 2 evidence: functioning workflow, technical decisions/reliability, plan progress, three improvements, usability. Round 3 evidence: final source/demo, reliability changes, privacy/security/accessibility explanation, known limitations and roadmap.

## Final acceptance before claiming the AI MVP works

The saved real-model run identifies a seeded factual error and an unsupported claim, preserves a clean control, cites valid approved material, proposes at least one safe correction, saves/rechecks a DOCX revision and permits a different authorised human to decide on that exact artifact. Key/material leaks, self-approval, stale approval and paid fallback counts are zero in the checked scenarios. The browser document remains editable and its downloaded form passes the supported fidelity matrix. Reports distinguish tested model behaviour, offline safety checks, untested features and coverage exclusions.

## Hackathon requirement and judging traceability

| Problem-statement requirement | Delivery task | Evidence for judges |
|---|---|---|
| Approved guidelines, facts, terminology and assets | Existing foundation plus 5 and 11 | Owner approval/version change; discarded text not used; private asset/source links. |
| Text, images and documents | 2, 3 and 10 | Real Word edit/save/export; selectable PDF; supported OCR/visual coverage with explicit exclusions. |
| Tone, terms, claims, facts and messaging | 4–7 | Real model result beside exact checks; wrong-price, unsupported-claim, tone and clean-control examples. |
| Visual consistency and accessibility | 7, 11 and 13 | Reference/region findings, known contrast/font cases and actual UI accessibility results. |
| Explanations and source references | 5–7 and 12 | Clickable approved excerpts; fabricated and irrelevant citations rejected. |
| Corrections preserving intent | 8 | Compare/apply/recheck with protected links, factual fidelity and DOCX round trip. |
| Collaboration, comments and revision approval | 1, 3 and 9 | Version trail, Request changes, exact-artifact decision, self/stale approval failures. |
| Recurring mistakes and unclear guidance | 12 | Counts from stored records with denominators and source examples. |
| Confidentiality, external AI disclosure and human control | 4, 9 and 13 | Outbound preview/redaction, blocked ineligible routes and human decision audit. |

| Round 2 criterion | Points | Planned proof |
|---|---:|---|
| Core workflow runs end to end | 30 | One uninterrupted real review → edit → recheck → eligible human decision demo. |
| Technical depth and reliability | 25 | Private retrieval, verified evidence, revision/file hashes, free-route policy and failed-path tests. |
| Progress against the plan | 20 | Status checklist with actual completed tasks, commands, dated changes and remaining work. |
| Three named improvements | 15 | Separate demonstrations of visual checks, finding-aware assistant and governance insights. |
| Usability so far | 10 | Clean contextual editor, keyboard/mobile flows and honest structured feedback. |

Round 3 retains the organiser's weighting: completeness 25, the three improvements 20, normal-use reliability 20, usability/real-world fit 20, documentation/roadmap 15. Task 14 packages actual proof for these categories. Do not replace missing implementation or user testing with presentation claims. Source repository/deployment access, external-component and AI disclosures, required participant information and contributions remain submission requirements; do not invent any of them.
