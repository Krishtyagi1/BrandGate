# Railway Deployment Implementation Plan

> **For agentic workers:** execute inline using superpowers:executing-plans.

**Goal:** Deploy the current complete app using Railway trial credits and return
a verified public URL.

**Architecture:** One Next.js/FastAPI Docker service, separate PostgreSQL, private
upload volume. Restricted database runtime login and separate migration credentials.

**Tech Stack:** Docker, Python 3.12, Node 22, PostgreSQL, Railway.

**Spec:** `docs/superpowers/specs/2026-10-25-railway-deployment-design.md`

## Global Constraints

- Trial credits only; no paid upgrade or purchase.
- All local work stays in this checkout; preserve existing edits.
- No confidential data, environment files or local database in deploy context.
- Free-only AI, backend approval and tenant-isolation controls remain enforced.

## Review Focus

- Missing origin/credentials must fail before binding a public port.
- Existing privileged runtime roles must be rejected.
- Child process failure or termination must stop the other service.
- Uploads must survive app deployment via the volume, not image contents.
- Trial or authentication failures must not become a claimed public deployment.

### Task 1: Hosted startup

Files: `scripts/hosted.py`, `services/api/tests/test_hosted_startup.py`.

- [ ] Test missing/unsafe configuration and credential URL escaping.
- [ ] Implement validation, restricted-role bootstrap, and coordinated app startup.
- [ ] Test real PostgreSQL bootstrap and run the full backend suite.

### Task 2: Deployment packaging

Files: `Dockerfile`, `.dockerignore`, `docs/RAILWAY_DEPLOYMENT.md`.

- [ ] Add locked-dependency container build and runtime configuration.
- [ ] Validate build, manifests and excluded private data; document setup.

### Task 3: Provision and verify

- [ ] Confirm Railway account/trial availability without upgrading.
- [ ] Create PostgreSQL, app service and upload volume with private variables.
- [ ] Deploy source-only current checkout and inspect build/runtime logs.
- [ ] Verify public HTTPS happy/negative paths and update implementation status.

Ruling: no source commit or shared-branch push is needed for CLI source upload.
If GitHub deployment is used, use only reviewed source and signed commits.

Ruling: official Railway docs now prohibit Config as Code for new services.
Use automatic Dockerfile detection and dashboard/API health/restart settings;
do not ship a new deprecated `railway.json` file.
