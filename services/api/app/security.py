import hashlib
import secrets
import time
from collections import defaultdict, deque
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import Depends, HTTPException, Request
from pwdlib import PasswordHash

from .db import set_org, transaction

passwords = PasswordHash.recommended()
dummy_hash = passwords.hash("constant-time-placeholder-password")
attempts = defaultdict(deque)


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def expiry(seconds):
    return datetime.now(UTC) + timedelta(seconds=seconds)


def rate_limit(request, action, limit=20):
    key = (request.client.host if request.client else "local", action)
    now = time.monotonic()
    queue = attempts[key]
    while queue and queue[0] < now - 60:
        queue.popleft()
    if len(queue) >= limit:
        raise HTTPException(
            429,
            "Too many attempts. Try again in one minute.",
            headers={"Retry-After": "60"},
        )
    queue.append(now)


def current_user(request: Request):
    token = request.cookies.get("inkloom_session")
    if not token:
        raise HTTPException(401, "Sign in to continue.")
    with transaction() as conn:
        user = conn.execute(
            "SELECT u.id,u.email,u.name FROM sessions s JOIN users u ON u.id=s.user_id WHERE s.token_hash=%s AND s.expires_at>now()",
            (digest(token),),
        ).fetchone()
    if not user:
        raise HTTPException(401, "Your session expired. Sign in again.")
    return user


@contextmanager
def org_transaction(user, org_id: UUID, owner=False):
    with transaction(user) as conn:
        member = conn.execute(
            "SELECT * FROM memberships WHERE org_id=%s AND user_id=%s AND status='active'",
            (org_id, user["id"]),
        ).fetchone()
        if not member:
            raise HTTPException(404, "Organisation not found or access unavailable.")
        set_org(conn, org_id)
        member = conn.execute(
            "SELECT * FROM memberships WHERE org_id=%s AND user_id=%s AND status='active' FOR SHARE",
            (org_id, user["id"]),
        ).fetchone()
        if not member:
            raise HTTPException(404, "Organisation not found or access unavailable.")
        if owner and member["role"] != "owner":
            raise HTTPException(403, "Only the organisation owner can do this.")
        yield conn, member


User = Depends(current_user)


def random_token():
    return secrets.token_urlsafe(32)
