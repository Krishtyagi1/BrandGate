import hashlib
import json
from uuid import UUID

from fastapi import APIRouter, HTTPException

from privacy.redaction import redact
from providers.openrouter import POLICY, POLICY_VERSION, settings
from retrieval.approved_sources import evidence, retrieve

from .config import LOCAL
from .db import audit
from .review_models import ConsentBody
from .security import User, org_transaction

router = APIRouter(prefix="/api/organisations/{org_id}/ai")


def prepare_payload(version, rules, channel, context=None):
    selected = retrieve(rules, version["text"])
    sources = [evidence(r) for r in selected]
    delimiter = "\n---INKLOOM-FIELD-BOUNDARY---\n"
    fields = (
        [version["text"]]
        + [field for r in sources for field in (r["value"], r["excerpt"])]
        + [
            (context or {}).get("task_instructions", ""),
            (context or {}).get("company_instructions", ""),
        ]
    )
    if any(delimiter in field for field in fields):
        raise HTTPException(422, "Remove the reserved payload field marker.")
    try:
        cleaned, mapping = redact(delimiter.join(fields))
    except ValueError as error:
        raise HTTPException(422, str(error)) from None
    chunks = cleaned.split(delimiter)
    for index, source in enumerate(sources):
        source["value"], source["excerpt"] = chunks[1 + index * 2 : 3 + index * 2]
        source.pop("source_document_id", None)
    payload = {
        "content": chunks[0],
        "channel": channel,
        "approved_sources": sources,
        "policy_version": POLICY_VERSION,
        "version_id": str(version["id"]),
        "model_selection": settings()["OPENROUTER_MODEL"],
    }
    if context is not None:
        payload["review_scope"] = {
            **context,
            "task_instructions": chunks[-2],
            "company_instructions": chunks[-1],
        }
    payload["source_selection"] = {
        "included": len(selected),
        "available": len(rules),
        "limit": 24,
        "notice": "Only the listed sources are sent. Contextual checks with omitted guidance remain incomplete."
        if len(selected) < len(rules)
        else "All applicable selected guidance is included.",
    }
    preview_hash = hashlib.sha256(
        json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()
    ).hexdigest()
    return payload, mapping, preview_hash, selected


def require_consent(conn, org_id):
    row = conn.execute("SELECT * FROM ai_processing_consents WHERE org_id=%s", (org_id,)).fetchone()
    if not row or not row["enabled"] or row["policy_version"] != POLICY_VERSION:
        raise HTTPException(
            409, "The owner must enable this external AI processing policy in Team & settings."
        )


@router.get("/status")
def status(org_id: UUID, user=User):
    with org_transaction(user, org_id) as (conn, _):
        consent = conn.execute(
            "SELECT enabled,policy_version,created_at FROM ai_processing_consents WHERE org_id=%s",
            (org_id,),
        ).fetchone()
        usage = conn.execute(
            "SELECT status,count(*) AS count FROM ai_request_usage WHERE org_id=%s AND created_at>now()-interval '24 hours' GROUP BY status",
            (org_id,),
        ).fetchall()
    reports = [LOCAL / "test-results/ai-smoke.json", LOCAL / "test-results/live-review-smoke.json"]
    available = [p for p in reports if p.exists()]
    smoke = None
    if available:
        raw = json.loads(max(available, key=lambda p: p.stat().st_mtime).read_text())
        smoke = {
            "status": raw.get("status"),
            "reason": raw.get("reason"),
            "model": raw.get("model") or (raw.get("metadata") or {}).get("model"),
            "provider": (raw.get("metadata") or {}).get("provider"),
        }
    return {
        "configured": bool(settings()["OPENROUTER_API_KEY"]),
        "model": settings()["OPENROUTER_MODEL"],
        "policy_version": POLICY_VERSION,
        "routing_policy": POLICY,
        "consent": consent,
        "usage": usage,
        "synthetic_connection_test": smoke,
        "privacy_note": "Redacted text and selected approved excerpts leave this machine. Pattern redaction can miss confidential business information. Routing settings do not guarantee confidentiality.",
    }


@router.post("/consent")
def consent(org_id: UUID, body: ConsentBody, user=User):
    if body.policy_version != POLICY_VERSION:
        raise HTTPException(409, "Processing policy changed. Refresh before confirming.")
    with org_transaction(user, org_id, owner=True) as (conn, _):
        conn.execute(
            "INSERT INTO ai_processing_consents(org_id,approved_by,policy_version,enabled) VALUES (%s,%s,%s,%s) ON CONFLICT(org_id) DO UPDATE SET approved_by=excluded.approved_by,policy_version=excluded.policy_version,enabled=excluded.enabled,created_at=now()",
            (org_id, user["id"], POLICY_VERSION, body.enabled),
        )
        audit(
            conn,
            user["id"],
            org_id,
            "ai.processing_policy_changed",
            "organisation",
            org_id,
            {"enabled": body.enabled, "policy_version": POLICY_VERSION},
        )
    return {"enabled": body.enabled}
