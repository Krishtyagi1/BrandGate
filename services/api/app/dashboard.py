"""Current authorised review results, kept separate from historical recurrence."""

from collections import Counter
from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Query

from .review_findings import effective_findings
from .review_scope import current_run_binding
from .security import User, org_transaction

router = APIRouter(prefix="/api/organisations/{org_id}")


@router.get("/dashboard")
def dashboard(org_id: UUID, days: int = Query(default=30, ge=1, le=90), user=User):
    end = datetime.now(UTC)
    start = end - timedelta(days=days)
    with org_transaction(user, org_id) as (conn, member):
        all_content = member["role"] != "creator"
        # Authorise before computing totals; this intentionally has no listing LIMIT.
        drafts = conn.execute(
            """SELECT d.*,u.name AS creator_name FROM drafts d JOIN users u ON u.id=d.creator_id
            WHERE d.org_id=%s AND (%s OR d.creator_id=%s) ORDER BY d.updated_at DESC,d.id DESC""",
            (org_id, all_content, user["id"]),
        ).fetchall()
        runs = conn.execute(
            """SELECT DISTINCT ON (r.draft_id) r.* FROM review_runs r
            JOIN drafts d ON d.org_id=r.org_id AND d.id=r.draft_id
            WHERE r.org_id=%s AND r.run_kind='review' AND (%s OR d.creator_id=%s)
            ORDER BY r.draft_id,r.created_at DESC,r.id DESC""",
            (org_id, all_content, user["id"]),
        ).fetchall()
        latest = {r["draft_id"]: r for r in runs}
        activity = conn.execute(
            """SELECT (r.created_at AT TIME ZONE 'UTC')::date AS day,r.status,count(*) AS count
            FROM review_runs r JOIN drafts d ON d.org_id=r.org_id AND d.id=r.draft_id
            WHERE r.org_id=%s AND r.run_kind='review' AND (%s OR d.creator_id=%s)
            AND r.created_at >= %s AND r.created_at <= %s GROUP BY day,r.status ORDER BY day""",
            (org_id, all_content, user["id"], start, end),
        ).fetchall()
        documents = []
        for draft in drafts:
            run = latest.get(draft["id"])
            state, findings = "unchecked", []
            if run:
                if draft["current_version_id"] != run["version_id"] or not current_run_binding(
                    conn, org_id, draft, run
                ):
                    state = "stale"
                else:
                    state = run["status"]
                    findings = effective_findings(conn, org_id, run)
            open_findings = [f for f in findings if not f.get("dismissed")]
            coverage = (
                (run["result"] or {}).get("check_coverage", []) if run and state != "stale" else []
            )
            missing = any(c["status"] not in ("passed", "issues_found") for c in coverage)
            extraction = (
                (run["result"] or {}).get("coverage", {}) if run and state != "stale" else {}
            )
            missing = missing or extraction.get("text_complete") is False
            documents.append(
                {
                    "id": str(draft["id"]),
                    "title": draft["title"],
                    "creator_name": draft["creator_name"],
                    "channel": draft["channel"],
                    "workflow_status": draft["status"],
                    "review_state": state,
                    "run_id": str(run["id"]) if run else None,
                    "updated_at": draft["updated_at"],
                    "coverage_incomplete": missing,
                    "open_flags": len(open_findings),
                    "high_flags": sum(f.get("severity") == "high" for f in open_findings),
                    "findings": [
                        {
                            k: f.get(k)
                            for k in (
                                "id",
                                "category",
                                "severity",
                                "status",
                                "quote",
                                "reason",
                                "dismissed",
                            )
                        }
                        for f in findings
                    ],
                }
            )
    breakdowns = {key: Counter() for key in ("category", "severity", "status")}
    dismissed = 0
    for document in documents:
        for finding in document["findings"]:
            if finding["dismissed"]:
                dismissed += 1
                continue
            for key in breakdowns:
                breakdowns[key][finding[key] or "unknown"] += 1
    daily = {}
    for row in activity:
        day = str(row["day"])
        entry = daily.setdefault(
            day,
            {
                "day": day,
                "total": 0,
                "completed": 0,
                "incomplete": 0,
                "failed": 0,
                "in_progress": 0,
            },
        )
        group = (
            "completed"
            if row["status"] == "completed"
            else "incomplete"
            if row["status"] == "incomplete"
            else "in_progress"
            if row["status"] in ("queued", "running")
            else "failed"
        )
        entry[group] += row["count"]
        entry["total"] += row["count"]
    return {
        "scope": "organisation" if all_content else "your_documents",
        "refreshed_at": end,
        "period_start": start,
        "period_end": end,
        "days": days,
        "summary": {
            "documents": len(documents),
            "checked_documents": sum(d["review_state"] == "completed" for d in documents),
            "flagged_documents": sum(d["open_flags"] > 0 for d in documents),
            "open_flags": sum(d["open_flags"] for d in documents),
            "high_flags": sum(d["high_flags"] for d in documents),
            "incomplete_documents": sum(
                d["review_state"]
                in ("incomplete", "failed", "cancelled", "interrupted", "queued", "running")
                or d["coverage_incomplete"]
                for d in documents
            ),
            "stale_documents": sum(d["review_state"] == "stale" for d in documents),
            "unchecked_documents": sum(d["review_state"] == "unchecked" for d in documents),
            "pending_approvals": sum(d["workflow_status"] == "pending_approval" for d in documents),
            "dismissed_flags": dismissed,
        },
        "breakdowns": {
            key: [{"label": label, "count": count} for label, count in counts.most_common()]
            for key, counts in breakdowns.items()
        },
        "activity": list(daily.values()),
        "documents": documents,
        "notice": "Current totals use each document's latest review, excluding stale results and rewrite runs. Open flags exclude dismissed findings. Completed checks are not compliance guarantees. Activity counts review runs started in the selected period, including rechecks; days use UTC. Current totals are independent of that period.",
    }
