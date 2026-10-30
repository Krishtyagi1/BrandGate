# Document explanation chatbot

Date: 30 October 2026
Status: approved by the user's “do both” on 30 October 2026; implemented locally.

## Intent and scope

The user selected document chat: explain all flags with cited follow-up answers.
Extend the existing review workspace, FastAPI backend, OpenRouter adapter and
AG-UI transport. Existing build-window authorisation is recorded in
`docs/BUILD_LEDGER.md` and `docs/IMPLEMENTATION_STATUS.md`.

## Approaches

1. Document chat (user selected, recommended): one conversation beside the
   findings, covering the saved review and follow-up questions. More useful for
   understanding an entire review; requires bounded context and history.
2. Finding chat: upgrade each existing finding helper to AI. Smaller context,
   but users must move among separate conversations to understand the document.
3. Retain the local extractive helper: no provider dependency, but only predefined
   why/fix questions work. This does not meet the requested AI chatbot behavior.

## User experience

Add an “Ask about this document” panel beside the findings, retaining the editor
and existing finding cards. Include “Why was this document flagged?”, “Which
issues need attention first?” and “What should I change?” shortcuts, a question
box, readable conversation history, sending/error states and retry. Individual
findings can open the document conversation with that finding selected.

Answers identify the affected wording, explain the stored reason and status,
and show numbered, expandable approved-source citations with private download
links. Unsupported claims are described as lacking evidence, not proven false.
Incomplete checks, dismissed findings and advisory visual findings remain
explicit. Zero findings must not be presented as a compliance guarantee.

Show that questions and selected review excerpts are sent to the configured AI
provider and stored privately. Let users inspect the redacted outbound payload
before sending. Preserve the current model, pricing and privacy restrictions.
Display a clear unavailable state on provider failure; do not label local
extracts or test doubles as AI responses.

## Backend and evidence

Add review-scoped chat preview, send, history and saved-answer stream endpoints.
Keep the existing local finding-follow-up endpoint compatible. Store chat turns
in an additive tenant-isolated table with immutable question, validated answer,
actor, review ID, request key and provider metadata. History is private to the
requesting user and exact review. Enforce idempotency and rate limits.

Each send checks membership, draft access, latest review, saved content revision,
knowledge snapshot, review scope and owner processing consent. Repeat those checks
before recording or replaying an answer, including after inference. Do not hold
a database transaction open during the model request. Changes require a fresh
review and a new conversation; old answers cannot silently describe new content.

Send a bounded, consistently redacted payload containing the question, recent
saved turns, findings, coverage and exact verified excerpts from the review's
pinned knowledge snapshot. Do not send original files, image pixels, all company
sources or unrelated drafts. Reject or explicitly disclose context limits rather
than silently omitting issues from an “all flags” explanation.

Use the existing structured provider adapter and usage accounting. The model
returns bounded explanation items referencing finding IDs and citation IDs.
Resolve citations on the backend; never trust model-generated excerpts, URLs,
source locations or identifiers. Reject invented references and unknown protected
tokens. Missing evidence requires an explicit uncertainty response. Citation
identity validation cannot prove semantic support; document that limitation and
evaluate substantive support with labelled synthetic cases.

Treat every question, stored finding and source excerpt as untrusted data.
No browsing, executable tools, document edits, new review decisions, approvals,
source activation or publishing. Proposed edits remain advice; the existing
save/recheck/human approval workflow owns any change.

AG-UI streams the validated saved answer using existing message events. Show
“Preparing explanation” while inference runs; do not present unvalidated model
tokens as final explanations. Recover an interrupted stream from the saved turn.

## Validation and delivery

Test multi-finding explanations, evidence-free flags, incomplete/clean reviews,
bounded history, invalid/forged citations, injection attempts, protected values,
missing consent, provider failures, retry idempotency, foreign organisation and
unauthorised creator access, plus revision/source changes during inference and
stream replay. Verify no draft, approval or guideline changes occur.

Run the relevant backend suite, lint, frontend typecheck and production build.
Exercise the panel at desktop/mobile widths and verify accessible input, progress,
errors and citations. Use explicit provider doubles for automated checks; attempt
real inference only with synthetic content and eligible existing configuration.
Report live-provider unavailability honestly. Update implementation status and
decisions with actual commands and outcomes. Deployment is outside this feature
request.

## Implementation choices proposed by the builder

Reuse the current stack and provider; add no chatbot service or model dependency.
Retain the local finding helper as a compatible backend path, while routing new
document conversations through the new endpoints. Keep history bounded to the
exact review and user. These choices are proposals, not additional user decisions.
