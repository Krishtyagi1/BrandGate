"""Append-only human assessments, separate from advisory output and approvals."""

from typing import Literal
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException
from pydantic import Field

from .db import audit
from .followup import current_finding
from .review_models import Strict
from .reviews import run_access
from .security import User, org_transaction

router = APIRouter(prefix="/api/organisations/{org_id}/review-runs/{run_id}/visual-confirmations")


class VisualConfirmation(Strict):
    finding_id: str = Field(min_length=1, max_length=100)
    verdict: Literal["confirmed", "not_an_issue", "uncertain"]
    note: str = Field(min_length=1, max_length=1000, pattern=r"\S")


@router.post("", status_code=201)
def confirm(org_id: UUID, run_id: UUID, body: VisualConfirmation, user=User):
    with org_transaction(user, org_id) as (conn, member):
        _, draft, finding = current_finding(conn, org_id, run_id, body.finding_id, user, member)
        if member["role"] not in ("owner", "reviewer") or draft["creator_id"] == user["id"]:
            raise HTTPException(
                403, "A separate authorised reviewer must assess this visual finding."
            )
        if finding.get("category") not in ("visual", "accessibility") or not finding.get("region"):
            raise HTTPException(422, "This finding has no visual region to assess.")
        row = conn.execute(
            "INSERT INTO visual_confirmations(id,org_id,run_id,actor_id,finding_id,verdict,note) VALUES (%s,%s,%s,%s,%s,%s,%s) RETURNING *",
            (uuid4(), org_id, run_id, user["id"], body.finding_id, body.verdict, body.note.strip()),
        ).fetchone()
        audit(
            conn,
            user["id"],
            org_id,
            "visual.assessed",
            "review_run",
            run_id,
            {"finding_id": body.finding_id, "verdict": body.verdict},
        )
        return row


@router.get("")
def listing(org_id: UUID, run_id: UUID, user=User):
    with org_transaction(user, org_id) as (conn, member):
        run_access(conn, org_id, run_id, user, member)
        return conn.execute(
            "SELECT v.*,u.name AS actor_name FROM visual_confirmations v JOIN users u ON u.id=v.actor_id WHERE v.org_id=%s AND v.run_id=%s ORDER BY v.created_at,v.id",
            (org_id, run_id),
        ).fetchall()
