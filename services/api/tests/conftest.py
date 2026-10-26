from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.security import attempts
from providers.openrouter import ProviderUnavailable

HEADERS = {"X-Inkloom-CSRF": "1"}
PASSWORD = "Correct horse battery staple 42!"


@pytest.fixture(autouse=True)
def offline_provider(monkeypatch):
    """Never depend on a developer credential or contact the live provider."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "synthetic-offline-test-key")
    monkeypatch.setenv("OPENROUTER_MODEL", "synthetic/model:free")
    monkeypatch.setenv("OPENROUTER_ALLOW_PROVIDER_RETENTION", "false")

    def disabled():
        raise ProviderUnavailable("Live network disabled in automated tests.")

    monkeypatch.setattr("providers.openrouter.client", disabled)


@pytest.fixture(scope="session", autouse=True)
def lifespan():
    with TestClient(app):
        yield


@pytest.fixture(autouse=True)
def clear_rate_limit():
    attempts.clear()


@pytest.fixture
def account():
    clients = []

    def create(sign_in=True):
        client = TestClient(app, headers=HEADERS)
        clients.append(client)
        email = f"test-{uuid4().hex}@example.com"
        body = {"email": email, "name": "Test Human", "password": PASSWORD}
        response = client.post("/api/auth/register", json=body)
        assert response.status_code == 201, response.text
        if sign_in:
            login = client.post("/api/auth/login", json={"email": email, "password": PASSWORD})
            assert login.status_code == 200, login.text
        return client, email, None

    yield create
    for client in clients:
        client.close()


@pytest.fixture
def workspace(account):
    owner, email, _ = account()
    result = owner.post("/api/organisations", json={"name": "Synthetic Brand"})
    assert result.status_code == 201, result.text
    return owner, result.json()["id"], email


def add_member(owner, org_id, client, email, role="creator"):
    invitation = owner.post(
        f"/api/organisations/{org_id}/invites", json={"email": email, "role": role}
    )
    assert invitation.status_code == 201, invitation.text
    token = invitation.json()["token"]
    joined = client.post("/api/invitations/accept", json={"token": token})
    assert joined.status_code == 200, joined.text
    return token


def create_version(owner, org_id):
    result = owner.post(f"/api/organisations/{org_id}/guidelines/versions")
    assert result.status_code == 201, result.text
    return result.json()["id"]


def add_rule(owner, org_id, version, **changes):
    body = {
        "type": "approved_fact",
        "rule_key": "monthly_price",
        "value": "Rs 999/month",
        "approved": True,
        **changes,
    }
    response = owner.post(
        f"/api/organisations/{org_id}/guidelines/versions/{version}/rules", json=body
    )
    assert response.status_code == 201, response.text
    return response.json()
