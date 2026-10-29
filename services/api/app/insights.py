"""Observed review recurrence, not creator scores or current compliance claims."""

from collections import defaultdict
from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query

from .security import User, org_transaction

router = APIRouter(prefix="/api/organisations/{org_id}")


def summarize(rows, questions):
    groups = {
        key: defaultdict(set)
        for key in ("finding_types", "by_channel", "by_creator", "by_campaign")
    }
    gaps = {}
    for row in rows:
        draft = str(row["draft_id"])
        for finding in row["result"].get("findings", []):
            category = finding.get("issue_type") or finding.get("category", "unknown")
            status = finding.get("status", "unknown")
            kind = (category, category, status)
            groups["finding_types"][kind].add(draft)
            for dimension, label in (
                ("by_channel", row["channel"]),
                ("by_creator", str(row["creator_id"]) + "|" + row["creator_name"]),
                ("by_campaign", row["campaign"] or "No campaign"),
            ):
                groups[dimension][(label, category, status)].add(draft)
            if status == "unverified":
                label = finding.get("quote", "Unverified claim")[:500]
                key = ("unverified_claim", label.strip().casefold())
                entry = gaps.setdefault(
                    key, {"kind": "unverified_claim", "question": label, "draft_ids": set()}
                )
                entry["draft_ids"].add(draft)
    for row in questions:
        label = row["question"]
        key = ("unanswered_question", label.strip().casefold())
        entry = gaps.setdefault(
            key, {"kind": "unanswered_question", "question": label, "draft_ids": set()}
        )
        entry["draft_ids"].add(str(row["draft_id"]))
    result = {}
    for dimension, values in groups.items():
        result[dimension] = sorted(
            (
                {
                    "label": label.split("|", 1)[-1] if dimension == "by_creator" else label,
                    "key": label,
                    "status": status,
                    "finding_type": category,
                    "drafts": len(ids),
                }
                for (label, category, status), ids in values.items()
            ),
            key=lambda r: (-r["drafts"], r["label"], r["status"]),
        )
    result["guideline_gaps"] = sorted(
        (
            {
                "kind": r["kind"],
                "question": r["question"],
                "drafts": len(r["draft_ids"]),
                "draft_ids": sorted(r["draft_ids"])[:3],
            }
            for r in gaps.values()
        ),
        key=lambda r: (-r["drafts"], r["question"]),
    )[:50]
    latest = {}
    for row in rows:
        latest.setdefault(str(row["draft_id"]), row)
    result["reviewed_drafts"] = len(latest)
    result["drafts_with_findings"] = len(
        {str(r["draft_id"]) for r in rows if r["result"].get("findings")}
    )
    result["incomplete_drafts"] = sum(r["status"] != "completed" for r in latest.values())
    return result


@router.get("/insights")
def insights(org_id: UUID, days: int = Query(default=30, ge=1, le=365), user=User):
    end = datetime.now(UTC)
    start = end - timedelta(days=days)
    with org_transaction(user, org_id) as (conn, member):
        if member["role"] == "creator":
            raise HTTPException(403, "Insights are available to owners and reviewers.")
        # Recurrence is historical: retain issues that were subsequently fixed,
        # but summarize() counts a draft only once per type/status. The ordering
        # also identifies each draft's most recent check for the failure count.
        rows = conn.execute(
            """SELECT r.*,r.draft_id,d.creator_id,u.name AS creator_name,
            coalesce(r.review_scope->>'channel',d.channel) AS channel,d.campaign
            FROM review_runs r JOIN drafts d ON d.org_id=r.org_id AND d.id=r.draft_id
            JOIN users u ON u.id=d.creator_id
            WHERE r.org_id=%s AND r.run_kind='review' AND r.created_at >= %s AND r.created_at <= %s
            ORDER BY r.created_at DESC,r.id DESC""",
            (org_id, start, end),
        ).fetchall()
        questions = conn.execute(
            """SELECT f.question,r.draft_id FROM finding_followups f
            JOIN review_runs r ON r.org_id=f.org_id AND r.id=f.run_id
            WHERE f.org_id=%s AND f.created_at >= %s AND f.created_at <= %s
            AND f.answer->>'covered'='false' ORDER BY f.created_at DESC LIMIT 5000""",
            (org_id, start, end),
        ).fetchall()
        return {
            **summarize(rows, questions),
            "period_start": start,
            "period_end": end,
            "days": days,
            "question_limit_reached": len(questions) == 5000,
            "denominator": "Distinct drafts with a review started in this period, including earlier revisions. Each type/status and breakdown counts a draft once, even across rechecks. Corrected and dismissed findings remain historical observations; categories can overlap. The incomplete count uses each draft's latest check in the period. Campaign labels are current metadata. Unanswered questions are counted separately across this period; unsupported question wording can also cause abstention.",
        }
