# Overall review dashboard

Date: 30 October 2026
Status: approved alongside document chat by the user's “do both” on 30 October 2026; implemented locally.

## Intent

The user requested a dashboard showing overall findings, results and flags.
Continue the document chatbot as part of the same requested work. Build on the
current white Rules / New review / Tracking interface and persisted review data.

## Approaches and recommendation

1. Recommended: make Tracking an overview with summary counts, simple charts,
   actionable flags and the existing searchable document list. This keeps the
   established three primary tabs and puts results beside the work they describe.
2. Add a fourth Dashboard tab: gives the overview a dedicated destination but
   changes the explicitly established navigation and separates it from Tracking.
3. Extend only Recurring issues & guideline gaps: smallest visual change, but its
   historical counts cannot accurately describe current unresolved work.

The user approved option 1 alongside the document-chat design.

## Proposed contents

- Counts: total documents, checked documents, documents with open flags, open
  high-severity flags, incomplete/failed checks, stale reviews and pending human
  approvals. Report finding counts separately from document counts.
- Findings breakdown by category, severity and status, with text labels and exact
  counts. Distinguish confirmed mismatch, unverified, advisory and dismissed.
- Review activity over 7/30/90 days, with counts for completed, incomplete and
  failed checks. Rechecks are review activity, not additional documents.
- A “Needs attention” list linking each document to its flags, reason, current
  review state and the document explanation chatbot.
- The existing document search, workflow filters and assigned-approval queue.
- Owner/reviewer access to existing historical recurrence and guideline gaps.

Clickable summaries filter the underlying documents; category/severity/status
filters combine predictably and show a clear reset action. Include loading,
empty, error/retry states, a last-refreshed timestamp and an explicit Refresh
action. Preserve responsive layout and keyboard/screen-reader access. No new
visualization dependency is necessary for simple count bars.

## Data semantics and permissions

Add a backend summary endpoint using persisted records under organisation RLS.
Owners/reviewers see permitted organisation content; creators see only their own
documents and clearly labelled personal totals. Authorise before aggregation;
never return hidden document counts, names or flags. Do not aggregate the current
200-row frontend document-list response as if it represented the entire company.

For current flags, inspect only the latest review-kind run of each document.
Exclude rewrite runs; do not fall back to an older completed review when a newer
review failed. Validate the latest run against current content, approved snapshot
and scope using the existing review binding checks. Stale results appear in a
separate stale count and remain inspectable, not current unresolved totals.
Dismissed observations remain available in a labelled breakdown and do not count
as open flags. Keep stored human approval state separate from AI review status.

Show current-work counts independently of the selected historical activity
period. Historical trends are review runs started within that period; recurrence
continues to use the existing documented distinct-draft semantics. Labels disclose
the different denominators. No invented compliance percentage, inferred model
accuracy, creator score or guarantee from zero findings. Incomplete coverage
remains visible even when a document has no recorded flags.

## Delivery and validation

Implement after the document chatbot, sharing the same review links and permission
semantics. No model call is needed to calculate dashboard statistics. No automatic
approvals, publication, new hosting or deployment is included.

Test count accuracy across repeated reviews, rewrites, failed/latest runs,
dismissals, mixed severity, incomplete coverage and stale content/source/scope.
Verify creator and cross-organisation isolation and totals beyond the document
list limit. Test filter drill-downs, period boundaries, empty organisations,
errors/retry, mobile layout and accessible chart equivalents. Run backend tests,
lint, frontend typecheck/build and browser checks. Record commands and actual
outcomes in implementation status; record the selected navigation decision in
decisions after approval.
