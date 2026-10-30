from uuid import uuid4

from conftest import add_member
from test_review_workflow import setup_review


def preview(owner, base, run, question="Why was this document flagged?"):
    return owner.post(f"{base}/review-runs/{run['id']}/chat/preview", json={"question": question})


def send_chat(owner, base, run, body, key=None):
    return owner.post(
        f"{base}/review-runs/{run['id']}/chat",
        json={
            "question": body["payload"]["question"],
            "preview_hash": body["preview_hash"],
            "idempotency_key": key or str(uuid4()),
        },
    )


def chat_provider(monkeypatch, *, forged=False, callback=None, failure=False):
    from providers.openrouter import ProviderUnavailable

    calls = []

    def complete(system, payload, schema, purpose, usage_callback):
        calls.append(payload)
        if callback:
            callback()
        if failure:
            raise ProviderUnavailable("Synthetic provider outage")
        return schema(
            message="Here is what the saved review found.",
            items=[
                {
                    "finding_id": f["id"],
                    "explanation": "The required disclaimer is missing.",
                    "citation_ids": ["invented"] if forged else [e["id"] for e in f["evidence"]],
                }
                for f in payload["findings"]
            ],
        ), {"model": "SYNTHETIC_TEST_DOUBLE"}

    monkeypatch.setattr("providers.openrouter.complete", complete)
    return calls


def test_document_chat_preview_history_citations_stream_and_idempotency(workspace, monkeypatch):
    owner, org, _ = workspace
    base, draft, _, run = setup_review(owner, org, monkeypatch, text="Everyday care.")
    calls = chat_provider(monkeypatch)
    p = preview(owner, base, run)
    assert p.status_code == 200, p.text
    key = str(uuid4())
    result = send_chat(owner, base, run, p.json(), key)
    assert result.status_code == 200, result.text
    answer = result.json()
    assert answer["items"][0]["citations"][0]["excerpt"] == "Results vary."
    assert answer["mode"] == "live_ai"
    assert send_chat(owner, base, run, p.json(), key).json()["id"] == answer["id"]
    assert len(calls) == 1
    history = owner.get(f"{base}/review-runs/{run['id']}/chat").json()
    assert len(history["turns"]) == 1
    streamed = owner.post(f"{base}/review-runs/{run['id']}/chat/{answer['id']}/stream")
    assert "TEXT_MESSAGE_CONTENT" in streamed.text and "RUN_FINISHED" in streamed.text
    assert owner.get(f"{base}/drafts/{draft['id']}").json()["status"] == "draft"
    follow = preview(owner, base, run, "What does that mean?").json()
    assert len(follow["payload"]["history"]) == 1
    assert send_chat(owner, base, run, follow).status_code == 200


def test_document_chat_rejects_forged_citations_and_provider_failure(workspace, monkeypatch):
    owner, org, _ = workspace
    base, _, _, run = setup_review(owner, org, monkeypatch, text="Everyday care.")
    chat_provider(monkeypatch, forged=True)
    result = send_chat(owner, base, run, preview(owner, base, run).json())
    assert result.status_code == 502, result.text
    chat_provider(monkeypatch, failure=True)
    result = send_chat(owner, base, run, preview(owner, base, run).json())
    assert result.status_code == 503
    assert "Synthetic provider outage" in result.text


def test_document_chat_access_consent_and_stale_during_inference(workspace, account, monkeypatch):
    owner, org, _ = workspace
    base, draft, _, run = setup_review(owner, org, monkeypatch, text="Everyday care.")
    stranger, email, _ = account()
    assert preview(stranger, base, run).status_code == 404
    add_member(owner, org, stranger, email, "creator")
    assert preview(stranger, base, run).status_code == 404
    p = preview(owner, base, run).json()
    owner.post(
        f"{base}/ai/consent",
        json={"enabled": False, "policy_version": "openrouter-free-zdr-redacted-v1"},
    )
    calls = chat_provider(monkeypatch)
    assert send_chat(owner, base, run, p).status_code == 409
    assert not calls
    owner.post(
        f"{base}/ai/consent",
        json={"enabled": True, "policy_version": "openrouter-free-zdr-redacted-v1"},
    )

    def edit():
        owner.post(
            f"{base}/drafts/{draft['id']}/versions",
            json={
                "expected_current_version_id": draft["current_version_id"],
                "text": "Changed.",
            },
        )

    chat_provider(monkeypatch, callback=edit)
    assert send_chat(owner, base, run, p).status_code == 409
    assert owner.get(f"{base}/review-runs/{run['id']}/chat").status_code == 409


def test_document_chat_redaction_hash_and_private_history(workspace, account, monkeypatch):
    owner, org, _ = workspace
    base, _, _, run = setup_review(owner, org, monkeypatch, text="Everyday care.")
    p = preview(owner, base, run, "Explain this for person@example.com").json()
    assert "person@example.com" not in str(p["payload"])
    assert "[PRIVATE_" in p["payload"]["question"]
    calls = chat_provider(monkeypatch)
    body = {
        "question": "Explain this for person@example.com",
        "preview_hash": "0" * 64,
        "idempotency_key": str(uuid4()),
    }
    assert owner.post(f"{base}/review-runs/{run['id']}/chat", json=body).status_code == 409
    assert not calls
    body["preview_hash"] = p["preview_hash"]
    answer = owner.post(f"{base}/review-runs/{run['id']}/chat", json=body)
    assert answer.status_code == 200, answer.text
    assert "person@example.com" not in str(calls)
    reviewer, email, _ = account()
    add_member(owner, org, reviewer, email, "reviewer")
    assert reviewer.get(f"{base}/review-runs/{run['id']}/chat").json()["turns"] == []
    assert (
        reviewer.post(
            f"{base}/review-runs/{run['id']}/chat/{answer.json()['id']}/stream"
        ).status_code
        == 404
    )


def test_document_chat_failed_request_retry_is_stable(workspace, monkeypatch):
    owner, org, _ = workspace
    base, _, _, run = setup_review(owner, org, monkeypatch, text="Everyday care.")
    calls = chat_provider(monkeypatch, failure=True)
    p, key = preview(owner, base, run).json(), str(uuid4())
    assert send_chat(owner, base, run, p, key).status_code == 503
    assert send_chat(owner, base, run, p, key).status_code == 503
    assert len(calls) == 1


def test_document_chat_overview_cannot_silently_omit_flags(workspace, monkeypatch):
    owner, org, _ = workspace
    base, _, _, run = setup_review(owner, org, monkeypatch, text="Everyday care.")
    monkeypatch.setattr(
        "providers.openrouter.complete",
        lambda system, payload, schema, *a: (
            schema(message="No issues need attention.", items=[]),
            {"model": "SYNTHETIC_TEST_DOUBLE"},
        ),
    )
    assert send_chat(owner, base, run, preview(owner, base, run).json()).status_code == 502


def test_document_chat_context_overflow_and_unknown_private_tokens(workspace, monkeypatch):
    from uuid import UUID

    from psycopg.types.json import Jsonb

    from app.db import transaction

    owner, org, _ = workspace
    base, _, _, run = setup_review(owner, org, monkeypatch, text="Everyday care.")
    monkeypatch.setattr(
        "providers.openrouter.complete",
        lambda system, payload, schema, *a: (
            schema(message="[PRIVATE_999]", items=[]),
            {"model": "SYNTHETIC_TEST_DOUBLE"},
        ),
    )
    assert send_chat(owner, base, run, preview(owner, base, run).json()).status_code == 502
    user = owner.get("/api/auth/me").json()
    with transaction(user, UUID(org)) as conn:
        result = conn.execute(
            "SELECT result FROM review_runs WHERE id=%s", (run["id"],)
        ).fetchone()["result"]
        f = result["findings"][0]
        result["findings"] = [{**f, "id": f"flag-{i}"} for i in range(61)]
        conn.execute("UPDATE review_runs SET result=%s WHERE id=%s", (Jsonb(result), run["id"]))
    assert preview(owner, base, run).status_code == 422


def test_document_chat_dismissed_context_and_revoked_history(workspace, monkeypatch):
    owner, org, _ = workspace
    base, _, _, run = setup_review(owner, org, monkeypatch, text="Everyday care.")
    finding = owner.get(f"{base}/review-runs/{run['id']}").json()["result"]["findings"][0]
    owner.post(
        f"{base}/review-runs/{run['id']}/dismiss",
        json={"finding_id": finding["id"], "reason": "Synthetic dismissal"},
    )
    p = preview(owner, base, run).json()
    assert p["payload"]["findings"][0]["dismissed"] is True
    chat_provider(monkeypatch)
    assert send_chat(owner, base, run, p).status_code == 200
    owner.post(
        f"{base}/ai/consent",
        json={"enabled": False, "policy_version": "openrouter-free-zdr-redacted-v1"},
    )
    assert owner.get(f"{base}/review-runs/{run['id']}/chat").status_code == 409


def test_document_chat_authority_rows_locked_during_consent_check(workspace, monkeypatch):
    from psycopg.errors import LockNotAvailable

    from app import document_chat
    from app.db import transaction

    owner, org, _ = workspace
    base, _, _, run = setup_review(owner, org, monkeypatch, text="Everyday care.")
    original = document_chat.require_consent
    observed = []

    def require_locked(conn, org_id):
        original(conn, org_id)
        for table, key in (("organisations", "id"), ("ai_processing_consents", "org_id")):
            try:
                with transaction(owner.get("/api/auth/me").json(), org_id) as other:
                    other.execute(
                        f"SELECT * FROM {table} WHERE {key}=%s FOR UPDATE NOWAIT", (org_id,)
                    )
                observed.append(False)
            except LockNotAvailable:
                observed.append(True)

    monkeypatch.setattr(document_chat, "require_consent", require_locked)
    chat_provider(monkeypatch)
    assert send_chat(owner, base, run, preview(owner, base, run).json()).status_code == 200
    assert observed and all(observed)
