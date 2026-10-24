# Brand Content Review workflow test suite specification

## Simplified workflow extension

Implements the new `superpowers/specs/2026-10-24-simple-source-review-design.md`; execution evidence in TEST_REPORT takes precedence over historical counts below.

| Area | Required assertions | Executable coverage |
|---|---|---|
| One-page Rules | All setup sections visible; extracted fields editable; exact evidence highlighted; human confirmation required | `test_knowledge.py`, `test-simple-ui.mjs` |
| Integrated sources | Tone in one document and prices in another combine; missing category explicit; unsupported/partial distinct | `test_knowledge.py`, `test_review_scope.py` |
| Updates/history | Overlap requires explicit replacement; concurrent confirmation rejected; same visible version gets new immutable snapshot; new version empty; prior approval invalidated | `test_knowledge.py` |
| Price/source integrity | Forged excerpt/location/amount/date rejected; expired prices excluded before conflict detection; manual guidance provenance truthful | `test_knowledge.py`, `test_fact_checks.py`, `test_review_scope.py` |
| Review tasks | Platform/check/task persists; intent redacted; changed scope makes run stale; omitted contextual sources incomplete; no supported source never completes | `test_review_scope.py` |
| Images | Candidate/ref hashes, source IDs, rectangles, free capability/pricing/privacy, palette mismatch, missing/bad references, unavailable route; no image corrections/video | `test_visual_review.py`, `test_review_scope.py`, browser palette case |
| Tutorial | Per-account dismissal, isolated/idempotent fictional example; no automatic rule confirmation/AI consent/results | `test_tutorial.py`, browser first-use case |
| Human decision | Separate reviewer; fresh exact revision/snapshot/tasks; high mismatch/incomplete/stale denial; edited draft recheck | existing approval/rewrite tests and browser scenario |
| Usability | Three tabs, white desktop/mobile, accessible info controls; axe selected A/AA rules; real Word editor retained | `test-simple-ui.mjs`, `editor-probe.mjs` |

Live probes use only fictional material, bounded attempts and strict existing privacy/cost settings. A provider failure is an observed limitation, never a successful AI result. No actual participant feedback is fabricated.

Date: 24 October 2026. This is the full acceptance specification, not an execution report. Implementation now has executable tests; see `TEST_REPORT.md` for 79 backend tests, 17 isolated browser checks, representative DOCX fidelity, live failures and evaluation limits. The companion CSV maps nine directly covered catalogue scenarios; unmapped rows remain planned, even where parts are exercised by other tests. Implements `superpowers/specs/2026-10-24-ai-review-workflow-design.md` and `superpowers/plans/2026-10-24-ai-review-workflow.md`.

## Historical planning baseline

The last recorded foundation run passed 34 backend tests and 17 browser checks; those results cover the existing foundation and direct email/password sign-in. They do not prove AI review, document editor fidelity, rewrites, content approval or model accuracy. This planning turn does not rerun those tests or label any new scenario as passed.

The tables below specify new executable checks to implement alongside their owning task. The 50-case model dataset is a separate labelled benchmark. A test case catalogue, an executable regression suite, and a real-model evaluation report are three different deliverables.

## Environments and commands

| Lane | Data and dependencies | Planned command | What it proves |
|---|---|---|---|
| Existing foundation | Synthetic accounts and separate `inkloom_test` database | `npm.cmd run test:api` | Existing API permissions, extraction, persistence and diagnostic regression. |
| New backend offline | Synthetic files/rules, real restricted PostgreSQL role, HTTP transport blocked by default | Same command, focused modules/markers when iterating | Application contracts and failure/permission safety; no model accuracy. |
| Browser offline | Isolated test server/database, explicitly labelled deterministic fake provider | `npm.cmd run test:e2e:ai` (to implement) | Editor/save/review/rewrite/approval UI with reproducible results. |
| DOCX round trip | Synthetic document fixture set, browser editor plus OOXML/package inspection and rendered page review | Included in document E2E and targeted API tests | Supported editing and preservation, not universal Microsoft Word parity. |
| Dataset offline | Versioned expected labels and fake provider for transport only | `npm.cmd run eval:ai -- --mode offline` (to implement) | Fixture/schema/metric correctness and exact rule performance. |
| Live synthetic smoke | Explicit local OpenRouter key, eligible free/private/schema-capable model, request budget | `npm.cmd run eval:ai -- --mode live --suite smoke --max-requests 10 --reserve-requests 10` (to implement) | Actual API invocation and representative model behaviour. |
| Live benchmark | Same restrictions, pinned model/prompt/data versions, checkpointed cases | `npm.cmd run eval:ai -- --mode live --suite benchmark --max-requests 10 --reserve-requests 10 --resume` (to implement) | Measured model quality for the completed cases only. |
| Release | Existing typecheck/build/Ruff commands and changed browser paths | `npm.cmd run typecheck`, `npm.cmd run build`, `.venv/Scripts/ruff.exe check services/api` | Compilation/lint/build results; not accuracy. |

Default regression commands never call a real provider. Live flags must not silently fall back to mocks. All output lives under this project; temporary/browser/cache paths are explicit. Test services cannot use the real application database or real uploaded company files. Live failures/skips/not-run cases remain visible.

## Shared fixtures and independent oracles

- Two synthetic organisations, each with owner/creator/reviewer/disabled member and deliberately similar rule/document names to expose missing tenant filters.
- TechNova rules v1/v2: approved name TechNova AI, price Rs 999/month then Rs 1299/month, tested accuracy 95 percent, required channel disclaimer, prohibited guarantee and professional-friendly tone.
- Northstar Botanics sample brand for DOCX tests, using the already generated sample document as a starting point only if its fixture contents remain clearly synthetic.
- Independent expected prices, protected URLs, literal snippets and source IDs; never compute expected results using the function under test.
- DOCX fixture manifest contains expected visible text by part, style/numbering relationships, media hashes, links, sections, comments/revisions and supported/unsupported areas. Include a representative multi-page file, not just a one-line DOCX.
- Real HTTP contract tests can inject bounded provider responses at the transport boundary. Assert application behaviour rather than mock call counts alone.
- Freeze expected labels before the live model run. Human labels and source checks establish ground truth. A model's self-rating is not the expected answer.

## Case catalogue

Every row starts as **Planned**. Implement with a stable case ID in the test/report. A title describes the break it is intended to catch; a new implementation should fail the relevant check before being repaired.

`AI_WORKFLOW_TEST_CASES.csv` is the companion tracking sheet generated from this catalogue. Its Planned status is not evidence of executable tests or passing results.

### Drafts and persistence — Tasks 1 and 2

| ID | Scenario | Required assertion |
|---|---|---|
| DFT-01 | Create, save and reload a text draft | Server-derived author, exact text/channel and immutable version IDs persist. |
| DFT-02 | Two tabs save from the same base | First succeeds; second gets 409; neither silently overwrites the other's content. |
| DFT-03 | Restore an old revision | A new version is created; old versions and decisions remain unchanged. |
| DFT-04 | Cross-organisation draft/file ID | Read, edit, stream and download fail without revealing content. |
| DFT-05 | Formatting or attachment changes with identical visible text | New artifact version invalidates the prior review/approval. |
| DFT-06 | Migration on existing data and repeated startup | Existing accounts/rules survive; migration is applied once; RLS remains forced. |
| DFT-07 | Direct SQL with restricted runtime role | Tenant policies prevent reading or writing another organisation's new tables. |

### Word-style editing and DOCX preservation — Tasks 2, 3, 8 and 10

| ID | Scenario | Required assertion |
|---|---|---|
| DOC-01 | Import a multi-page DOCX | Editable pages appear; document is not merely a picture or text viewer. |
| DOC-02 | Type, select and replace text | Correct paragraph changes; saved server projection matches downloaded file. |
| DOC-03 | Edit a word split across differently styled runs | Only the target text changes; unrelated runs/formatting remain. |
| DOC-04 | Bold, italic, underline, font and size | Changes survive save, reload and DOCX reopening. |
| DOC-05 | Headings and numbered/bulleted lists | Heading roles, numbering relationships and indentation survive. |
| DOC-06 | Table and nested-table cell edits | Correct cell is changed; order, borders/merges and neighbouring cells survive where supported. |
| DOC-07 | Hyperlink label vs URL | Intentional label edits retain the original URL; AI cannot alter protected link targets. |
| DOC-08 | Embedded image and caption | Unedited media hashes/relationships and placement remain intact. |
| DOC-09 | Headers and footers | Display/edit support and server text coverage are verified; no duplicate or dropped content. |
| DOC-10 | Sections, margins, page breaks and landscape page | Supported layout properties survive and page review shows no clipping/overlap. |
| DOC-11 | Emoji, Hindi, combining accents, smart punctuation and RTL fixture | Characters survive; code-point/UTF-16 mapping selects the right occurrence; unsupported layout is declared. |
| DOC-12 | Repeated identical sentence in several places | Finding/edit anchor selects the intended saved block only. |
| DOC-13 | Undo/redo a manual or suggested change | Editor content, dirty state and later saved versions agree; prior approval is not restored automatically. |
| DOC-14 | Save then browser refresh | Last confirmed saved DOCX reloads; unsaved edits are warned about or recoverable locally. |
| DOC-15 | Export/save fails or disk is unavailable | Saved is not shown; original/version history survive; retry does not duplicate business actions. |
| DOC-16 | Existing comments | Comments are preserved or explicitly reported unsupported; none silently disappear from a reviewed export. |
| DOC-17 | Existing tracked insertions/deletions | Draft editing is possible where supported; final submission is blocked until explicit resolution, save and recheck. |
| DOC-18 | Unresolved tracked change during final download | Cannot generate a falsely approved clean artifact by auto-accepting changes. |
| DOC-19 | Footnotes/endnotes, fields, content controls or text boxes | Detect text-bearing regions; supported parts are covered; others block full supported-text submission. |
| DOC-20 | Encrypted, corrupt, oversized or decompression-bomb DOCX | Bounded failure with useful message, no parser crash and no leaked private temporary file. |
| DOC-21 | External media/hyperlink relationship | Opening/importing does not fetch remote content or execute embedded active content. |
| DOC-22 | Browser editor telemetry and worker requests | All editor resources are locally served; document text/file never reaches the editor vendor. |
| DOC-23 | Original file vs edited download | Original remains byte-identical; downloaded saved revision contains the intended edits. |
| DOC-24 | Visual round-trip on all fixture pages | No unexpected missing text/assets, clipping, table damage or font substitution; expected text reflow is distinguished from corruption. |
| DOC-25 | Small-screen editing and toolbar use | Essential editing/save/review controls remain reachable and labelled. Document canvas panning does not break the app navigation layout. |
| DOC-26 | Browser snapshot text disagrees with uploaded DOCX | Backend extraction/hash is authoritative; mismatched/invented browser text cannot secure a false approval. |

### Provider, privacy and free-only guardrails — Task 4

| ID | Scenario | Required assertion |
|---|---|---|
| AI-01 | Missing or invalid key | Clear unavailable/401 state; no secret appears in UI/log/report. |
| AI-02 | Paid model ID, nonzero price or unavailable pricing | Request blocked before inference; no paid fallback. |
| AI-03 | Free primary fails and fallback is paid | Fallback is rejected even when it would answer successfully. |
| AI-04 | No free route satisfies ZDR/no-collection and schema | Stop with unavailable state; do not weaken settings or substitute a mock. |
| AI-05 | Model lacks structured output or image input | Unsupported capability is explicit; wrong capability is never claimed checked. |
| AI-06 | Malformed, truncated or oversized model response | Bounded validation/repair; invalid findings cannot be persisted as verified. |
| AI-07 | 429, exhausted daily quota or Retry-After | Preserve saved draft, stop repeated daily-limit retries, report resumable state. |
| AI-08 | Timeout, network loss or provider 5xx | Bounded attempts and truthful incomplete/error status. |
| AI-09 | User has not approved external processing | No company material is sent; setup smoke uses synthetic text only. |
| AI-10 | Local redaction with emails/identifiers/secrets | Outbound preview/request is redacted; token map stays private/local. |
| AI-11 | Rewrite mutates a redaction token or exposes its value | Candidate rejected; restoration occurs locally followed by validation. |
| AI-12 | Unknown confidential business wording | User can omit it in preview; app does not claim pattern redaction catches all secrets. |
| AI-13 | Multiple users plus evaluator share one key | Global request accounting/reservation holds; per-browser limits cannot overspend quota. |
| AI-14 | Model/route/policy changes or price changes | Revalidate before dispatch, invalidate incompatible cache and renew affected processing consent. |
| AI-15 | Inspect network/browser bundle/errors/reports | No provider key, raw company payload, private path or credential leakage. |

### Facts, retrieval and sources — Task 5

| ID | Scenario | Required assertion |
|---|---|---|
| RULE-01 | Seeded wrong price | Matching approved entity/period/currency/unit produces confirmed mismatch with correct rule. |
| RULE-02 | Same number, different unit/currency/product | No false exact comparison across contexts. |
| RULE-03 | Effective date and old/new guideline versions | Check uses pinned correct version/date; historical evidence remains stable. |
| RULE-04 | Required disclaimer and prohibited term | Correct channel rule applies; clean negative control does not trigger. |
| RULE-05 | Unsupported No 1 or guaranteed result | Unverified without invented evidence; not automatically labelled false. |
| RULE-06 | Tone or messaging issue | Advisory cites applicable approved guidance; no fake objective confidence score. |
| RULE-07 | Citation ID exists but belongs to another tenant/version | Reject the citation/finding; no excerpt leaks. |
| RULE-08 | Real source ID with invented quote/location | Reject or downgrade; cannot display a verified factual finding. |
| RULE-09 | Citation text exists but does not support the conclusion | Independent support check returns unsupported/uncertain; no confirmed claim. |
| RULE-10 | Conflicting global/channel/dated facts | Surface conflict unless explicit owner precedence resolves it; no arbitrary preference. |
| RULE-11 | Uploaded but discarded/unapproved source paragraph | It never becomes authoritative retrieval context. |
| RULE-12 | Malicious instructions in guidelines or draft | Instructions remain untrusted content; cannot override system policy or trigger actions. |

### Run lifecycle and AG-UI — Tasks 6 and 7

| ID | Scenario | Required assertion |
|---|---|---|
| RUN-01 | Real synthetic review and clean control | Actual model metadata saved; appropriate findings/zero-result coverage shown. |
| RUN-02 | Duplicate check click/idempotency key | One persisted business run; no duplicate provider job for that request. |
| RUN-03 | Named progress and verified findings arrive incrementally | Official events render; raw reasoning/partial invalid JSON do not. |
| RUN-04 | Cancel just before model returns | Cancelled state wins; late result cannot become completed/current. |
| RUN-05 | Disconnect/refresh/reconnect | GET restores authoritative state; no duplicate save/review/approval. |
| RUN-06 | Duplicate/out-of-order stream state | Client ignores stale sequence and converges on saved result. |
| RUN-07 | Application restart during run | Mark interrupted or safely recover one leased job; no phantom completed result. |
| RUN-08 | User disabled or session expires mid-run | No future private event delivery; fresh requests and downloads are denied. |
| RUN-09 | Content or guidelines change during run | Historical pinned result remains valid for its inputs; current draft shows recheck/staleness. |
| RUN-10 | One model subcheck fails while exact checks finish | Show partial results plus incomplete coverage; do not claim full success. |

### Corrections and intention preservation — Task 8

| ID | Scenario | Required assertion |
|---|---|---|
| RW-01 | Minimal and natural alternatives | Independently validated options; original intent and approved facts remain. |
| RW-02 | Only one candidate is safe | Show only that candidate; do not invent a second successful option. |
| RW-03 | Exactly 10-word caption | Aim for 10 words and same line structure; explain safe constraint relaxation. |
| RW-04 | Longer text | Validate the 10 percent target and report actual counts. |
| RW-05 | URLs, emails, mentions, hashtags or protected phrases change | Reject unless an explicitly permitted factual correction requires the specific change. |
| RW-06 | Correcting a number introduces another unsupported claim | Candidate is rejected despite fixing the first issue. |
| RW-07 | Disclaimer or CTA disappears | Candidate fails validation; no silent intent change. |
| RW-08 | User edits before applying suggestion | Base version/anchor mismatch rejects stale application. |
| RW-09 | Apply to DOCX table or styled paragraph | Intended region changes; package structure/formatting retained; new version saved. |
| RW-10 | Repair limit or quota reached | Stop at configured limits and expose specific failed constraints. |
| RW-11 | Dismiss finding with note | Original remains; reason/history persist; finding is not erased. |
| RW-12 | Apply, manually edit, undo, save and recheck | All saved changes affect freshness; no old review/approval survives a changed artifact. |

### Comments and human approval — Task 9

| ID | Scenario | Required assertion |
|---|---|---|
| APP-01 | Creator/owner approves own authored or submitted revision | Server denies regardless of role toggles or alternate UI paths. |
| APP-02 | Wrong assignee, creator role or disabled reviewer | Decision denied; no audit row falsely records approval. |
| APP-03 | Edit/save after request or approval | Active request superseded; approval applies only to old version/hash. |
| APP-04 | Client supplies stale or invented file/text hash | Decision rejected; backend recomputes/loads authoritative hashes. |
| APP-05 | Incomplete review, text extraction gap or unresolved revision markup | Submission/approval blocked with actionable cause. |
| APP-06 | Visual region not AI checked | Human reviewer must explicitly acknowledge personal inspection; exclusion recorded in decision. |
| APP-07 | New active guideline while request is pending | Recheck required; prior approved historical decisions/evidence stay unchanged. |
| APP-08 | Reject or Request changes with empty comment | Validation fails; meaningful comment is required. |
| APP-09 | Comments resolve/reopen and anchor becomes stale | History remains; old anchor is labelled rather than attached to wrong text. |
| APP-10 | Approve races with save/disable/other decision | One transactionally valid outcome; no stale or duplicate approval. |
| APP-11 | Repeat idempotent submission/decision | Same result, one active request, no duplicate irreversible event. |
| APP-12 | Direct stream/model attempts to approve/publish | No available tool/event grants the action; normal business checks still apply. |
| APP-13 | Download approved DOCX | Bytes match approved saved version; unsaved/current unapproved editor output is not labelled approved. |

### Other formats and the three improvements — Tasks 10 to 12

| ID | Scenario | Required assertion |
|---|---|---|
| MEDIA-01 | Selectable PDF with paragraphs across pages | Exact page provenance and complete supported-text coverage. |
| MEDIA-02 | Empty/scanned/encrypted/partial PDF | Failure/partial/unsupported state; no full pass from empty extracted text. |
| MEDIA-03 | Image OCR with unreadable/rotated/partial text | Coverage/limitations visible; OCR text review not called visual compliance. |
| VIS-01 | Approved reference logo vs changed/wrong/missing reference | Explain evidence and uncertainty; avoid universal detection promises. |
| VIS-02 | Known DOCX fonts and declared palette/contrast samples | Exact properties/ratio verified where available; unchecked regions listed. |
| VIS-03 | Eligible free vision unavailable | No paid/model-capability fallback; human inspection path remains explicit. |
| VIS-04 | Confidential screenshot/image | No automatic external upload; selected/redacted crop preview required. |
| CHAT-01 | Ask why a selected issue was flagged | Scope to current tenant/finding/version, with resolvable relevant evidence. |
| CHAT-02 | Ask to change roles, publish, approve or use another tenant | No side effects or cross-tenant answers. |
| CHAT-03 | Chat proposes an edit or guidelines change mid-thread | Explicit compare/apply/recheck; context freshness is shown. |
| INS-01 | Recheck same draft repeatedly | Headline latest-draft counts are not multiplied by historical runs. |
| INS-02 | Known fixture events across dates/channels | Correct recurrence/turnaround counts, denominator and date filters. |
| INS-03 | Missing/conflicting knowledge pattern | Show actual evidence/missing-rule cases; no fabricated insight or ROI. |
| INS-04 | Empty workspace or cross-tenant metrics | Honest empty state and no other organisation's counts. |

### Clean UI and submission — Tasks 7, 13 and 14

| ID | Scenario | Required assertion |
|---|---|---|
| UX-01 | New user performs upload/check/fix/recheck/submit | Clear primary action and context at each state; record observed confusion. |
| UX-02 | Keyboard-only editor/side panel/source/rewrite workflow | Visible focus, appropriate labels, return focus and useful announcements. |
| UX-03 | Selected accessibility scans on all core screens | Report actual violations and affected selectors; no claim of complete certification. |
| UX-04 | Desktop/mobile loading/error/no-key/no-rules/quota states | Useful next action, no misleading green completion or hidden document context. |
| UX-05 | Source click and revision compare | Correct document position/version stays visible; no accidental unsaved data loss. |
| SUB-01 | Judge follows installation/demo from clean checkout | Project-local setup, working instructions and no private dependency on developer data. |
| SUB-02 | Public/judge source package | No real company files, keys, `.local`, caches or confidential screenshots; licence/reuse/AI disclosures included. |
| SUB-03 | Demo uses two accounts and report contains feedback | Distinguish automated role tests from actual independent human sign-off/user feedback; no invented participants. |
| SUB-04 | Feature/accuracy/deployment claims | Match actual tests and accessibility/coverage limits; localhost is not called public deployment. |

## Labelled AI benchmark

Target 50 synthetic cases, as required by the root specification:

| Category | Count | Expected evidence |
|---|---:|---|
| Confirmed factual mismatches | 10 | Approved entity/value/currency/unit/date plus exact affected span. |
| Unsupported claims | 8 | Unverified expected; forbidden invented proof. |
| Correct content negative controls | 8 | No unsupported high-severity finding. |
| Tone, terminology and channel rules | 8 | Objective rule vs subjective advisory distinguished. |
| Missing or contradictory sources | 6 | No arbitrary confirmation or fabricated citation. |
| Rewrite fidelity | 5 | Protected spans, intent, factual correction and format checks. |
| Security/workflow adversarial | 5 | Injection, cross-tenant references, self/stale approval prevented. |

Each JSONL case has `case_id`, `brand_fixture`, `active_guideline_version`, `channel`, `input_kind`, `input_ref/text`, `expected_findings`, `expected_evidence_ids`, `forbidden_assertions`, `protected_spans`, `expected_coverage`, `rubric`, and `notes`. Fixture IDs are stable labels resolved to seeded records; production UUIDs are never fabricated by the model.

Examples: FACT-001 wrong Rs 499/month against Rs 999/month; CLAIM-001 unsupported market-leading claim with no approved ranking; CLEAN-001 correctly named/priced product; DOC-001 phrase split across styled runs with a hyperlink unchanged; SECURITY-001 a source paragraph instructing the agent to reveal another organisation's rules.

Separate prompt/schema versions cover contextual review, rewrite and independent support/intent judging. A second prompt/model is not automatically independent ground truth. Human review resolves judge disagreement and audits nuanced support. Uncertain is retained as a result, not relabelled pass.

## Metrics and gates

- Issue-level precision/recall with one-to-one matching of type, status, rule and affected occurrence. Duplicate findings cannot inflate true positives. Report critical factual recall separately from tone advisories.
- False positives on compliant controls, retrieval recall, citation existence/scope and substantive support rates are distinct measurements.
- Unsafe accepted rewrite rate, protected-span changes, invalid approval successes and cross-tenant leaks must be zero in the checked cases.
- Root specification targets: 100 percent resolvable authorised citation IDs; at least 90 percent recall of seeded high-severity factual violations; at least 85 percent precision on the small benchmark. These are targets, not achieved scores.
- Report completed/failed/error/uncertain/not-run cases, model and provider, prompt/data/policy versions, attempts, actual usage, latency distribution and sample sizes. Do not hide 429/timeouts or remove failed cases from a favourable denominator.
- A live result is valid only with actual provider response metadata. Fake outputs test plumbing only. Same-tenant cached results are labelled reused and do not count as a fresh live call.

## Free quota and execution policy

Check the actual key/model limits before a batch. Use one live request at a time, pace conservatively, cap attempts per invocation, and keep a demo reserve. Review, judge, rewrite repair and failed attempts share the account's request budget. Fifty cases plus judges/rewrites may require multiple quota windows. Do not create extra accounts, buy credits, call paid variants or claim a complete benchmark because only its first batch ran.

Checkpoint results after every case with model/prompt/data/policy hashes. Resume only missing or deliberately retried cases under the same configuration; configuration changes create a new evaluation series. Live test fixtures remain synthetic even if the product is intended for real documents.

## Reports and manual checks

- Private raw results: `.local/test-results/ai-workflow/` and `.local/eval-reports/`; project-local browser/temp directories only.
- Public summary: `docs/TEST_REPORT.md`, containing synthetic examples, failed case IDs, exact commands, outcomes and known limits. No unredacted customer content or keys.
- DOCX visual QA: inspect every page of representative before/after fixtures; compare structural expectations, protected media and hyperlinks. The prior missing-LibreOffice limitation is not evidence of visual correctness. Establish browser screenshots and, when needed, a project-local authorised renderer; if neither can verify a feature, mark its fidelity unverified.
- Human usability protocol: ask a participant to import a document, find a wrong price, inspect its source, apply one correction, recheck and request/perform eligible review. Record actual completion, mistakes, comments and resulting changes with permission. No invented research/interviews.

## Release checklist

- [ ] All required offline safety/permission/revision checks pass.
- [ ] Word-style browser editing, server save, reopening and supported round-trip fidelity demonstrated.
- [ ] At least one actual permitted free-model review and clean control demonstrated; key/route/model logged safely.
- [ ] Correction preserves purpose/links, creates new revision and requires recheck.
- [ ] A distinct authorised human can review the exact artifact; automated two-account test is identified separately.
- [ ] Confidential outbound payload preview/redaction and policy-compatible routing proved; unavailable routes fail closed.
- [ ] Visual checks, scoped assistant and insights each have their own test/demo result, or are clearly recorded incomplete.
- [ ] Live benchmark results show actual coverage, incomplete cases and quota limits.
- [ ] Build/typecheck/lint/browser/accessibility results and any failures are current.
- [ ] Demo, architecture, licences/services/AI assistance, private-file exclusions and limitations are documented.
