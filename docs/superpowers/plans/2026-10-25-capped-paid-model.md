# Capped Paid Model Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans to implement task-by-task.

**Goal:** Configure real text inference within the user's USD 1 total cap.
**Architecture:** Keep the existing OpenRouter adapter; opt into one explicitly allowed paid model with verified key cap and a fresh processing-policy version.
**Tech Stack:** FastAPI/Pydantic/httpx, Next.js, Docker, AWS SSM.
**Spec:** docs/superpowers/specs/2026-10-25-capped-paid-model-design.md

## Global Constraints
USD 1 total key cap, no reset; privacy filters and owner consent retained; no secrets in logs or release artifacts; no self/automatic approval.

## Review Focus
Missing or resetting key limit must block dispatch. Decimal NaN/negative prices must fail closed. Paid model overrides must match the configured allowlist. Paid image inputs must fail. Previous free consent must not authorize the new paid policy.

### Task 1: Bounded paid adapter and disclosure
- [ ] Add failing provider boundary tests for configured model, catalogue ceilings, key cap/reset/remaining checks and HTTP policy.
- [ ] Run provider tests and confirm new failures.
- [ ] Implement minimal explicit paid settings, model and key validation; retain free defaults.
- [ ] Update processing-policy version and UI wording; document server-only setting.
- [ ] Run all API tests, Ruff, typecheck and build.

### Task 2: Secure rollout and real verification
- [ ] Verify real key has <= USD 1 nonresetting cap and account has prepaid balance.
- [ ] Run bounded synthetic model probe and review; no confidential inputs.
- [ ] Build ARM container, transfer through private deployment artifacts and SSM; preserve database/uploads.
- [ ] Verify deployed environment, public real review and key usage; remove temporary secret-transfer parameter/permission.
- [ ] Update implementation status, test report, decisions and source archive with actual outcomes.
