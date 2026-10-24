# Build ledger — 2026-10-24 AI workflow

Plan: `docs/superpowers/plans/2026-10-24-ai-review-workflow.md`

User approved implementation on 2026-10-24. Build-window authorisation was already supplied in this conversation.

Ruling: work in the existing project directory, with this ledger instead of Git worktree helper scripts — the user restricts all writes to this directory and Git discovery reaches a parent repository. No parent repository operations or outside worktree.

Pre-flight: saved revision IDs, artifact hashes and pinned guideline IDs are shared across editor, reviews and approvals. Backend persistence is authoritative; streams cannot authorise transitions. Rewrite runs must not replace the latest review.

Task 0: in progress. No root `.env` found; live synthetic inference awaits a locally configured key. DOCX package and browser probes use synthetic files only.

Key was subsequently configured by the user. Synthetic requests: sampled free routes rejected ZDR; Xing4.0/Phala reached the provider but returned upstream shared-pool 429. No company materials sent and no privacy downgrade. Editor package pinned to SuperDoc 2.26.0. Its separately licensed DOCX Engine permits the current evaluation/development use; preserve both licence notices and disclose the proprietary dependency.

Ruling: implement the defined interfaces and offline integration checks while the live route is unavailable — no guessed provider output or requirement downgrade. Live workflow gate remains open.

Draft/projection/policy/exact-fact checks: 10 passed. Review/approval integration: 4 passed, including self-approval rejection, exact artifact hash, edit invalidation and provider failure. Foundation plus these additions: 48 passed before later additions (provider is an explicitly labelled test double in integration checks).

Browser DOCX probe exposed WIN1252 PostgreSQL encoding. Non-destructive UTF-8 migration retained the original database and runtime config, copied all application tables, and verified every row count; evidence `.local/test-results/utf8-migration.json`. Runtime now uses `inkloom_utf8`; tests use separate `inkloom_test_utf8`. Unicode/DOCX regression and approval/rule/consent/cancellation checks: 6 passed.

Rewrite validation: 3 passed. Browser editor open/edit/export gate still in progress. TypeScript passed after editor/workspace integration. No whole-workflow completion claim yet.

DOCX gate subsequently passed: real paragraph/table edits, save/export/reopen; nine representative fidelity assertions passed. No external browser requests observed. UI workflow: 15 checks passed, including four axe scans and 390px layout, using an explicit synthetic provider double on isolated ports/database. Production build passed before the subsequent image/restore additions.

Real inference: successful synthetic review through Xing4.0/Phala, cost 0, persisted AI tone advisory and cited local fact mismatch. Subsequent free upstream 429s and a failed rewrite remain reported failures; no company payload used. Full live E2E is being attempted with bounded retries and safe manual correction fallback.

Image capability probe: Windows local OCR extracted the synthetic price image correctly; no external model/finetuning. Image/transcript/restore targeted checks: 4 passed. Images require explicit creator transcript verification, then a fresh review, and reviewer visual acknowledgement.

Offline evaluation: 50 synthetic developer-labelled cases; 23 passed, 27 contextual cases not run. Do not infer whole-model accuracy from the small deterministic subset.

Final review: five Important issues fixed in one pass with regressions (revision binding, pending-request recheck, DOCX drawing coverage, mixed PDF coverage, price boundaries). 79 backend tests passed; final extended currency case rerun pending. Final isolated browser run: 17 checks/four axe scans passed. Production build and full API Ruff passed. Real DOCX probe: 4 checks and 9 fidelity assertions passed. Final bounded real workflow: two 429s, incomplete, P0 live gate remains open and P1 held. Release documents and licence notices prepared; no company materials sent.

Final extended API rerun: 79 passed in 123.55s. DOCX probe 4/4 and fidelity 9/9 reran successfully against production web. Source-only project Git initialized on codex/inkloom-ai, with no parent changes and no fabricated commit history. Typecheck launcher now regenerates local editor assets on a fresh checkout before checking types. Documentation/source packaging remains inside this project.

Release archive generated: .local/releases/inkloom-source.zip, 118 curated files; source-manifest.json records per-file/archive hashes. Actual key/pattern scan passed. No complete secret-scanner or clean-machine installation claim. Nine catalogue rows mapped to direct synthetic regression evidence; remaining acceptance cases retain planned status. Public repository/deployment and real human feedback remain outstanding.

24 October 2026 — simplified workflow delivery: implemented the user-authorised three white tabs, one-page Rules with integrated sources/editable proposals/human confirmation, same-visible-version internal snapshots and explicit replacement, task/platform scope, missing-source coverage, static palette/optional free vision, isolated tutorial example. No old user data reset. Final independent review findings (omitted contextual sources and ignored company instructions) fixed and tested. Simplified browser 17 checks/four axe scans passed; existing concurrency browser 17 checks/four scans passed; real DOCX editor 4 checks and representative fidelity 9 checks passed. Production build/typecheck and Ruff passed. Initial full backend 128 passed in154.49s; final extra visual-only approval regression is being checked in the fresh complete suite. Latest real synthetic intake 429 and vision no eligible free/ZDR/schema endpoint; no live success claimed. Current local app 127.0.0.1:3000, API8000, DB54329. Source ZIP refreshed with145curatedfiles, no keys/private data/dependencies; final document update requires regeneration. No public push/deployment or invented user feedback.
Final verification complete: 129 backend tests passed in197.30s. Final production build/types and Ruff passed, simplified browser17/17 and legacy AI/concurrency browser17/17 passed (four clean selected axe scans each). Real editor4/4 and roundtrip9/9 passed. Main preview health APIok/web200 after restart. Local-source package contains145curatedfiles; regenerated after this final documentation update. Live intake/vision limitations remain as recorded. No public deployment/source push.
