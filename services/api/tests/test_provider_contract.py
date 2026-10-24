import json

import httpx
import pytest

from app.review_models import ReviewResponse
from providers import openrouter


@pytest.fixture
def provider(monkeypatch):
    monkeypatch.setattr(
        openrouter,
        "settings",
        lambda: {"OPENROUTER_API_KEY": "synthetic-key", "OPENROUTER_MODEL": "synthetic/model:free"},
    )
    monkeypatch.setattr(openrouter, "selected_model", lambda: {"id": "synthetic/model:free"})
    monkeypatch.setattr(openrouter, "_attempts", 0)
    monkeypatch.setattr(openrouter, "_last_call", 0)
    monkeypatch.setattr(openrouter.time, "sleep", lambda _: None)
    requests = []

    def configure(status=200, content=None, remaining=40):
        def handler(request):
            requests.append(request)
            if request.url.path.endswith("/key"):
                return httpx.Response(
                    200, json={"data": {"free_model_daily_requests": {"remaining": remaining}}}
                )
            return httpx.Response(
                status,
                json=content
                or {
                    "id": "synthetic-request",
                    "model": "synthetic/model:free",
                    "provider": "SyntheticTransport",
                    "choices": [{"message": {"content": '{"findings":[]}'}}],
                    "usage": {"prompt_tokens": 1, "completion_tokens": 1},
                },
            )

        monkeypatch.setattr(
            openrouter, "client", lambda: httpx.Client(transport=httpx.MockTransport(handler))
        )
        return requests

    return configure


def test_http_request_enforces_privacy_schema_and_zero_prices(provider):
    requests = provider()
    parsed, meta = openrouter.complete(
        "Synthetic system", {"content": "Synthetic data"}, ReviewResponse
    )
    request = next(r for r in requests if r.url.path.endswith("/chat/completions"))
    body = json.loads(request.content)
    assert body["provider"]["zdr"] is True
    assert body["provider"]["data_collection"] == "deny"
    assert body["provider"]["max_price"] == {"prompt": 0, "completion": 0, "request": 0, "image": 0}
    assert not body["provider"]["allow_fallbacks"]
    assert body["response_format"]["json_schema"]["strict"] is True
    assert parsed.findings == [] and meta["model"] == "synthetic/model:free"


@pytest.mark.parametrize("status", [401, 402, 403, 404, 429, 503])
def test_http_provider_errors_never_become_a_pass(provider, status):
    provider(status)
    with pytest.raises(openrouter.ProviderUnavailable):
        openrouter.complete("Synthetic", {}, ReviewResponse)


def test_quota_reserve_prevents_completion_dispatch(provider):
    requests = provider(remaining=10)
    with pytest.raises(openrouter.ProviderUnavailable):
        openrouter.complete("Synthetic", {}, ReviewResponse)
    assert all(not r.url.path.endswith("/chat/completions") for r in requests)


def test_invalid_structured_output_never_becomes_a_pass(provider):
    provider(content={"choices": [{"message": {"content": '{"findings":[],"approve":true}'}}]})
    with pytest.raises(openrouter.ProviderUnavailable):
        openrouter.complete("Synthetic", {}, ReviewResponse)
