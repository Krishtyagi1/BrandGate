> Superseded by the user’s final production-on-`prod` correction. See docs/GITHUB_ACTIONS_PRODUCTION.md. No GitHub environment; repo secrets; native ARM build; prod-branch OIDC; user monitors Actions.

# Nonprod Actions Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans task-by-task.

**Goal:** Reviewable CI and manual nonprod deployment, ready for user-managed cloud/GitHub setup.
**Architecture:** Reusable check workflow, ARM image build, private S3 release, SSM orchestration and on-host rollback. Existing t4g.micro demo data remains private and persistent.
**Tech Stack:** GitHub Actions, AWS CLI/OIDC, Docker, Python standard library, Bash.
**Spec:** docs/superpowers/specs/2026-10-28-nonprod-actions-design.md

## Global Constraints
Only nonprod; manual deploy from main after CI; no static AWS credentials; secrets excluded; no remote activation; retain database/uploads; builds off-host.

## Review Focus
Malformed config cannot inject commands. Secret env file cannot enter Git/archive/image. Failed new image restores old container. Concurrent host deploys fail safely. Startup/SSM errors cannot be reported as successful deployment.

### Task 1: Deployment scripts and regression checks
- [x] Write failing tests for configuration validation and host rollback using fake external Docker calls.
- [x] Implement local dotenv validation and AWS CLI orchestration with bounded SSM wait; on-host lock/backup/swap/health/rollback script.
- [x] Run regression tests, including fail-before-mutation and rollback failure cases.

### Task 2: CI, configuration and documentation
- [x] Add reusable CI and manual ARM deployment workflows with pinned actions and nonprod environment.
- [x] Create ignored mode-0600 `.env.deploy`, committed example, IAM templates and setup instructions.
- [x] Validate workflows and all backend/typecheck/build checks; scan packaging for credentials.
- [x] Review changes and update implementation/test status with actual results and pending user setup.

Ruling: use the existing reduced demo as nonprod without provisioning more resources. User applies IAM/OIDC/tag/secrets setup; no hosted CI deployment claimed. Author self-check plus independent scoped reviewer passed; seven deployment tests and 148 API tests pass. No application behavior changed.

User steering: no GitHub environment; repository Actions secrets. Exact main-branch immutable OIDC subject replaces environment-bound subject. This is the final deployment contract.
