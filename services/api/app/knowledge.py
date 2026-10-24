"""Owner-confirmed source collections with immutable internal knowledge snapshots."""

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import APIRouter, BackgroundTasks, Form, HTTPException, UploadFile
from psycopg.types.json import Jsonb
from pydantic import Field, field_validator, model_validator

from ingestion.knowledge_intake import MAX_CHUNKS, analyse_chunk, chunks, validate_rule_check
from providers.openrouter import ProviderUnavailable

from .ai_settings import require_consent
from .config import LOCAL
from .db import audit
from .guidelines import check_source, version_record
from .knowledge_snapshots import (
    DEFAULT_CHECKS,
    append_snapshot,
    current_snapshot,
    rule_check,
    rules_overlap,
    snapshot_rules,
)
from .models import Input, RuleInput
from .security import User, org_transaction

router = APIRouter(prefix="/api/organisations/{org_id}/knowledge")


class VersionBody(Input):
    version_id: UUID


class Preferences(VersionBody):
    checks: list[str] = Field(max_length=8)
    instructions: str = Field(default="", max_length=4000)

    @field_validator("checks")
    @classmethod
    def valid_checks(cls, values):
        if any(c not in DEFAULT_CHECKS for c in values) or len(values) != len(set(values)):
            raise ValueError("Select supported, unique check categories.")
        return values


class ProposalBody(RuleInput):
    version_id: UUID
    check: str

    @field_validator("check")
    @classmethod
    def valid_check(cls, value):
        if value not in DEFAULT_CHECKS:
            raise ValueError("Unsupported check category.")
        return value

    @model_validator(mode="after")
    def consistent_check(self):
        validate_rule_check(self, self.check)
        return self


class Confirmation(VersionBody):
    proposal_ids: list[UUID] = Field(max_length=200)
    replace_rule_ids: dict[str, UUID] = Field(default_factory=dict)
    expected_snapshot_id: UUID | None


def editable_collection(conn, org_id, version_id):
    conn.execute("SELECT id FROM organisations WHERE id=%s FOR UPDATE", (org_id,))
    version = version_record(conn, org_id, version_id)
    if version["status"] == "archived":
        raise HTTPException(
            409, "This version is archived. Select the current collection or create a new version."
        )
    return version


def coverage(checks, rules, proposals, sources, extraction):
    complete = extraction["status"] == "completed" and set(extraction.get("source_ids", [])) == {
        str(s["id"]) for s in sources
    }
    output = []
    for check in checks:
        if any(rule_check(r) == check for r in rules):
            status, reason = (
                "available",
                "Confirmed guidance is available across this source collection.",
            )
        elif any(p["check"] == check and p["status"] == "pending" for p in proposals):
            status, reason = (
                "needs_confirmation",
                "Review and confirm the source-backed proposals before using this guidance.",
            )
        elif complete:
            status, reason = (
                "source_missing",
                "No guidance for this check was found across the processed sources. Add a source or a company-entered rule.",
            )
        else:
            status, reason = (
                "not_checked",
                "Source analysis is incomplete or has not run. Missing guidance cannot yet be determined.",
            )
        output.append({"check": check, "status": status, "reason": reason})
    return output


def knowledge_view(conn, org_id, version_id=None):
    if version_id:
        version = version_record(conn, org_id, version_id)
    else:
        version = conn.execute(
            "SELECT * FROM guideline_versions WHERE org_id=%s ORDER BY (status='draft') DESC,(status='active') DESC,version DESC LIMIT 1",
            (org_id,),
        ).fetchone()
    if not version:
        return {
            "version": None,
            "snapshot_id": None,
            "checks": DEFAULT_CHECKS,
            "instructions": "",
            "sources": [],
            "rules": [],
            "proposals": [],
            "coverage": [],
            "extraction": {"status": "not_started"},
        }
    snapshot = current_snapshot(conn, org_id, version["id"])
    rules = snapshot_rules(conn, org_id, snapshot["id"]) if snapshot else []
    # Existing draft-rule administration remains usable through the simpler screen.
    legacy = conn.execute(
        "SELECT * FROM structured_rules WHERE org_id=%s AND guideline_version_id=%s AND approved_by IS NULL ORDER BY created_at,id",
        (org_id, version["id"]),
    ).fetchall()
    proposals = conn.execute(
        "SELECT *,check_name AS check FROM knowledge_proposals WHERE org_id=%s AND guideline_version_id=%s ORDER BY created_at,id",
        (org_id, version["id"]),
    ).fetchall()
    known = {str(p["id"]) for p in proposals}
    for row in legacy:
        if str(row["id"]) not in known:
            proposals.append(
                {
                    **row,
                    "check": rule_check(row),
                    "status": "pending",
                    "method": "local_suggestion"
                    if row["source_document_id"]
                    else "company_entered",
                    "existing_rule_id": None,
                }
            )
    sources = conn.execute(
        "SELECT id,filename,media_type,extraction_status,locations,sha256 FROM source_documents WHERE org_id=%s AND guideline_version_id=%s ORDER BY created_at,id",
        (org_id, version["id"]),
    ).fetchall()
    for source in sources:
        source["download_url"] = f"/api/organisations/{org_id}/sources/{source['id']}/download"
        source["warnings"] = [s["warning"] for s in source["locations"] if s.get("warning")]
    extraction = conn.execute(
        "SELECT id,status,error,processed,total,source_ids,metadata FROM knowledge_extractions WHERE org_id=%s AND guideline_version_id=%s ORDER BY created_at DESC LIMIT 1",
        (org_id, version["id"]),
    ).fetchone() or {"status": "not_started"}
    return {
        "version": {key: version[key] for key in ("id", "version", "status")},
        "snapshot_id": snapshot["id"] if snapshot else None,
        "checks": version["checks"],
        "instructions": version["instructions"],
        "sources": sources,
        "rules": rules,
        "proposals": proposals,
        "coverage": coverage(version["checks"], rules, proposals, sources, extraction),
        "extraction": extraction,
        "limits": {
            "max_file_bytes": 5 * 1024 * 1024,
            "max_pdf_pages": 100,
            "max_extracted_characters": 200000,
            "max_sources": 10,
            "max_ai_chunks_per_run": MAX_CHUNKS,
        },
    }


@router.get("")
@router.get("/")
def get_knowledge(org_id: UUID, version_id: UUID | None = None, user=User):
    with org_transaction(user, org_id) as (conn, _):
        return knowledge_view(conn, org_id, version_id)


@router.post("/new-version", status_code=201)
def new_version(org_id: UUID, user=User):
    with org_transaction(user, org_id, owner=True) as (conn, _):
        conn.execute("SELECT id FROM organisations WHERE id=%s FOR UPDATE", (org_id,))
        number = conn.execute(
            "SELECT coalesce(max(version),0)+1 AS n FROM guideline_versions WHERE org_id=%s",
            (org_id,),
        ).fetchone()["n"]
        version_id = uuid4()
        conn.execute(
            "INSERT INTO guideline_versions(id,org_id,version,checks) VALUES (%s,%s,%s,'[]')",
            (version_id, org_id, number),
        )
        audit(
            conn,
            user["id"],
            org_id,
            "guideline.created",
            "guideline_version",
            version_id,
            {"version": number, "empty": True},
        )
        return knowledge_view(conn, org_id, version_id)


@router.post("/preferences")
def preferences(org_id: UUID, body: Preferences, user=User):
    with org_transaction(user, org_id, owner=True) as (conn, _):
        version = editable_collection(conn, org_id, body.version_id)
        changed = version["checks"] != body.checks or version["instructions"] != body.instructions
        updated = conn.execute(
            "UPDATE guideline_versions SET checks=%s,instructions=%s WHERE org_id=%s AND id=%s RETURNING *",
            (Jsonb(body.checks), body.instructions, org_id, body.version_id),
        ).fetchone()
        snapshot = current_snapshot(conn, org_id, body.version_id)
        if changed and snapshot:
            append_snapshot(
                conn, org_id, updated, snapshot_rules(conn, org_id, snapshot["id"]), user["id"]
            )
        audit(
            conn,
            user["id"],
            org_id,
            "knowledge.preferences_confirmed",
            "guideline_version",
            body.version_id,
        )
        return knowledge_view(conn, org_id, body.version_id)


def insert_proposal(conn, org_id, version_id, body, method):
    snapshot = current_snapshot(conn, org_id, version_id)
    rules = snapshot_rules(conn, org_id, snapshot["id"]) if snapshot else []
    existing = next((r for r in rules if rules_overlap(r, body)), None)
    row = conn.execute(
        "INSERT INTO knowledge_proposals(org_id,guideline_version_id,type,rule_key,value,check_name,scope_channel,source_document_id,source_excerpt,source_location,fact,existing_rule_id,method) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING *,check_name AS check",
        (
            org_id,
            version_id,
            body["type"],
            body["rule_key"],
            body["value"],
            body["check"],
            body.get("scope_channel", "global"),
            body.get("source_document_id"),
            body.get("source_excerpt"),
            body.get("source_location"),
            Jsonb(body["fact"]) if body.get("fact") else None,
            existing["id"] if existing else None,
            method,
        ),
    ).fetchone()
    return row


@router.post("/proposals", status_code=201)
def manual_proposal(org_id: UUID, body: ProposalBody, user=User):
    with org_transaction(user, org_id, owner=True) as (conn, _):
        editable_collection(conn, org_id, body.version_id)
        check_source(conn, org_id, body.version_id, body)
        return insert_proposal(
            conn, org_id, body.version_id, body.model_dump(mode="json"), "company_entered"
        )


@router.patch("/proposals/{proposal_id}")
def edit_proposal(org_id: UUID, proposal_id: UUID, body: ProposalBody, user=User):
    with org_transaction(user, org_id, owner=True) as (conn, _):
        editable_collection(conn, org_id, body.version_id)
        proposal = conn.execute(
            "SELECT * FROM knowledge_proposals WHERE org_id=%s AND guideline_version_id=%s AND id=%s FOR UPDATE",
            (org_id, body.version_id, proposal_id),
        ).fetchone()
        if not proposal:
            legacy = conn.execute(
                "SELECT * FROM structured_rules WHERE org_id=%s AND guideline_version_id=%s AND id=%s FOR UPDATE",
                (org_id, body.version_id, proposal_id),
            ).fetchone()
            if not legacy:
                raise HTTPException(404, "Proposal not found in this version.")
            if legacy["approved_by"]:
                raise HTTPException(409, "Confirmed rules require a new proposal.")
            # Existing unapproved source lines are visible proposals too. Preserve their
            # legacy record while staging an editable copy under the same visible ID.
            proposal = conn.execute(
                "INSERT INTO knowledge_proposals(id,org_id,guideline_version_id,type,rule_key,value,check_name,scope_channel,source_document_id,source_excerpt,source_location,fact,method) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING *",
                (
                    legacy["id"],
                    org_id,
                    body.version_id,
                    legacy["type"],
                    legacy["rule_key"],
                    legacy["value"],
                    rule_check(legacy),
                    legacy["scope_channel"],
                    legacy["source_document_id"],
                    legacy["source_excerpt"],
                    legacy["source_location"],
                    Jsonb(legacy["fact"]) if legacy["fact"] else None,
                    "local_suggestion" if legacy["source_document_id"] else "company_entered",
                ),
            ).fetchone()
        if proposal["status"] != "pending":
            raise HTTPException(
                409, "Only pending proposals can be edited. Confirmed rules require a new proposal."
            )
        source_fields = {"source_document_id", "source_excerpt", "source_location"}
        provided_sources = source_fields & body.model_fields_set
        changes = body.model_dump(mode="json")
        if provided_sources and provided_sources != source_fields:
            raise HTTPException(
                422,
                "Provide source document, excerpt and location together, or preserve the existing evidence.",
            )
        if not provided_sources:
            changes.update({key: proposal[key] for key in source_fields})
        validated = ProposalBody.model_validate(changes)
        check_source(conn, org_id, body.version_id, validated)
        snapshot = current_snapshot(conn, org_id, body.version_id)
        rules = snapshot_rules(conn, org_id, snapshot["id"]) if snapshot else []
        existing = next((r for r in rules if rules_overlap(r, changes)), None)
        row = conn.execute(
            "UPDATE knowledge_proposals SET type=%s,rule_key=%s,value=%s,check_name=%s,scope_channel=%s,source_document_id=%s,source_excerpt=%s,source_location=%s,fact=%s,existing_rule_id=%s,method='company_entered' WHERE org_id=%s AND guideline_version_id=%s AND id=%s RETURNING *,check_name AS check",
            (
                validated.type,
                validated.rule_key,
                validated.value,
                validated.check,
                validated.scope_channel,
                validated.source_document_id,
                validated.source_excerpt,
                validated.source_location,
                Jsonb(validated.fact.model_dump(mode="json")) if validated.fact else None,
                existing["id"] if existing else None,
                org_id,
                body.version_id,
                proposal_id,
            ),
        ).fetchone()
        audit(
            conn,
            user["id"],
            org_id,
            "knowledge.proposal_edited",
            "knowledge_proposal",
            proposal_id,
            {
                "source_changed": any(
                    str(proposal[key]) != str(getattr(validated, key)) for key in source_fields
                ),
                "requires_confirmation": True,
            },
        )
        return row


def save_source(conn, org_id, version_id, file, actor_id):
    """Save a private file and literal extraction; does not invoke AI or confirm rules."""
    suffix = Path(file.filename or "").suffix.lower()
    media = {
        ".pdf": "application/pdf",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
    }
    if suffix not in media or file.content_type not in (
        media.get(suffix),
        "application/octet-stream",
    ):
        raise HTTPException(
            415,
            "Upload PDF, DOCX, PNG or JPEG (maximum 5 MB; PDF maximum 100 pages; extracted text maximum 200,000 characters).",
        )
    data = file.file.read(5 * 1024 * 1024 + 1)
    if len(data) > 5 * 1024 * 1024:
        raise HTTPException(413, "File exceeds 5 MB.")
    if (
        conn.execute(
            "SELECT count(*) AS n FROM source_documents WHERE org_id=%s AND guideline_version_id=%s AND extraction_status<>'embedded_reference'",
            (org_id, version_id),
        ).fetchone()["n"]
        >= 10
    ):
        raise HTTPException(409, "Each visible version supports at most 10 sources.")
    source_id = uuid4()
    directory = LOCAL / "uploads" / str(org_id)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{source_id}{suffix}"
    filename = Path((file.filename or "Source").replace("\\", "/")).name[:200]
    created_paths = [path]
    embedded = {"images": [], "warnings": []}
    try:
        if suffix in (".pdf", ".docx"):
            if not data.startswith(b"%PDF" if suffix == ".pdf" else b"PK"):
                raise HTTPException(422, "File contents do not match its extension.")
            path.write_bytes(data)
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
                if "No selectable text was found" in extracted.get("error", ""):
                    extracted = {
                        "status": "partial",
                        "text": "",
                        "locations": [
                            {
                                "location": "Text extraction availability",
                                "text": "",
                                "warning": "No selectable text found. OCR is unavailable; extracted images can be confirmed as visual references only.",
                            }
                        ],
                    }
                else:
                    raise HTTPException(422, extracted.get("error", "Document extraction failed."))
            # A separate bounded process preserves text intake even when visual extraction fails.
            visual_directory = directory / f"{source_id}_references"
            visual_directory.mkdir(exist_ok=True)
            try:
                visual_result = subprocess.run(
                    [
                        sys.executable,
                        str(Path(__file__).parents[1] / "ingestion/knowledge_intake.py"),
                        str(path),
                        str(visual_directory),
                    ],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    timeout=15,
                    check=False,
                )
                embedded = json.loads(visual_result.stdout)
                if not isinstance(embedded.get("images"), list):
                    raise ValueError("Invalid extraction output")
            except (ValueError, subprocess.TimeoutExpired):
                embedded = {
                    "images": [],
                    "warnings": [
                        "Embedded visual references could not be extracted; upload PNG/JPEG reference files separately."
                    ],
                }
            if embedded.get("warnings"):
                extracted["status"] = "partial"
                extracted["locations"].extend(
                    {"location": "Visual extraction availability", "text": "", "warning": warning}
                    for warning in embedded["warnings"]
                )
        else:
            from io import BytesIO

            from PIL import Image

            with Image.open(BytesIO(data)) as image:
                if (
                    image.format != ("PNG" if suffix == ".png" else "JPEG")
                    or image.width * image.height > 16000000
                ):
                    raise HTTPException(
                        422, "Image format is invalid or exceeds 16 million pixels."
                    )
                image.verify()
            path.write_bytes(data)
            label = f"Company-uploaded reference image: {filename}"
            extracted = {
                "status": "reference_only",
                "text": label,
                "locations": [{"location": "Reference image", "text": label}],
            }
        path.chmod(0o600)
        conn.execute(
            "INSERT INTO source_documents(id,org_id,guideline_version_id,filename,private_path,sha256,extraction_status,extracted_text,locations,media_type) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (
                source_id,
                org_id,
                version_id,
                filename,
                str(path.relative_to(LOCAL)),
                hashlib.sha256(data).hexdigest(),
                extracted["status"],
                extracted["text"],
                Jsonb(extracted["locations"]),
                media[suffix],
            ),
        )
        if suffix in (".png", ".jpg", ".jpeg"):
            insert_proposal(
                conn,
                org_id,
                version_id,
                {
                    "type": "approved_fact",
                    "rule_key": f"reference_{source_id.hex}",
                    "value": filename,
                    "check": "logos",
                    "source_document_id": source_id,
                    "source_excerpt": extracted["text"],
                    "source_location": "Reference image",
                },
                "company_entered",
            )
        for index, image in enumerate(embedded["images"], 1):
            image_path = (visual_directory / image["filename"]).resolve()
            if (
                not image_path.is_relative_to(visual_directory.resolve())
                or not image_path.is_file()
            ):
                continue
            created_paths.append(image_path)
            image_id = uuid4()
            label = f"Embedded company reference image from {filename}, {image['location']}"
            image_bytes = image_path.read_bytes()
            locations = [
                {
                    "location": image["location"],
                    "text": label,
                    "parent_source_document_id": str(source_id),
                }
            ]
            conn.execute(
                "INSERT INTO source_documents(id,org_id,guideline_version_id,filename,private_path,sha256,extraction_status,extracted_text,locations,media_type) VALUES (%s,%s,%s,%s,%s,%s,'embedded_reference',%s,%s,'image/png')",
                (
                    image_id,
                    org_id,
                    version_id,
                    f"{filename} — image {index}.png"[:200],
                    str(image_path.relative_to(LOCAL.resolve())),
                    hashlib.sha256(image_bytes).hexdigest(),
                    label,
                    Jsonb(locations),
                ),
            )
            insert_proposal(
                conn,
                org_id,
                version_id,
                {
                    "type": "approved_fact",
                    "rule_key": f"reference_{image_id.hex}",
                    "value": f"{filename} — image {index}",
                    "check": "logos",
                    "source_document_id": image_id,
                    "source_excerpt": label,
                    "source_location": image["location"],
                },
                "company_entered",
            )
        audit(
            conn,
            actor_id,
            org_id,
            "source.uploaded",
            "source_document",
            source_id,
            {"extraction_status": extracted["status"], "provider_called": False},
        )
        return source_id
    except HTTPException:
        for created in created_paths:
            created.unlink(missing_ok=True)
        raise
    except Exception:
        for created in created_paths:
            created.unlink(missing_ok=True)
        raise HTTPException(422, "Source could not be read within the supported limits.") from None


@router.post("/sources", status_code=201)
def upload_source(org_id: UUID, file: UploadFile, version_id: UUID = Form(...), user=User):
    with org_transaction(user, org_id, owner=True) as (conn, _):
        editable_collection(conn, org_id, version_id)
        save_source(conn, org_id, version_id, file, user["id"])
        return knowledge_view(conn, org_id, version_id)


@router.post("/confirm")
def confirm(org_id: UUID, body: Confirmation, user=User):
    with org_transaction(user, org_id, owner=True) as (conn, _):
        version = editable_collection(conn, org_id, body.version_id)
        snapshot = current_snapshot(conn, org_id, body.version_id)
        if str(snapshot["id"] if snapshot else None) != str(body.expected_snapshot_id):
            raise HTTPException(
                409, "Knowledge changed in another window. Reload the evidence before confirming."
            )
        if len(set(body.proposal_ids)) != len(body.proposal_ids):
            raise HTTPException(422, "Select each proposal once.")
        if set(body.replace_rule_ids) - {str(i) for i in body.proposal_ids}:
            raise HTTPException(422, "Replacement confirmation must refer to a selected proposal.")
        rules = (
            snapshot_rules(conn, org_id, snapshot["id"])
            if snapshot
            else conn.execute(
                "SELECT * FROM structured_rules WHERE org_id=%s AND guideline_version_id=%s AND approved_by IS NOT NULL ORDER BY created_at,id",
                (org_id, body.version_id),
            ).fetchall()
        )
        for proposal_id in body.proposal_ids:
            row = conn.execute(
                "SELECT *,check_name AS check FROM knowledge_proposals WHERE org_id=%s AND guideline_version_id=%s AND id=%s AND status='pending' FOR UPDATE",
                (org_id, body.version_id, proposal_id),
            ).fetchone()
            legacy = False
            if not row:
                row = conn.execute(
                    "SELECT * FROM structured_rules WHERE org_id=%s AND guideline_version_id=%s AND id=%s AND approved_by IS NULL FOR UPDATE",
                    (org_id, body.version_id, proposal_id),
                ).fetchone()
                legacy = True
            if not row:
                raise HTTPException(
                    409, "A selected proposal is unavailable or was already confirmed."
                )
            parsed = RuleInput.model_validate(
                {
                    key: row.get(key)
                    for key in (
                        "type",
                        "rule_key",
                        "value",
                        "source_document_id",
                        "source_excerpt",
                        "source_location",
                        "fact",
                        "scope_channel",
                    )
                }
            )
            check_source(conn, org_id, body.version_id, parsed)
            try:
                validate_rule_check(parsed, row.get("check", rule_check(row)))
            except ValueError as error:
                raise HTTPException(422, str(error)) from None
            overlap = [r for r in rules if rules_overlap(r, row)]
            replacement = body.replace_rule_ids.get(str(proposal_id))
            if overlap:
                if len(overlap) != 1 or str(overlap[0]["id"]) != str(replacement):
                    raise HTTPException(
                        409,
                        "This rule overlaps confirmed guidance. Explicitly confirm the old rule to replace.",
                    )
                rules = [r for r in rules if str(r["id"]) != str(replacement)]
            elif replacement:
                raise HTTPException(
                    409, "The selected replacement does not match this fact's identity."
                )
            if legacy:
                rule = conn.execute(
                    "UPDATE structured_rules SET approved_by=%s WHERE org_id=%s AND id=%s RETURNING *",
                    (user["id"], org_id, proposal_id),
                ).fetchone()
            else:
                rule = conn.execute(
                    "INSERT INTO structured_rules(org_id,guideline_version_id,type,rule_key,value,scope_channel,source_document_id,source_excerpt,source_location,fact,approved_by) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING *",
                    (
                        org_id,
                        body.version_id,
                        row["type"],
                        row["rule_key"],
                        row["value"],
                        row["scope_channel"],
                        row["source_document_id"],
                        row["source_excerpt"],
                        row["source_location"],
                        Jsonb(row["fact"]) if row["fact"] else None,
                        user["id"],
                    ),
                ).fetchone()
                conn.execute(
                    "UPDATE knowledge_proposals SET status='confirmed',confirmed_rule_id=%s WHERE org_id=%s AND id=%s",
                    (rule["id"], org_id, proposal_id),
                )
            rules.append({**rule, "check": row.get("check", rule_check(row))})
        if not rules:
            raise HTTPException(409, "Confirm at least one rule or reference before activation.")
        if not body.proposal_ids:
            raise HTTPException(422, "Select at least one pending proposal.")
        if version["status"] == "draft":
            conn.execute(
                "UPDATE guideline_versions SET status='archived' WHERE org_id=%s AND status='active'",
                (org_id,),
            )
            conn.execute(
                "UPDATE guideline_versions SET status='active',approved_by=%s,activated_at=now() WHERE org_id=%s AND id=%s",
                (user["id"], org_id, body.version_id),
            )
        new_snapshot = append_snapshot(conn, org_id, version, rules, user["id"])
        audit(
            conn,
            user["id"],
            org_id,
            "knowledge.confirmed",
            "knowledge_snapshot",
            new_snapshot["id"],
            {
                "version_id": str(body.version_id),
                "proposal_ids": [str(i) for i in body.proposal_ids],
                "replaced_rule_ids": [str(i) for i in body.replace_rule_ids.values()],
            },
        )
        return knowledge_view(conn, org_id, body.version_id)


def run_extraction(user, org_id, version_id, job_id):
    try:
        with org_transaction(user, org_id, owner=True) as (conn, _):
            require_consent(conn, org_id)
            sources = conn.execute(
                "SELECT * FROM source_documents WHERE org_id=%s AND guideline_version_id=%s ORDER BY created_at,id",
                (org_id, version_id),
            ).fetchall()
            parts = list(chunks(sources))
            instructions = version_record(conn, org_id, version_id).get("instructions") or ""
            old = conn.execute(
                "SELECT metadata FROM knowledge_extractions WHERE org_id=%s AND guideline_version_id=%s AND status='partial' AND id<>%s ORDER BY created_at DESC LIMIT 1",
                (org_id, version_id, job_id),
            ).fetchone()
            # Resume only exactly the same immutable source collection.
            source_ids = [str(s["id"]) for s in sources]
            offset = (
                old["metadata"].get("next_chunk", 0)
                if old
                and old["metadata"].get("source_ids") == source_ids
                and not old["metadata"].get("invalid_proposals")
                else 0
            )
            conn.execute(
                "UPDATE knowledge_extractions SET status='running',total=%s,processed=%s,source_ids=%s WHERE org_id=%s AND id=%s",
                (len(parts), offset, Jsonb(source_ids), org_id, job_id),
            )
        processed, invalid = offset, 0

        def usage(status, metadata, attempt=None):
            with org_transaction(user, org_id, owner=True) as (conn, _):
                if attempt:
                    conn.execute(
                        "UPDATE ai_request_usage SET status=%s,metadata=%s WHERE org_id=%s AND id=%s",
                        (status, Jsonb(metadata), org_id, attempt),
                    )
                    return attempt
                attempt = uuid4()
                conn.execute(
                    "INSERT INTO ai_request_usage(id,org_id,actor_id,model,purpose,status,metadata) VALUES (%s,%s,%s,%s,'knowledge_extraction',%s,%s)",
                    (
                        attempt,
                        org_id,
                        user["id"],
                        metadata.get("requested_model", "unknown"),
                        status,
                        Jsonb(metadata),
                    ),
                )
                return attempt

        for batch in parts[offset : offset + MAX_CHUNKS]:
            with org_transaction(user, org_id, owner=True) as (conn, _):
                require_consent(conn, org_id)
                version_record(conn, org_id, version_id)
            candidates, metadata, dropped = analyse_chunk(batch, sources, usage, instructions)
            invalid += dropped
            with org_transaction(user, org_id, owner=True) as (conn, _):
                editable_collection(conn, org_id, version_id)
                require_consent(conn, org_id)
                for candidate in candidates:
                    duplicate = conn.execute(
                        "SELECT 1 FROM knowledge_proposals WHERE org_id=%s AND guideline_version_id=%s AND source_document_id=%s AND source_excerpt=%s AND rule_key=%s AND value=%s AND status<>'discarded'",
                        (
                            org_id,
                            version_id,
                            candidate["source_document_id"],
                            candidate["source_excerpt"],
                            candidate["rule_key"],
                            candidate["value"],
                        ),
                    ).fetchone()
                    if not duplicate:
                        insert_proposal(conn, org_id, version_id, candidate, "ai")
                processed += 1
                conn.execute(
                    "UPDATE knowledge_extractions SET processed=%s,metadata=%s WHERE org_id=%s AND id=%s",
                    (
                        processed,
                        Jsonb(
                            {
                                **metadata,
                                "next_chunk": processed,
                                "source_ids": source_ids,
                                "invalid_proposals": invalid,
                            }
                        ),
                        org_id,
                        job_id,
                    ),
                )
        partial = (
            processed < len(parts)
            or invalid > 0
            or any(s["extraction_status"] == "partial" for s in sources)
        )
        with org_transaction(user, org_id, owner=True) as (conn, _):
            error = (
                "Analysis remains partial: some source chunks or invalid proposals need another check."
                if partial
                else None
            )
            conn.execute(
                "UPDATE knowledge_extractions SET status=%s,error=%s,completed_at=now(),metadata=metadata||%s WHERE org_id=%s AND id=%s",
                (
                    "partial" if partial else "completed",
                    error,
                    Jsonb(
                        {
                            "next_chunk": processed,
                            "source_ids": source_ids,
                            "invalid_proposals": invalid,
                        }
                    ),
                    org_id,
                    job_id,
                ),
            )
    except Exception as error:
        # Only known safe provider messages leave this boundary; never expose request data.
        message = (
            str(error)[:350]
            if isinstance(error, ProviderUnavailable)
            else "Source analysis stopped. Sources are saved; verify membership, consent and provider availability before retrying."
        )
        with org_transaction(user, org_id) as (conn, _):
            conn.execute(
                "UPDATE knowledge_extractions SET status='partial',error=%s,completed_at=now() WHERE org_id=%s AND id=%s",
                (message, org_id, job_id),
            )


@router.post("/analyse", status_code=202)
def analyse(org_id: UUID, body: VersionBody, background: BackgroundTasks, user=User):
    with org_transaction(user, org_id, owner=True) as (conn, _):
        editable_collection(conn, org_id, body.version_id)
        require_consent(conn, org_id)
        conn.execute(
            "UPDATE knowledge_extractions SET status='partial',error='The previous analysis exceeded its time limit or the server restarted. Retry to resume saved progress.',completed_at=now() WHERE org_id=%s AND guideline_version_id=%s AND status IN ('queued','running') AND created_at<now()-interval '15 minutes'",
            (org_id, body.version_id),
        )
        if conn.execute(
            "SELECT 1 FROM knowledge_extractions WHERE org_id=%s AND guideline_version_id=%s AND status IN ('queued','running')",
            (org_id, body.version_id),
        ).fetchone():
            raise HTTPException(409, "Source analysis is already running.")
        if not conn.execute(
            "SELECT 1 FROM source_documents WHERE org_id=%s AND guideline_version_id=%s",
            (org_id, body.version_id),
        ).fetchone():
            raise HTTPException(409, "Add a source before analysing.")
        recent = conn.execute(
            "SELECT count(*) AS n FROM knowledge_extractions WHERE org_id=%s AND created_at>now()-interval '1 hour'",
            (org_id,),
        ).fetchone()["n"]
        if recent >= 6:
            raise HTTPException(
                429, "Source analysis reached the six-run hourly limit. Retry later."
            )
        job = conn.execute(
            "INSERT INTO knowledge_extractions(org_id,guideline_version_id,actor_id,status) VALUES (%s,%s,%s,'queued') RETURNING id,status",
            (org_id, body.version_id, user["id"]),
        ).fetchone()
        audit(
            conn,
            user["id"],
            org_id,
            "knowledge.analysis_requested",
            "knowledge_extraction",
            job["id"],
        )
    background.add_task(run_extraction, user, org_id, body.version_id, job["id"])
    return {"extraction": job}
