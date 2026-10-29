"""Extractive, finding-scoped follow-up. No LLM calls, tools or authority writes."""

import re
from uuid import UUID, uuid4

from ag_ui.core import (
    RunFinishedEvent,
    RunStartedEvent,
    TextMessageContentEvent,
    TextMessageEndEvent,
    TextMessageStartEvent,
)
from ag_ui.encoder import EventEncoder
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from psycopg.types.json import Jsonb
from pydantic import Field

from retrieval.approved_sources import evidence

from .knowledge_snapshots import snapshot_rules
from .review_models import Strict
from .review_scope import current_run_binding
from .reviews import run_access
from .security import User, org_transaction, rate_limit

router = APIRouter(prefix="/api/organisations/{org_id}")


class FollowupRequest(Strict):
    finding_id: str = Field(min_length=1, max_length=100)
    question: str = Field(min_length=1, max_length=500)
    idempotency_key: str = Field(min_length=8, max_length=100)


def current_finding(conn, org_id, run_id, finding_id, user, member):
    run, draft = run_access(conn, org_id, run_id, user, member)
    latest = conn.execute(
        "SELECT id FROM review_runs WHERE org_id=%s AND draft_id=%s AND run_kind='review' ORDER BY created_at DESC,id DESC LIMIT 1",
        (org_id, draft["id"]),
    ).fetchone()
    if (
        run["status"] not in ("completed", "incomplete")
        or draft["current_version_id"] != run["version_id"]
        or not current_run_binding(conn, org_id, draft, run)
        or not latest
        or latest["id"] != run_id
    ):
        raise HTTPException(409, "This finding needs a fresh check. Open the latest review first.")
    finding = next((f for f in run["result"].get("findings", []) if f["id"] == finding_id), None)
    if not finding:
        raise HTTPException(404, "Finding not found in this review.")
    return run, draft, finding


def answer_finding(finding, rules, question):
    sources = {str(r["id"]): evidence(r) for r in rules}
    citations = []
    for ref in finding.get("evidence", []):
        source = sources.get(str(ref.get("id")))
        if source and all(
            ref.get(k) == source.get(k) for k in ("excerpt", "source_document_id", "location")
        ):
            if source["id"] not in {c["id"] for c in citations}:
                citations.append(source)
    normalized = re.sub(r"[?!.]+$", "", question.strip().casefold())
    why = normalized in {
        "why",
        "why was this flagged",
        "why is this flagged",
        "explain this finding",
    }
    fix = normalized in {
        "fix",
        "how can i fix it",
        "how can i fix this",
        "how do i fix this",
        "suggest a fix",
    }
    covered = bool(citations) and (why or fix)
    if not covered:
        text = "not covered by the guidelines — there is insufficient verified evidence for this question. Ask an owner to add or clarify approved guidance."
        citations = []
    else:
        introduction = "Compare the flagged content with the approved guidance below."
        if fix:
            introduction = {
                "messaging": "Check whether the cited required wording is present; add it where applicable, then save and recheck.",
                "terminology": "Revise the flagged wording to follow the cited terminology rule, then save and recheck.",
                "visual": "Compare the highlighted area with the approved reference and usage guidance. Adjust the original artwork, upload it again and recheck.",
            }.get(
                finding.get("category"),
                "Use the cited guidance to revise this finding's content, then save and recheck. A safe complete replacement is not established by this excerpt alone.",
            )
        text = (
            introduction
            + "\n\n"
            + "\n\n".join(
                f"[{i + 1}] {c['excerpt']}\nSource: {c['location']}"
                for i, c in enumerate(citations)
            )
        )
        text += "\n\nThis is an extract from approved guidance, not a new compliance decision. Human review is required."
    return {"covered": covered, "answer": text, "citations": citations, "mode": "local_extractive"}


@router.post("/review-runs/{run_id}/follow-up")
def follow_up(org_id: UUID, run_id: UUID, body: FollowupRequest, request: Request, user=User):
    rate_limit(request, f"followup:{user['id']}", 20)
    with org_transaction(user, org_id) as (conn, member):
        run, _, finding = current_finding(conn, org_id, run_id, body.finding_id, user, member)
        prior = conn.execute(
            "SELECT * FROM finding_followups WHERE org_id=%s AND actor_id=%s AND idempotency_key=%s",
            (org_id, user["id"], body.idempotency_key),
        ).fetchone()
        if prior:
            if (
                prior["run_id"] != run_id
                or prior["finding_id"] != body.finding_id
                or prior["question"] != body.question
            ):
                raise HTTPException(
                    409, "This request key was already used for a different question."
                )
            return {"id": prior["id"], **prior["answer"]}
        rules = snapshot_rules(
            conn, org_id, run["knowledge_snapshot_id"], run["review_scope"].get("channel")
        )
        answer = answer_finding(finding, rules, body.question)
        answer_id = uuid4()
        conn.execute(
            "INSERT INTO finding_followups(id,org_id,run_id,actor_id,finding_id,question,answer,idempotency_key) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
            (
                answer_id,
                org_id,
                run_id,
                user["id"],
                body.finding_id,
                body.question,
                Jsonb(answer),
                body.idempotency_key,
            ),
        )
        return {"id": answer_id, **answer}


@router.post("/follow-ups/{answer_id}/stream")
def stream_answer(org_id: UUID, answer_id: UUID, user=User):
    with org_transaction(user, org_id) as (conn, member):
        row = conn.execute(
            "SELECT * FROM finding_followups WHERE org_id=%s AND id=%s AND actor_id=%s",
            (org_id, answer_id, user["id"]),
        ).fetchone()
        if not row:
            raise HTTPException(404, "Answer not found.")
        _, draft, _ = current_finding(conn, org_id, row["run_id"], row["finding_id"], user, member)
        thread, run, message = str(draft["id"]), str(answer_id), str(answer_id)
        events = [
            RunStartedEvent(thread_id=thread, run_id=run),
            TextMessageStartEvent(message_id=message, role="assistant"),
            TextMessageContentEvent(message_id=message, delta=row["answer"]["answer"]),
            TextMessageEndEvent(message_id=message),
            RunFinishedEvent(thread_id=thread, run_id=run),
        ]
    encoder = EventEncoder(accept="text/event-stream")
    return StreamingResponse(
        iter(encoder.encode(e) for e in events),
        media_type="text/event-stream",
        headers={"X-Accel-Buffering": "no"},
    )
