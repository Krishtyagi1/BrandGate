import hashlib
import json
import subprocess
import sys
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, UploadFile
from fastapi.responses import FileResponse
from psycopg.types.json import Jsonb

from .config import LOCAL
from .db import audit
from .models import RuleInput
from .security import User, org_transaction

router = APIRouter(prefix="/api/organisations/{org_id}")


def version_record(conn, org_id, version_id, editable=False):
    version = conn.execute(
        "SELECT * FROM guideline_versions WHERE org_id=%s AND id=%s FOR UPDATE",
        (org_id, version_id),
    ).fetchone()
    if not version:
        raise HTTPException(404, "Guideline version not found.")
    if editable and version["status"] != "draft":
        raise HTTPException(
            409,
            "Activated versions are read-only. Create a new version to make changes.",
        )
    return version


@router.get("/guidelines/versions")
def versions(org_id: UUID, user=User):
    with org_transaction(user, org_id) as (conn, _):
        return conn.execute(
            "SELECT v.*,(SELECT count(*) FROM structured_rules r WHERE r.guideline_version_id=v.id) AS rule_count FROM guideline_versions v WHERE v.org_id=%s ORDER BY version DESC",
            (org_id,),
        ).fetchall()


@router.post("/guidelines/versions", status_code=201)
def create_version(org_id: UUID, user=User):
    with org_transaction(user, org_id, owner=True) as (conn, _):
        conn.execute("SELECT id FROM organisations WHERE id=%s FOR UPDATE", (org_id,))
        next_version = conn.execute(
            "SELECT coalesce(max(version),0)+1 AS n FROM guideline_versions WHERE org_id=%s",
            (org_id,),
        ).fetchone()["n"]
        version = conn.execute(
            "INSERT INTO guideline_versions(id,org_id,version) VALUES (%s,%s,%s) RETURNING *",
            (uuid4(), org_id, next_version),
        ).fetchone()
        audit(
            conn,
            user["id"],
            org_id,
            "guideline.created",
            "guideline_version",
            version["id"],
            {"version": next_version},
        )
    return version


@router.get("/guidelines/versions/{version_id}")
def get_version(org_id: UUID, version_id: UUID, user=User):
    with org_transaction(user, org_id) as (conn, _):
        version = version_record(conn, org_id, version_id)
        rules = conn.execute(
            "SELECT * FROM structured_rules WHERE org_id=%s AND guideline_version_id=%s ORDER BY created_at,id",
            (org_id, version_id),
        ).fetchall()
        sources = conn.execute(
            "SELECT id,filename,sha256,extraction_status,locations FROM source_documents WHERE org_id=%s AND guideline_version_id=%s ORDER BY created_at",
            (org_id, version_id),
        ).fetchall()
    return {**version, "rules": rules, "sources": sources}


def check_source(conn, org_id, version_id, body):
    if body.source_document_id:
        source = conn.execute(
            "SELECT extracted_text,locations FROM source_documents WHERE org_id=%s AND id=%s AND guideline_version_id=%s",
            (org_id, body.source_document_id, version_id),
        ).fetchone()
        if (
            not source
            or not body.source_excerpt
            or body.source_excerpt not in source["extracted_text"]
        ):
            raise HTTPException(422, "Source excerpt must match a stored document in this version.")
        if not any(
            s["location"] == body.source_location and body.source_excerpt in s["text"]
            for s in source["locations"]
        ):
            raise HTTPException(422, "Source location and excerpt do not match.")
    elif body.source_excerpt or body.source_location:
        raise HTTPException(422, "Select a document before adding a source excerpt.")
    if body.fact:
        from ingestion.knowledge_intake import validate_price_evidence

        try:
            validate_price_evidence(body)
        except ValueError as error:
            raise HTTPException(422, str(error)) from None


@router.post("/guidelines/versions/{version_id}/rules", status_code=201)
def add_rule(org_id: UUID, version_id: UUID, body: RuleInput, user=User):
    with org_transaction(user, org_id, owner=True) as (conn, _):
        version_record(conn, org_id, version_id, editable=True)
        check_source(conn, org_id, version_id, body)
        rule = conn.execute(
            "INSERT INTO structured_rules(org_id,guideline_version_id,type,rule_key,value,scope_channel,source_document_id,source_excerpt,source_location,approved_by,fact) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING *",
            (
                org_id,
                version_id,
                body.type,
                body.rule_key,
                body.value,
                body.scope_channel,
                body.source_document_id,
                body.source_excerpt,
                body.source_location,
                user["id"] if body.approved else None,
                Jsonb(body.fact.model_dump(mode="json")) if body.fact else None,
            ),
        ).fetchone()
        audit(
            conn,
            user["id"],
            org_id,
            "rule.created",
            "structured_rule",
            rule["id"],
            {"approved": body.approved},
        )
    return rule


@router.patch("/guidelines/versions/{version_id}/rules/{rule_id}")
def edit_rule(org_id: UUID, version_id: UUID, rule_id: UUID, body: RuleInput, user=User):
    with org_transaction(user, org_id, owner=True) as (conn, _):
        version_record(conn, org_id, version_id, editable=True)
        check_source(conn, org_id, version_id, body)
        row = conn.execute(
            "UPDATE structured_rules SET type=%s,rule_key=%s,value=%s,scope_channel=%s,source_document_id=%s,source_excerpt=%s,source_location=%s,approved_by=%s,fact=%s,revision=revision+1 WHERE org_id=%s AND guideline_version_id=%s AND id=%s AND revision=%s RETURNING *",
            (
                body.type,
                body.rule_key,
                body.value,
                body.scope_channel,
                body.source_document_id,
                body.source_excerpt,
                body.source_location,
                user["id"] if body.approved else None,
                Jsonb(body.fact.model_dump(mode="json")) if body.fact else None,
                org_id,
                version_id,
                rule_id,
                body.revision,
            ),
        ).fetchone()
        if not row:
            raise HTTPException(
                409, "This rule changed in another window. Reload it before saving."
            )
        audit(
            conn,
            user["id"],
            org_id,
            "rule.updated",
            "structured_rule",
            rule_id,
            {"approved": body.approved, "revision": row["revision"]},
        )
    return row


@router.post("/guidelines/versions/{version_id}/activate")
def activate(org_id: UUID, version_id: UUID, user=User):
    with org_transaction(user, org_id, owner=True) as (conn, _):
        conn.execute("SELECT id FROM organisations WHERE id=%s FOR UPDATE", (org_id,))
        version = version_record(conn, org_id, version_id, editable=True)
        rules = conn.execute(
            "SELECT * FROM structured_rules WHERE org_id=%s AND guideline_version_id=%s",
            (org_id, version_id),
        ).fetchall()
        if not rules or any(not rule["approved_by"] for rule in rules):
            raise HTTPException(
                409,
                "Review and approve every proposed rule before activating this version.",
            )
        values = {}
        for rule in rules:
            if rule["type"] in ("approved_fact", "product_name"):
                key = (rule["type"], rule["rule_key"], rule["scope_channel"])
                if key in values and values[key] != rule["value"].casefold():
                    raise HTTPException(
                        409,
                        f"Conflicting values for {rule['rule_key']}. Resolve them before activation.",
                    )
                values[key] = rule["value"].casefold()
        conn.execute(
            "UPDATE guideline_versions SET status='archived' WHERE org_id=%s AND status='active'",
            (org_id,),
        )
        conn.execute(
            "UPDATE guideline_versions SET status='active',approved_by=%s,activated_at=now() WHERE org_id=%s AND id=%s",
            (user["id"], org_id, version_id),
        )
        from .knowledge_snapshots import append_snapshot

        append_snapshot(conn, org_id, version, rules, user["id"])
        conn.execute(
            "UPDATE approval_requests SET status='superseded' WHERE org_id=%s AND status='pending'",
            (org_id,),
        )
        conn.execute(
            "UPDATE drafts SET status='draft' WHERE org_id=%s AND status='pending_approval'",
            (org_id,),
        )
        audit(
            conn,
            user["id"],
            org_id,
            "guideline.activated",
            "guideline_version",
            version_id,
            {"version": version["version"]},
        )
    return {"message": f"Version {version['version']} is active.", "id": version_id}


@router.delete("/guidelines/versions/{version_id}/rules/{rule_id}")
def discard_rule(org_id: UUID, version_id: UUID, rule_id: UUID, user=User):
    with org_transaction(user, org_id, owner=True) as (conn, _):
        version_record(conn, org_id, version_id, editable=True)
        row = conn.execute(
            "DELETE FROM structured_rules WHERE org_id=%s AND guideline_version_id=%s AND id=%s RETURNING id",
            (org_id, version_id, rule_id),
        ).fetchone()
        if not row:
            raise HTTPException(404, "Rule not found.")
        audit(conn, user["id"], org_id, "rule.discarded", "structured_rule", rule_id)
    return {"message": "Proposed rule discarded."}


@router.post("/guidelines/versions/{version_id}/uploads", status_code=201)
def upload(org_id: UUID, version_id: UUID, file: UploadFile, user=User):
    suffix = Path(file.filename or "").suffix.lower()
    mime = {
        ".pdf": "application/pdf",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }
    if suffix not in mime or file.content_type not in (
        mime.get(suffix),
        "application/octet-stream",
    ):
        raise HTTPException(415, "Upload a text-based PDF or DOCX file (maximum 5 MB).")
    data = file.file.read(5 * 1024 * 1024 + 1)
    if len(data) > 5 * 1024 * 1024:
        raise HTTPException(413, "File exceeds 5 MB.")
    if (suffix == ".pdf" and not data.startswith(b"%PDF")) or (
        suffix == ".docx" and not data.startswith(b"PK")
    ):
        raise HTTPException(422, "File contents do not match its extension.")
    with org_transaction(user, org_id, owner=True) as (conn, _):
        version_record(conn, org_id, version_id, editable=True)
        if (
            conn.execute(
                "SELECT count(*) AS n FROM source_documents WHERE org_id=%s AND guideline_version_id=%s",
                (org_id, version_id),
            ).fetchone()["n"]
            >= 10
        ):
            raise HTTPException(409, "Each guideline version supports at most 10 source documents.")
        source_id = uuid4()
        directory = LOCAL / "uploads" / str(org_id)
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"{source_id}{suffix}"
        path.write_bytes(data)
        path.chmod(0o600)
        try:
            result = subprocess.run(
                [
                    sys.executable,
                    str(Path(__file__).parents[1] / "ingestion/extract.py"),
                    str(path),
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=15,
                check=False,
            )
            extracted = json.loads(result.stdout)
            if result.returncode or "error" in extracted:
                raise HTTPException(422, extracted.get("error", "Document extraction failed."))
            conn.execute(
                "INSERT INTO source_documents(id,org_id,guideline_version_id,filename,private_path,sha256,extraction_status,extracted_text,locations) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (
                    source_id,
                    org_id,
                    version_id,
                    Path(file.filename.replace("\\", "/")).name[:200],
                    str(path.relative_to(LOCAL)),
                    hashlib.sha256(data).hexdigest(),
                    extracted["status"],
                    extracted["text"],
                    Jsonb(extracted["locations"]),
                ),
            )
            # Deterministic proposals only. These are unapproved source lines, not AI conclusions.
            for number, section in enumerate(extracted["locations"], 1):
                excerpt = section["text"].strip()[:1800]
                if not excerpt:
                    continue
                conn.execute(
                    "INSERT INTO structured_rules(org_id,guideline_version_id,type,rule_key,value,source_document_id,source_excerpt,source_location) VALUES (%s,%s,'approved_fact',%s,%s,%s,%s,%s)",
                    (
                        org_id,
                        version_id,
                        f"proposed_{str(source_id)[:8]}_{number}",
                        excerpt,
                        source_id,
                        excerpt,
                        section["location"],
                    ),
                )
            audit(
                conn,
                user["id"],
                org_id,
                "source.uploaded",
                "source_document",
                source_id,
                {"extraction_status": extracted["status"]},
            )
        except (subprocess.TimeoutExpired, json.JSONDecodeError):
            path.unlink(missing_ok=True)
            raise HTTPException(
                422, "Document could not be extracted within the supported limits."
            ) from None
        except Exception:
            path.unlink(missing_ok=True)
            raise
    return {
        "id": source_id,
        "extraction_status": extracted["status"],
        "message": "Text extracted. Proposed source lines require owner review; no AI interpretation was performed.",
    }


@router.get("/sources/{source_id}")
def source(org_id: UUID, source_id: UUID, user=User):
    with org_transaction(user, org_id) as (conn, _):
        row = conn.execute(
            "SELECT id,filename,extraction_status,locations FROM source_documents WHERE org_id=%s AND id=%s",
            (org_id, source_id),
        ).fetchone()
        if not row:
            raise HTTPException(404, "Source not found.")
        return row


@router.get("/sources/{source_id}/download")
def download(org_id: UUID, source_id: UUID, user=User):
    with org_transaction(user, org_id) as (conn, _):
        row = conn.execute(
            "SELECT * FROM source_documents WHERE org_id=%s AND id=%s",
            (org_id, source_id),
        ).fetchone()
        if not row:
            raise HTTPException(404, "Source not found.")
        path = (LOCAL / row["private_path"]).resolve()
        if not path.is_relative_to((LOCAL / "uploads").resolve()) or not path.is_file():
            raise HTTPException(404, "Source file unavailable.")
        return FileResponse(
            path,
            filename=row["filename"],
            media_type=row.get("media_type")
            if row.get("media_type") in ("image/png", "image/jpeg", "application/pdf")
            else "application/octet-stream",
            content_disposition_type="inline"
            if row.get("media_type") in ("image/png", "image/jpeg", "application/pdf")
            else "attachment",
        )
