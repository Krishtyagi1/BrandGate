"""Explicit fictional example workspace and per-account tutorial state."""

from io import BytesIO
from uuid import uuid4

from fastapi import APIRouter, UploadFile
from psycopg.types.json import Jsonb
from starlette.datastructures import Headers

from .db import audit, set_org, transaction
from .drafts import create_record, save_version, set_scope
from .knowledge import insert_proposal, save_source
from .review_models import Strict
from .security import User

router = APIRouter(prefix="/api/tutorial")


class TutorialState(Strict):
    completed: bool | None = None
    dismissed: bool | None = None


def state(conn, user):
    conn.execute(
        "INSERT INTO tutorial_states(user_id) VALUES (%s) ON CONFLICT DO NOTHING", (user["id"],)
    )
    return conn.execute(
        "SELECT * FROM tutorial_states WHERE user_id=%s FOR UPDATE", (user["id"],)
    ).fetchone()


@router.get("")
def get_state(user=User):
    with transaction(user) as conn:
        row = state(conn, user)
        return {
            "completed": row["completed"],
            "dismissed": row["dismissed"],
            "example": {
                "org_id": row["example_org_id"],
                "draft_id": row["example_draft_id"],
                "version_id": row["example_version_id"],
            }
            if row["example_org_id"]
            else None,
        }


@router.post("")
def update_state(body: TutorialState, user=User):
    with transaction(user) as conn:
        row = state(conn, user)
        result = conn.execute(
            "UPDATE tutorial_states SET completed=%s,dismissed=%s,updated_at=now() WHERE user_id=%s RETURNING completed,dismissed",
            (
                body.completed if body.completed is not None else row["completed"],
                body.dismissed if body.dismissed is not None else row["dismissed"],
                user["id"],
            ),
        ).fetchone()
        return result


def graphic(background, wording):
    from PIL import Image, ImageDraw

    image = Image.new("RGB", (640, 360), background)
    draw = ImageDraw.Draw(image)
    draw.text((35, 40), "NORTHSTAR BOTANICS", fill="white", font_size=28)
    draw.text((35, 120), wording, fill="white", font_size=22)
    result = BytesIO()
    image.save(result, format="PNG")
    return result.getvalue()


@router.post("/example", status_code=201)
def create_example(user=User):
    from docx import Document

    checks = ["prices", "tone", "language", "required_wording", "colours_fonts", "logos"]
    with transaction(user) as conn:
        row = state(conn, user)
        if row["example_org_id"]:
            return {
                "org_id": row["example_org_id"],
                "draft_id": row["example_draft_id"],
                "version_id": row["example_version_id"],
            }
        org_id, version_id = uuid4(), uuid4()
        set_org(conn, org_id)
        conn.execute(
            "INSERT INTO organisations(id,name,owner_id) VALUES (%s,%s,%s)",
            (org_id, "Northstar Botanics — fictional example", user["id"]),
        )
        conn.execute(
            "INSERT INTO memberships(org_id,user_id,role) VALUES (%s,%s,'owner')",
            (org_id, user["id"]),
        )
        conn.execute(
            "INSERT INTO guideline_versions(id,org_id,version,checks) VALUES (%s,%s,1,%s)",
            (version_id, org_id, Jsonb(checks)),
        )
        paragraphs = [
            "FICTIONAL DEMONSTRATION ONLY. Northstar Botanics and all product facts below are invented for this tutorial.",
            "Cloudberry Daily Cleanser 150ml costs INR 799. Effective from 2026-01-01.",
            "A gentle rinse-off cleanser that removes surface oil.",
            "Tone: write in a calm, clear and helpful voice. Avoid exaggerated promises, shouting and unnecessary urgency.",
            "Terminology: never use the word miracle.",
            "Required wording: Results vary. Read the product label before use.",
            "Brand palette: teal #167569, ink #162841 and white #FFFFFF. The separately uploaded Northstar reference image is the visual example.",
        ]
        doc = Document()
        for text in paragraphs:
            doc.add_paragraph(text)
        stream = BytesIO()
        doc.save(stream)
        source_id = save_source(
            conn,
            org_id,
            version_id,
            UploadFile(
                filename="Northstar-example-guidelines.docx",
                file=BytesIO(stream.getvalue()),
                headers=Headers(
                    {
                        "content-type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    }
                ),
            ),
            user["id"],
        )
        locations = conn.execute(
            "SELECT locations FROM source_documents WHERE org_id=%s AND id=%s", (org_id, source_id)
        ).fetchone()["locations"]

        def proposal(kind, key, value, check, paragraph, fact=None):
            source = next(item for item in locations if item["text"] == paragraphs[paragraph])
            insert_proposal(
                conn,
                org_id,
                version_id,
                {
                    "type": kind,
                    "rule_key": key,
                    "value": value,
                    "check": check,
                    "source_document_id": source_id,
                    "source_excerpt": source["text"],
                    "source_location": source["location"],
                    "fact": fact,
                },
                "company_entered",
            )

        proposal(
            "approved_fact",
            "cleanser_price",
            paragraphs[1],
            "prices",
            1,
            {
                "kind": "price",
                "entity": "Cloudberry Daily Cleanser",
                "amount": "799",
                "currency": "INR",
                "unit": "150ml",
                "effective_from": "2026-01-01",
                "effective_to": None,
            },
        )
        proposal("approved_fact", "cleanser_benefit", paragraphs[2], "claims", 2)
        proposal("tone", "brand_tone", paragraphs[3], "tone", 3)
        proposal("prohibited_term", "avoid_miracle", "miracle", "language", 4)
        proposal(
            "required_disclaimer",
            "product_disclaimer",
            "Results vary. Read the product label before use.",
            "required_wording",
            5,
        )
        proposal("channel_instruction", "brand_palette", paragraphs[6], "colours_fonts", 6)
        reference = graphic(
            "#167569", "Gentle daily care.\nCloudberry Daily Cleanser 150ml\nINR 799"
        )
        save_source(
            conn,
            org_id,
            version_id,
            UploadFile(
                filename="Northstar-approved-visual-example.png",
                file=BytesIO(reference),
                headers=Headers({"content-type": "image/png"}),
            ),
            user["id"],
        )
        draft = create_record(
            conn, org_id, user, "Example: review this launch post", "instagram", "text"
        )
        set_scope(
            conn,
            org_id,
            draft,
            {
                "category": "social_media",
                "platform": "instagram",
                "requested_checks": ["prices", "tone", "language", "required_wording"],
                "task_instructions": "Check the price, terminology, required wording and tone against the confirmed sources.",
            },
        )
        save_version(
            conn,
            org_id,
            draft,
            user,
            text="Cloudberry Daily Cleanser 150ml costs INR 499. A miracle cleanser! BUY NOW!!!",
        )
        image_draft = create_record(
            conn, org_id, user, "Example: inspect this advertisement", "advertisement", "image"
        )
        set_scope(
            conn,
            org_id,
            image_draft,
            {
                "category": "visuals",
                "requested_checks": ["colours_fonts", "logos"],
                "task_instructions": "Compare this static advertisement to the confirmed palette and reference image.",
            },
        )
        save_version(
            conn,
            org_id,
            image_draft,
            user,
            data=graphic("#DC143C", "BUY NOW!!!\nCloudberry Daily Cleanser 150ml\nINR 499"),
            filename="Northstar-advertisement-to-review.png",
        )
        conn.execute(
            "UPDATE tutorial_states SET example_org_id=%s,example_draft_id=%s,example_version_id=%s,updated_at=now() WHERE user_id=%s",
            (org_id, draft["id"], version_id, user["id"]),
        )
        audit(
            conn,
            user["id"],
            org_id,
            "tutorial.example_created",
            "guideline_version",
            version_id,
            {"fictional": True, "confirmed": False, "provider_called": False},
        )
        return {
            "org_id": org_id,
            "draft_id": draft["id"],
            "image_draft_id": image_draft["id"],
            "version_id": version_id,
        }
