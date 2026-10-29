"""Local, manually selected image observations. Never changes approval state."""

from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import Field

from .drafts import get_draft
from .knowledge_snapshots import current_snapshot, snapshot_references
from .review_models import Strict
from .security import User, org_transaction
from .visual_review import _image

router = APIRouter(prefix="/api/organisations/{org_id}/drafts")


@router.get("/{draft_id}/visual-references")
def references(org_id: UUID, draft_id: UUID, user=User):
    with org_transaction(user, org_id) as (conn, member):
        get_draft(conn, org_id, draft_id, user, member)
        policy = conn.execute(
            "SELECT id FROM guideline_versions WHERE org_id=%s AND status='active'", (org_id,)
        ).fetchone()
        snapshot = current_snapshot(conn, org_id, policy["id"]) if policy else None
        refs = snapshot_references(conn, org_id, snapshot["id"]) if snapshot else []
        return {
            "snapshot_id": snapshot["id"] if snapshot else None,
            "references": [
                {
                    "id": r["id"],
                    "label": r["label"],
                    "excerpt": r["source_excerpt"],
                    "location": r["source_location"],
                    "sha256": r["sha256"],
                    "url": f"/api/organisations/{org_id}/sources/{r['source_document_id']}/download",
                }
                for r in refs
            ],
            "notice": "Current owner-confirmed references for manual comparison. A different, older review may use a different snapshot.",
        }


class Point(Strict):
    x: float = Field(ge=0, lt=1, allow_inf_nan=False)
    y: float = Field(ge=0, lt=1, allow_inf_nan=False)


class ContrastRequest(Strict):
    version_id: UUID
    foreground: Point
    background: Point


def sample_contrast(path, foreground, background, expected_hash=None):
    meta, image, _ = _image(path, expected_hash)

    def colour(point):
        point = Point.model_validate(point)
        pixel = image.getpixel((int(point.x * image.width), int(point.y * image.height)))
        if pixel[3] != 255:
            raise ValueError("The selected pixel is transparent; select an opaque colour.")
        return pixel[:3]

    def luminance(rgb):
        linear = [
            v / 255 / 12.92 if v / 255 <= 0.04045 else ((v / 255 + 0.055) / 1.055) ** 2.4
            for v in rgb
        ]
        return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]

    fg, bg = colour(foreground), colour(background)
    low, high = sorted((luminance(fg), luminance(bg)))
    ratio = (high + 0.05) / (low + 0.05)
    return {
        "status": "advisory",
        "ratio": ratio,
        "foreground": "#{:02x}{:02x}{:02x}".format(*fg),
        "background": "#{:02x}{:02x}{:02x}".format(*bg),
        "normal_text_threshold_met": ratio >= 4.5,
        "large_text_threshold_met": ratio >= 3,
        "image_sha256": meta["sha256"],
        "notice": "Manually sampled opaque pixels only. Anti-aliasing, gradients, text size and context require human inspection. This does not certify accessibility or logo compliance.",
        "method_reference": "https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html",
    }


@router.post("/{draft_id}/contrast")
def contrast(org_id: UUID, draft_id: UUID, body: ContrastRequest, user=User):
    with org_transaction(user, org_id) as (conn, member):
        draft = get_draft(conn, org_id, draft_id, user, member)
        if draft["format"] != "image":
            raise HTTPException(422, "Select a static image draft.")
        if draft["current_version_id"] != body.version_id:
            raise HTTPException(409, "The image revision changed. Reload before sampling.")
        version = conn.execute(
            "SELECT * FROM draft_versions WHERE org_id=%s AND id=%s", (org_id, body.version_id)
        ).fetchone()
        try:
            return sample_contrast(
                version["private_path"],
                body.foreground.model_dump(),
                body.background.model_dump(),
                version["file_sha256"],
            )
        except ValueError as error:
            raise HTTPException(422, str(error)) from None
