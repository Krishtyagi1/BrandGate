from uuid import uuid4

import pytest
from conftest import add_member, add_rule, create_version

from app.review_models import ReviewResponse
from providers.openrouter import ProviderUnavailable


@pytest.fixture(autouse=True)
def no_live_network(monkeypatch):
    def disabled(*args, **kwargs):
        raise ProviderUnavailable("Live network disabled in automated tests.")

    monkeypatch.setattr("providers.openrouter.complete", disabled)


def setup_review(owner, org, monkeypatch, text="Everyday care. Results vary."):
    monkeypatch.setattr(
        "providers.openrouter.complete",
        lambda *a, **kw: (
            ReviewResponse(findings=[]),
            {
                "model": "synthetic-test-double",
                "provider": "offline-fixture",
                "policy_version": "test",
            },
        ),
    )
    v = create_version(owner, org)
    add_rule(
        owner, org, v, type="required_disclaimer", rule_key="disclaimer", value="Results vary."
    )
    base = f"/api/organisations/{org}"
    assert owner.post(f"{base}/guidelines/versions/{v}/activate").status_code == 200
    assert (
        owner.post(
            f"{base}/ai/consent",
            json={"enabled": True, "policy_version": "openrouter-free-zdr-redacted-v1"},
        ).status_code
        == 200
    )
    draft = owner.post(f"{base}/drafts", json={"text": text}).json()
    preview = owner.get(f"{base}/drafts/{draft['id']}/ai-preview").json()
    body = {
        "version_id": draft["current_version_id"],
        "preview_hash": preview["preview_hash"],
        "idempotency_key": str(uuid4()),
    }
    run = owner.post(f"{base}/drafts/{draft['id']}/reviews", json=body)
    assert run.status_code == 202, run.text
    return base, draft, body, run.json()


def test_review_persisted_idempotency_stream_and_edit_stale(workspace, monkeypatch):
    owner, org, _ = workspace
    base, draft, body, run = setup_review(owner, org, monkeypatch)
    duplicate = owner.post(f"{base}/drafts/{draft['id']}/reviews", json=body)
    assert duplicate.json()["id"] == run["id"]
    result = owner.get(f"{base}/review-runs/{run['id']}").json()
    assert result["status"] == "completed" and not result["stale"]
    assert result["result"]["metadata"]["model"] == "synthetic-test-double"
    events = owner.post(f"{base}/review-runs/{run['id']}/stream")
    assert "RUN_STARTED" in events.text and "RUN_FINISHED" in events.text
    assert (
        owner.post(
            f"{base}/drafts/{draft['id']}/versions",
            json={
                "expected_current_version_id": draft["current_version_id"],
                "text": "Changed. Results vary.",
            },
        ).status_code
        == 201
    )
    assert owner.get(f"{base}/review-runs/{run['id']}").json()["stale"]


def test_provider_failure_is_incomplete_and_no_approval(workspace, monkeypatch):
    owner, org, _ = workspace
    base, draft, _, _ = setup_review(owner, org, monkeypatch)
    monkeypatch.setattr(
        "providers.openrouter.complete",
        lambda *a, **kw: (_ for _ in ()).throw(ProviderUnavailable("Synthetic provider outage")),
    )
    preview = owner.get(f"{base}/drafts/{draft['id']}/ai-preview").json()
    r = owner.post(
        f"{base}/drafts/{draft['id']}/reviews",
        json={
            "version_id": draft["current_version_id"],
            "preview_hash": preview["preview_hash"],
            "idempotency_key": str(uuid4()),
        },
    ).json()
    result = owner.get(f"{base}/review-runs/{r['id']}").json()
    assert result["status"] == "incomplete"
    assert result["result"]["mode"] == "local_checks_only"


def test_approval_separate_reviewer_exact_hash_and_changes_invalidate(
    workspace, account, monkeypatch
):
    owner, org, email = workspace
    reviewer, reviewer_email, _ = account()
    add_member(owner, org, reviewer, reviewer_email, "reviewer")
    reviewer_id = reviewer.get("/api/auth/me").json()["id"]
    owner_id = owner.get("/api/auth/me").json()["id"]
    base, draft, _, _ = setup_review(owner, org, monkeypatch)
    body = {
        "version_id": draft["current_version_id"],
        "reviewer_id": owner_id,
        "idempotency_key": str(uuid4()),
    }
    assert owner.post(f"{base}/drafts/{draft['id']}/approvals", json=body).status_code == 409
    body["reviewer_id"] = reviewer_id
    request = owner.post(f"{base}/drafts/{draft['id']}/approvals", json=body)
    assert request.status_code == 201, request.text
    decision = {
        "expected_version_id": draft["current_version_id"],
        "artifact_sha256": draft["current_version"]["artifact_sha256"],
        "decision": "approved",
    }
    path = f"{base}/approvals/{request.json()['id']}/decision"
    assert owner.post(path, json=decision).status_code == 403
    wrong = {**decision, "artifact_sha256": "0" * 64}
    assert reviewer.post(path, json=wrong).status_code == 409
    assert reviewer.post(path, json=decision).status_code == 200
    assert reviewer.post(path, json=decision).status_code == 409
    assert owner.get(f"{base}/drafts/{draft['id']}").json()["status"] == "approved"
    owner.post(
        f"{base}/drafts/{draft['id']}/versions",
        json={
            "expected_current_version_id": draft["current_version_id"],
            "text": "Edited. Results vary.",
        },
    )
    assert owner.get(f"{base}/drafts/{draft['id']}").json()["status"] == "draft"


def test_high_issue_blocks_submit(workspace, account, monkeypatch):
    owner, org, _ = workspace
    reviewer, email, _ = account()
    add_member(owner, org, reviewer, email, "reviewer")
    base, draft, _, _ = setup_review(owner, org, monkeypatch, text="No required disclaimer.")
    body = {
        "version_id": draft["current_version_id"],
        "reviewer_id": reviewer.get("/api/auth/me").json()["id"],
        "idempotency_key": str(uuid4()),
    }
    assert owner.post(f"{base}/drafts/{draft['id']}/approvals", json=body).status_code == 409


def test_new_guidelines_invalidate_pending_request(workspace, account, monkeypatch):
    owner, org, _ = workspace
    reviewer, email, _ = account()
    add_member(owner, org, reviewer, email, "reviewer")
    base, draft, _, _ = setup_review(owner, org, monkeypatch)
    response = owner.post(
        f"{base}/drafts/{draft['id']}/approvals",
        json={
            "version_id": draft["current_version_id"],
            "reviewer_id": reviewer.get("/api/auth/me").json()["id"],
            "idempotency_key": str(uuid4()),
        },
    )
    assert response.status_code == 201
    next_version = create_version(owner, org)
    add_rule(owner, org, next_version, value="New approved fact")
    assert owner.post(f"{base}/guidelines/versions/{next_version}/activate").status_code == 200
    assert (
        reviewer.post(
            f"{base}/approvals/{response.json()['id']}/decision",
            json={
                "expected_version_id": draft["current_version_id"],
                "artifact_sha256": draft["current_version"]["artifact_sha256"],
                "decision": "approved",
            },
        ).status_code
        == 409
    )


def test_preview_changed_and_consent_revocation_block_dispatch(workspace, monkeypatch):
    owner, org, _ = workspace
    base, draft, body, _ = setup_review(owner, org, monkeypatch)
    body["idempotency_key"] = str(uuid4())
    body["preview_hash"] = "0" * 64
    assert owner.post(f"{base}/drafts/{draft['id']}/reviews", json=body).status_code == 409
    owner.post(
        f"{base}/ai/consent",
        json={"enabled": False, "policy_version": "openrouter-free-zdr-redacted-v1"},
    )
    assert owner.post(f"{base}/drafts/{draft['id']}/reviews", json=body).status_code == 409


def test_fake_model_evidence_prevents_completed_check(workspace, monkeypatch):
    owner, org, _ = workspace
    base, draft, body, _ = setup_review(owner, org, monkeypatch)
    fake = {
        "category": "fact",
        "severity": "high",
        "quote": "Everyday care.",
        "reason": "Invented evidence",
        "evidence_ids": ["fabricated"],
    }
    monkeypatch.setattr(
        "providers.openrouter.complete",
        lambda *a, **kw: (ReviewResponse(findings=[fake]), {"model": "synthetic-fixture"}),
    )
    body["idempotency_key"] = str(uuid4())
    started = owner.post(f"{base}/drafts/{draft['id']}/reviews", json=body).json()
    run = owner.get(f"{base}/review-runs/{started['id']}").json()
    assert run["status"] == "incomplete" and run["result"]["validation_dropped"] == 1


def test_failed_latest_check_cannot_use_previous_pass_for_approval(workspace, account, monkeypatch):
    owner, org, _ = workspace
    reviewer, email, _ = account()
    add_member(owner, org, reviewer, email, "reviewer")
    base, draft, body, _ = setup_review(owner, org, monkeypatch)
    monkeypatch.setattr(
        "providers.openrouter.complete",
        lambda *a, **kw: (_ for _ in ()).throw(ProviderUnavailable("Offline outage")),
    )
    body["idempotency_key"] = str(uuid4())
    owner.post(f"{base}/drafts/{draft['id']}/reviews", json=body)
    response = owner.post(
        f"{base}/drafts/{draft['id']}/approvals",
        json={
            "version_id": draft["current_version_id"],
            "reviewer_id": reviewer.get("/api/auth/me").json()["id"],
            "idempotency_key": str(uuid4()),
        },
    )
    assert response.status_code == 409


def test_cancelled_run_cannot_be_completed_by_late_result(workspace, monkeypatch):
    from app.db import transaction
    from app.reviews import finish_run

    owner, org, _ = workspace
    base, draft, _, run = setup_review(owner, org, monkeypatch)
    actor = owner.get("/api/auth/me").json()
    with transaction(actor, org) as conn:
        conn.execute(
            "UPDATE review_runs SET status='cancelled' WHERE org_id=%s AND id=%s", (org, run["id"])
        )
    finish_run(actor, org, run["id"], "completed", {"findings": []}, None)
    assert owner.get(f"{base}/review-runs/{run['id']}").json()["status"] == "cancelled"


def test_recheck_supersedes_pending_approval_and_allows_resubmission(
    workspace, account, monkeypatch
):
    owner, org, _ = workspace
    reviewer, email, _ = account()
    add_member(owner, org, reviewer, email, "reviewer")
    base, draft, body, _ = setup_review(owner, org, monkeypatch)
    request_body = {
        "version_id": draft["current_version_id"],
        "reviewer_id": reviewer.get("/api/auth/me").json()["id"],
        "idempotency_key": str(uuid4()),
    }
    first = owner.post(f"{base}/drafts/{draft['id']}/approvals", json=request_body)
    assert first.status_code == 201
    body["idempotency_key"] = str(uuid4())
    assert owner.post(f"{base}/drafts/{draft['id']}/reviews", json=body).status_code == 202
    current = owner.get(f"{base}/drafts/{draft['id']}").json()
    assert current["approval_requests"][0]["status"] == "superseded"
    assert current["status"] == "draft"
    request_body["idempotency_key"] = str(uuid4())
    assert (
        owner.post(f"{base}/drafts/{draft['id']}/approvals", json=request_body).status_code == 201
    )
