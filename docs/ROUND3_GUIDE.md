# Round 3: visual review, finding explanations and insights

Source is pushed to `prod`. The existing workflow handles deployment; hosted rollout has not been verified in this chat.

## Visual review

Upload a static PNG/JPEG banner, poster or website screenshot. In Rules, an owner must confirm the logo references and usage guidance before they become authority. Use the existing explicit outbound preview/processing consent for external vision. The model route remains free-only, requires supported image/schema capabilities, and enforces the existing privacy policy. No downgrade or paid fallback was added.

When available, model observations identify a suspected old/different logo, placement or distortion, with a source and image rectangle. An outdated logo requires explicit source guidance: visual difference alone is insufficient proof of age. All observations remain advisory. A separate owner/reviewer can record a visual judgement and note; this leaves the AI finding unchanged and does not approve the draft.

**Working fallback:** open “Compare with current approved references” beneath the image. Inspect symbol, placement and proportions manually. Correct artwork outside the app, upload it again, recheck and use the existing separate-human approval flow. The references are from the current confirmed snapshot; historical reports remain pinned to their original evidence.

Open “Measure sampled colour contrast”, select foreground/background points by clicking or entering percentage coordinates, and calculate the ratio locally. Only opaque pixels are accepted. Coordinates follow displayed EXIF orientation, and original file hashes remain unchanged. Calculation and unrounded threshold comparison follow [W3C contrast guidance](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html). Text size, logo exceptions, gradients, anti-aliasing and actual foreground/background selection require human assessment. This is not automatic accessibility certification.

## Finding-scoped assistant

### Document AI chatbot (30 October addition)

In a current review, open **Ask about this document**. Choose **Why was this document flagged?**, ask what to fix first, or type a follow-up. **Discuss in document chat** on a finding prefills a question about that issue. Inspect the redacted payload, then choose **Send question to AI**. Your configured provider generates an explanation; numbered source details show exact server-validated approved excerpts. Missing evidence stays unverified. Answers do not change the document or its approval state.

Questions/answers are private to you and that review and survive reload. Only the last six successful turns go to the model; the latest 30 requests are shown. A new revision or source/scope change requires a fresh review and conversation. Oversized context is rejected rather than silently omitting findings. Provider failures show errors, and saved answers can recover from interrupted streams. Existing owner AI consent, model availability, pricing/privacy settings and request caps apply. Citation checks do not guarantee every generated explanation is correct; assess the source support yourself.

### Local helper retained

Open “Ask about this finding” and use “Why was this flagged?” or “How can I fix it?”. Answers quote exact approved excerpts from the finding's pinned source snapshot. Citations must match stored IDs, excerpts, locations and source identities. The current revision, guideline snapshot, task scope and latest review must still match.

The assistant is **local and extractive**, not a generative model. It supports the two named questions and a few equivalent phrases; it abstains on unsupported questions rather than inferring an answer. Missing evidence returns “not covered by the guidelines”. Citations are validated for identity/exactness; that does not prove a source substantively supports every original contextual observation. A person still evaluates that support.

Questions and answers are stored privately for organisation insights, with bounded length, rate limits and retry keys. No external AI call is made. Official AG-UI message events deliver the saved answer; interrupted streams fall back to the saved text. There are no assistant tools to edit, approve or activate anything. Corrections continue through the existing explicit rewrite/save/recheck workflow.

## Recurrence and guideline gaps

### Tracking review overview (30 October addition)

Tracking opens with current results and flags, pending approvals and incomplete/outdated checks. Click a count or category/severity/status bar to filter its document list. Use **Reset dashboard filters** or **Refresh dashboard** as needed. High-severity filters match the same finding as the chosen category/status. Dismissed observations have their own count. The existing saved-work list below retains its independent search/approval queue.

Current totals use the latest review per document and exclude stale flags and rewrite runs. Completed checks do not guarantee compliance. Activity uses review runs started in the chosen 7/30/90-day period, including rechecks, with UTC day labels. Current totals cover all authorised documents regardless of the activity period. Creators see their own documents; owners/reviewers see the organisation overview. Historical **Recurring issues & guideline gaps** remains a separate report.

Owners/reviewers open Tracking → “Recurring issues & guideline gaps”. Creators retain their existing draft visibility; they cannot access organisation-wide insights. Choose the last 7, 30 or 90 days.

Each finding type/status is counted once per draft across reviews started in the reporting period, including earlier revisions and issues later corrected. Rechecking the same issue does not increase its count. Channel comes from recorded scope; campaign is optional current metadata. Incomplete checks and dismissed observations stay disclosed. The incomplete count uses each draft’s latest check within the period. Counts are observations, not creator performance scores. Multiple categories can overlap, so their totals need not equal the number of reviewed drafts.

Unverified quotes and unanswered assistant questions appear with links to underlying drafts. Questions use their own period-based denominator, include older revisions, and deduplicate repeated wording per draft. The latest 5,000 unanswered questions and the top 50 gap groups are shown; unsupported phrasing may cause abstention without proving a rule is missing. Owners decide what to add or clarify through the existing rule-confirmation workflow.

## Vision preflight and local pixel benchmark (30 October follow-up)

In Settings → AI processing & privacy → Vision route availability, “Check vision availability” fetches public model/endpoint metadata only. No draft, source or image is included. Before real inference, the selected vision model must have an exact model/provider/tag match in OpenRouter’s published ZDR endpoint list, with endpoint-level zero prices and schema parameters. The existing runtime routing policy, owner consent and outbound preview still apply; passing metadata does not prove an inference route works.

The check inspects at most sixteen catalogue-compatible candidates, with streamed 5 MB response caps, ten-second endpoint inactivity timeouts and a shared 30-second endpoint-metadata deadline after the existing model-catalogue lookup. Unknown/malformed metadata fails closed. A metadata refresh may still be needed when endpoint policies change. This is an additional conservative gate and can abstain if the published list is incomplete. Official interfaces: [model endpoints](https://openrouter.ai/docs/api/api-reference/endpoints/list-all-endpoints-for-a-model) and [ZDR policy/list](https://openrouter.ai/docs/guides/features/zdr).

The 30 October read-only probe found both free catalogue-compatible image/schema models absent from the published ZDR list; `evals/reports/vision-endpoint-preflight.json` records that evidence. No inference was retried and no privacy setting changed.

Run the independent **code-check** regression benchmark:

```sh
PYTHONPATH=services/api .venv/bin/python -m evals.local_visual_run
```

It checks eight known opaque contrast pairs (including near-threshold controls) and four dominant-palette cases, including one expected transparent-image rejection. Current measured result: **12/12 expected outcomes**. This is a tiny synthetic deterministic benchmark, not AI accuracy, automatic text detection, real-image coverage or independent human agreement. See `evals/fixtures/visual_local_cases.jsonl` and `evals/reports/visual-localchecks.json`. The original model benchmark remains 0/12 evaluated.

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
