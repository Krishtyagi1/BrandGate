import json
from uuid import uuid4

import psycopg
import pytest
from conftest import HEADERS, PASSWORD
from fastapi.testclient import TestClient
from test_document_chat import chat_provider, preview, send_chat
from test_review_workflow import setup_review

from app.config import ADMIN_URL
from app.main import app
from app.security import digest


@pytest.fixture
def demo_config(workspace, tmp_path, monkeypatch):
    owner, org, email = workspace
    path = tmp_path / "demo.json"
    value = {"email": email, "password": PASSWORD, "org_id": org}
    path.write_text(json.dumps(value))
    path.chmod(0o600)
    monkeypatch.setenv("DEMO_LOGIN_FILE", str(path))
    return owner, org, email, path, value


def enter():
    client = TestClient(app, headers=HEADERS)
    response = client.post("/api/auth/demo")
    assert response.status_code == 200, response.text
    assert PASSWORD not in response.text and "password" not in response.text
    return client, response


def test_demo_cookie_scope_expiry_logout_and_normal_login_unchanged(demo_config):
    owner, org, email, _, _ = demo_config
    other = owner.post("/api/organisations", json={"name": "Private other organisation"}).json()[
        "id"
    ]
    visitor, response = enter()
    assert "httponly" in response.headers["set-cookie"].lower()
    assert "max-age=3600" in response.headers["set-cookie"].lower()
    me = visitor.get("/api/auth/me").json()
    assert me["demo_org_id"] == org and me["email"] == email
    # A rollback to an older API must never interpret this as a normal owner session.
    with psycopg.connect(ADMIN_URL) as conn:
        assert (
            conn.execute(
                "SELECT 1 FROM sessions WHERE token_hash=%s",
                (digest(visitor.cookies["inkloom_session"]),),
            ).fetchone()
            is None
        )
    orgs = visitor.get("/api/organisations").json()
    assert [(item["id"], item["role"]) for item in orgs] == [(org, "creator")]
    assert visitor.get(f"/api/organisations/{other}").status_code == 404
    assert owner.get(f"/api/organisations/{org}").json()["role"] == "owner"
    assert visitor.post("/api/auth/logout").status_code == 200
    assert visitor.get("/api/auth/me").status_code == 401
    again, _ = enter()
    with psycopg.connect(ADMIN_URL) as conn:
        conn.execute(
            "UPDATE demo_sessions SET expires_at=now()-interval '1 second' WHERE token_hash=%s",
            (digest(again.cookies["inkloom_session"]),),
        )
    assert again.get("/api/auth/me").status_code == 401


@pytest.mark.parametrize(
    "method,suffix,body",
    [
        ("PATCH", "", {"name": "Defaced"}),
        ("POST", "/invites", {"email": "attacker@example.com", "role": "creator"}),
        (
            "PATCH",
            "/members/00000000-0000-0000-0000-000000000001",
            {"role": "reviewer", "status": "active"},
        ),
        ("POST", "/guidelines/versions", None),
        (
            "POST",
            "/ai/consent",
            {"enabled": False, "policy_version": "openrouter-free-zdr-redacted-v1"},
        ),
        ("POST", "/drafts/00000000-0000-0000-0000-000000000001/approvals", {}),
        ("POST", "/approvals/00000000-0000-0000-0000-000000000001/decision", {}),
    ],
)
def test_demo_denies_administration_and_human_approval(demo_config, method, suffix, body):
    _, org, _, _, _ = demo_config
    visitor, _ = enter()
    assert (
        visitor.request(method, f"/api/organisations/{org}{suffix}", json=body).status_code == 403
    )
    assert visitor.post("/api/organisations", json={"name": "Escape"}).status_code == 403
    assert visitor.post("/api/invitations/accept", json={"token": "anything"}).status_code == 403
    assert visitor.post("/api/tutorial/example").status_code == 403


def test_demo_can_edit_comment_review_and_chat(demo_config, monkeypatch):
    owner, org, _, _, _ = demo_config
    base, draft, _, run = setup_review(owner, org, monkeypatch, text="Everyday care.")
    visitor, _ = enter()
    assert visitor.get(f"{base}/drafts/{draft['id']}").status_code == 200
    assert (
        visitor.post(
            f"{base}/drafts/{draft['id']}/comments",
            json={"body": "Synthetic demo note", "version_id": draft["current_version_id"]},
        ).status_code
        == 201
    )
    chat_provider(monkeypatch)
    p = preview(visitor, base, run)
    assert p.status_code == 200, p.text
    answer = send_chat(visitor, base, run, p.json())
    assert answer.status_code == 200, answer.text
    saved = visitor.post(
        f"{base}/drafts/{draft['id']}/versions",
        json={
            "expected_current_version_id": draft["current_version_id"],
            "text": "Revised. Results vary.",
        },
    )
    assert saved.status_code == 201, saved.text
    from app.review_models import ReviewResponse

    monkeypatch.setattr(
        "providers.openrouter.complete",
        lambda *a, **kw: (ReviewResponse(findings=[]), {"model": "offline-test-double"}),
    )
    outbound = visitor.get(f"{base}/drafts/{draft['id']}/ai-preview").json()
    checked = visitor.post(
        f"{base}/drafts/{draft['id']}/reviews",
        json={
            "version_id": saved.json()["id"],
            "preview_hash": outbound["preview_hash"],
            "idempotency_key": str(uuid4()),
        },
    )
    assert checked.status_code == 202, checked.text
    stream = visitor.post(f"{base}/review-runs/{checked.json()['id']}/stream")
    assert "RUN_FINISHED" in stream.text, stream.text
    assert visitor.get(f"{base}/review-runs/{checked.json()['id']}").json()["status"] == "completed"


def test_demo_chat_keeps_numeric_protocol_ids_but_redacts_private_text(demo_config, monkeypatch):
    owner, org, _, _, _ = demo_config
    base, _, _, run = setup_review(owner, org, monkeypatch, text="Everyday care.")
    finding_id = "12345678-1234-4123-8123-123456789012"
    with psycopg.connect(ADMIN_URL) as conn:
        conn.execute(
            "UPDATE review_runs SET result=jsonb_set(result,'{findings,0,id}',to_jsonb(%s::text)) WHERE id=%s",
            (finding_id, run["id"]),
        )
    visitor, _ = enter()
    chat_provider(monkeypatch)
    p = preview(visitor, base, run, "Explain the flag for private-person@example.com.")
    assert p.status_code == 200, p.text
    assert p.json()["payload"]["findings"][0]["id"] == finding_id
    assert "private-person@example.com" not in json.dumps(p.json()["payload"])
    answer = visitor.post(
        f"{base}/review-runs/{run['id']}/chat",
        json={
            "question": "Explain the flag for private-person@example.com.",
            "preview_hash": p.json()["preview_hash"],
            "idempotency_key": str(uuid4()),
        },
    )
    assert answer.status_code == 200, answer.text


@pytest.mark.parametrize(
    "change", ["missing", "malformed", "password", "org", "disabled", "permissions"]
)
def test_demo_fails_closed_without_leaking_configuration(demo_config, change):
    _, org, email, path, value = demo_config
    if change == "missing":
        path.unlink()
    elif change == "malformed":
        path.write_text("private invalid configuration")
    elif change == "permissions":
        path.chmod(0o644)
    elif change == "disabled":
        with psycopg.connect(ADMIN_URL) as conn:
            conn.execute("UPDATE memberships SET status='disabled' WHERE org_id=%s", (org,))
    else:
        value["password" if change == "password" else "org_id"] = (
            "bad-password" if change == "password" else str(uuid4())
        )
        path.write_text(json.dumps(value))
    visitor = TestClient(app, headers=HEADERS)
    result = visitor.post("/api/auth/demo")
    assert result.status_code == 503
    assert email not in result.text and PASSWORD not in result.text and str(path) not in result.text
    assert "set-cookie" not in result.headers


def test_demo_csrf_origin_and_rate_limit(demo_config):
    visitor = TestClient(app)
    assert visitor.post("/api/auth/demo").status_code == 403
    visitor.headers.update(HEADERS)
    assert (
        visitor.post("/api/auth/demo", headers={"Origin": "https://attacker.example"}).status_code
        == 403
    )
    for _ in range(10):
        assert visitor.post("/api/auth/demo").status_code == 200
    assert visitor.post("/api/auth/demo").status_code == 429
