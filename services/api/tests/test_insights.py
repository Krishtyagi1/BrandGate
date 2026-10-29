from uuid import uuid4

from conftest import add_member
from test_review_workflow import setup_review


def test_insights_deduplicates_categories_per_draft_and_keeps_statuses_separate():
    from app.insights import summarize

    observation = {
        "id": "f",
        "category": "visual",
        "status": "advisory",
        "quote": "logo",
        "issue_type": "placement",
    }
    rows = [
        {
            "draft_id": "one",
            "creator_id": "human",
            "creator_name": "Human",
            "channel": "website",
            "campaign": "Launch",
            "status": "completed",
            "result": {"findings": [observation, {**observation, "id": "other"}]},
        },
        {
            "draft_id": "two",
            "creator_id": "human",
            "creator_name": "Human",
            "channel": "email",
            "campaign": "",
            "status": "incomplete",
            "result": {
                "findings": [{"category": "claim", "status": "unverified", "quote": "Best ever"}]
            },
        },
    ]
    result = summarize(rows, [])
    assert result["reviewed_drafts"] == 2 and result["incomplete_drafts"] == 1
    assert result["finding_types"][0]["drafts"] == 1
    assert sum(r["drafts"] for r in result["finding_types"]) == 2
    assert result["guideline_gaps"][0]["drafts"] == 1
    assert {r["label"] for r in result["by_campaign"]} == {"Launch", "No campaign"}
    assert (
        next(r for r in result["by_channel"] if r["label"] == "website")["finding_type"]
        == "placement"
    )


def test_insights_latest_run_campaign_and_access(workspace, account, monkeypatch):
    owner, org, _ = workspace
    base, draft, body, _ = setup_review(owner, org, monkeypatch, text="Everyday care.")
    meta = owner.post(
        f"{base}/drafts/{draft['id']}/campaign",
        json={
            "expected_current_version_id": draft["current_version_id"],
            "campaign": "Autumn launch",
        },
    )
    assert meta.status_code == 200, meta.text
    assert (
        owner.post(
            f"{base}/drafts/{draft['id']}/campaign",
            json={"expected_current_version_id": str(uuid4()), "campaign": "Wrong"},
        ).status_code
        == 409
    )
    owner.post(
        f"{base}/drafts/{draft['id']}/reviews", json={**body, "idempotency_key": str(uuid4())}
    )
    response = owner.get(f"{base}/insights?days=30")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["reviewed_drafts"] == 1
    assert data["by_campaign"][0]["label"] == "Autumn launch"
    assert data["finding_types"][0]["drafts"] == 1
    assert owner.get(f"{base}/insights?days=0").status_code == 422
    stranger, email, _ = account()
    assert stranger.get(f"{base}/insights").status_code == 404
    add_member(owner, org, stranger, email, "creator")
    assert stranger.get(f"{base}/insights").status_code == 403
    second_org = owner.post("/api/organisations", json={"name": "Empty"}).json()["id"]
    assert owner.get(f"/api/organisations/{second_org}/insights").json()["reviewed_drafts"] == 0


def test_insights_reporting_period_and_unanswered_questions(workspace, monkeypatch):
    from datetime import UTC, datetime, timedelta

    from test_followup import ask

    from app.db import transaction

    owner, org, _ = workspace
    base, _, _, run = setup_review(owner, org, monkeypatch, text="Everyday care.")
    finding = owner.get(f"{base}/review-runs/{run['id']}").json()["result"]["findings"][0]
    for _ in range(2):
        assert (
            ask(
                owner, base, run, finding, question="Is this claim independently tested?"
            ).status_code
            == 200
        )
    data = owner.get(f"{base}/insights?days=7").json()
    assert data["guideline_gaps"][0]["drafts"] == 1
    actor = owner.get("/api/auth/me").json()
    with transaction(actor, org) as conn:
        conn.execute(
            "UPDATE review_runs SET created_at=%s WHERE org_id=%s AND id=%s",
            (datetime.now(UTC) - timedelta(days=10), org, run["id"]),
        )
    assert owner.get(f"{base}/insights?days=7").json()["reviewed_drafts"] == 0
    assert owner.get(f"{base}/insights?days=30").json()["reviewed_drafts"] == 1


def test_visual_confirmation_separate_person_and_immutable_observation(
    workspace, account, monkeypatch
):
    from psycopg.types.json import Jsonb

    from app.db import transaction

    owner, org, _ = workspace
    base, draft, _, run = setup_review(owner, org, monkeypatch, text="Everyday care.")
    actor = owner.get("/api/auth/me").json()
    finding = {
        "id": "visual-test",
        "category": "visual",
        "status": "advisory",
        "quote": "Image appearance",
        "reason": "Possible distortion",
        "evidence": [],
        "region": {"x": 0, "y": 0, "width": 0.5, "height": 0.5},
    }
    with transaction(actor, org) as conn:
        conn.execute(
            "UPDATE review_runs SET result=%s WHERE org_id=%s AND id=%s",
            (Jsonb({"findings": [finding]}), org, run["id"]),
        )
    url = f"{base}/review-runs/{run['id']}/visual-confirmations"
    body = {
        "finding_id": finding["id"],
        "verdict": "confirmed",
        "note": "Compared with approved example.",
    }
    assert owner.post(url, json=body).status_code == 403
    reviewer, email, _ = account()
    add_member(owner, org, reviewer, email, "reviewer")
    confirmed = reviewer.post(url, json=body)
    assert confirmed.status_code == 201, confirmed.text
    assert reviewer.get(url).json()[0]["verdict"] == "confirmed"
    assert (
        owner.get(f"{base}/review-runs/{run['id']}").json()["result"]["findings"][0]["status"]
        == "advisory"
    )
    assert owner.get(f"{base}/drafts/{draft['id']}").json()["decisions"] == []


def test_recurrence_retains_corrected_errors_without_counting_rechecks_twice(
    workspace, monkeypatch
):
    owner, org, _ = workspace
    base, draft, body, _ = setup_review(owner, org, monkeypatch, text="Everyday care.")
    owner.post(
        f"{base}/drafts/{draft['id']}/reviews", json={**body, "idempotency_key": str(uuid4())}
    )
    saved = owner.post(
        f"{base}/drafts/{draft['id']}/versions",
        json={
            "expected_current_version_id": draft["current_version_id"],
            "text": "Everyday care. Results vary.",
        },
    ).json()
    preview = owner.get(f"{base}/drafts/{draft['id']}/ai-preview").json()
    owner.post(
        f"{base}/drafts/{draft['id']}/reviews",
        json={
            "version_id": saved["id"],
            "preview_hash": preview["preview_hash"],
            "idempotency_key": str(uuid4()),
        },
    )
    data = owner.get(f"{base}/insights?days=30").json()
    assert data["reviewed_drafts"] == 1
    assert data["drafts_with_findings"] == 1
    assert data["finding_types"][0]["drafts"] == 1
    assert data["finding_types"][0]["label"] == "messaging"
