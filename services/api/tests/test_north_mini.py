"""North Mini returns schema arguments, never executable application tools."""

import json

import httpx
import pytest
from fastapi import HTTPException

from app import ai_settings
from app.review_models import ReviewResponse
from providers import openrouter

NORTH = "cohere/north-mini-code:free"
MODEL = {
    "id": NORTH,
    "pricing": {"prompt": "0", "completion": "0"},
    "supported_parameters": ["tools", "tool_choice", "reasoning"],
}


@pytest.fixture
def north(monkeypatch):
    monkeypatch.setenv("OPENROUTER_MODEL", NORTH)
    monkeypatch.setenv("OPENROUTER_ALLOW_PROVIDER_RETENTION", "true")
    monkeypatch.setattr(openrouter, "get_models", lambda: [MODEL])
    monkeypatch.setattr(openrouter, "_attempts", 0)
    monkeypatch.setattr(openrouter, "_last_call", 0)
    monkeypatch.setattr(openrouter.time, "sleep", lambda _: None)
    requests = []

    def configure(calls=None):
        def handler(request):
            requests.append(request)
            if request.url.path.endswith("/key"):
                return httpx.Response(
                    200, json={"data": {"free_model_daily_requests": {"remaining": 40}}}
                )
            return httpx.Response(
                200,
                json={
                    "id": "synthetic-north-request",
                    "model": NORTH,
                    "provider": "SyntheticTransport",
                    "choices": [
                        {
                            "finish_reason": "tool_calls",
                            "message": {
                                "content": None,
                                "reasoning": "Never expose this synthetic reasoning",
                                "tool_calls": calls
                                if calls is not None
                                else [
                                    {
                                        "type": "function",
                                        "function": {
                                            "name": "emit_result",
                                            "arguments": '{"findings":[]}',
                                        },
                                    }
                                ],
                            },
                        }
                    ],
                    "usage": {"cost": 0},
                },
            )

        monkeypatch.setattr(
            openrouter, "client", lambda: httpx.Client(transport=httpx.MockTransport(handler))
        )
        return requests

    return configure


def test_north_tool_result_is_validated_without_executing_tools(north):
    requests = north()
    result, metadata = openrouter.complete("Synthetic instructions", {}, ReviewResponse)
    body = json.loads(next(r.content for r in requests if r.url.path.endswith("/chat/completions")))
    assert "response_format" not in body
    assert body["tool_choice"] == {"type": "function", "function": {"name": "emit_result"}}
    assert len(body["tools"]) == 1
    assert body["tools"][0]["function"]["parameters"]["additionalProperties"] is False
    assert body["reasoning"] == {"exclude": True}
    assert body["provider"]["data_collection"] == "deny"
    assert body["provider"].get("zdr") is not True
    assert body["provider"]["max_price"] == {"prompt": 0, "completion": 0, "request": 0, "image": 0}
    assert result.findings == []
    assert metadata["policy_version"] == "openrouter-north-retention-redacted-v1"
    assert "reasoning" not in json.dumps(metadata)


@pytest.mark.parametrize(
    "calls",
    [
        [],
        [
            {
                "type": "function",
                "function": {"name": "approve_content", "arguments": '{"findings":[]}'},
            }
        ],
        [
            {
                "type": "function",
                "function": {"name": "emit_result", "arguments": '{"findings":[],"approve":true}'},
            }
        ],
        [{"type": "function", "function": {"name": "emit_result", "arguments": "not json"}}],
        [{"type": "function", "function": {"name": "emit_result", "arguments": '{"findings":[]}'}}]
        * 2,
    ],
)
def test_unexpected_or_invalid_tool_calls_never_pass(north, calls):
    requests = north(calls)
    with pytest.raises(openrouter.ProviderUnavailable):
        openrouter.complete("Synthetic", {}, ReviewResponse)
    assert len([r for r in requests if r.url.path.endswith("/chat/completions")]) == 2


def test_retention_opt_in_is_narrow_and_old_consent_fails(north, monkeypatch):
    north()
    assert openrouter.validate_model(MODEL)
    assert openrouter.policy_version() != openrouter.POLICY_VERSION

    class Connection:
        def execute(self, *_):
            return self

        def fetchone(self):
            return {"enabled": True, "policy_version": openrouter.POLICY_VERSION}

    with pytest.raises(HTTPException) as rejected:
        ai_settings.require_consent(Connection(), "synthetic-org")
    assert rejected.value.status_code == 409
    monkeypatch.setenv("OPENROUTER_ALLOW_PROVIDER_RETENTION", "false")
    assert openrouter.routing_policy(NORTH)["zdr"] is True
    assert openrouter.policy_version() == openrouter.POLICY_VERSION
    monkeypatch.setenv("OPENROUTER_MODEL", "synthetic/model:free")
    monkeypatch.setenv("OPENROUTER_ALLOW_PROVIDER_RETENTION", "true")
    assert openrouter.routing_policy("synthetic/model:free")["zdr"] is True


def test_north_schema_repair_stays_in_function_transport(north):
    requests = north([])
    with pytest.raises(openrouter.ProviderUnavailable):
        openrouter.complete("Synthetic", {}, ReviewResponse)
    bodies = [json.loads(r.content) for r in requests if r.url.path.endswith("/chat/completions")]
    assert "Call emit_result" in bodies[0]["messages"][0]["content"]
    assert '"enum"' in bodies[0]["messages"][0]["content"]
    assert "Return exactly the JSON object" not in bodies[1]["messages"][0]["content"]
    assert "Call emit_result" in bodies[1]["messages"][0]["content"]
