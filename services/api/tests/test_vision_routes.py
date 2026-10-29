import json

import httpx
import pytest

from providers import openrouter, vision


def route_fixture(monkeypatch, zdr_models=(), bad_metadata=False):
    models = [
        {
            "id": f"synthetic/{name}:free",
            "pricing": {"prompt": "0", "completion": "0"},
            "architecture": {"input_modalities": ["text", "image"]},
            "supported_parameters": ["response_format", "structured_outputs"],
        }
        for name in ("a", "b")
    ]
    endpoints = [
        {
            "model_id": m["id"],
            "provider_name": "Synthetic",
            "tag": name,
            "pricing": m["pricing"],
            "supported_parameters": m["supported_parameters"],
        }
        for name, m in zip(("a", "b"), models)
    ]
    requests = []
    monkeypatch.setattr(openrouter, "get_models", lambda: models)
    monkeypatch.setattr(
        openrouter,
        "settings",
        lambda: {"OPENROUTER_API_KEY": "synthetic", "OPENROUTER_MODEL": "synthetic/a:free"},
    )

    def handler(request):
        requests.append(request)
        if request.url.path.endswith("/endpoints/zdr"):
            return httpx.Response(
                200,
                json={
                    "data": "invalid"
                    if bad_metadata
                    else [e for e in endpoints if e["model_id"] in zdr_models]
                },
            )
        if request.url.path.endswith("/endpoints"):
            endpoint = next(e for e in endpoints if e["model_id"] in request.url.path)
            return httpx.Response(200, json={"data": {"endpoints": [endpoint]}})
        if request.url.path.endswith("/key"):
            return httpx.Response(
                200, json={"data": {"free_model_daily_requests": {"remaining": 40}}}
            )
        return httpx.Response(
            200, json={"choices": [{"message": {"content": json.dumps({"findings": []})}}]}
        )

    monkeypatch.setattr(
        openrouter, "client", lambda: httpx.Client(transport=httpx.MockTransport(handler))
    )
    monkeypatch.setattr(openrouter, "_last_call", 0)
    monkeypatch.setattr(openrouter, "_attempts", 0)
    return endpoints, requests


def test_vision_selects_actual_zdr_endpoint_instead_of_first_catalogue_model(monkeypatch):
    route_fixture(monkeypatch, zdr_models=("synthetic/b:free",))
    assert vision.selected_vision_model()["id"] == "synthetic/b:free"


def test_vision_missing_published_zdr_endpoint_sends_no_image_post(monkeypatch):
    _, requests = route_fixture(monkeypatch)
    with pytest.raises(openrouter.ProviderUnavailable, match="zero-retention"):
        vision.evaluate({"requested_checks": ["logos"]}, ["data:image/png;base64,AA=="])
    assert not any(r.method == "POST" for r in requests)


def test_vision_malformed_policy_metadata_fails_closed(monkeypatch):
    route_fixture(monkeypatch, bad_metadata=True)
    with pytest.raises(openrouter.ProviderUnavailable):
        vision.selected_vision_model()


def test_vision_endpoint_itself_must_be_zero_price_and_schema_capable(monkeypatch):
    endpoints, _ = route_fixture(monkeypatch, zdr_models=("synthetic/a:free", "synthetic/b:free"))
    endpoints[0]["pricing"] = {"prompt": "0.01", "completion": "0"}
    endpoints[1]["supported_parameters"] = ["response_format"]
    with pytest.raises(openrouter.ProviderUnavailable):
        vision.selected_vision_model()


def test_vision_status_is_org_scoped_and_uses_metadata_only(workspace, account, monkeypatch):
    owner, org, _ = workspace
    _, requests = route_fixture(monkeypatch)
    url = f"/api/organisations/{org}/ai/vision-status"
    response = owner.get(url)
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "blocked"
    assert response.json()["candidates"][0]["eligible"] is False
    assert not any(r.method == "POST" for r in requests)
    stranger, _, _ = account()
    assert stranger.get(url).status_code == 404


def test_zdr_endpoint_identity_cannot_be_borrowed_from_another_tag(monkeypatch):
    endpoints, _ = route_fixture(monkeypatch, zdr_models=("synthetic/a:free",))
    # The ZDR list and model listing must agree on the whole endpoint identity.
    original_client = openrouter.client

    def client():
        inner = original_client()
        original_send = inner.send

        def send(request, **kwargs):
            response = original_send(request, **kwargs)
            if request.url.path.endswith("/models/synthetic/a:free/endpoints"):
                body = response.json()
                body["data"]["endpoints"][0]["tag"] = "different-retaining-endpoint"
                return httpx.Response(200, json=body, request=request)
            return response

        inner.send = send
        return inner

    monkeypatch.setattr(openrouter, "client", client)
    with pytest.raises(openrouter.ProviderUnavailable):
        vision.selected_vision_model()


def test_null_endpoint_parameters_return_unavailable_instead_of_crashing(monkeypatch):
    from providers.vision_routes import inspect_routes

    endpoints, _ = route_fixture(monkeypatch, zdr_models=("synthetic/a:free",))
    endpoints[0]["supported_parameters"] = None
    result = inspect_routes()
    assert result["status"] == "blocked"
    assert not any(c["eligible"] for c in result["candidates"])


def test_metadata_stream_stops_reading_at_byte_cap():
    from providers.vision_routes import _read

    chunks_read = []

    class Oversized(httpx.SyncByteStream):
        def __iter__(self):
            for index in range(20):
                chunks_read.append(index)
                yield b"x" * 1_000_000

    with httpx.Client(
        transport=httpx.MockTransport(lambda request: httpx.Response(200, stream=Oversized()))
    ) as client:
        with pytest.raises(openrouter.ProviderUnavailable):
            _read(client, "/endpoints/zdr")
    assert len(chunks_read) <= 6


def test_metadata_deadline_stops_a_trickling_response(monkeypatch):
    from providers import vision_routes

    clock = [0]
    chunks_read = []
    monkeypatch.setattr(vision_routes.time, "monotonic", lambda: clock[0])

    class Trickle(httpx.SyncByteStream):
        def __iter__(self):
            for index in range(10):
                chunks_read.append(index)
                clock[0] += 6
                yield b" "

    with httpx.Client(
        transport=httpx.MockTransport(lambda request: httpx.Response(200, stream=Trickle()))
    ) as client:
        with pytest.raises(openrouter.ProviderUnavailable):
            vision_routes._read(client, "/endpoints/zdr", deadline=10)
    assert len(chunks_read) == 2
