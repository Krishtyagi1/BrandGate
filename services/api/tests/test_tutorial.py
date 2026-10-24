def test_tutorial_state_is_per_account(account):
    first, _, _ = account()
    second, _, _ = account()
    assert first.get("/api/tutorial").json()["completed"] is False
    assert (
        first.post("/api/tutorial", json={"completed": True, "dismissed": True}).status_code == 200
    )
    assert first.get("/api/tutorial").json()["completed"]
    assert not second.get("/api/tutorial").json()["completed"]


def test_example_is_isolated_idempotent_and_requires_human_confirmation(workspace):
    owner, org, _ = workspace
    first = owner.post("/api/tutorial/example")
    assert first.status_code == 201, first.text
    data = first.json()
    assert data["org_id"] != org
    second = owner.post("/api/tutorial/example")
    assert second.json()["org_id"] == data["org_id"]
    assert owner.get("/api/tutorial").json()["example"]["org_id"] == data["org_id"]
    knowledge = owner.get(f"/api/organisations/{data['org_id']}/knowledge").json()
    assert knowledge["version"]["status"] == "draft"
    assert not knowledge["rules"]
    assert len(knowledge["proposals"]) >= 5
    assert all(p["status"] == "pending" for p in knowledge["proposals"])
    assert all(p["source_document_id"] and p["source_excerpt"] for p in knowledge["proposals"])
    assert owner.get(f"/api/organisations/{org}/drafts").json() == []
