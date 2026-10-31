# Shared Demo Login Implementation Plan

> Execute inline in this session with test-first implementation and a final independent review.

**Goal:** One-click restricted demo sign in using server-side AWS credentials.

**Architecture:** Host retrieves an SSM SecureString into a private mounted file. FastAPI validates the configured account and records a restricted, org-bound session. Next.js uses the existing session flow and routes demo visitors to Tracking.

**Tech Stack:** Next.js, FastAPI, PostgreSQL, AWS CLI SSM.

**Spec:** docs/superpowers/specs/2026-10-31-demo-login-design.md

## Constraints and review focus

- No secret in responses, browser bundles, logs or version control.
- Deny administrative writes and cross-organisation access on every demo request; normal sessions remain unchanged.
- A disabled membership, bad password or invalid/missing parameter cannot create a session.
- New mutation endpoints default to denied; do not bypass existing RLS, consent or approval checks.
- Shared edits and AI history must be disclosed. No automatic approval or processing on login.

## Task 1

- [x] Write API integration tests for demo sign in, restrictions, permitted editing and AI routing, CSRF/rate limits and invalid configuration. Run and observe failure.
- [x] Add app/demo_login.py, migrations 007/008 and accounts/security integration. Host loader scripts/load-demo-credentials.py and deployment hooks retrieve the exact configured SecureString without printing it. Test loader validation and private permissions.
- [x] Add the login button, shared-demo banner, restricted navigation and dashboard landing to auth.tsx/workspace.tsx; extend User contracts.
- [x] Run npm run test:api, deployment tests, lint, typecheck/build and local browser checks. Record outcomes in docs/IMPLEMENTATION_STATUS.md and docs/DECISIONS.md.
- [x] Independent review of final change, fix important findings and re-run affected checks. Signed commit, then apply the authorised production rollout and verify public demo sign in.

Completed: 214 API tests, 13 deployment tests, Ruff, typecheck, Next.js build,
ARM64 image build, native Chrome local and production button tests. SSM release
passed internal/public health; both domains passed the auth/permissions/content
smoke. See docs/IMPLEMENTATION_STATUS.md for release identifiers and actual limits.

Ruling: continue in the existing folder because the recorded project preference explicitly forbids outside worktrees. Git rejects branch names beginning with `-`; use `demo-login` for this feature.

Review: independent reviewer found optional-loader failure aborted normal operation. Hook regression reproduced failure before fixing both hooks. No other important finding reported. Later test-first hardening isolates tokens from the legacy session registry, fixes demo SSE reauthentication, and preserves server protocol references through chat text redaction. No deferred review findings.
