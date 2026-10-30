from uuid import UUID, uuid4

from conftest import add_member
from test_review_workflow import setup_review

from app.db import transaction
from providers.openrouter import ProviderUnavailable


def test_dashboard_latest_flags_rechecks_stale_and_failures(workspace, monkeypatch):
    owner, org, _ = workspace
    base, draft, body, _ = setup_review(owner, org, monkeypatch, text="Everyday care.")
    data = owner.get(f"{base}/dashboard").json()
    assert data["summary"]["documents"] == 1
    assert data["summary"]["flagged_documents"] == 1
    assert data["summary"]["open_flags"] == 1
    assert data["breakdowns"]["category"][0]["label"] == "messaging"
    assert len(data["documents"][0]["findings"]) == 1
    owner.post(
        f"{base}/drafts/{draft['id']}/reviews", json={**body, "idempotency_key": str(uuid4())}
    )
    data = owner.get(f"{base}/dashboard?days=7").json()
    assert data["summary"]["open_flags"] == 1
    assert sum(day["total"] for day in data["activity"]) == 2
    owner.post(
        f"{base}/drafts/{draft['id']}/versions",
        json={
            "expected_current_version_id": draft["current_version_id"],
            "text": "Changed.",
        },
    )
    data = owner.get(f"{base}/dashboard").json()
    assert data["summary"]["stale_documents"] == 1
    assert data["summary"]["open_flags"] == 0
    assert data["documents"][0]["review_state"] == "stale"

    def unavailable(*a, **kw):
        raise ProviderUnavailable("Synthetic outage")

    monkeypatch.setattr("providers.openrouter.complete", unavailable)
    current = owner.get(f"{base}/drafts/{draft['id']}").json()
    preview = owner.get(f"{base}/drafts/{draft['id']}/ai-preview").json()
    owner.post(
        f"{base}/drafts/{draft['id']}/reviews",
        json={
            "version_id": current["current_version_id"],
            "preview_hash": preview["preview_hash"],
            "idempotency_key": str(uuid4()),
        },
    )
    data = owner.get(f"{base}/dashboard").json()
    assert data["summary"]["incomplete_documents"] == 1
    assert data["summary"]["stale_documents"] == 0
    assert data["documents"][0]["review_state"] == "incomplete"


def test_dashboard_creator_isolation_empty_and_period(workspace, account, monkeypatch):
    owner, org, _ = workspace
    base, _, _, _ = setup_review(owner, org, monkeypatch)
    stranger, email, _ = account()
    assert stranger.get(f"{base}/dashboard").status_code == 404
    add_member(owner, org, stranger, email, "creator")
    mine = stranger.post(f"{base}/drafts", json={"title": "Only mine", "text": "Draft"}).json()
    result = stranger.get(f"{base}/dashboard").json()
    assert result["scope"] == "your_documents"
    assert result["summary"]["documents"] == 1
    assert [d["id"] for d in result["documents"]] == [mine["id"]]
    assert result["activity"] == []
    assert owner.get(f"{base}/dashboard?days=0").status_code == 422
    empty = owner.post("/api/organisations", json={"name": "Empty"}).json()["id"]
    assert owner.get(f"/api/organisations/{empty}/dashboard").json()["summary"]["documents"] == 0


def test_dashboard_counts_all_documents_beyond_listing_limit_and_ignores_rewrites(
    workspace, monkeypatch
):
    owner, org, _ = workspace
    base, draft, _, run = setup_review(owner, org, monkeypatch, text="Everyday care.")
    user = owner.get("/api/auth/me").json()
    with transaction(user, UUID(org)) as conn:
        # Clone only synthetic document records and revisions in the isolated test DB.
        for n in range(201):
            did, vid = uuid4(), uuid4()
            conn.execute(
                "INSERT INTO drafts(id,org_id,creator_id,title,channel,format) VALUES (%s,%s,%s,%s,'general','text')",
                (did, org, user["id"], f"Synthetic {n}"),
            )
            conn.execute(
                """INSERT INTO draft_versions(id,org_id,draft_id,revision,author_id,text,artifact_sha256,projection)
                         SELECT %s,org_id,%s,1,author_id,text,artifact_sha256,projection FROM draft_versions WHERE id=%s""",
                (vid, did, draft["current_version_id"]),
            )
            conn.execute("UPDATE drafts SET current_version_id=%s WHERE id=%s", (vid, did))
        conn.execute(
            """INSERT INTO review_runs(id,org_id,draft_id,version_id,guideline_version_id,knowledge_snapshot_id,actor_id,run_kind,status,step,idempotency_key)
                     SELECT %s,org_id,draft_id,version_id,guideline_version_id,knowledge_snapshot_id,actor_id,'rewrite','incomplete','Synthetic rewrite',%s FROM review_runs WHERE id=%s""",
            (uuid4(), str(uuid4()), run["id"]),
        )
    data = owner.get(f"{base}/dashboard").json()
    assert data["summary"]["documents"] == 202
    assert len(data["documents"]) == 202
    assert data["summary"]["open_flags"] == 1
    assert data["summary"]["unchecked_documents"] == 201


def test_dashboard_dismissal_audit_is_not_an_open_flag(workspace, monkeypatch):
    owner, org, _ = workspace
    base, _, _, run = setup_review(owner, org, monkeypatch, text="Everyday care.")
    finding = owner.get(f"{base}/review-runs/{run['id']}").json()["result"]["findings"][0]
    response = owner.post(
        f"{base}/review-runs/{run['id']}/dismiss",
        json={"finding_id": finding["id"], "reason": "Synthetic human review"},
    )
    assert response.status_code == 200, response.text
    data = owner.get(f"{base}/dashboard").json()
    assert data["summary"]["open_flags"] == 0
    assert data["summary"]["dismissed_flags"] == 1
