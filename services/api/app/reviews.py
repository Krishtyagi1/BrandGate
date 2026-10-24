import json
from uuid import UUID, uuid4

from ag_ui.core import (
    RunErrorEvent,
    RunFinishedEvent,
    RunStartedEvent,
    StateSnapshotEvent,
    StepFinishedEvent,
    StepStartedEvent,
)
from ag_ui.encoder import EventEncoder
from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from fastapi.responses import StreamingResponse
from psycopg.types.json import Jsonb

from agents.review_graph import build_graph
from evaluators.facts import check_facts
from providers.openrouter import POLICY_VERSION, ProviderUnavailable, settings

from .ai_settings import prepare_payload, require_consent
from .config import LOCAL
from .db import audit, transaction
from .drafts import get_draft
from .knowledge_snapshots import current_snapshot, snapshot_references, snapshot_rules
from .review_models import RunStart
from .review_scope import (
    VISUAL,
    classify_rule,
    coverage_rows,
    current_run_binding,
    scope_context,
    scoped_findings,
    selected_rules,
)
from .security import User, digest, org_transaction

router = APIRouter(prefix="/api/organisations/{org_id}")


def inputs(conn, org_id, draft, version_id):
    if draft["current_version_id"] != version_id:
        raise HTTPException(409, "Save and use the current document revision.")
    version = conn.execute(
        "SELECT * FROM draft_versions WHERE org_id=%s AND id=%s AND draft_id=%s",
        (org_id, version_id, draft["id"]),
    ).fetchone()
    policy = conn.execute(
        "SELECT * FROM guideline_versions WHERE org_id=%s AND status='active'", (org_id,)
    ).fetchone()
    if not policy:
        raise HTTPException(409, "Activate owner-approved brand rules before reviewing content.")
    snapshot = current_snapshot(conn, org_id, policy["id"])
    if not snapshot:
        raise HTTPException(409, "Confirm company sources before reviewing content.")
    policy = {
        **policy,
        "snapshot_id": snapshot["id"],
        "checks": snapshot["checks"],
        "instructions": snapshot["instructions"],
    }
    rules = selected_rules(
        snapshot_rules(conn, org_id, snapshot["id"], draft["channel"]), scope_context(draft, policy)
    )
    return version, policy, rules


def payload_context(conn, org_id, draft, version, policy, rules):
    context = {**scope_context(draft, policy), "knowledge_snapshot_id": str(policy["snapshot_id"])}
    if draft["format"] == "image" and set(context["requested_checks"]) & (
        VISUAL | {"accessibility"}
    ):
        from .visual_review import visual_manifest

        refs = snapshot_references(conn, org_id, policy["snapshot_id"])
        try:
            context["visual_inputs"] = visual_manifest(
                {**version, "artifact_sha256": version.get("file_sha256")}, rules, refs
            )
        except ValueError as error:
            raise HTTPException(409, str(error)) from error
    return context


@router.get("/drafts/{draft_id}/ai-preview")
def preview(org_id: UUID, draft_id: UUID, user=User):
    with org_transaction(user, org_id) as (conn, member):
        draft = get_draft(conn, org_id, draft_id, user, member, edit=True)
        version, policy, rules = inputs(conn, org_id, draft, draft["current_version_id"])
        context = payload_context(conn, org_id, draft, version, policy, rules)
        payload, mapping, preview_hash, _ = prepare_payload(
            version, rules, draft["channel"], context
        )
        return {
            "payload": payload,
            "preview_hash": preview_hash,
            "redacted_values": len(mapping),
            "guideline_version": policy["version"],
            "policy_version": POLICY_VERSION,
            "check_coverage": coverage_rows(
                rules, context, references=snapshot_references(conn, org_id, policy["snapshot_id"])
            ),
            "visual_images": (
                [
                    {
                        "label": "Your image",
                        "url": f"/api/organisations/{org_id}/drafts/{draft_id}/versions/{version['id']}/download",
                    }
                ]
                + [
                    {
                        "label": r["label"],
                        "url": f"/api/organisations/{org_id}/sources/{r['source_document_id']}/download",
                    }
                    for r in snapshot_references(conn, org_id, policy["snapshot_id"])
                ]
            )
            if context.get("visual_inputs")
            else [],
            "notice": "This redacted text and selected approved excerpts will be sent to OpenRouter. When visual inputs are shown, the original candidate and reference images are also sent; text redaction does not redact image pixels. Inspect every preview for confidential information.",
        }


def run_access(conn, org_id, run_id, user, member):
    run = conn.execute(
        "SELECT * FROM review_runs WHERE org_id=%s AND id=%s", (org_id, run_id)
    ).fetchone()
    if not run:
        raise HTTPException(404, "Review not found.")
    draft = get_draft(conn, org_id, run["draft_id"], user, member)
    return run, draft


def record_event(conn, org_id, run_id, event):
    sequence = conn.execute(
        "SELECT coalesce(max(sequence),0)+1 AS n FROM review_events WHERE org_id=%s AND run_id=%s",
        (org_id, run_id),
    ).fetchone()["n"]
    conn.execute(
        "INSERT INTO review_events(org_id,run_id,sequence,event) VALUES (%s,%s,%s,%s)",
        (org_id, run_id, sequence, Jsonb(event.model_dump(mode="json", by_alias=True))),
    )


def execute_review(user, org_id, run_id):
    def progress(label):
        with org_transaction(user, org_id) as (conn, _):
            run = conn.execute(
                "SELECT * FROM review_runs WHERE org_id=%s AND id=%s FOR UPDATE", (org_id, run_id)
            ).fetchone()
            if not run or run["status"] not in ("queued", "running"):
                raise ProviderUnavailable("Review was cancelled.")
            require_consent(conn, org_id)
            conn.execute(
                "UPDATE review_runs SET status='running',step=%s WHERE org_id=%s AND id=%s",
                (label, org_id, run_id),
            )
            if run["status"] == "running":
                record_event(conn, org_id, run_id, StepFinishedEvent(step_name=run["step"]))
            record_event(conn, org_id, run_id, StepStartedEvent(step_name=label))
            record_event(
                conn,
                org_id,
                run_id,
                StateSnapshotEvent(
                    snapshot={"runId": str(run_id), "status": "running", "progress": label}
                ),
            )

    def usage(status, metadata, attempt=None):
        with org_transaction(user, org_id) as (conn, _):
            require_consent(conn, org_id)
            if attempt:
                conn.execute(
                    "UPDATE ai_request_usage SET status=%s,metadata=%s WHERE org_id=%s AND id=%s",
                    (status, Jsonb(metadata), org_id, attempt),
                )
                return attempt
            attempt = uuid4()
            conn.execute(
                "INSERT INTO ai_request_usage(id,org_id,actor_id,model,purpose,status,metadata) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                (
                    attempt,
                    org_id,
                    user["id"],
                    metadata.get("requested_model", settings()["OPENROUTER_MODEL"]),
                    metadata.get("purpose", "review"),
                    status,
                    Jsonb(metadata),
                ),
            )
            return attempt

    findings = []
    coverage = {}
    check_coverage = []
    scope = {}
    rules = []
    try:
        progress("Reading saved content and approved rules")
        with org_transaction(user, org_id) as (conn, _):
            run = conn.execute(
                "SELECT * FROM review_runs WHERE org_id=%s AND id=%s", (org_id, run_id)
            ).fetchone()
            version = conn.execute(
                "SELECT * FROM draft_versions WHERE org_id=%s AND id=%s",
                (org_id, run["version_id"]),
            ).fetchone()
            draft = conn.execute(
                "SELECT * FROM drafts WHERE org_id=%s AND id=%s", (org_id, run["draft_id"])
            ).fetchone()
            snapshot = conn.execute(
                "SELECT * FROM knowledge_snapshots WHERE org_id=%s AND id=%s",
                (org_id, run["knowledge_snapshot_id"]),
            ).fetchone()
            if not snapshot:
                raise ProviderUnavailable("The confirmed source snapshot is unavailable.")
            scope = run.get("review_scope") or scope_context(draft, snapshot)
            rules = selected_rules(
                snapshot_rules(
                    conn, org_id, snapshot["id"], scope.get("channel", draft["channel"])
                ),
                scope,
            )
            refs = snapshot_references(conn, org_id, snapshot["id"])
            context = payload_context(
                conn,
                org_id,
                {**draft, **scope},
                version,
                {"snapshot_id": snapshot["id"], **snapshot},
                rules,
            )
            payload, mapping, _, selected = prepare_payload(
                version, rules, draft["channel"], context
            )
        coverage = version["projection"]["coverage"]
        findings = scoped_findings(check_facts(version["text"], rules), rules, scope)
        check_coverage = coverage_rows(rules, scope, findings, references=refs)
        # Pure exact checks do not consume inference; a missing requested source stays visible.
        contextual = {"tone", "claims", "language", "accessibility"} & set(
            scope["requested_checks"]
        )
        needs_contextual = (
            (
                "prices" in scope["requested_checks"]
                and any(not r.get("fact") and classify_rule(r) == "prices" for r in rules)
            )
            or "claims" in contextual
            or any(
                r["check"] in contextual and r["status"] != "source_missing" for r in check_coverage
            )
        )
        output = {"findings": findings, "validation_dropped": 0}
        if needs_contextual:
            graph = build_graph(version, rules, payload, mapping, progress, usage)
            output = graph.invoke({"findings": []}, {"recursion_limit": 8})
            findings = scoped_findings(output["findings"], rules, scope)
        check_coverage = coverage_rows(rules, scope, findings, completed=True, references=refs)
        # Exact code checks see every rule; contextual inference sees only the previewed subset.
        selected_ids = {str(r["id"]) for r in selected}
        omitted_checks = {
            classify_rule(r)
            for r in rules
            if str(r["id"]) not in selected_ids
            and (
                classify_rule(r) in {"tone", "claims", "accessibility"}
                or (classify_rule(r) == "prices" and not r.get("fact"))
            )
        }
        check_coverage = [
            {
                **row,
                "status": "not_checked",
                "reason": "Some required contextual guidance exceeded the 24-source preview limit. Narrow the selected checks or reduce overlapping guidance and recheck.",
            }
            if row["check"] in omitted_checks
            else row
            for row in check_coverage
        ]
        visual = None
        requested_visual = set(scope["requested_checks"]) & (
            VISUAL | ({"accessibility"} if draft["format"] == "image" else set())
        )
        if requested_visual:
            if draft["format"] == "image":
                from .visual_review import evaluate_visual

                progress("Comparing the static image with confirmed references")
                visual = evaluate_visual(
                    LOCAL / version["private_path"], rules, refs, list(requested_visual), usage
                )
                findings += visual["findings"]
                replacements = {
                    r["check"]: {
                        **r,
                        "status": "passed" if r["status"] == "checked" else r["status"],
                    }
                    for r in visual["check_coverage"]
                }
            else:
                replacements = {
                    key: {
                        "check": key,
                        "status": "unsupported",
                        "reason": "Visual appearance checks require a static PNG/JPEG. Text and document checks continue separately; inspect embedded visuals manually.",
                    }
                    for key in requested_visual
                }
            check_coverage = [replacements.get(r["check"], r) for r in check_coverage]
        text_requested = (
            set(scope["requested_checks"])
            - VISUAL
            - ({"accessibility"} if draft["format"] == "image" else set())
        )
        complete = (
            (coverage["text_complete"] or not text_requested)
            and output.get("validation_dropped", 0) == 0
            and not any(r["status"] in ("unavailable", "not_checked") for r in check_coverage)
            and any(r["status"] in ("passed", "issues_found") for r in check_coverage)
        )
        result = {
            "findings": findings,
            "coverage": coverage,
            "metadata": output.get("metadata"),
            "visual_metadata": (visual or {}).get("metadata"),
            "check_coverage": check_coverage,
            "review_scope": scope,
            "knowledge_snapshot_id": str(run["knowledge_snapshot_id"]),
            "checks": [
                r["check"] for r in check_coverage if r["status"] in ("passed", "issues_found")
            ],
            "rules_considered": len(selected),
            "active_rules": len(rules),
            "validation_dropped": output.get("validation_dropped", 0),
            "mode": "live_ai"
            if output.get("metadata") or (visual or {}).get("mode") == "live"
            else "local_checks",
        }
        finish_run(
            user,
            org_id,
            run_id,
            "completed" if complete else "incomplete",
            result,
            None
            if complete
            else "Some requested checks have no usable source, unsupported content, or unvalidated model output. See coverage for details.",
        )
    except Exception as error:
        reason = (
            str(error)
            if isinstance(error, (ProviderUnavailable, HTTPException))
            else "Review could not finish. Your saved document is preserved."
        )
        finish_run(
            user,
            org_id,
            run_id,
            "incomplete",
            {
                "findings": findings,
                "coverage": coverage,
                "mode": "local_checks_only",
                "checks": [],
                "check_coverage": coverage_rows(rules, scope, findings)
                if scope
                else check_coverage,
            },
            reason[:400],
        )


def finish_run(user, org_id, run_id, status, result, error):
    with transaction(user, org_id) as conn:
        prior = conn.execute(
            "SELECT * FROM review_runs WHERE org_id=%s AND id=%s FOR UPDATE", (org_id, run_id)
        ).fetchone()
        if not prior or prior["status"] not in ("queued", "running"):
            return
        run = conn.execute(
            "UPDATE review_runs SET status=%s,result=%s,error=%s,step=%s,completed_at=now() WHERE org_id=%s AND id=%s AND status IN ('queued','running') RETURNING *",
            (
                status,
                Jsonb(result),
                error,
                "Review complete" if status == "completed" else "Review incomplete",
                org_id,
                run_id,
            ),
        ).fetchone()
        if not run:
            return
        if status == "completed" and prior["run_kind"] == "review":
            record_event(conn, org_id, run_id, StepFinishedEvent(step_name=prior["step"]))
        record_event(
            conn,
            org_id,
            run_id,
            StateSnapshotEvent(
                snapshot={"runId": str(run_id), "status": status, "result": result, "error": error}
            ),
        )
        terminal = (
            RunFinishedEvent(thread_id=str(run["draft_id"]), run_id=str(run_id))
            if status == "completed"
            else RunErrorEvent(message=error or "Review incomplete.", code="INCOMPLETE")
        )
        record_event(conn, org_id, run_id, terminal)
        audit(
            conn,
            user["id"],
            org_id,
            run["run_kind"] + "." + status,
            "review_run",
            run_id,
            {"findings": len(result.get("findings", [])), "mode": result.get("mode")},
        )


@router.post("/drafts/{draft_id}/reviews", status_code=202)
def start(
    org_id: UUID, draft_id: UUID, body: RunStart, background_tasks: BackgroundTasks, user=User
):
    with org_transaction(user, org_id) as (conn, member):
        conn.execute("SELECT id FROM organisations WHERE id=%s FOR UPDATE", (org_id,))
        draft = get_draft(conn, org_id, draft_id, user, member, edit=True)
        existing = conn.execute(
            "SELECT * FROM review_runs WHERE org_id=%s AND actor_id=%s AND run_kind='review' AND idempotency_key=%s",
            (org_id, user["id"], body.idempotency_key),
        ).fetchone()
        if existing:
            if existing["draft_id"] != draft_id or existing["version_id"] != body.version_id:
                raise HTTPException(409, "This request key belongs to another revision.")
            return existing
        require_consent(conn, org_id)
        if not settings()["OPENROUTER_API_KEY"]:
            raise HTTPException(409, "OpenRouter key is missing. Configure the project root .env.")
        version, policy, rules = inputs(conn, org_id, draft, body.version_id)
        scope = scope_context(draft, policy)
        if (
            draft["format"] == "image"
            and set(scope["requested_checks"]) - (VISUAL | {"accessibility"})
            and not version["projection"]["coverage"]["text_complete"]
        ):
            raise HTTPException(
                409, "Verify the OCR transcript against the original image, save and then review."
            )
        _, _, actual_hash, _ = prepare_payload(
            version,
            rules,
            draft["channel"],
            payload_context(conn, org_id, draft, version, policy, rules),
        )
        if actual_hash != body.preview_hash:
            raise HTTPException(
                409, "The AI payload changed. Inspect its current preview before checking."
            )
        if conn.execute(
            "SELECT 1 FROM review_runs WHERE org_id=%s AND draft_id=%s AND status IN ('queued','running')",
            (org_id, draft_id),
        ).fetchone():
            raise HTTPException(409, "A review is already running for this draft.")
        run_id = uuid4()
        superseded = conn.execute(
            "UPDATE approval_requests SET status='superseded' WHERE org_id=%s AND draft_id=%s AND status='pending' RETURNING id",
            (org_id, draft_id),
        ).fetchall()
        if superseded:
            conn.execute(
                "UPDATE drafts SET status='draft',updated_at=now() WHERE org_id=%s AND id=%s",
                (org_id, draft_id),
            )
            for request in superseded:
                audit(
                    conn,
                    user["id"],
                    org_id,
                    "approval.superseded_by_recheck",
                    "approval_request",
                    request["id"],
                    {"new_run_id": str(run_id)},
                )
        run = conn.execute(
            "INSERT INTO review_runs(id,org_id,draft_id,version_id,guideline_version_id,actor_id,idempotency_key,knowledge_snapshot_id,review_scope) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING *",
            (
                run_id,
                org_id,
                draft_id,
                version["id"],
                policy["id"],
                user["id"],
                body.idempotency_key,
                policy["snapshot_id"],
                Jsonb(scope),
            ),
        ).fetchone()
        record_event(
            conn, org_id, run_id, RunStartedEvent(thread_id=str(draft_id), run_id=str(run_id))
        )
        audit(
            conn,
            user["id"],
            org_id,
            "review.started",
            "review_run",
            run_id,
            {"version_id": str(version["id"]), "guideline_version_id": str(policy["id"])},
        )
    background_tasks.add_task(execute_review, dict(user), org_id, run_id)
    return run


@router.get("/review-runs/{run_id}")
def get_run(org_id: UUID, run_id: UUID, user=User):
    with org_transaction(user, org_id) as (conn, member):
        run, draft = run_access(conn, org_id, run_id, user, member)
        active = conn.execute(
            "SELECT id FROM guideline_versions WHERE org_id=%s AND status='active'", (org_id,)
        ).fetchone()
        dismissals = conn.execute(
            "SELECT metadata FROM audit_events WHERE org_id=%s AND target_id=%s AND action='finding.dismissed'",
            (org_id, str(run_id)),
        ).fetchall()
        for f in run["result"].get("findings", []):
            f["dismissed"] = any(d["metadata"].get("finding_id") == f["id"] for d in dismissals)
        return {
            **run,
            "stale": draft["current_version_id"] != run["version_id"]
            or not active
            or not current_run_binding(conn, org_id, draft, run),
        }


@router.post("/review-runs/{run_id}/cancel")
def cancel(org_id: UUID, run_id: UUID, user=User):
    with org_transaction(user, org_id) as (conn, member):
        run, _ = run_access(conn, org_id, run_id, user, member)
        if run["actor_id"] != user["id"]:
            raise HTTPException(403, "Only the person who started this review can cancel it.")
        row = conn.execute(
            "UPDATE review_runs SET status='cancelled',step='Cancelled',completed_at=now() WHERE org_id=%s AND id=%s AND status IN ('queued','running') RETURNING id",
            (org_id, run_id),
        ).fetchone()
        if not row:
            raise HTTPException(409, "Review has already ended.")
        record_event(
            conn, org_id, run_id, RunErrorEvent(message="Review cancelled.", code="CANCELLED")
        )
    return {"status": "cancelled"}


@router.post("/review-runs/{run_id}/stream")
async def stream(org_id: UUID, run_id: UUID, request: Request, user=User):
    import asyncio

    with org_transaction(user, org_id) as (conn, member):
        run_access(conn, org_id, run_id, user, member)
    token_hash = digest(request.cookies.get("inkloom_session", ""))
    encoder = EventEncoder(accept="text/event-stream")

    async def events():
        sequence = 0
        for _ in range(360):
            if await request.is_disconnected():
                return
            try:
                with org_transaction(user, org_id) as (conn, member):
                    if not conn.execute(
                        "SELECT 1 FROM sessions WHERE token_hash=%s AND expires_at>now()",
                        (token_hash,),
                    ).fetchone():
                        return
                    run, _ = run_access(conn, org_id, run_id, user, member)
                    rows = conn.execute(
                        "SELECT sequence,event FROM review_events WHERE org_id=%s AND run_id=%s AND sequence>%s ORDER BY sequence",
                        (org_id, run_id, sequence),
                    ).fetchall()
                for row in rows:
                    sequence = row["sequence"]
                    yield "data: " + json.dumps(row["event"]) + "\n\n"
                if run["status"] not in ("queued", "running"):
                    return
            except HTTPException:
                return
            await asyncio.sleep(0.5)
        yield encoder.encode(
            RunErrorEvent(
                message="Stream timed out. Refresh saved review status.", code="RECONNECT"
            )
        )

    return StreamingResponse(
        events(), media_type="text/event-stream", headers={"X-Accel-Buffering": "no"}
    )
