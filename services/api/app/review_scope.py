"""Saved review intent and source coverage; instructions are never company authority."""

CHECKS = [
    "prices",
    "claims",
    "tone",
    "language",
    "required_wording",
    "colours_fonts",
    "logos",
    "accessibility",
]
VISUAL = {"colours_fonts", "logos"}
PLATFORMS = {"linkedin", "instagram", "x", "facebook", "threads", "tiktok", "youtube", "pinterest"}


def needs_text(format, scope):
    excluded = VISUAL | ({"accessibility"} if format == "image" else set())
    return bool(set(scope.get("requested_checks") or CHECKS) - excluded)


def classify_rule(rule):
    from .knowledge_snapshots import rule_check

    return rule_check(rule)


def scope_context(draft, policy=None):
    policy = policy or {}
    return {
        "category": draft.get("category") or "other",
        "platform": draft.get("platform"),
        "channel": draft.get("channel") or "general",
        "requested_checks": sorted(
            set(draft.get("requested_checks") or policy.get("checks") or CHECKS)
        ),
        "task_instructions": draft.get("task_instructions") or "",
        "company_instructions": policy.get("instructions") or "",
    }


def selected_rules(rules, scope):
    from evaluators.facts import applicable_rules

    return [
        rule for rule in applicable_rules(rules) if classify_rule(rule) in scope["requested_checks"]
    ]


def finding_check(finding, rules):
    by_id = {str(rule["id"]): classify_rule(rule) for rule in rules}
    categories = {by_id.get(str(e["id"])) for e in finding.get("evidence", [])}
    if len(categories - {None}) == 1:
        return next(iter(categories - {None}))
    return {
        "tone": "tone",
        "terminology": "language",
        "fact": "prices",
        "claim": "claims",
        "messaging": "required_wording",
        "accessibility": "accessibility",
        "visual": "colours_fonts",
    }.get(finding["category"], "claims")


def scoped_findings(findings, rules, scope):
    return [f for f in findings if finding_check(f, rules) in scope["requested_checks"]]


def coverage_rows(rules, scope, findings=(), completed=False, references=()):
    available = {classify_rule(rule) for rule in rules}
    if references:
        available.add("logos")
    rows = []
    for check in scope["requested_checks"]:
        present = check in available
        issues = any(finding_check(f, rules) == check for f in findings)
        rows.append(
            {
                "check": check,
                "status": "source_missing"
                if not present
                else ("issues_found" if issues else "passed")
                if completed
                else "not_checked",
                "reason": "No confirmed source supports this check. Add and confirm guidance in Rules."
                if not present
                else "Checked against confirmed company sources."
                if completed
                else "This check has not completed.",
            }
        )
    return rows


def current_run_binding(conn, org_id, draft, run):
    from .knowledge_snapshots import current_snapshot

    policy = conn.execute(
        "SELECT * FROM guideline_versions WHERE org_id=%s AND status='active'", (org_id,)
    ).fetchone()
    if not policy or policy["id"] != run["guideline_version_id"]:
        return False
    snapshot = current_snapshot(conn, org_id, policy["id"])
    if not snapshot or snapshot["id"] != run.get("knowledge_snapshot_id"):
        return False
    recorded = run.get("review_scope")
    if recorded:
        recorded = {**recorded, "requested_checks": sorted(recorded.get("requested_checks") or [])}
    if recorded:
        recorded.setdefault("company_instructions", "")
    return not recorded or recorded == scope_context(draft, snapshot)
