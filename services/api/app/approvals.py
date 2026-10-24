from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException
from psycopg.types.json import Jsonb

from .db import audit
from .drafts import get_draft
from .review_models import ApprovalDecision, ApprovalStart, CommentBody
from .review_scope import current_run_binding, needs_text
from .security import User, org_transaction

router = APIRouter(prefix="/api/organisations/{org_id}")


def ready(conn, org_id, draft, version_id):
    if draft["current_version_id"] != version_id:
        raise HTTPException(409, "This draft changed. Check its latest saved revision first.")
    version = conn.execute(
        "SELECT * FROM draft_versions WHERE org_id=%s AND draft_id=%s AND id=%s",
        (org_id, draft["id"], version_id),
    ).fetchone()
    active = conn.execute(
        "SELECT id FROM guideline_versions WHERE org_id=%s AND status='active'", (org_id,)
    ).fetchone()
    run = conn.execute(
        "SELECT * FROM review_runs WHERE org_id=%s AND draft_id=%s AND version_id=%s AND run_kind='review' ORDER BY created_at DESC LIMIT 1",
        (org_id, draft["id"], version_id),
    ).fetchone()
    if (
        not run
        or run["status"] != "completed"
        or not active
        or active["id"] != run["guideline_version_id"]
        or not current_run_binding(conn, org_id, draft, run)
    ):
        raise HTTPException(
            409, "Complete a fresh review using the current active guidelines before approval."
        )
    if (
        needs_text(draft["format"], run.get("review_scope") or {})
        and not version["projection"]["coverage"]["text_complete"]
    ) or version["projection"]["unresolved_changes"]:
        raise HTTPException(
            409,
            "Resolve tracked changes and unsupported text regions, save and recheck before submitting.",
        )
    if any(
        f["severity"] == "high" and f["status"] in ("confirmed_mismatch", "conflicting_sources")
        for f in run["result"].get("findings", [])
    ):
        raise HTTPException(
            409, "Fix the confirmed high-severity issues, save and recheck before submitting."
        )
    return version, run


@router.post("/drafts/{draft_id}/comments", status_code=201)
def comment(org_id: UUID, draft_id: UUID, body: CommentBody, user=User):
    if not body.body.strip():
        raise HTTPException(422, "Enter a comment.")
    with org_transaction(user, org_id) as (conn, member):
        get_draft(conn, org_id, draft_id, user, member)
        if not conn.execute(
            "SELECT 1 FROM draft_versions WHERE org_id=%s AND draft_id=%s AND id=%s",
            (org_id, draft_id, body.version_id),
        ).fetchone():
            raise HTTPException(404, "Draft version unavailable.")
        row = conn.execute(
            "INSERT INTO review_comments(id,org_id,draft_id,version_id,actor_id,body) VALUES (%s,%s,%s,%s,%s,%s) RETURNING *",
            (uuid4(), org_id, draft_id, body.version_id, user["id"], body.body.strip()),
        ).fetchone()
        audit(conn, user["id"], org_id, "review.comment_added", "draft_version", body.version_id)
        return row


@router.post("/drafts/{draft_id}/approvals", status_code=201)
def submit(org_id: UUID, draft_id: UUID, body: ApprovalStart, user=User):
    with org_transaction(user, org_id) as (conn, member):
        conn.execute("SELECT id FROM organisations WHERE id=%s FOR UPDATE", (org_id,))
        draft = get_draft(conn, org_id, draft_id, user, member, edit=True)
        existing = conn.execute(
            "SELECT * FROM approval_requests WHERE org_id=%s AND submitted_by=%s AND idempotency_key=%s",
            (org_id, user["id"], body.idempotency_key),
        ).fetchone()
        if existing:
            if (
                existing["draft_id"] != draft_id
                or existing["version_id"] != body.version_id
                or existing["reviewer_id"] != body.reviewer_id
            ):
                raise HTTPException(409, "This request key was used for another approval.")
            return existing
        version, run = ready(conn, org_id, draft, body.version_id)
        if body.reviewer_id in (user["id"], draft["creator_id"], version["author_id"]):
            raise HTTPException(
                409,
                "Choose a separate authorised reviewer. Authors and submitters cannot approve their own content.",
            )
        reviewer = conn.execute(
            "SELECT * FROM memberships WHERE org_id=%s AND user_id=%s AND status='active' AND role IN ('owner','reviewer') FOR SHARE",
            (org_id, body.reviewer_id),
        ).fetchone()
        if not reviewer:
            raise HTTPException(409, "Choose an active owner or reviewer in this organisation.")
        if conn.execute(
            "SELECT 1 FROM approval_requests WHERE org_id=%s AND draft_id=%s AND status='pending'",
            (org_id, draft_id),
        ).fetchone():
            raise HTTPException(409, "This draft already has a pending approval request.")
        row = conn.execute(
            "INSERT INTO approval_requests(id,org_id,draft_id,version_id,run_id,submitted_by,reviewer_id,idempotency_key) VALUES (%s,%s,%s,%s,%s,%s,%s,%s) RETURNING *",
            (
                uuid4(),
                org_id,
                draft_id,
                version["id"],
                run["id"],
                user["id"],
                body.reviewer_id,
                body.idempotency_key,
            ),
        ).fetchone()
        conn.execute(
            "UPDATE drafts SET status='pending_approval' WHERE org_id=%s AND id=%s",
            (org_id, draft_id),
        )
        audit(
            conn,
            user["id"],
            org_id,
            "approval.requested",
            "approval_request",
            row["id"],
            {"version_id": str(version["id"]), "reviewer_id": str(body.reviewer_id)},
        )
        return row


@router.get("/approvals")
def queue(org_id: UUID, user=User):
    with org_transaction(user, org_id) as (conn, member):
        return conn.execute(
            "SELECT a.*,d.title,d.channel,d.current_version_id,u.name AS creator_name,r.name AS reviewer_name FROM approval_requests a JOIN drafts d ON d.org_id=a.org_id AND d.id=a.draft_id JOIN users u ON u.id=d.creator_id JOIN users r ON r.id=a.reviewer_id WHERE a.org_id=%s AND (%s OR d.creator_id=%s) ORDER BY a.created_at DESC LIMIT 200",
            (org_id, member["role"] != "creator", user["id"]),
        ).fetchall()


@router.post("/approvals/{request_id}/decision")
def decide(org_id: UUID, request_id: UUID, body: ApprovalDecision, user=User):
    with org_transaction(user, org_id) as (conn, member):
        conn.execute("SELECT id FROM organisations WHERE id=%s FOR UPDATE", (org_id,))
        request = conn.execute(
            "SELECT * FROM approval_requests WHERE org_id=%s AND id=%s", (org_id, request_id)
        ).fetchone()
        if not request:
            raise HTTPException(404, "Approval request unavailable.")
        if member["role"] not in ("owner", "reviewer") or request["reviewer_id"] != user["id"]:
            raise HTTPException(403, "Only the assigned authorised reviewer can decide.")
        draft = get_draft(conn, org_id, request["draft_id"], user, member)
        request = conn.execute(
            "SELECT * FROM approval_requests WHERE org_id=%s AND id=%s FOR UPDATE",
            (org_id, request_id),
        ).fetchone()
        if (
            request["status"] != "pending"
            or request["version_id"] != body.expected_version_id
            or draft["current_version_id"] != body.expected_version_id
        ):
            raise HTTPException(
                409, "This request ended or its draft changed. Recheck and request review again."
            )
        version, run = ready(conn, org_id, draft, body.expected_version_id)
        if user["id"] in (draft["creator_id"], request["submitted_by"], version["author_id"]):
            raise HTTPException(403, "Authors and submitters cannot approve their own content.")
        if body.artifact_sha256 != version["artifact_sha256"] or run["id"] != request["run_id"]:
            raise HTTPException(
                409,
                "The reviewed artifact or check changed. Request approval for the latest check.",
            )
        if body.decision != "approved" and not body.comment.strip():
            raise HTTPException(422, "A comment is required when requesting changes or rejecting.")
        coverage = version["projection"]["coverage"]
        if (
            body.decision == "approved"
            and coverage.get("exclusions")
            and not body.manual_visual_ack
        ):
            raise HTTPException(
                409, "Personally inspect the excluded visual areas and confirm before approving."
            )
        decision = conn.execute(
            "INSERT INTO approval_decisions(id,org_id,request_id,actor_id,decision,comment,artifact_sha256,manual_visual_ack,coverage) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING *",
            (
                uuid4(),
                org_id,
                request_id,
                user["id"],
                body.decision,
                body.comment.strip(),
                version["artifact_sha256"],
                body.manual_visual_ack,
                Jsonb(coverage),
            ),
        ).fetchone()
        conn.execute(
            "UPDATE approval_requests SET status=%s WHERE org_id=%s AND id=%s",
            (body.decision, org_id, request_id),
        )
        conn.execute(
            "UPDATE drafts SET status=%s,updated_at=now() WHERE org_id=%s AND id=%s",
            (body.decision, org_id, draft["id"]),
        )
        audit(
            conn,
            user["id"],
            org_id,
            "approval." + body.decision,
            "approval_request",
            request_id,
            {
                "version_id": str(version["id"]),
                "artifact_sha256": version["artifact_sha256"],
                "manual_visual_ack": body.manual_visual_ack,
            },
        )
        return decision
