# North Mini Model Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans task-by-task.

**Goal:** Deploy the user-selected free North Mini Code model with honest privacy disclosure.
**Architecture:** Model-specific function result parsing in the existing OpenRouter adapter, backend schema validation, explicit retention opt-in and new owner-consent policy.
**Tech Stack:** FastAPI/Pydantic/httpx, Next.js, Docker ARM64, AWS SSM.
**Spec:** docs/superpowers/specs/2026-10-25-north-mini-model-design.md

## Global Constraints
Exact model `cohere/north-mini-code:free`; no-training filter retained; provider retention disclosed; fresh owner consent required; zero pricing; never execute model tools; no real-person photos.

## Review Focus
Reject wrong/multiple function names and malformed arguments. Never accept arbitrary prose as a result. Model without opt-in must remain ZDR. Free/ZDR consent cannot authorize retention policy. Never expose provider reasoning.

### Task 1: Adapter, privacy and regression verification
- [x] Add model-specific failing tests for tool transport, invalid call rejection and policy opt-in.
- [x] Run tests and confirm expected failures.
- [x] Implement transport and policy helper; update consent comparison and UI disclosure.
- [x] Run API suite, Ruff, typecheck and build; verify real synthetic model completion.

### Task 2: Redeploy and verify
- [x] Build ARM image and private release artifact.
- [x] Install model and retention opt-in on host; preserve key/database/upload data.
- [x] Roll out tested image through SSM; verify public real review and retained data.
- [x] Update reports/status/decisions and source release. Record actual limitations.

Ruling: initial public failure required one schema-repair correction. Added a RED→GREEN regression, made tool transport explicit, and retained the existing validator. Fresh API suite: 148 passed. No further privacy relaxation or model fallback.

Completed: 148 API tests passed, corrected ARM image deployed with SHA-256 verification, public real review completed via Cohere at reported cost 0, retained session/draft confirmed. No independent human approval or broad accuracy benchmark claimed.
