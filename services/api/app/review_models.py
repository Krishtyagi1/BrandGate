from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

Channel = Literal[
    "general",
    "linkedin",
    "instagram",
    "x",
    "facebook",
    "threads",
    "tiktok",
    "youtube",
    "pinterest",
    "website",
    "email",
    "advertisement",
]
Category = Literal["email", "social_media", "visuals", "website", "documents", "other"]
Platform = Literal[
    "linkedin", "instagram", "x", "facebook", "threads", "tiktok", "youtube", "pinterest"
]
CheckName = Literal[
    "prices",
    "claims",
    "tone",
    "language",
    "required_wording",
    "colours_fonts",
    "logos",
    "accessibility",
]


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class DraftCreate(Strict):
    title: str = Field(default="Untitled draft", min_length=1, max_length=160)
    channel: Channel = "general"
    text: str = Field(min_length=1, max_length=30000)
    category: Category | None = None
    platform: Platform | None = None
    requested_checks: list[CheckName] | None = Field(default=None, min_length=1, max_length=8)
    task_instructions: str = Field(default="", max_length=2000)
    campaign: str = Field(default="", max_length=120)


class CampaignSave(Strict):
    expected_current_version_id: UUID
    campaign: str = Field(max_length=120)


class ScopeSave(Strict):
    expected_current_version_id: UUID
    category: Category = "other"
    platform: Platform | None = None
    requested_checks: list[CheckName] = Field(min_length=1, max_length=8)
    task_instructions: str = Field(default="", max_length=2000)


class DraftSave(Strict):
    expected_current_version_id: UUID
    text: str = Field(min_length=1, max_length=30000)


class TranscriptSave(DraftSave):
    verified: Literal[True]


class RestoreVersion(Strict):
    expected_current_version_id: UUID
    source_version_id: UUID


class RunStart(Strict):
    version_id: UUID
    idempotency_key: str = Field(min_length=8, max_length=100)
    preview_hash: str = Field(min_length=64, max_length=64)


class ModelFinding(Strict):
    category: Literal["tone", "terminology", "messaging", "claim", "fact", "accessibility"]
    severity: Literal["high", "medium", "low"]
    quote: str = Field(min_length=1, max_length=2000)
    reason: str = Field(min_length=1, max_length=1500)
    evidence_ids: list[str] = Field(max_length=8)


class ReviewResponse(Strict):
    findings: list[ModelFinding] = Field(max_length=30)


class RewriteResponse(Strict):
    minimal: str = Field(min_length=1, max_length=4000)
    natural: str = Field(min_length=1, max_length=4000)


class CommentBody(Strict):
    version_id: UUID
    body: str = Field(min_length=1, max_length=3000)


class ApprovalStart(Strict):
    version_id: UUID
    reviewer_id: UUID
    idempotency_key: str = Field(min_length=8, max_length=100)


class ApprovalDecision(Strict):
    expected_version_id: UUID
    artifact_sha256: str
    decision: Literal["approved", "needs_changes", "rejected"]
    comment: str = Field(default="", max_length=3000)
    manual_visual_ack: bool = False


class ConsentBody(Strict):
    enabled: bool
    policy_version: str


class RewriteStart(Strict):
    finding_id: str
    preview_hash: str
    idempotency_key: str = Field(min_length=8, max_length=100)


class ApplyRewrite(Strict):
    expected_current_version_id: UUID
    option_id: str


class DismissFinding(Strict):
    finding_id: str
    reason: str = Field(min_length=1, max_length=1000)
