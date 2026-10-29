import hashlib
import json
from io import BytesIO
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import APIRouter, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, Response
from psycopg.types.json import Jsonb

from ingestion.document_projection import canonical, project_document
from ingestion.image_projection import project_image

from .config import LOCAL
from .db import audit
from .review_models import (
    CampaignSave,
    DraftCreate,
    DraftSave,
    RestoreVersion,
    ScopeSave,
    TranscriptSave,
)
from .review_scope import PLATFORMS
from .security import User, org_transaction

router = APIRouter(prefix="/api/organisations/{org_id}/drafts")


def get_draft(conn, org_id, draft_id, user, member, edit=False):
    row = conn.execute(
        "SELECT * FROM drafts WHERE org_id=%s AND id=%s FOR UPDATE", (org_id, draft_id)
    ).fetchone()
    if not row or (member["role"] == "creator" and row["creator_id"] != user["id"]):
        raise HTTPException(404, "Draft not found or unavailable.")
    if edit and row["creator_id"] != user["id"]:
        raise HTTPException(403, "Only the creator can edit this draft.")
    return row


def version_view(row):
    return {k: v for k, v in row.items() if k != "private_path"}


def save_version(conn, org_id, draft, user, text=None, data=None, filename=None):
    version_id = uuid4()
    private_path = None
    if data is not None:
        suffix = Path(filename).suffix.lower()
        if suffix == ".docx":
            try:
                projection = project_document(data)
            except (ValueError, KeyError) as error:
                raise HTTPException(422, str(error)) from None
        elif suffix == ".pdf":
            from pypdf import PdfReader

            try:
                reader = PdfReader(BytesIO(data), strict=True)
                if reader.is_encrypted or len(reader.pages) > 100:
                    raise ValueError()
                pages = [p.extract_text() or "" for p in reader.pages]
                uncertain_pages = [
                    i + 1
                    for i, page in enumerate(reader.pages)
                    if not pages[i].strip() or len(page.images) > 0
                ]
                text = canonical("\n".join(pages))
                if not text.strip() or len(text) > 30000:
                    raise ValueError()
                projection = {
                    "text": text,
                    "blocks": [],
                    "unresolved_changes": 0,
                    "coverage": {
                        "text_complete": not uncertain_pages,
                        "unsupported": [
                            f"Page {i}: image or missing text; full wording extraction cannot be verified. Use a verified DOCX/text source."
                            for i in uncertain_pages
                        ],
                        "exclusions": ["PDF graphics and layout require human inspection."],
                        "parts": ["PDF selectable text"],
                    },
                }
            except Exception:
                raise HTTPException(
                    422,
                    "Upload an unlocked text-based PDF with at most 100 pages and 30,000 characters. Scanned PDF OCR is unavailable.",
                ) from None
        elif suffix in (".png", ".jpg", ".jpeg"):
            try:
                projection = project_image(data, verified_text=text)
                if (suffix == ".png") != (projection["image"]["format"] == "PNG"):
                    raise ValueError("The image format does not match its filename extension.")
            except ValueError as error:
                raise HTTPException(422, str(error)) from None
        else:
            raise HTTPException(415, "Supported formats: DOCX, text-based PDF, PNG and JPEG.")
        if len(projection["text"]) > 30000:
            raise HTTPException(
                422, "Review supports at most 30,000 characters. Split this document."
            )
        directory = LOCAL / "content" / str(org_id)
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"{version_id}{suffix}"
        path.write_bytes(data)
        path.chmod(0o600)
        private_path = str(path.relative_to(LOCAL))
        text = projection["text"]
        file_hash = hashlib.sha256(data).hexdigest()
    else:
        text = canonical(text)
        if not text.strip():
            raise HTTPException(422, "Enter some content first.")
        file_hash = None
        projection = {
            "text": text,
            "blocks": [
                {"part": "text", "block_id": "text", "start": 0, "end": len(text), "quote": text}
            ],
            "coverage": {
                "text_complete": True,
                "unsupported": [],
                "exclusions": [],
                "parts": ["Text"],
            },
            "unresolved_changes": 0,
        }
    artifact_hash = file_hash or hashlib.sha256(text.encode()).hexdigest()
    if draft["format"] == "image":
        artifact_hash = hashlib.sha256((file_hash + "\0" + text).encode()).hexdigest()
    revision = conn.execute(
        "SELECT coalesce(max(revision),0)+1 AS n FROM draft_versions WHERE org_id=%s AND draft_id=%s",
        (org_id, draft["id"]),
    ).fetchone()["n"]
    row = conn.execute(
        "INSERT INTO draft_versions(id,org_id,draft_id,revision,author_id,text,artifact_sha256,file_sha256,private_path,filename,projection) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING *",
        (
            version_id,
            org_id,
            draft["id"],
            revision,
            user["id"],
            text,
            artifact_hash,
            file_hash,
            private_path,
            filename,
            Jsonb(projection),
        ),
    ).fetchone()
    conn.execute(
        "UPDATE drafts SET current_version_id=%s,status='draft',updated_at=now() WHERE org_id=%s AND id=%s",
        (version_id, org_id, draft["id"]),
    )
    conn.execute(
        "UPDATE approval_requests SET status='superseded' WHERE org_id=%s AND draft_id=%s AND status='pending'",
        (org_id, draft["id"]),
    )
    audit(
        conn, user["id"], org_id, "draft.saved", "draft_version", version_id, {"revision": revision}
    )
    return version_view(row)


def create_record(conn, org_id, user, title, channel, format):
    return conn.execute(
        "INSERT INTO drafts(id,org_id,creator_id,title,channel,format) VALUES (%s,%s,%s,%s,%s,%s) RETURNING *",
        (uuid4(), org_id, user["id"], title, channel, format),
    ).fetchone()


@router.post("", status_code=201)
def create(org_id: UUID, body: DraftCreate, user=User):
    with org_transaction(user, org_id) as (conn, _):
        draft = create_record(conn, org_id, user, body.title, body.channel, "text")
        draft = set_scope(
            conn, org_id, draft, body.model_dump(), preserve_channel=body.category is None
        )
        version = save_version(conn, org_id, draft, user, text=body.text)
        return {**draft, "current_version_id": version["id"], "current_version": version}


@router.post("/upload", status_code=201)
def upload(
    org_id: UUID,
    file: UploadFile,
    title: str = Form("Document review"),
    channel: str = Form("general"),
    category: str | None = Form(None),
    platform: str | None = Form(None),
    requested_checks: str | None = Form(None),
    task_instructions: str = Form(""),
    campaign: str = Form(""),
    user=User,
):
    if (
        channel not in {"general", "website", "email", "advertisement", *PLATFORMS}
        or not 1 <= len(title) <= 160
    ):
        raise HTTPException(422, "Invalid title or channel.")
    data = file.file.read(5 * 1024 * 1024 + 1)
    if len(data) > 5 * 1024 * 1024:
        raise HTTPException(413, "Maximum file size is 5 MB.")
    filename = Path((file.filename or "document").replace("\\", "/")).name[:160]
    if Path(filename).suffix.lower() not in (".docx", ".pdf", ".png", ".jpg", ".jpeg"):
        raise HTTPException(415, "Use DOCX, PDF, PNG or JPEG. Video review is not supported.")
    try:
        checks = json.loads(requested_checks) if requested_checks else None
        validated = DraftCreate(
            campaign=campaign,
            title=title,
            channel=channel,
            text="scope",
            category=category,
            platform=platform or None,
            requested_checks=checks,
            task_instructions=task_instructions,
        )
    except (ValueError, TypeError):
        raise HTTPException(422, "Choose valid review categories and checks.") from None
    with org_transaction(user, org_id) as (conn, _):
        draft = create_record(
            conn,
            org_id,
            user,
            title,
            channel,
            "image"
            if Path(filename).suffix.lower() in (".png", ".jpg", ".jpeg")
            else Path(filename).suffix.lower().lstrip("."),
        )
        draft = set_scope(
            conn, org_id, draft, validated.model_dump(), preserve_channel=category is None
        )
        version = save_version(conn, org_id, draft, user, data=data, filename=filename)
        return {**draft, "current_version_id": version["id"], "current_version": version}


def set_scope(conn, org_id, draft, body, preserve_channel=False):
    channel = (
        draft["channel"]
        if preserve_channel
        else body.get("platform")
        or {"email": "email", "website": "website", "visuals": "advertisement"}.get(
            body.get("category"), "general"
        )
    )
    return conn.execute(
        "UPDATE drafts SET category=%s,platform=%s,requested_checks=%s,task_instructions=%s,channel=%s,campaign=%s WHERE org_id=%s AND id=%s RETURNING *",
        (
            body.get("category")
            or {"email": "email", "website": "website", "advertisement": "visuals"}.get(
                channel, "social_media" if channel in PLATFORMS else "other"
            ),
            body.get("platform") or (channel if channel in PLATFORMS else None),
            Jsonb(sorted(set(body.get("requested_checks") or []))),
            body.get("task_instructions") or "",
            channel,
            body.get("campaign", draft.get("campaign", "")).strip(),
            org_id,
            draft["id"],
        ),
    ).fetchone()


@router.post("/{draft_id}/campaign")
def update_campaign(org_id: UUID, draft_id: UUID, body: CampaignSave, user=User):
    with org_transaction(user, org_id) as (conn, member):
        draft = get_draft(conn, org_id, draft_id, user, member, edit=True)
        if draft["current_version_id"] != body.expected_current_version_id:
            raise HTTPException(409, "The draft changed. Reload before updating its campaign.")
        conn.execute("UPDATE drafts SET campaign=%s WHERE org_id=%s AND id=%s", (body.campaign.strip(), org_id, draft_id))
        audit(conn, user["id"], org_id, "draft.campaign_changed", "draft", draft_id)
        return {"campaign": body.campaign.strip()}


@router.post("/{draft_id}/scope")
def update_scope(org_id: UUID, draft_id: UUID, body: ScopeSave, user=User):
    with org_transaction(user, org_id) as (conn, member):
        conn.execute("SELECT id FROM organisations WHERE id=%s FOR UPDATE", (org_id,))
        draft = get_draft(conn, org_id, draft_id, user, member, edit=True)
        if draft["current_version_id"] != body.expected_current_version_id:
            raise HTTPException(
                409, "The saved revision changed. Reload before changing review tasks."
            )
        updated = set_scope(conn, org_id, draft, body.model_dump())
        if any(
            updated.get(key) != draft.get(key)
            for key in ("category", "platform", "requested_checks", "task_instructions", "channel")
        ):
            conn.execute(
                "UPDATE approval_requests SET status='superseded' WHERE org_id=%s AND draft_id=%s AND status='pending'",
                (org_id, draft_id),
            )
            conn.execute(
                "UPDATE drafts SET status='draft',updated_at=now() WHERE org_id=%s AND id=%s",
                (org_id, draft_id),
            )
            audit(conn, user["id"], org_id, "review.scope_changed", "draft", draft_id)
        return updated


@router.get("")
def listing(org_id: UUID, user=User):
    with org_transaction(user, org_id) as (conn, member):
        return conn.execute(
            "SELECT d.*,u.name AS creator_name,v.revision,v.text AS preview FROM drafts d JOIN users u ON u.id=d.creator_id JOIN draft_versions v ON v.org_id=d.org_id AND v.id=d.current_version_id WHERE d.org_id=%s AND (%s OR d.creator_id=%s) ORDER BY d.updated_at DESC LIMIT 200",
            (org_id, member["role"] != "creator", user["id"]),
        ).fetchall()


@router.get("/{draft_id}")
def detail(org_id: UUID, draft_id: UUID, user=User):
    with org_transaction(user, org_id) as (conn, member):
        draft = get_draft(conn, org_id, draft_id, user, member)
        versions = conn.execute(
            "SELECT * FROM draft_versions WHERE org_id=%s AND draft_id=%s ORDER BY revision DESC",
            (org_id, draft_id),
        ).fetchall()
        runs = conn.execute(
            "SELECT * FROM review_runs WHERE org_id=%s AND draft_id=%s ORDER BY created_at DESC LIMIT 30",
            (org_id, draft_id),
        ).fetchall()
        comments = conn.execute(
            "SELECT c.*,u.name AS actor_name FROM review_comments c JOIN users u ON u.id=c.actor_id WHERE c.org_id=%s AND c.draft_id=%s ORDER BY c.created_at",
            (org_id, draft_id),
        ).fetchall()
        requests = conn.execute(
            "SELECT a.*,u.name AS reviewer_name FROM approval_requests a JOIN users u ON u.id=a.reviewer_id WHERE a.org_id=%s AND a.draft_id=%s ORDER BY a.created_at DESC",
            (org_id, draft_id),
        ).fetchall()
        decisions = conn.execute(
            "SELECT a.*,u.name AS actor_name FROM approval_decisions a JOIN users u ON u.id=a.actor_id JOIN approval_requests r ON r.org_id=a.org_id AND r.id=a.request_id WHERE a.org_id=%s AND r.draft_id=%s ORDER BY a.created_at DESC",
            (org_id, draft_id),
        ).fetchall()
        return {
            **draft,
            "current_version": version_view(versions[0]),
            "versions": [version_view(v) for v in versions],
            "runs": runs,
            "comments": comments,
            "approval_requests": requests,
            "decisions": decisions,
        }


@router.post("/{draft_id}/versions", status_code=201)
def save(org_id: UUID, draft_id: UUID, body: DraftSave, user=User):
    with org_transaction(user, org_id) as (conn, member):
        draft = get_draft(conn, org_id, draft_id, user, member, edit=True)
        if draft["format"] != "text":
            raise HTTPException(409, "Save the document file to retain its layout.")
        if draft["current_version_id"] != body.expected_current_version_id:
            raise HTTPException(
                409, "A newer revision exists. Keep your local edits and reload before saving."
            )
        return save_version(conn, org_id, draft, user, text=body.text)


@router.post("/{draft_id}/transcript", status_code=201)
def transcript(org_id: UUID, draft_id: UUID, body: TranscriptSave, user=User):
    with org_transaction(user, org_id) as (conn, member):
        draft = get_draft(conn, org_id, draft_id, user, member, edit=True)
        if (
            draft["format"] != "image"
            or draft["current_version_id"] != body.expected_current_version_id
        ):
            raise HTTPException(
                409, "Use the current image revision before verifying its transcript."
            )
        version = conn.execute(
            "SELECT * FROM draft_versions WHERE org_id=%s AND id=%s",
            (org_id, draft["current_version_id"]),
        ).fetchone()
        path = (LOCAL / version["private_path"]).resolve()
        if not path.is_relative_to((LOCAL / "content").resolve()) or not path.is_file():
            raise HTTPException(404, "Image unavailable.")
        row = save_version(
            conn,
            org_id,
            draft,
            user,
            text=body.text,
            data=path.read_bytes(),
            filename=version["filename"],
        )
        audit(conn, user["id"], org_id, "image.transcript_verified", "draft_version", row["id"])
        return row


@router.post("/{draft_id}/file-versions", status_code=201)
def save_file(
    org_id: UUID,
    draft_id: UUID,
    file: UploadFile,
    expected_current_version_id: UUID = Form(...),
    user=User,
):
    data = file.file.read(5 * 1024 * 1024 + 1)
    if len(data) > 5 * 1024 * 1024:
        raise HTTPException(413, "Maximum file size is 5 MB.")
    with org_transaction(user, org_id) as (conn, member):
        draft = get_draft(conn, org_id, draft_id, user, member, edit=True)
        if draft["format"] != "docx" or Path(file.filename or "").suffix.lower() != ".docx":
            raise HTTPException(415, "This editor saves DOCX documents.")
        if draft["current_version_id"] != expected_current_version_id:
            raise HTTPException(
                409, "This document changed elsewhere. Download your edits before reloading."
            )
        return save_version(conn, org_id, draft, user, data=data, filename=Path(file.filename).name)


@router.post("/{draft_id}/restore", status_code=201)
def restore(org_id: UUID, draft_id: UUID, body: RestoreVersion, user=User):
    with org_transaction(user, org_id) as (conn, member):
        draft = get_draft(conn, org_id, draft_id, user, member, edit=True)
        if draft["current_version_id"] != body.expected_current_version_id:
            raise HTTPException(409, "The current revision changed. Reload before restoring.")
        version = conn.execute(
            "SELECT * FROM draft_versions WHERE org_id=%s AND draft_id=%s AND id=%s",
            (org_id, draft_id, body.source_version_id),
        ).fetchone()
        if not version:
            raise HTTPException(404, "Saved revision unavailable.")
        if version["private_path"]:
            path = (LOCAL / version["private_path"]).resolve()
            if not path.is_relative_to((LOCAL / "content").resolve()) or not path.is_file():
                raise HTTPException(404, "Original file unavailable.")
            row = save_version(
                conn,
                org_id,
                draft,
                user,
                data=path.read_bytes(),
                filename=version["filename"],
                text=version["text"]
                if draft["format"] == "image" and version["projection"]["coverage"]["text_complete"]
                else None,
            )
        else:
            row = save_version(conn, org_id, draft, user, text=version["text"])
        audit(
            conn,
            user["id"],
            org_id,
            "draft.restored",
            "draft_version",
            row["id"],
            {"source_version_id": str(version["id"])},
        )
        return row


@router.get("/{draft_id}/versions/{version_id}/download")
def download(org_id: UUID, draft_id: UUID, version_id: UUID, user=User):
    with org_transaction(user, org_id) as (conn, member):
        get_draft(conn, org_id, draft_id, user, member)
        version = conn.execute(
            "SELECT * FROM draft_versions WHERE org_id=%s AND draft_id=%s AND id=%s",
            (org_id, draft_id, version_id),
        ).fetchone()
        if not version:
            raise HTTPException(404, "Version unavailable.")
        if not version["private_path"]:
            return Response(
                version["text"],
                media_type="text/plain",
                headers={"Content-Disposition": 'attachment; filename="draft.txt"'},
            )
        path = (LOCAL / version["private_path"]).resolve()
        if not path.is_relative_to((LOCAL / "content").resolve()) or not path.is_file():
            raise HTTPException(404, "File unavailable.")
        mime = {
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".pdf": "application/pdf",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
        }[path.suffix]
        return FileResponse(path, filename=version["filename"], media_type=mime)
