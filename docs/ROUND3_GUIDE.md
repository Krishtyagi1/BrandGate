# Round 3: visual review, finding explanations and insights

These changes run locally. They have not been deployed in this task.

## Visual review

Upload a static PNG/JPEG banner, poster or website screenshot. In Rules, an owner must confirm the logo references and usage guidance before they become authority. Use the existing explicit outbound preview/processing consent for external vision. The model route remains free-only, requires supported image/schema capabilities, and enforces the existing privacy policy. No downgrade or paid fallback was added.

When available, model observations identify a suspected old/different logo, placement or distortion, with a source and image rectangle. An outdated logo requires explicit source guidance: visual difference alone is insufficient proof of age. All observations remain advisory. A separate owner/reviewer can record a visual judgement and note; this leaves the AI finding unchanged and does not approve the draft.

**Working fallback:** open “Compare with current approved references” beneath the image. Inspect symbol, placement and proportions manually. Correct artwork outside the app, upload it again, recheck and use the existing separate-human approval flow. The references are from the current confirmed snapshot; historical reports remain pinned to their original evidence.

Open “Measure sampled colour contrast”, select foreground/background points by clicking or entering percentage coordinates, and calculate the ratio locally. Only opaque pixels are accepted. Coordinates follow displayed EXIF orientation, and original file hashes remain unchanged. Calculation and unrounded threshold comparison follow [W3C contrast guidance](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html). Text size, logo exceptions, gradients, anti-aliasing and actual foreground/background selection require human assessment. This is not automatic accessibility certification.

## Finding-scoped assistant

Open “Ask about this finding” and use “Why was this flagged?” or “How can I fix it?”. Answers quote exact approved excerpts from the finding's pinned source snapshot. Citations must match stored IDs, excerpts, locations and source identities. The current revision, guideline snapshot, task scope and latest review must still match.

The assistant is **local and extractive**, not a generative model. It supports the two named questions and a few equivalent phrases; it abstains on unsupported questions rather than inferring an answer. Missing evidence returns “not covered by the guidelines”. Citations are validated for identity/exactness; that does not prove a source substantively supports every original contextual observation. A person still evaluates that support.

Questions and answers are stored privately for organisation insights, with bounded length, rate limits and retry keys. No external AI call is made. Official AG-UI message events deliver the saved answer; interrupted streams fall back to the saved text. There are no assistant tools to edit, approve or activate anything. Corrections continue through the existing explicit rewrite/save/recheck workflow.

## Recurrence and guideline gaps

Owners/reviewers open Tracking → “Recurring issues & guideline gaps”. Creators retain their existing draft visibility; they cannot access organisation-wide insights. Choose the last 7, 30 or 90 days.

Each finding type/status is counted once per draft across reviews started in the reporting period, including earlier revisions and issues later corrected. Rechecking the same issue does not increase its count. Channel comes from recorded scope; campaign is optional current metadata. Incomplete checks and dismissed observations stay disclosed. The incomplete count uses each draft’s latest check within the period. Counts are observations, not creator performance scores. Multiple categories can overlap, so their totals need not equal the number of reviewed drafts.

Unverified quotes and unanswered assistant questions appear with links to underlying drafts. Questions use their own period-based denominator, include older revisions, and deduplicate repeated wording per draft. The latest 5,000 unanswered questions and the top 50 gap groups are shown; unsupported phrasing may cause abstention without proving a rule is missing. Owners decide what to add or clarify through the existing rule-confirmation workflow.

## Evaluation and current limits

Generate the twelve fictional image fixtures and run an explicitly bounded live probe:

```sh
PYTHONPATH=services/api .venv/bin/python -m evals.visual_run --live --limit 4
```

Without `--live`, generation/reporting makes no provider call. Images are reproducible under `.local/visual-eval`; the committed manifest contains hashes and developer labels. The report is `evals/reports/visual-round3.json`. The evaluator excludes unavailable/unrun cases from every agreement denominator, returning null when no comparison exists.

The 29 October 2026 selected-route probe returned no eligible endpoint for `dots-studio/dots-3-note-preview:free` under the strict request policy. **0/12 images evaluated; model agreement is unmeasured.** A separate explicit probe of `nvidia/nemotron-3.5-super-vl:free` also returned no endpoint; see `evals/reports/visual-second-route.json`. These were the two catalogue-compatible free image/schema models at probe time. Availability can change; this is not a general claim about future routes. Fixtures cover simple geometry, not natural backgrounds or independent human judgements. Real-image labels, successful live comparisons and independent human agreement remain future validation work.

Verification commands:

```sh
npm run db
npm run test:api
npm run test:e2e:simple
npm run typecheck
npm run build
.venv/bin/ruff check services/api evals/visual_metrics.py evals/visual_run.py
```

Browser fixtures use a separate synthetic test server/database and do not measure model accuracy. Actual outcomes are recorded in `docs/ROUND3_PROGRESS.md` and `docs/IMPLEMENTATION_STATUS.md`.
