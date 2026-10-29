# Round 3 progress — 2026-10-29

Plan: docs/superpowers/plans/2026-10-29-round3.md

User requested execution after reviewing the three-feature scope. Reuse existing checkout and existing stack. Previous build authorisation is recorded; no official Round 3 dates are claimed. No deployment/push requested.

Pre-flight: all three features share draft/run/snapshot IDs; assistant and visual confirmations must not mutate review output or approval state. Insights use persisted review observations and explicit denominators. New metadata is not factual authority.

Task 1: in progress. No new verification outcome yet.


Task 1: implemented local sampled contrast, region overlays, separate-person append-only assessments and manual approved-reference fallback. Targeted visual/contrast checks: 33 passed. Live probe: selected free model returned 404; 0/12 benchmark cases evaluated; agreement null. No live vision success claimed.
Task 2: implemented local extractive assistant with validated citations, abstention, stale/latest/source checks, private gap logging and AG-UI delivery. Browser verifies cited answer and refusal of an approval instruction.
Task 3: implemented campaign metadata and owner/reviewer insights under Tracking. Browser integration: 22 checks passed with six selected accessibility scans. Additional regression coverage for reporting periods, superseded reviews and guideline activation passed.
Final review: independent read-only reviewer found one Important issue, EXIF/browser sampling coordinate mismatch. Regression reproduced ratio 1 instead of21; ImageOps.exif_transpose fixed it while preserving file hashes. Visual suite33 passed; subsequent full backend162 passed in30.40s. No other Critical/Important/minor findings were reported. Reviewer did not judge unavailable live quality or pending documentation.
Ruling: latest-only recurrence erased corrected errors. Retain period-based historical observations across revisions, deduplicated per draft/type/status; latest check controls only the incomplete count. The new regression failed before the change. This trades a current-only compliance summary for useful historical recurrence; UI explicitly labels these observations.
Final reruns after the recurrence correction are pending below. No commits/push/deployment.


Final backend verification after recurrence correction: `npm run test:api` → **163 passed in25.74s**. `npm run build` → production compilation, TypeScript and routes passed. `.venv/bin/ruff check services/api evals/visual_metrics.py evals/visual_run.py` → all checks passed. `git diff --check` passed.
Second explicit route diagnostic: `nvidia/nemotron-3.5-super-vl:free` → HTTP404/no endpoint under strict free/ZDR/schema. These were both catalogue-compatible free vision candidates at probe time. `evals/reports/visual-second-route.json` records the second outcome. No privacy downgrade or paid route.
Mobile-specific new-panel browser extension is receiving its final run; no outcome claimed yet.


Final browser verification (after recurrence correction and EXIF fix): `npm run test:e2e:simple` → **26 checks passed**, including **8 selected axe scans, zero reported violations**. Tested desktop and390px insights with populated tables, visible mobile contrast/manual-reference controls, cited assistant answer and authority-request abstention, correction/recheck and separate-reviewer approval. Evidence: `.local/test-results/simple-workflow-browser.json`, `round3-insights.png`, `round3-insights-mobile.png`. Screenshots inspected for layout. No overall accessibility-certification or model-accuracy claim.
Final: all implementation tasks delivered locally with documented strict-vision fallback. Actual model agreement remains unmeasured (0/12). Independent human labels/real-image study remain outstanding. No deferred minor findings. No commit/push/deployment or changes to hosted runtime.

Final mobile visual QA: widened tables to preserve readable labels within keyboard-focusable local scroll regions. The existing390px browser assertion caught an intermediate grid min-content overflow; explicit zero minimum grid/panel sizing fixed it. Final `npm run test:e2e:simple` rerun passed26/26 with8 clean selected axe scans; mobile screenshot re-inspected. This was a layout-only fix after the163-test backend pass.

## 30 October 2026 — user-requested push and continuation

User explicitly requested “push and continue working”. Current branch is `prod`; its existing push workflow runs CI and production deployment. Push is authorised; prior instruction leaving Actions monitoring to the user remains in force. Fresh pre-push checks: backend163 passed in22.20s; production build/TypeScript and Ruff passed; diff whitespace check passed. No live deployment success is asserted. Continuing with vision-route eligibility and reproducible evaluation under the existing free/privacy constraints.

Continuation plan — 30 October: (1) add fail-closed published-endpoint preflight before vision inference, verify zero price/schema and exact ZDR endpoint identity, expose an on-demand metadata-only status check; (2) add synthetic pixel-based palette/contrast benchmark with independently specified labels and separate metrics from the blocked vision benchmark. Reuse existing stack, privacy and owner-consent gates. Add failing tests before implementation. Read-only endpoint investigation found both free image/schema candidates absent from the published ZDR list. No new inference request or company pixels sent during investigation.


30 October continuation: signed commit3d797a6 push to origin/prod succeeded. Added exact published ZDR endpoint/zero-price/schema preflight, metadata-only Settings check and separate local pixel benchmark. New regression tests were run failing first, then passed after implementation. Updated synthetic vision HTTP fixtures to include real metadata-shaped GET responses; UI test server now explicitly blocks live metadata requests.

Measured local benchmark: `PYTHONPATH=services/api .venv/bin/python -m evals.local_visual_run` →12/12 expected outcomes (8 contrast pairs,4 palette cases including1 expected transparency rejection). No model calls/accuracy claim. Published endpoint check report: both candidates blocked,0 omitted; no new inference/company pixels sent. Reports committed separately from the original0/12 model benchmark.

Independent read-only continuation review found no Critical issues. Two “minor” findings were treated as required reliability fixes because they could cause an error page or excessive buffering: malformed null endpoint parameters and response buffering before size enforcement. Regression tests reproduced TypeError and20 streamed chunks being consumed, then passed after field checks and streamed byte caps. Added a trickle-response deadline regression; it also passed after the shared endpoint-metadata deadline. Targeted vision/local-eval suite36 passed. No deferred minor findings.

Browser continuation verification: `npm run test:e2e:simple` →28 checks passed,9 selected axe scans with0 reported violations, including mobile Settings metadata-unavailable state. Existing correction/recheck/separate-human approval coverage passed. Final full-suite and production-build reruns follow below.


Final continuation: `npm run test:api` →174 passed in20.17s; production build/TypeScript passed; Ruff and diff checks passed. Browser28/28 with9 clean selected axe scans. Twelve local pixel-check expectations passed; model agreement remains unmeasured and both free candidates remain blocked by current published policy metadata. Signing/pushing the verified follow-up is authorised by the user's push/continue instruction. No Actions monitoring or verified hosted rollout claim.
