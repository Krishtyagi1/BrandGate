from uuid import uuid4

from test_review_workflow import setup_review

from app.review_models import RewriteResponse
from app.rewrites import RewriteJudge


def test_correction_creates_revision_and_requires_recheck(workspace, monkeypatch):
    owner, org, _ = workspace
    base, draft, _, parent = setup_review(owner, org, monkeypatch, text="Care today.")
    detail = owner.get(f"{base}/review-runs/{parent['id']}").json()
    finding = detail["result"]["findings"][0]

    def fake(system, payload, schema, purpose="review", usage_callback=None):
        if schema is RewriteResponse:
            return RewriteResponse(
                minimal="Care today. Results vary.", natural="Everyday care. Results vary."
            ), {"model": "synthetic-rewrite-fixture"}
        if schema is RewriteJudge:
            return RewriteJudge(
                minimal_safe=True, natural_safe=True, reason="Synthetic safe fixture"
            ), {"model": "synthetic-judge-fixture"}
        raise AssertionError("Unexpected schema")

    monkeypatch.setattr("providers.openrouter.complete", fake)
    preview = owner.get(f"{base}/drafts/{draft['id']}/ai-preview").json()
    body = {
        "finding_id": finding["id"],
        "preview_hash": preview["preview_hash"],
        "idempotency_key": str(uuid4()),
    }
    started = owner.post(f"{base}/review-runs/{parent['id']}/rewrites", json=body)
    assert started.status_code == 202, started.text
    job = owner.get(f"{base}/review-runs/{started.json()['id']}").json()
    assert job["status"] == "completed", job
    assert len(job["result"]["options"]) == 2
    duplicate = owner.post(f"{base}/review-runs/{parent['id']}/rewrites", json=body)
    assert duplicate.json()["id"] == job["id"]
    option = job["result"]["options"][0]
    applied = owner.post(
        f"{base}/drafts/{draft['id']}/apply-rewrite",
        json={
            "expected_current_version_id": draft["current_version_id"],
            "option_id": option["id"],
        },
    )
    assert applied.status_code == 201, applied.text
    assert applied.json()["text"] == "Care today. Results vary."
    assert owner.get(f"{base}/review-runs/{parent['id']}").json()["stale"]
    assert (
        owner.post(
            f"{base}/drafts/{draft['id']}/apply-rewrite",
            json={
                "expected_current_version_id": draft["current_version_id"],
                "option_id": option["id"],
            },
        ).status_code
        == 409
    )


def test_unsafe_judge_blocks_correction_options(workspace, monkeypatch):
    owner, org, _ = workspace
    base, draft, _, parent = setup_review(owner, org, monkeypatch, text="Care today.")
    finding = owner.get(f"{base}/review-runs/{parent['id']}").json()["result"]["findings"][0]

    def fake(system, payload, schema, purpose="review", usage_callback=None):
        if schema is RewriteResponse:
            return RewriteResponse(
                minimal="Cures disease. Results vary.", natural="Guaranteed cure. Results vary."
            ), {"model": "synthetic-unsafe-fixture"}
        return RewriteJudge(minimal_safe=False, natural_safe=False, reason="Unsupported claims"), {
            "model": "synthetic-judge-fixture"
        }

    monkeypatch.setattr("providers.openrouter.complete", fake)
    preview = owner.get(f"{base}/drafts/{draft['id']}/ai-preview").json()
    started = owner.post(
        f"{base}/review-runs/{parent['id']}/rewrites",
        json={
            "finding_id": finding["id"],
            "preview_hash": preview["preview_hash"],
            "idempotency_key": str(uuid4()),
        },
    ).json()
    result = owner.get(f"{base}/review-runs/{started['id']}").json()
    assert result["status"] == "incomplete" and result["result"]["options"] == []
