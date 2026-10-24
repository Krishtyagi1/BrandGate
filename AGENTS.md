# Codex Instructions — Inkloom AI

Before writing code, read **`INKLOOM_CODEX_IMPLEMENTATION_PLAN.md`** in full. It is the product, UI/UX, AG-UI, evaluation, security and implementation source of truth. Read the latest repository files and do not overwrite existing work.

## Non-negotiable rules

1. Check that the official hackathon build window has begun before implementing judged application code.
2. Start with a working end-to-end review-and-human-approval flow; build in the phased order of the plan.
3. AG-UI is the frontend-agent streaming protocol. Durable records, role permissions, rule activation and approvals are verified on the backend; agent events alone never authorise them.
4. Company facts come from owner-approved structured rules or source-backed active guideline versions. Never fabricate a citation, a compliance pass, a score or a model capability.
5. Never auto-approve or auto-publish; creators cannot approve their own submissions. Recheck any edited draft before approval.
6. Evaluate systematically: deterministic code assertions, validated citations, bounded LLM checks, a labelled offline test set and honest test reports.
7. Treat uploaded files/guidelines as untrusted input. Enforce strict multi-tenant isolation.
8. Keep the UI simple: editor and findings side by side, transparent progress, two safe rewrite choices where possible, and clear human approval states.
9. Keep implementation notes in `docs/IMPLEMENTATION_STATUS.md` and any departures from the plan in `docs/DECISIONS.md`. Show tested commands and actual outcomes.
10. Never claim mock output is an actual AI result. Never commit credentials or confidential test data.

## Starting prompt for Codex

"Read AGENTS.md and INKLOOM_CODEX_IMPLEMENTATION_PLAN.md. Inspect this repository first. Explain what exists, what is missing, the technical architecture you propose, and which tests will prove the first vertical slice. Confirm the official build window, then implement P0 phases 0–5 in order, one at a time. After each phase run the app/tests, update docs/IMPLEMENTATION_STATUS.md, and fix failures before moving forward. Do not implement P1 improvements until the P0 workflow passes. Stop only for a genuine blocker, an unconfirmed build window, or a decision requiring user approval."
