import asyncio
from typing import TypedDict
from uuid import UUID

from ag_ui.core import (
    RunAgentInput,
    RunErrorEvent,
    RunFinishedEvent,
    RunStartedEvent,
    StateSnapshotEvent,
    StepFinishedEvent,
    StepStartedEvent,
)
from ag_ui.encoder import EventEncoder
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from langgraph.config import get_stream_writer
from langgraph.graph import END, START, StateGraph
from psycopg.errors import UniqueViolation

from .db import transaction
from .security import User, org_transaction, rate_limit

router = APIRouter(prefix="/api/organisations/{org_id}/diagnostics")


class DiagnosticState(TypedDict):
    steps_completed: int


def build_graph(user, org_id, run_id):
    graph = StateGraph(DiagnosticState)
    labels = [
        ("membership", "Checking organisation access"),
        ("guidelines", "Loading guideline versions"),
        ("complete", "Connection check complete"),
    ]
    for index, (key, label) in enumerate(labels):

        async def step(state, label=label, index=index):
            writer = get_stream_writer()
            writer({"kind": "start", "label": label})
            # Short, cancellable diagnostic interval; no model or compliance checks.
            for _ in range(4):
                await asyncio.sleep(0.1)
                with org_transaction(user, org_id) as (conn, _member):
                    row = conn.execute(
                        "SELECT status FROM diagnostic_runs WHERE org_id=%s AND id=%s AND actor_id=%s",
                        (org_id, run_id, user["id"]),
                    ).fetchone()
                    if not row or row["status"] != "running":
                        raise asyncio.CancelledError()
            with org_transaction(user, org_id) as (conn, _member):
                count = conn.execute(
                    "SELECT count(*) AS n FROM guideline_versions WHERE org_id=%s",
                    (org_id,),
                ).fetchone()["n"]
            writer(
                {
                    "kind": "state",
                    "snapshot": {
                        "mode": "diagnostic_only",
                        "progress": label,
                        "stepsCompleted": index + 1,
                        "guidelineVersions": count,
                        "orgId": str(org_id),
                    },
                }
            )
            writer({"kind": "end", "label": label})
            return {"steps_completed": index + 1}

        graph.add_node(key, step)
    graph.add_edge(START, "membership")
    graph.add_edge("membership", "guidelines")
    graph.add_edge("guidelines", "complete")
    graph.add_edge("complete", END)
    return graph.compile()


@router.post("/stream")
def stream(org_id: UUID, body: RunAgentInput, request: Request, user=User):
    rate_limit(request, "diagnostic", 20)
    try:
        run_id, thread_id = UUID(body.run_id), UUID(body.thread_id)
    except ValueError:
        raise HTTPException(422, "Run and thread IDs must be UUIDs.") from None
    with org_transaction(user, org_id) as (conn, _):
        try:
            conn.execute(
                "INSERT INTO diagnostic_runs(id,org_id,actor_id,thread_id,status) VALUES (%s,%s,%s,%s,'running')",
                (run_id, org_id, user["id"], thread_id),
            )
        except UniqueViolation:
            raise HTTPException(
                409,
                "This diagnostic run already exists. Fetch its saved status or start a new run.",
            ) from None
    encoder = EventEncoder(accept="text/event-stream")

    def save_status(status):
        with transaction(user, org_id) as conn:
            conn.execute(
                "UPDATE diagnostic_runs SET status=%s,completed_at=now() WHERE org_id=%s AND id=%s AND actor_id=%s AND status='running'",
                (status, org_id, run_id, user["id"]),
            )

    async def events():
        status = "cancelled"
        try:
            yield encoder.encode(RunStartedEvent(thread_id=str(thread_id), run_id=str(run_id)))
            graph = build_graph(user, org_id, run_id)
            async for event in graph.astream({"steps_completed": 0}, stream_mode="custom"):
                if await request.is_disconnected():
                    return
                if event["kind"] == "start":
                    yield encoder.encode(StepStartedEvent(step_name=event["label"]))
                elif event["kind"] == "end":
                    yield encoder.encode(StepFinishedEvent(step_name=event["label"]))
                else:
                    yield encoder.encode(StateSnapshotEvent(snapshot=event["snapshot"]))
            status = "completed"
            save_status(status)
            yield encoder.encode(RunFinishedEvent(thread_id=str(thread_id), run_id=str(run_id)))
        except asyncio.CancelledError:
            save_status("cancelled")
            if not await request.is_disconnected():
                yield encoder.encode(
                    RunErrorEvent(message="Connection check cancelled.", code="CANCELLED")
                )
        except Exception:
            status = "failed"
            save_status(status)
            yield encoder.encode(
                RunErrorEvent(
                    message="Connection check failed. Your organisation data is unchanged.",
                    code="DIAGNOSTIC_FAILED",
                )
            )
        finally:
            save_status(status)

    return StreamingResponse(
        events(), media_type="text/event-stream", headers={"X-Accel-Buffering": "no"}
    )


@router.get("/runs/{run_id}")
def run_status(org_id: UUID, run_id: UUID, user=User):
    with org_transaction(user, org_id) as (conn, _):
        row = conn.execute(
            "SELECT id,status,created_at,completed_at FROM diagnostic_runs WHERE org_id=%s AND id=%s AND actor_id=%s",
            (org_id, run_id, user["id"]),
        ).fetchone()
        if not row:
            raise HTTPException(404, "Connection check not found.")
        return row


@router.post("/runs/{run_id}/cancel")
def cancel_run(org_id: UUID, run_id: UUID, user=User):
    with org_transaction(user, org_id) as (conn, _):
        row = conn.execute(
            "UPDATE diagnostic_runs SET status='cancelled',completed_at=now() WHERE org_id=%s AND id=%s AND actor_id=%s AND status='running' RETURNING id",
            (org_id, run_id, user["id"]),
        ).fetchone()
        if not row:
            raise HTTPException(409, "The connection check has already ended or is unavailable.")
    return {"status": "cancelled"}
