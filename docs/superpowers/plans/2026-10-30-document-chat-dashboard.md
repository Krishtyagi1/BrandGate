# Document Chat and Tracking Dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Explain saved document flags conversationally and expose reliable current results in Tracking.

**Architecture:** Add independent authenticated chat and dashboard routers using the existing review bindings, RLS, provider adapter and AG-UI models. Add a document chat component to the review panel and a dashboard above Tracking's existing document list.

**Tech Stack:** FastAPI, Pydantic, psycopg/PostgreSQL, Next.js/React/TypeScript, AG-UI.

**Spec:** `docs/superpowers/specs/2026-10-30-document-chat-design.md` and `docs/superpowers/specs/2026-10-30-review-dashboard-design.md` (user approved both on 30 October).

## Global Constraints

- Reuse the current stack and provider; add no chatbot service or model dependency.
- Keep history bounded to the exact review and user.
- No automatic approvals, publication, new hosting or deployment is included.
- Preserve the current model, pricing and privacy restrictions.
- Continue in this project folder as authorised by the existing build ledger; no outside worktree or parent Git changes.

## Review Focus

- Content or permission changes during inference must prevent stale answer persistence/replay.
- Repeated send requests must not spend quota twice or create duplicate turns.
- Context limits must disclose/reject omissions, including large multi-finding reviews.
- Latest failed/rewrite reviews must not resurrect old flags or mask incompleteness.
- Creator totals and drill-downs must never leak other creators' records.

### Task 1: Document chat backend

**Files:** create `services/api/app/document_chat.py`, `services/api/migrations/006_document_chat.sql`, `services/api/tests/test_document_chat.py`; modify `services/api/app/main.py`.

**Interfaces:** review-scoped GET `/review-runs/{id}/chat`, POST `/review-runs/{id}/chat/preview`, POST `/review-runs/{id}/chat`, POST `/review-runs/{id}/chat/{turn}/stream`. Preview returns payload/hash; send requires matching hash and retry key. Structured AI response items reference saved finding/citation IDs; server resolves source text.

- [x] Write integration tests for preview/send/history/stream, consent, evidence-free and forged references, private history, failures, idempotency, redaction, context overflow and stale-during-inference.
- [x] Run `npm run test:api -- -k document_chat` and confirm missing endpoints fail.
- [x] Implement additive immutable RLS storage, bounded redacted contexts, preview hashing, retry claim before provider call, accounting and post-inference access checks. Preserve failed claims and allow explicit new-key retry.
- [x] Run the same targeted tests until green.

### Task 2: Document chat interface

**Files:** create `apps/web/components/document-chat.tsx`; modify `apps/web/components/review-workspace.tsx`, `apps/web/app/simple.css`, `scripts/test-ui-server.py`, `scripts/test-simple-ui.mjs`.

**Interfaces:** `DocumentChat({base,runId,disabled})` uses Task 1 endpoints; per-finding action opens the shared panel with a finding-specific question.

- [x] Add browser assertions for whole-document conversation, inspect/send, follow-up/history, source display and disabled stale state.
- [x] Build accessible panel, shortcuts, preview confirmation, structured answers/citations and AG-UI saved-turn stream recovery.
- [x] Run browser tests with the explicit synthetic provider, frontend typecheck/build.

### Task 3: Dashboard backend and Tracking interface

**Files:** create `services/api/app/dashboard.py`, `services/api/tests/test_dashboard.py`, `apps/web/components/review-dashboard.tsx`; modify main router registration, `content-library.tsx`, `simple.css`, browser tests.

**Interfaces:** GET `/organisations/{id}/dashboard?days=7|30|90` returns authorised current documents, latest valid findings, summary counts, breakdowns and period activity. Dashboard filters its returned complete current-document inventory and links to review/chat. Fetch independently of the existing list limit.

- [x] Write failing tests for initial/flagged/dismissed/stale/failed/latest/rewrite cases, period counts, >200 documents and creator/cross-tenant isolation.
- [x] Run `npm run test:api -- -k dashboard` to verify RED.
- [x] Implement role-filtered queries, current binding validation, unambiguous count semantics and exact filter drill-downs. Keep historical insights separate.
- [x] Implement responsive Tracking overview with summary/filter buttons, labelled bars, activity counts, refresh, errors and attention list.
- [x] Run targeted backend and browser dashboard tests, including mobile overflow/accessibility.

### Task 4: Verify and document

**Files:** `docs/IMPLEMENTATION_STATUS.md`, `docs/DECISIONS.md`, this plan/progress.

- [x] Run full API tests, Ruff, typecheck, production build and synthetic browser workflow.
- [x] Inspect browser screenshots and fix material failures; perform independent final review.
- [x] Attempt bounded real inference only with synthetic data and existing eligible configuration; report failures without changing policy.
- [x] Record exact outcomes, limitations and deferred work. Leave deployment separate.

## Progress and execution rulings

User's “do both” authorises execution in this chat without another plan-approval round. Existing project-local workflow preference supersedes worktree helper setup. No automatic commits/pushes: this checkout is on the auto-deploying prod branch, and this request authorises implementation and tests only.

Pre-flight: Tasks 1/2 share preview/hash/answer contracts; Task 3 uses the same latest-review/content/snapshot/scope semantics. Both validate backend access and never alter review/approval state.

Initial test attempt blocked by local database not running; start the existing project-local database, then rerun baseline. No dependency installation needed.


## Completion evidence — 30 October 2026

Task 1 complete: missing endpoints first failed (4 new failures / 5 existing helper passes); implemented endpoints passed. Added regressions reproduced saved-failure replay, omitted overview flags, dismissals and missing authority locks before fixes. Final full API suite: 187 passed in 27.20s.

Task 2 complete: browser exercised multi-turn previews/sends, validated excerpts, saved history after reload, mobile accessibility, and disabled stale chat. Final browser workflow: 34 checks / 12 selected axe scans, zero violations. Real synthetic endpoint/stream/history flow also completed with North Mini, reported chat cost 0.

Task 3 complete: missing dashboard endpoints first failed; backend checks cover 202 documents, isolation, rechecks, rewrites, stale/latest/incomplete results and dismissals. Browser first reproduced period-label and mixed-severity filter errors; final workflow passed after fixes. Screenshots inspected at desktop and 390px.

Task 4 complete: API 187 passed; Ruff passed; typecheck passed; final production build passed; diff whitespace check passed. Implementation status and decisions record commands, evidence and limits. Local test DB and fictional fixtures only; no push/deployment.

Final independent review: six findings fixed, no deferred findings. Shared audit dismissal overlay reflects human records; overview responses must cover all saved findings; failure retries keep original errors; history respects revoked consent; org/draft/consent locks guard persistence; high-severity/category/status filters select the same finding.

Ruling: user-authorised inline execution in existing checkout; no auto-commit or prod push. Cost if wrong: changes remain local for review rather than being released automatically. Ruling: dashboard uses a complete authorised inventory response with incremental UI display; very large-workspace pagination/performance remains unbenchmarked, documented in implementation status. Ruling: structural citation validation and narrow synthetic live success are not general semantic accuracy evidence; human review remains required.
