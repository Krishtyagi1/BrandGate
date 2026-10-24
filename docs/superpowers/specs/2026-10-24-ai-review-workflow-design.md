# Inkloom AI review and document workflow design

Date: 24 October 2026, Asia/Calcutta. Status: proposed design for review. Companion implementation plan: `../plans/2026-10-24-ai-review-workflow.md`. Companion test specification: `../../AI_WORKFLOW_TEST_PLAN.md`.

## Intended result

A creator opens text, an image, a PDF or a Word document, checks it against owner-approved company rules, understands cited findings, chooses or edits corrections, saves a new revision, rechecks and requests another authorised person's approval. The product records exactly what was checked, what changed and what was approved. DOCX users edit in a Word-style browser interface and download the saved DOCX with its supported document structure retained.

The existing `INKLOOM_CODEX_IMPLEMENTATION_PLAN.md` remains the product source of truth. This design adds implementation detail and the user's decisions. No section describes new functionality as already implemented.

## Confirmed decisions and constraints

| Decision | Requirement |
|---|---|
| Provider and cost | OpenRouter free models only. No paid fallback, paid plugins, credit purchase or automatic upgrade. |
| Materials | Real company materials; local storage/editing and minimum necessary external AI processing. No claim that external free inference guarantees confidentiality. |
| Documents | Full Word-style browser editing and DOCX download; retain formatting, tables, images, headers, footers and supported review markup. Normal text reflow is expected. |
| Editor licensing | User accepts a compatible open-source application license. Evaluate and pin SuperDoc's actual package license; preserve required notices and source obligations. |
| Usability | Cleanest practical UI while retaining document, evidence, revision and approval context. |
| Deadline | Submission tonight, with only a few hours available. Exact cutoff was not provided; schedule uses relative effort boxes and executable gates. |
| Existing sign-in | Keep email/password sign-in without a verification code, as already requested. |
| Workspace | Every created/modified file, cache, dependency, report and temporary file stays under this project directory. No parent Git repository changes. |
| Scope | Complete the core workflow first, then the three named improvements: visual checks, source-aware follow-up, governance insights. |

No participant names or individual contributions are invented. Submission evidence must use the organiser's required truthful format when prepared.

## Starting point inspected

- Working foundation: Next.js 16.4.2, React 19.2.0, TypeScript; FastAPI, PostgreSQL, Pydantic, LangGraph and official AG-UI SDKs.
- Account/session, organisation, invitation and role APIs; PostgreSQL RLS; append-only audit records.
- Private PDF/DOCX guideline uploads, bounded extraction, manual/source-backed rules, owner approval, activation and archived versions.
- Current source extraction proposes text sections deterministically. It is not semantic AI extraction.
- Current `streaming.py` is a diagnostic only. Review editor, draft records, retrieval, model adapter, actual findings, rewrites, content approvals, insights and DOCX browser editing are absent.
- Historical foundation verification: 34 backend tests and 17 browser checks after sign-in simplification. These establish no AI accuracy. No tests were rerun merely to write this plan.
- Current DOCX extraction loses layout context. It cannot be reused as the Word editor's document representation. The packaged DOCX renderer previously failed because LibreOffice is unavailable; browser round-trip and visual QA must be established for the new editor.

## Product research and interpretation

Research checked 24 October 2026. These are public product descriptions, not access to competitors' implementation.

| Official source | Verified public behaviour | Inkloom decision |
|---|---|---|
| [Frontify Brand Assistant](https://help.frontify.com/en/articles/14718123-brand-assistant-in-guidelines) | Guideline-text retrieval, source references and permission-scoped answers; documents describe text-only limitations. | Retrieve approved text within the current organisation/version. Make source excerpts inspectable. Scope follow-up to the finding and its sources. |
| [Frontify approvals](https://help.frontify.com/en/articles/4111876-feedback-and-approval-process) | Named reviewers, revision settings and approval history. | One explicit reviewer first; bind decisions to saved revisions and retain superseded requests in history. Never adopt automatic deadline approval. |
| [Frontify publication revisions](https://help.frontify.com/en/articles/4768116-create-approvals-approve-publications) | Editing approved work requires approval again. | Any saved text, formatting or attachment change invalidates the current approval. |
| [Frontify Specs experiment](https://www.frontify.com/en/kitchen/brand-check-with-specs-the-reviewer-that-knows-your-guidelines) | Describes reference-aware visual/copy review; explicitly still in development. | Inspiration for a scoped review panel, not evidence that comprehensive visual compliance is solved. |
| [Adobe AI Reviewer](https://experienceleague.adobe.com/en/docs/workfront/using/review-and-approve-work/document-reviews-and-approvals/wf-ai-reviewer) | Separates AI recommendations from the human decision and publishes evaluation limits. | List supported/unchecked areas and preserve human sign-off. Avoid a universal compliance percentage. |
| [SuperDoc Editor](https://docs.superdoc.dev/editor/) | Browser DOCX editing uses OOXML-backed state without requiring its own server; AGPLv3 community licensing. | Proposed Word-style editor, self-hosted assets and workers, telemetry disabled. Prove fidelity on fixtures before accepting the integration. |
| [SuperDoc export](https://docs.superdoc.dev/editor/export-options/) | DOCX export returns bytes or downloads; export is separate from saving and has review-markup limitations. | Backend-confirmed save is authoritative. Export success is not approval, and options must be checked against the pinned release. |

### Approaches considered

1. **One prompt plus a plain text editor:** quickest wiring but loses document structure and cannot enforce reliable evidence or approval safety; fails this brief.
2. **Existing backend plus scoped retrieval/checks and a browser DOCX editor:** recommended. Reuses the foundation and supports the requested workflow without a separate document service.
3. **ONLYOFFICE-style document server plus a larger orchestration stack:** potentially suitable for a later deployment, but introduces infrastructure, storage callbacks and service operations within tonight's limited window. [Official architecture](https://api.onlyoffice.com/docs/docs-api/get-started/how-it-works).

The hybrid review architecture was already selected by the root specification. SuperDoc is the proposed editor; compatibility is a first execution gate, not an assumed success.

## The simple interface

Keep the existing palette: paper `#F6F8FC`, white `#FFFFFF`, ink `#162841`, indigo `#4546B8`, teal `#167569`, border `#E0E6EF`. Use the existing local Segoe UI/Calibri controls and a restrained heading scale. No new marketing hero or decorative dashboard tiles.

Five primary destinations remain Overview, Brand knowledge, Content, Approvals and Activity. Settings stays secondary. Insights initially fits inside Overview; no extra navigation overload.

```text
Brand / current organisation              role / account
Document title       Saved revision 3     Check content   Send for review
--------------------------------------------------------------------
Compact document toolbar                Findings | Comments | History
                                        2 issues need attention
Word pages or pasted text               Exact phrase and plain reason
                                        Source and guideline version
                                        Minimal fix | Natural fix
                                        Compare / Apply / Dismiss
--------------------------------------------------------------------
Draft revision 3    Checked with rules v2    Download saved DOCX
```

- Text mode uses a simple editor; DOCX mode uses genuine editable document pages. File format is an input choice, not another product section.
- Preserve the document position when inspecting a finding. Highlight and scroll to a stable document anchor; never move to a disconnected chat screen.
- One visible primary action changes with state: Check content, Recheck changes, then Send for review. Save state is always visible.
- Findings show status text, severity, exact affected content, reason and verified source. Optional detail expands in place.
- Rewrite comparison is inline. Show two safe options when available, changed wording and protected links/phrases. Applying requires a deliberate click.
- Comments and revision comparison share the side panel. Approval controls appear for the assigned authorised reviewer only, while the backend enforces access.
- Mobile uses Document, Findings and History tabs with a compact action bar. Basic document editing must remain usable without rendering both columns side by side.
- Important states: no active rules, no key, no eligible free route, quota exhausted, incomplete extraction, stale findings, saving conflict, failed save/export, interrupted review and no eligible second reviewer.
- No fake findings, placeholder counts, model confidence presented as accuracy, or AI-generated Approved badge.

## Data and revision contract

Add versioned migrations while preserving the existing baseline and application data. Use the separate test database for checks. New organisation-scoped tables require composite tenant foreign keys and forced RLS under the restricted runtime role.

New records: `drafts`, `draft_versions`, `content_files`, `document_blocks`, `source_chunks`, `review_runs`, `review_events`, `findings`, `rewrite_options`, `approval_requests`, `approval_decisions`, `review_comments`, `brand_assets`, `ai_processing_consents`, `ai_request_usage`, and later scoped `assistant_threads/messages`.

- `draft_versions` binds the saved text, immutable DOCX/file bytes, document anchors, content hash and file SHA256. The server re-extracts the saved file and computes hashes; it does not trust text supplied by the browser.
- Hash input text uses Unicode NFC and LF newlines; preserve meaningful spaces and render the saved canonical text. Text offsets are zero-based, half-open Unicode code-point ranges, with explicit conversion to JavaScript UTF-16 offsets.
- Document anchors include package part, paragraph/run or table-cell identity and quoted text with context. They belong to one saved revision. Invalid or ambiguous anchors require recheck, never a blind replacement.
- Formatting-only edits, attachment changes and accepted/rejected tracked changes create a new saved revision and require a new review. Do not try to preserve approval by comparing only visible text.
- A save requires `expected_current_version_id`; a stale save returns 409 with recoverable local edits. Original uploads stay immutable. Version restore creates a new version; it does not delete history.
- Separate document state (`draft`, `pending_approval`, `approved`, `needs_changes`, `rejected`) from review state (`not_checked`, `queued`, `running`, `completed`, `incomplete`, `failed`, `cancelled`, `interrupted`, `stale`).

## Approved knowledge and real AI pipeline

1. Authenticate membership/role and load one saved draft revision plus one active approved guideline version.
2. Pin both versions before doing work. Detect unsupported/partial document regions and show coverage.
3. Load typed structured facts and applicable global/channel rules. Add owner-confirmed product/entity, currency, unit, effective date and applicability fields without guessing them from ambiguous free text.
4. Retrieve approved rule text and approved supporting excerpts only. A whole uploaded document does not become authoritative just because some of its proposals were approved. Discarded/unapproved content never enters authoritative retrieval.
5. Run deterministic product/price/term/disclaimer checks. Exact comparisons need matching entity, dates, units and currency. Ambiguity becomes Unverified.
6. Send a minimized, locally redacted review payload to the eligible OpenRouter route. The model proposes contextual tone/messaging/claim findings in a strict schema. Company documents remain untrusted data, never system instructions.
7. Resolve every evidence ID against the pinned tenant/version and validate quoted content, location and actual support. Nuanced factual support uses a separately prompted judge or remains uncertain; existence of a citation alone is insufficient.
8. Persist verified findings, coverage, prompt/schema/model/provider versions, usage and timing. Publish safe AG-UI progress/snapshots only. The model receives no database, filesystem, role-change, publishing or approval tools.

Finding statuses: `confirmed_mismatch`, `unverified`, `conflicting_sources`, `advisory`. Supported checks with no detected issue can be summarized, but incomplete checks never become a full pass. Global and channel rule conflicts require explicit owner precedence or clarification; do not silently select a rule.

Use bounded local PostgreSQL text retrieval first. Embeddings are not needed to claim retrieval augmentation. Upgrade only if retrieval-recall fixtures demonstrate a need; never introduce a paid embedding service under this budget.

## OpenRouter free-only and confidentiality contract

[Free router](https://openrouter.ai/docs/guides/routing/routers/free-router), [structured output](https://openrouter.ai/docs/guides/features/structured-outputs), [routing controls](https://openrouter.ai/docs/guides/routing/provider-selection), [limits](https://openrouter.ai/docs/api_reference/limits), [pricing](https://openrouter.ai/pricing).

- Keep `OPENROUTER_API_KEY` in a root, ignored `.env`, loaded explicitly by the backend launcher. No `NEXT_PUBLIC` secret, browser key storage, source-control copy, prompt log or key echo.
- Select an explicit available `:free` model for reproducible evaluations; optionally allow `openrouter/free` for demo availability while recording the actual returned model. Never use `openrouter/auto` as a free-only substitute.
- Before requests, validate model/endpoints/capabilities and zero pricing. Enforce request-level zero max prices for prompt, completion, request and image dimensions where applicable. Fallbacks may use only free, policy-compatible routes; otherwise stop.
- Require compatible schema support with `provider.require_parameters=true` and `response_format.type=json_schema`. Always validate again in Pydantic. If no eligible endpoint exists, show the limitation and preserve the draft.
- Default external requests to `provider.data_collection=deny` and `provider.zdr=true`; disable optional prompt logging, plugins and telemetry. These are routing constraints and provider-policy claims, not a guarantee covering every system or all metadata. Confirm returned provider routing information where available and record the effective policy without storing confidential payloads.
- Real files remain in private local storage. Extract/redact locally before AI; show the user exactly which text/crops will leave the machine. Store explicit organisation approval of the provider, policy version and redaction profile. A changed provider/policy requires renewed consent. No real company payload is sent during setup or automatic smoke tests.
- Personal identifiers, emails, account numbers and secrets detected locally are replaced with stable tokens. Keep the replacement map local, version-scoped and protected. Pattern redaction can miss confidential business facts; the preview lets the user exclude those passages too.
- Redaction tokens are protected rewrite spans. Block outputs that invent, mutate, merge or expose tokens. Restore originals only locally and revalidate the restored candidate.
- If the company prohibits external processing, or no free ZDR/no-collection route supports the task, offer local/manual checks and leave AI unavailable. No silent policy weakening. A pretrained local model does not require fine-tuning, but hardware/setup are a separate later option.
- Free quotas are account-dependent and shared across app/review/judge/eval calls. Official pricing currently describes a low free-tier request ceiling; query `GET /api/v1/key` and handle quota fields being absent. Failed calls can consume quota. Default app concurrency 1, conservative local pacing, explicit request budget and reservation for the demo.
- Default live evaluation invocation allows at most 10 completion attempts, bounded by remaining quota minus a 10-request demo reserve. A review/rewrite action has a hard maximum of 6 provider attempts including retries/judges, with at most 2 rewrite repair passes. Honour Retry-After, stop on daily exhaustion and resume only deliberately. No paid request is allowed to improve reliability.
- Cache only private, same-tenant results keyed by exact draft/rule hashes, model, prompt, schema and privacy settings. Mark reused results and record their originating run; do not claim a cached replay is a fresh live call.

## DOCX editor and fidelity contract

Embed a pinned, licence-reviewed SuperDoc release in a client-only component; serve worker/font/code assets locally and disable external telemetry and remote linked-resource fetching. Verify actual API support from that release before integration.

The editor supports ordinary text entry, basic formatting, lists, tables, find/replace, undo/redo, comments/review markup as verified, pagination, save and DOCX export. Do not promise all Microsoft Word features. Import/export support must be proved for fonts, headings, numbering, hyperlinks, tables, images, sections, headers/footers and existing tracked changes on fixtures. Unsupported features are identified before editing; preserve the original and offer read-only access rather than flattening them silently.

Save exports current DOCX bytes and posts them with the expected base revision. Backend validation/re-extraction produces the saved revision and text map, then the UI acknowledges Saved. Check, Submit and approved download always bind to that saved version; unsaved changes require save first. Export from the editor alone is never enough to establish server approval.

AI proposals target the document through public editor operations and are applied as reviewable edits when supported. Native document tracked changes and Inkloom approval are distinct concepts. Proposed implementation policy: users may inspect and edit a file containing tracked changes, but must explicitly resolve every tracked insertion/deletion before final submission, save and recheck. No automatic acceptance or rejection of those changes. Review markup export preserves unresolved changes in draft downloads; it cannot create an approved clean export.

Coverage policy: tonight's machine review must completely cover the supported visible text in body paragraphs, tables, headers and footers. Unsupported text-bearing parts or failed extraction block submission. Images/layout that the machine has not checked appear as explicit exclusions, not successful checks. A separate reviewer may human-approve the full saved artifact only after acknowledging personal visual inspection of those exclusions. Persist machine coverage and this human acknowledgement with the decision. The result means human approval of an exact artifact; it does not certify comprehensive machine compliance. Requiring full automated visual coverage is a later policy option, not the default implied by the badge.

PDF is a preview/extraction format in this scope; editing extracted PDF content creates a new document, with explicit loss of original PDF layout. Image OCR and visual review are separate capabilities and report coverage independently.

## Rewrites and human approvals

- Generate Minimal correction and Natural alternative on demand. Validate each independently against approved facts, required phrases, links, emails, mentions, hashtags, redaction tokens, intended CTA and selected region.
- For at most 30 words, attempt equal word count and line structure; longer copy targets within 10 percent. Factual accuracy takes precedence and failed length constraints are explained.
- Apply requires the current saved version, finding anchor and expected text. It creates a new version, marks findings stale and invalidates/supersedes pending approval. Dismissing records a reason and does not erase the finding.
- Request approval requires a complete latest review for the current saved version and an active eligible second human. Unverified/advisory findings remain visible; unresolved confirmed high-severity mismatches and incomplete coverage block submission until fixed/rechecked. Exceptional policies need a later explicit design change.
- Approve, reject and request changes run in backend transactions. Lock draft/version, approval request, reviewer membership and applicable rule version; recheck role, assignment, content/file hashes, review completion and no intervening edit.
- Prevent approval by creator, submitting user or an author of the current revision, including an owner holding several roles. Reviewers comment/decide but do not silently edit creators' files.
- Pending requests require recheck when active guidelines change. Previously approved historical versions remain traceable as approved under their pinned rules; label older-guideline context, never rewrite historical evidence.
- A comment is required for Request changes or Reject. At most one active request per draft; duplicates with the same idempotency key return the same result. Superseded requests/decisions stay in history.
- Final decisions reject unresolved tracked changes and unacknowledged visual exclusions. Pending reviewer assignment is a role, not evidence that a second human exists; no test or demo should present a self-operated second account as independent human sign-off.
- Enforcement uses authenticated account IDs. Without verified identity/SSO, the prototype cannot prove that two accounts belong to different people. Document this limit, reject author/submitter account IDs, and distinguish actual human collaboration from a two-account automated demonstration.

## Reliability and stream boundaries

Persist run creation, immutable input pins and idempotency before starting analysis. A bounded single-process executor is sufficient for tonight if restart/lease behaviour is explicit. Never keep a database transaction open during a model request. Store ordered safe events or snapshots; GET run status is authoritative on refresh. Cancellation uses a conditional database transition so a late model response cannot complete a cancelled run.

AG-UI uses the installed official SDK for lifecycle, named steps and safe snapshots; no raw reasoning or secret payloads. Attaching/reconnecting a stream never creates another business action. Expired sessions/disabled memberships stop future delivery; persisted historical data still requires authorisation to read.

## Three judging improvements

1. **Visual checks:** approved asset storage plus verified deterministic font/color/contrast checks where source data allows; selected image/region review with an eligible free vision route. Vision findings are advisory, show region/reference and unchecked areas. OCR text review does not count as full visual validation.
2. **Finding-aware assistant:** source-scoped explanations beside the selected finding, with references and streaming. Cannot approve, publish, activate knowledge, change roles or apply a rewrite without a click.
3. **Governance insights:** real counts of repeated categories, unsupported claims, unclear rules and review turnaround. Show date range, denominator, access scope and empty states; no invented ROI or model-accuracy chart.

All three have explicit tests and demo evidence. A feature that cannot meet its gate is recorded as incomplete, even if another feature works.

## Deadline and completion policy

Use the ordered tasks in the companion plan. Tonight's target is a complete narrow text/DOCX workflow with actual free-model review, cited findings, safe corrections, save/recheck and separate-human approval. Preserve the three improvements as the next ordered deliverables; do not call the complete problem statement delivered until their gates pass. Full Word parity, broad visual accuracy, exhaustive document fidelity and a 50-case live benchmark are not credible promises within an unspecified few-hour window.

Before implementation, review this design and its plan. No further provider or editor choice is needed unless a compatibility/privacy gate fails. Remaining operational input is the exact cutoff and the availability of a policy-compatible free model. Neither is invented.
