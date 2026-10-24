# Simple source review implementation plan

> **For agentic workers:** Use executing-plans for integration. Independent modules may be delegated under dispatching-parallel-agents with disjoint file ownership; all edits remain inside this project. Steps use checkbox syntax.

**Goal:** Implement the user's one-page source-confirmation workflow, three white tabs, task-scoped reviews, static visual evaluation and replayable sample tutorial.

**Architecture:** Keep the existing application and authorisation. Immutable knowledge snapshots sit beneath mutable visible versions; staged proposals become active only through owner confirmation. Frontend and backend use the exact contracts below, with additive migrations and no data reset.

**Tech stack:** Existing Next.js/React/TypeScript, FastAPI/Pydantic/PostgreSQL, LangGraph/AG-UI, HTTPX, Pillow, pypdf and SuperDoc. OpenRouter free-only. No new paid service or outside workspace writes.

**Spec:** `../specs/2026-10-24-simple-source-review-design.md`.

## Global constraints and review focus

- Sources integrate across a visible version. Missing, unsupported and incomplete checks are distinct.
- Any confirmed change creates an immutable snapshot; no stale check/approval survives a snapshot change.
- Literal source evidence is validated server-side; an instruction inside a document has no authority.
- Same-version changes use explicit include/replacement confirmation. Explicit new versions start empty.
- Static images evaluate only; video unsupported; text corrections retain explicit application and recheck.
- All current account/tenant/role controls remain. Live/privacy failures are visible and never silently bypassed.

## Task 1 — Knowledge snapshots and source confirmation backend

Files: migration `003_simple_sources.sql`, `app/knowledge.py`, `ingestion/knowledge_intake.py`, `app/guidelines.py`, review/approval/rewrite binding, contracts; tests `test_knowledge.py`.

Contract prefix `/api/organisations/{org_id}/knowledge`:
- `GET /` → `{version:{id,version,status}, snapshot_id, checks:string[], instructions:string, sources:[], rules:[], proposals:[], coverage:[{check,status,reason}], extraction: {status,error?}}`. Returns selected draft or active version; optional `?version_id=`.
- `POST /preferences` `{version_id,checks,instructions}` → current knowledge view. Default categories: `prices,claims,tone,language,required_wording,colours_fonts,logos,accessibility`.
- `POST /sources` multipart `{version_id,file}` → saved source/updated state, no automatic confirmation or provider call.
- `POST /analyse` `{version_id}` → 202 persisted job state; explicit consent and bounded approved provider usage. `GET /` polls job/coverage/proposals.
- `POST /confirm` `{version_id,proposal_ids,replace_rule_ids:{proposal_id:rule_id},expected_snapshot_id}` → refreshed view. Authoritative changes snapshot atomically; implicit replacement forbidden. First confirmation activates a previously draft version if approved rules exist; confirmed rules only are included.
- `POST /new-version` → empty version and view. Optional manual proposed-rule entry retains truthful provenance.

- [x] Write focused regression tests for source integration/gaps, exact excerpt validation, replacement confirmation, concurrent snapshot conflict, history/approval invalidation and empty new version.
- [x] Add migration, immutable snapshots/backfill and intake/confirmation APIs. Snapshot rules feed all review/rewrite/approval paths, with existing routes kept compatible.
- [x] Preserve deterministic/source-only proposal paths as clearly identified; AI analysis reports partial/provider failures honestly.
- [x] Run targeted API tests and existing suite; update status/decisions.

## Task 2 — Review tasks, channels and static visual evaluation

Files: `review_models.py`, `drafts.py`, `reviews.py`, `ai_settings.py`, `agents/review_graph.py`, `app/visual_review.py`, provider image payload support, contracts; tests `test_review_scope.py`, `test_visual_review.py`.

Draft fields added: `category` enum `email,social_media,visuals,website,documents,other`, `platform` optional enum `linkedin,instagram,x,facebook,threads,tiktok,youtube,pinterest`, `requested_checks:string[]`, `task_instructions:string`. Old `channel` remains mapped for legacy records. Upload form accepts these fields too. Preview binds fields plus snapshot, selected rules and any explicitly previewed image references.

- [x] Persist category/platform/tasks and validate selected checks. Avoid treating instructions as factual authority.
- [x] Report per-check coverage and cite actual approved snapshot rules/reference assets. Partial source coverage does not turn an unchecked category into a pass.
- [x] Implement local visual reference/palette comparison and capability-verified optional free vision, with private originals and truthful unavailable states. No pixel mutation or image rewrite endpoint.
- [x] Test scope persistence, selected-rule filtering, source gaps, forged image evidence, mismatched palette, missing reference, video rejection and zero-cost/privacy contracts.

## Task 3 — Three-tab white interface and one-page Rules

Files: `workspace.tsx`, `ui.tsx`, layout/CSS, new `source-setup.tsx`, `review-workspace.tsx`, contracts/UI helpers and Tracking.

- [x] Rename visible product/title to Brand Content Review. White surfaces and restrained borders; three primary routes Rules (`brand`), New review (`reviews/new`), Tracking (`content`). Redirect legacy overview/approvals/activity usefully; Settings secondary.
- [x] Build one-page Rules using Task 1 contracts, selected defaults, uploads, aggregate missing-source feedback, source highlights, old/new proposals and explicit confirmation.
- [x] Add new review categories/platforms, accessible info buttons, check subset and optional task instruction fields using Task 2 contract. Retain real Word editing and all stale-save protections.
- [x] Combine content/status/assigned queue in Tracking and retain review history/comments/decision actions.
- [x] Run TypeScript/build and targeted browser workflow/accessibility checks; fix failures.

## Task 4 — Tutorial, example sources and integration evidence

Files: `app/tutorial.py`, `components/tutorial.tsx`, synthetic example files under `samples/`, status/decisions/test reports.

- [x] Persist one-time tutorial state and replay. Seed isolated fictional example sources/rules/content without fabricated approval or AI results; guide user confirmation and real checking.
- [x] Run end-to-end synthetic/browser regression plus bounded live probe if an eligible route is available. Preserve provider failures and unimplemented checks.
- [x] Independent final review, one meaningful fix pass, documentation and local source package update. Show actual preview and exact remaining limitations.

Execution continues under the user's explicit build request and subsequent workflow answers. No additional procedural permission is needed for reversible implementation within this folder. Choices that would change cost/privacy or remove human control still require a real decision.

## Execution evidence

Final backend: 129 passed in 197.30s. Simplified UI:17 checks/four axe scans passed; original AI workflow/concurrency:17 checks/four scans passed. DOCX editor:4 checks; representative fidelity:9 checks passed. Build/types/Ruff passed. One independent final code review and meaningful fix pass completed. Latest real intake hit429 and real vision found no free/ZDR/schema-compatible endpoint; live success is not claimed. Source archive refreshed under `.local/releases`, excluding private material. Main production preview is running on127.0.0.1:3000. See TEST_REPORT and IMPLEMENTATION_STATUS for scope and remaining live gates.

