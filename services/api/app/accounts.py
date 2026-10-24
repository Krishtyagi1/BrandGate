from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, Request, Response
from psycopg.errors import UniqueViolation

from .config import COOKIE_SECURE, SESSION_SECONDS
from .db import audit, set_org, transaction
from .models import InviteInput, Login, MemberInput, OrganisationInput, Register, Token
from .security import (
    User,
    digest,
    dummy_hash,
    expiry,
    org_transaction,
    passwords,
    random_token,
    rate_limit,
)

router = APIRouter(prefix="/api")


@router.post("/auth/register", status_code=201)
def register(body: Register, request: Request):
    rate_limit(request, "register", 10)
    try:
        with transaction() as conn:
            conn.execute(
                "INSERT INTO users(email,name,password_hash) VALUES (%s,%s,%s)",
                (str(body.email).casefold(), body.name, passwords.hash(body.password)),
            )
    except UniqueViolation:
        raise HTTPException(
            409, "An account with this email already exists. Sign in instead."
        ) from None
    return {"message": "Account created. Sign in with your email and password."}


@router.post("/auth/login")
def login(body: Login, request: Request, response: Response):
    rate_limit(request, "login")
    with transaction() as conn:
        user = conn.execute(
            "SELECT * FROM users WHERE email=%s", (str(body.email).casefold(),)
        ).fetchone()
        valid = passwords.verify(body.password, user["password_hash"] if user else dummy_hash)
        if not user or not valid:
            raise HTTPException(401, "Email or password is incorrect.")
        token = random_token()
        conn.execute(
            "INSERT INTO sessions VALUES (%s,%s,%s)",
            (digest(token), user["id"], expiry(SESSION_SECONDS)),
        )
    response.set_cookie(
        "inkloom_session",
        token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="lax",
        max_age=SESSION_SECONDS,
        path="/",
    )
    return {"id": user["id"], "name": user["name"], "email": user["email"]}


@router.post("/auth/logout")
def logout(request: Request, response: Response):
    with transaction() as conn:
        conn.execute(
            "DELETE FROM sessions WHERE token_hash=%s",
            (digest(request.cookies.get("inkloom_session", "")),),
        )
    response.delete_cookie("inkloom_session", path="/")
    return {"message": "Signed out."}


@router.get("/auth/me")
def me(user=User):
    return user


@router.get("/organisations")
def organisations(user=User):
    with transaction(user) as conn:
        return conn.execute(
            "SELECT o.*,m.role FROM organisations o JOIN memberships m ON m.org_id=o.id WHERE m.user_id=%s AND m.status='active' ORDER BY o.created_at",
            (user["id"],),
        ).fetchall()


@router.post("/organisations", status_code=201)
def create_org(body: OrganisationInput, user=User):
    org_id = uuid4()
    with transaction(user, org_id) as conn:
        org = conn.execute(
            "INSERT INTO organisations(id,name,owner_id) VALUES (%s,%s,%s) RETURNING *",
            (org_id, body.name, user["id"]),
        ).fetchone()
        conn.execute(
            "INSERT INTO memberships(org_id,user_id,role) VALUES (%s,%s,'owner')",
            (org_id, user["id"]),
        )
        audit(conn, user["id"], org_id, "organisation.created", "organisation", org_id)
    return {**org, "role": "owner"}


@router.get("/organisations/{org_id}")
def organisation(org_id: UUID, user=User):
    with org_transaction(user, org_id) as (conn, member):
        org = conn.execute("SELECT * FROM organisations WHERE id=%s", (org_id,)).fetchone()
        return {**org, "role": member["role"]}


@router.patch("/organisations/{org_id}")
def rename_org(org_id: UUID, body: OrganisationInput, user=User):
    with org_transaction(user, org_id, owner=True) as (conn, _):
        conn.execute("UPDATE organisations SET name=%s WHERE id=%s", (body.name, org_id))
        audit(
            conn,
            user["id"],
            org_id,
            "organisation.renamed",
            "organisation",
            org_id,
            {"name": body.name},
        )
    return {"message": "Organisation name saved."}


@router.get("/organisations/{org_id}/members")
def members(org_id: UUID, user=User):
    with org_transaction(user, org_id) as (conn, _):
        return conn.execute(
            "SELECT m.id,m.user_id,m.role,m.status,u.name,u.email FROM memberships m JOIN users u ON u.id=m.user_id WHERE m.org_id=%s ORDER BY m.created_at",
            (org_id,),
        ).fetchall()


@router.post("/organisations/{org_id}/invites", status_code=201)
def invite(org_id: UUID, body: InviteInput, user=User):
    token = random_token()
    with org_transaction(user, org_id, owner=True) as (conn, _):
        existing = conn.execute(
            "SELECT m.id FROM memberships m JOIN users u ON m.user_id=u.id WHERE m.org_id=%s AND u.email=%s",
            (org_id, str(body.email).casefold()),
        ).fetchone()
        if existing:
            raise HTTPException(
                409,
                "This account is already a member. Manage their role in the member list.",
            )
        invitation = conn.execute(
            "INSERT INTO invitations(org_id,email,role,token_hash,invited_by,expires_at) VALUES (%s,%s,%s,%s,%s,%s) RETURNING id,email,role,expires_at",
            (
                org_id,
                str(body.email).casefold(),
                body.role,
                digest(token),
                user["id"],
                expiry(86400),
            ),
        ).fetchone()
        audit(
            conn,
            user["id"],
            org_id,
            "invitation.created",
            "invitation",
            invitation["id"],
            {"email": str(body.email), "role": body.role},
        )
    return {**invitation, "token": token}


@router.post("/invitations/accept")
def accept_invitation(body: Token, user=User):
    with transaction(user) as conn:
        invite = conn.execute(
            "SELECT * FROM invitations WHERE token_hash=%s AND email=%s AND expires_at>now() AND accepted_at IS NULL FOR UPDATE",
            (digest(body.token), user["email"]),
        ).fetchone()
        if not invite:
            raise HTTPException(
                400,
                "Invitation is invalid, expired, used, or belongs to another email address.",
            )
        set_org(conn, invite["org_id"])
        try:
            conn.execute(
                "INSERT INTO memberships(org_id,user_id,role) VALUES (%s,%s,%s)",
                (invite["org_id"], user["id"], invite["role"]),
            )
        except UniqueViolation:
            raise HTTPException(409, "You already belong to this organisation.") from None
        conn.execute("UPDATE invitations SET accepted_at=now() WHERE id=%s", (invite["id"],))
        audit(
            conn,
            user["id"],
            invite["org_id"],
            "invitation.accepted",
            "invitation",
            invite["id"],
        )
    return {"org_id": invite["org_id"], "message": "Invitation accepted."}


@router.patch("/organisations/{org_id}/members/{member_id}")
def change_member(org_id: UUID, member_id: UUID, body: MemberInput, user=User):
    with org_transaction(user, org_id, owner=True) as (conn, _):
        member = conn.execute(
            "SELECT * FROM memberships WHERE org_id=%s AND id=%s FOR UPDATE",
            (org_id, member_id),
        ).fetchone()
        if not member:
            raise HTTPException(404, "Member not found.")
        if member["role"] == "owner":
            raise HTTPException(
                409, "The owner role cannot be changed or disabled in this prototype."
            )
        conn.execute(
            "UPDATE memberships SET role=%s,status=%s WHERE id=%s AND org_id=%s",
            (body.role, body.status, member_id, org_id),
        )
        if body.status != "active" or body.role not in ("owner", "reviewer"):
            affected = conn.execute(
                "UPDATE approval_requests SET status='superseded' WHERE org_id=%s AND reviewer_id=%s AND status='pending' RETURNING draft_id",
                (org_id, member["user_id"]),
            ).fetchall()
            for row in affected:
                conn.execute(
                    "UPDATE drafts SET status='draft' WHERE org_id=%s AND id=%s AND status='pending_approval'",
                    (org_id, row["draft_id"]),
                )
        audit(
            conn,
            user["id"],
            org_id,
            "membership.updated",
            "membership",
            member_id,
            body.model_dump(),
        )
    return {"message": "Member access updated."}


@router.get("/organisations/{org_id}/audit")
def audit_events(org_id: UUID, user=User):
    with org_transaction(user, org_id) as (conn, _):
        return conn.execute(
            "SELECT a.*,u.name AS actor_name FROM audit_events a JOIN users u ON u.id=a.actor_id WHERE a.org_id=%s ORDER BY a.created_at DESC LIMIT 100",
            (org_id,),
        ).fetchall()
