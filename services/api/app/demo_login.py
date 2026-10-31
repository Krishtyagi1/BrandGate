"""Server-only demo configuration and a deny-by-default session capability boundary."""

import os
import stat
from pathlib import Path
from uuid import UUID

from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, EmailStr, Field, SecretStr, ValidationError

from .config import LOCAL


class DemoCredentials(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: EmailStr
    password: SecretStr = Field(min_length=12, max_length=128)
    org_id: UUID


def credentials():
    path = Path(os.environ.get("DEMO_LOGIN_FILE") or LOCAL / "demo-login.json")
    try:
        info = path.lstat()
        if not stat.S_ISREG(info.st_mode) or info.st_mode & 0o077 or info.st_size > 4096:
            raise ValueError()
        return DemoCredentials.model_validate_json(path.read_bytes())
    except (OSError, ValueError, ValidationError):
        raise HTTPException(
            503, "Demo sign-in is temporarily unavailable. Try again later."
        ) from None


# The named FastAPI route template, not an attacker-controlled URL prefix.
DEMO_POSTS = {
    "/drafts",
    "/drafts/upload",
    "/drafts/{draft_id}/campaign",
    "/drafts/{draft_id}/scope",
    "/drafts/{draft_id}/versions",
    "/drafts/{draft_id}/file-versions",
    "/drafts/{draft_id}/transcript",
    "/drafts/{draft_id}/restore",
    "/drafts/{draft_id}/comments",
    "/drafts/{draft_id}/reviews",
    "/drafts/{draft_id}/apply-rewrite",
    "/drafts/{draft_id}/contrast",
    "/review-runs/{run_id}/cancel",
    "/review-runs/{run_id}/stream",
    "/review-runs/{parent_id}/rewrites",
    "/review-runs/{run_id}/dismiss",
    "/review-runs/{run_id}/follow-up",
    "/follow-ups/{answer_id}/stream",
    "/review-runs/{run_id}/chat/preview",
    "/review-runs/{run_id}/chat",
    "/review-runs/{run_id}/chat/{turn_id}/stream",
}


def guard_demo_request(request, user):
    org = user.get("demo_org_id")
    if not org:
        return
    route = request.scope["route"].path
    if request.method in ("GET", "HEAD") and route in (
        "/api/auth/me",
        "/api/organisations",
        "/api/tutorial",
    ):
        return
    prefix = "/api/organisations/{org_id}"
    if route == prefix or route.startswith(prefix + "/"):
        if str(request.path_params.get("org_id")) != str(org):
            raise HTTPException(404, "Organisation not found or access unavailable.")
        if request.method in ("GET", "HEAD"):
            return
        if request.method == "POST" and route[len(prefix) :] in DEMO_POSTS:
            return
    raise HTTPException(
        403,
        "Demo access allows document editing and AI checks, but not administration or human approval.",
    )
