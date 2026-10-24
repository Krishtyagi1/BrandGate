from uuid import uuid4

from test_review_workflow import setup_review


def test_review_scope_x_platform_and_task_persist(workspace):
    owner, org, _ = workspace
    response = owner.post(
        f"/api/organisations/{org}/drafts",
        json={
            "text": "Cloudberry costs INR 799.",
            "category": "social_media",
            "platform": "x",
            "requested_checks": ["prices", "tone"],
            "task_instructions": "Verify this product price and tone.",
        },
    )
    assert response.status_code == 201, response.text
    draft = response.json()
    assert draft["channel"] == draft["platform"] == "x"
    assert draft["category"] == "social_media"
    assert draft["requested_checks"] == ["prices", "tone"]
    assert (
        owner.get(f"/api/organisations/{org}/drafts/{draft['id']}").json()["task_instructions"]
        == "Verify this product price and tone."
    )


def test_changed_tasks_invalidate_previous_check_without_changing_content(workspace, monkeypatch):
    owner, org, _ = workspace
    base, draft, _, run = setup_review(owner, org, monkeypatch)
    changed = owner.post(
        f"{base}/drafts/{draft['id']}/scope",
        json={
            "expected_current_version_id": draft["current_version_id"],
            "category": "email",
            "requested_checks": ["required_wording"],
            "task_instructions": "Check disclaimer only.",
        },
    )
    assert changed.status_code == 200, changed.text
    assert owner.get(f"{base}/review-runs/{run['id']}").json()["stale"]
    assert (
        owner.get(f"{base}/drafts/{draft['id']}").json()["current_version_id"]
        == draft["current_version_id"]
    )
    preview = owner.get(f"{base}/drafts/{draft['id']}/ai-preview").json()
    assert preview["payload"]["review_scope"]["requested_checks"] == ["required_wording"]
    assert preview["payload"]["review_scope"]["task_instructions"] == "Check disclaimer only."


def test_missing_selected_tone_is_explicit_and_other_rules_checked(workspace, monkeypatch):
    owner, org, _ = workspace
    base, draft, _, _ = setup_review(owner, org, monkeypatch)
    owner.post(
        f"{base}/drafts/{draft['id']}/scope",
        json={
            "expected_current_version_id": draft["current_version_id"],
            "category": "other",
            "requested_checks": ["required_wording", "tone"],
        },
    )
    preview = owner.get(f"{base}/drafts/{draft['id']}/ai-preview").json()
    started = owner.post(
        f"{base}/drafts/{draft['id']}/reviews",
        json={
            "version_id": draft["current_version_id"],
            "preview_hash": preview["preview_hash"],
            "idempotency_key": str(uuid4()),
        },
    )
    assert started.status_code == 202, started.text
    run = owner.get(f"{base}/review-runs/{started.json()['id']}").json()
    statuses = {r["check"]: r["status"] for r in run["result"]["check_coverage"]}
    assert statuses["tone"] == "source_missing"
    assert statuses["required_wording"] == "passed"


def test_video_is_rejected_as_unsupported(workspace):
    owner, org, _ = workspace
    response = owner.post(
        f"/api/organisations/{org}/drafts/upload",
        files={"file": ("clip.mp4", b"synthetic-video", "video/mp4")},
    )
    assert response.status_code == 415 and "Video" in response.text


def test_all_selected_sources_missing_never_reports_complete(workspace, monkeypatch):
    owner, org, _ = workspace
    base, draft, _, _ = setup_review(owner, org, monkeypatch)
    owner.post(
        f"{base}/drafts/{draft['id']}/scope",
        json={
            "expected_current_version_id": draft["current_version_id"],
            "category": "email",
            "requested_checks": ["tone"],
        },
    )
    preview = owner.get(f"{base}/drafts/{draft['id']}/ai-preview").json()
    started = owner.post(
        f"{base}/drafts/{draft['id']}/reviews",
        json={
            "version_id": draft["current_version_id"],
            "preview_hash": preview["preview_hash"],
            "idempotency_key": str(uuid4()),
        },
    )
    run = owner.get(f"{base}/review-runs/{started.json()['id']}").json()
    assert run["status"] == "incomplete"
    assert run["result"]["checks"] == []
    assert run["result"]["check_coverage"][0]["status"] == "source_missing"


def test_visual_only_scope_does_not_require_a_text_transcript():
    from app.review_scope import needs_text

    assert not needs_text("image", {"requested_checks": ["logos", "colours_fonts"]})
    assert needs_text("image", {"requested_checks": ["prices", "logos"]})


def test_company_review_intent_reaches_preview_redacted():
    from app.ai_settings import prepare_payload
    from app.review_scope import scope_context

    scope = scope_context(
        {"requested_checks": ["tone"]}, {"instructions": "Email karan@example.com about tone."}
    )
    payload, _, _, _ = prepare_payload({"id": uuid4(), "text": "Hello"}, [], "general", scope)
    intent = payload["review_scope"]["company_instructions"]
    assert "karan@example.com" not in intent and "[PRIVATE_" in intent


def test_omitted_contextual_guidance_blocks_completion(workspace, monkeypatch):
    from conftest import add_rule, create_version

    owner, org, _ = workspace
    base = f"/api/organisations/{org}"
    v = create_version(owner, org)
    for index in range(24):
        add_rule(
            owner, org, v, type="prohibited_term", rule_key=f"term{index}", value=f"avoid{index}"
        )
    add_rule(
        owner,
        org,
        v,
        type="approved_fact",
        rule_key="approved_benefit",
        value="Our product removes surface oil.",
    )
    owner.post(f"{base}/guidelines/versions/{v}/activate")
    owner.post(
        f"{base}/ai/consent",
        json={"enabled": True, "policy_version": "openrouter-free-zdr-redacted-v1"},
    )
    from app.review_models import ReviewResponse

    monkeypatch.setattr(
        "providers.openrouter.complete",
        lambda *a, **kw: (ReviewResponse(findings=[]), {"model": "synthetic"}),
    )
    draft = owner.post(
        f"{base}/drafts",
        json={"text": "Welcome", "requested_checks": ["language", "claims"]},
    ).json()
    preview = owner.get(f"{base}/drafts/{draft['id']}/ai-preview").json()
    assert preview["payload"]["source_selection"]["included"] == 24
    started = owner.post(
        f"{base}/drafts/{draft['id']}/reviews",
        json={
            "version_id": draft["current_version_id"],
            "preview_hash": preview["preview_hash"],
            "idempotency_key": str(uuid4()),
        },
    )
    run = owner.get(f"{base}/review-runs/{started.json()['id']}").json()
    assert run["status"] == "incomplete"
    assert (
        next(r for r in run["result"]["check_coverage"] if r["check"] == "claims")["status"]
        == "not_checked"
    )


def test_historical_prices_do_not_create_a_current_conflict():
    from app.review_scope import selected_rules
    from evaluators.facts import check_facts

    def price(amount, start, end=None):
        return {
            "id": str(uuid4()),
            "type": "approved_fact",
            "rule_key": "price",
            "value": str(amount),
            "source_document_id": None,
            "source_location": "Company guidance",
            "source_excerpt": "",
            "fact": {
                "kind": "price",
                "entity": "Soap",
                "unit": "item",
                "currency": "INR",
                "amount": amount,
                "effective_from": start,
                "effective_to": end,
            },
        }

    old, current = price(100, "2020-01-01", "2020-12-31"), price(150, "2021-01-01")
    findings = check_facts("Soap costs INR 100", [old, current], "2026-10-24")
    assert len(findings) == 1 and findings[0]["status"] == "confirmed_mismatch"
    assert selected_rules([old], {"requested_checks": ["prices"]}) == []


def test_visual_only_review_can_reach_separate_human_without_transcript(workspace, account):
    from conftest import add_member

    owner, _, _ = workspace
    example = owner.post("/api/tutorial/example").json()
    org = example["org_id"]
    base = f"/api/organisations/{org}"
    knowledge = owner.get(f"{base}/knowledge").json()
    confirmed = owner.post(
        f"{base}/knowledge/confirm",
        json={
            "version_id": example["version_id"],
            "expected_snapshot_id": None,
            "proposal_ids": [p["id"] for p in knowledge["proposals"]],
            "replace_rule_ids": {},
        },
    )
    assert confirmed.status_code == 200, confirmed.text
    reviewer, email, _ = account()
    add_member(owner, org, reviewer, email, "reviewer")
    owner.post(
        f"{base}/ai/consent",
        json={"enabled": True, "policy_version": "openrouter-free-zdr-redacted-v1"},
    )
    draft = owner.get(f"{base}/drafts/{example['image_draft_id']}").json()
    owner.post(
        f"{base}/drafts/{draft['id']}/scope",
        json={
            "expected_current_version_id": draft["current_version_id"],
            "category": "visuals",
            "requested_checks": ["colours_fonts"],
        },
    )
    preview = owner.get(f"{base}/drafts/{draft['id']}/ai-preview").json()
    started = owner.post(
        f"{base}/drafts/{draft['id']}/reviews",
        json={
            "version_id": draft["current_version_id"],
            "preview_hash": preview["preview_hash"],
            "idempotency_key": str(uuid4()),
        },
    )
    run = owner.get(f"{base}/review-runs/{started.json()['id']}").json()
    assert run["status"] == "completed" and run["result"]["mode"] == "local_checks"
    assert not draft["current_version"]["projection"]["coverage"]["text_complete"]
    reviewer_id = reviewer.get("/api/auth/me").json()["id"]
    submitted = owner.post(
        f"{base}/drafts/{draft['id']}/approvals",
        json={
            "version_id": draft["current_version_id"],
            "reviewer_id": reviewer_id,
            "idempotency_key": str(uuid4()),
        },
    )
    assert submitted.status_code == 201, submitted.text
