"""Apply immutable human dismissal records to saved review findings."""


def effective_findings(conn, org_id, run):
    dismissals = conn.execute(
        "SELECT metadata FROM audit_events WHERE org_id=%s AND target_id=%s AND action='finding.dismissed'",
        (org_id, str(run["id"])),
    ).fetchall()
    dismissed = {row["metadata"].get("finding_id") for row in dismissals}
    return [
        {**finding, "dismissed": finding["id"] in dismissed}
        for finding in (run["result"] or {}).get("findings", [])
    ]
