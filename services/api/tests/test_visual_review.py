"""Synthetic pixels and HTTP fixtures only; no model accuracy or live calls."""

import hashlib
import json
from uuid import uuid4

import httpx
import pytest
from PIL import Image

from app.config import LOCAL
from providers import openrouter


@pytest.fixture
def visual_files():
    folder = LOCAL / "test-visual" / uuid4().hex
    folder.mkdir(parents=True)

    def create(name="candidate.png", colour="#ff0000"):
        path = folder / name
        Image.new("RGB", (60, 40), colour).save(path)
        return path

    yield create
    for path in folder.iterdir():
        path.unlink()
    folder.rmdir()


def palette_rule():
    return {
        "id": "rule-palette",
        "type": "approved_fact",
        "rule_key": "brand_palette",
        "value": "Use #0000ff",
        "source_document_id": "source-palette",
        "source_excerpt": "Use #0000ff",
        "source_location": "Page 1",
    }


def reference(path):
    return {
        "id": "reference-logo",
        "label": "Approved logo",
        "private_path": str(path.relative_to(LOCAL)),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "source_document_id": "source-logo",
        "source_location": "Image 1",
        "source_excerpt": "Approved logo example",
    }


def test_visual_palette_detects_dominant_mismatch_with_real_rule_evidence(visual_files):
    from app.visual_review import evaluate_visual

    result = evaluate_visual(visual_files(), [palette_rule()], [], ["colours_fonts"])
    assert result["findings"][0]["evidence"][0]["id"] == "rule-palette"
    assert result["findings"][0]["origin"] == "deterministic"
    assert result["check_coverage"][0]["status"] == "issues_found"
    assert "dominant" in result["check_coverage"][0]["reason"].lower()


def test_visual_palette_clean_control_is_scoped_and_never_claims_fonts(visual_files):
    from app.visual_review import evaluate_visual

    result = evaluate_visual(
        visual_files(colour="#0000ff"), [palette_rule()], [], ["colours_fonts"]
    )
    assert result["findings"] == []
    assert result["check_coverage"][0]["status"] == "checked"
    assert "font" in result["check_coverage"][0]["reason"].lower()
    assert result["mode"] == "local"


def test_visual_missing_references_and_accessibility_never_pass(visual_files):
    from app.visual_review import evaluate_visual

    result = evaluate_visual(visual_files(), [], [], ["logos", "accessibility"])
    assert {row["status"] for row in result["check_coverage"]} == {"source_missing"}
    assert result["findings"] == []


def test_visual_rejects_path_escape_hash_tampering_and_video(visual_files):
    from app.visual_review import evaluate_visual, visual_manifest

    path = visual_files()
    ref = reference(path)
    with pytest.raises(ValueError):
        visual_manifest({"private_path": "../AGENTS.md"}, [], [])
    result = evaluate_visual(path, [], [{**ref, "sha256": "0" * 64}], ["logos"])
    assert result["check_coverage"][0]["status"] == "unavailable"
    assert result["findings"] == []
    video = path.with_suffix(".mp4")
    video.write_bytes(b"not an image")
    result = evaluate_visual(video, [], [], ["logos"])
    assert result["check_coverage"][0]["status"] == "unsupported"


def test_visual_manifest_pins_actual_images_without_paths(visual_files):
    from app.visual_review import visual_manifest

    path = visual_files()
    ref = reference(path)
    result = visual_manifest(
        {"id": "candidate-v1", "private_path": ref["private_path"], "sha256": ref["sha256"]},
        [palette_rule()],
        [ref],
    )
    assert result["candidate"]["sha256"] == ref["sha256"]
    assert result["references"][0]["id"] == "reference-logo"
    assert "private_path" not in json.dumps(result)
    assert str(path) not in json.dumps(result)


@pytest.fixture
def vision_http(monkeypatch):
    model = {
        "id": "synthetic/vision:free",
        "pricing": {"prompt": "0", "completion": "0", "image": "0"},
        "architecture": {"input_modalities": ["text", "image"]},
        "supported_parameters": ["response_format", "structured_outputs"],
    }
    monkeypatch.setattr(
        openrouter,
        "settings",
        lambda: {"OPENROUTER_API_KEY": "synthetic", "OPENROUTER_MODEL": "openrouter/free"},
    )
    monkeypatch.setattr(openrouter, "get_models", lambda: [model])
    monkeypatch.setattr(openrouter, "_attempts", 0)
    monkeypatch.setattr(openrouter, "_last_call", 0)
    monkeypatch.setattr(openrouter.time, "sleep", lambda _: None)

    def configure(findings=None, remaining=40, status=200):
        requests = []

        def handler(request):
            requests.append(request)
            endpoint = {"model_id": model["id"], "provider_name": "SyntheticTransport", "tag": "synthetic", "pricing": model["pricing"], "supported_parameters": model["supported_parameters"]}
            if request.url.path.endswith("/endpoints/zdr"):
                return httpx.Response(200, json={"data": [endpoint]})
            if request.url.path.endswith("/endpoints"):
                return httpx.Response(200, json={"data": {"endpoints": [endpoint]}})
            if request.url.path.endswith("/key"):
                return httpx.Response(
                    200, json={"data": {"free_model_daily_requests": {"remaining": remaining}}}
                )
            return httpx.Response(
                status,
                json={
                    "id": "synthetic",
                    "model": model["id"],
                    "provider": "SyntheticTransport",
                    "usage": {},
                    "choices": [{"message": {"content": json.dumps({"findings": findings or []})}}],
                },
            )

        monkeypatch.setattr(
            openrouter, "client", lambda: httpx.Client(transport=httpx.MockTransport(handler))
        )
        return model, requests

    return configure


def vision_issue(**changes):
    return {
        "check": "logos",
        "severity": "medium",
        "reason": "The candidate symbol differs from the approved example.",
        "evidence_ids": ["reference-logo"],
        "region": {"x": 0.1, "y": 0.1, "width": 0.5, "height": 0.5},
        **changes,
    }


def test_visual_actual_image_http_contract_and_advisory_evidence(visual_files, vision_http):
    from app.visual_review import evaluate_visual

    model, requests = vision_http([vision_issue()])
    path = visual_files()
    events = []
    result = evaluate_visual(
        path, [], [reference(path)], ["logos"], lambda *args: events.append(args)
    )
    posts = [r for r in requests if r.method == "POST"]
    assert len(posts) == 1
    body = json.loads(posts[0].content)
    assert body["model"] == model["id"]
    assert body["provider"]["zdr"] and body["provider"]["data_collection"] == "deny"
    assert body["provider"]["allow_fallbacks"] is False
    assert all(value == 0 for value in body["provider"]["max_price"].values())
    assert (
        len([part for part in body["messages"][1]["content"] if part["type"] == "image_url"]) == 2
    )
    assert str(path) not in json.dumps(body)
    assert result["findings"][0]["status"] == "advisory"
    assert result["findings"][0]["evidence"][0]["source_document_id"] == "source-logo"
    assert result["mode"] == "live"
    assert [event[0] for event in events] == ["attempted", "completed"]


@pytest.mark.parametrize(
    "change",
    [
        {"evidence_ids": ["forged"]},
        {"region": {"x": 0.8, "y": 0, "width": 0.5, "height": 0.5}},
        {"region": {"x": -1, "y": 0, "width": 0.1, "height": 0.1}},
    ],
)
def test_visual_forged_image_evidence_is_rejected_without_pass(visual_files, vision_http, change):
    from app.visual_review import evaluate_visual

    vision_http([vision_issue(**change)])
    path = visual_files()
    result = evaluate_visual(path, [], [reference(path)], ["logos"])
    assert result["findings"] == []
    assert result["check_coverage"][0]["status"] == "unavailable"


@pytest.mark.parametrize(
    "guard",
    [
        "quota",
        "attempts",
        "modality",
        "schema",
        "image_pricing",
        "token_pricing",
        "missing_token_pricing",
        "429",
    ],
)
def test_visual_no_inference_when_budget_or_capabilities_fail(
    visual_files, vision_http, monkeypatch, guard
):
    from app.visual_review import evaluate_visual

    model, requests = vision_http(
        remaining=10 if guard == "quota" else 40, status=429 if guard == "429" else 200
    )
    if guard == "attempts":
        monkeypatch.setattr(openrouter, "_attempts", 10)
    elif guard == "modality":
        model["architecture"]["input_modalities"] = ["text"]
    elif guard == "schema":
        model["supported_parameters"] = ["response_format"]
    elif guard == "image_pricing":
        model["pricing"]["image"] = "0.1"
    elif guard == "token_pricing":
        model["pricing"]["completion"] = "0.1"
    elif guard == "missing_token_pricing":
        del model["pricing"]["prompt"]
    path = visual_files()
    result = evaluate_visual(path, [], [reference(path)], ["logos"])
    assert result["check_coverage"][0]["status"] == "unavailable"
    assert result["findings"] == []
    assert len([r for r in requests if r.method == "POST"]) == (1 if guard == "429" else 0)


def test_visual_palette_requires_literal_source_support(visual_files):
    from app.visual_review import evaluate_visual

    rule = {**palette_rule(), "source_excerpt": "This source never specifies a colour"}
    result = evaluate_visual(visual_files(), [rule], [], ["colours_fonts"])
    assert result["findings"] == []
    assert result["check_coverage"][0]["status"] == "source_missing"


def test_visual_requested_font_guidance_is_not_hidden_by_palette_success(visual_files, vision_http):
    from app.visual_review import evaluate_visual

    vision_http(status=429)
    path = visual_files(colour="#0000ff")
    font = {
        **palette_rule(),
        "id": "font-rule",
        "rule_key": "brand_font",
        "value": "Use a serif font",
        "source_excerpt": "Use a serif font",
    }
    result = evaluate_visual(path, [palette_rule(), font], [reference(path)], ["colours_fonts"])
    assert result["check_coverage"][0]["status"] == "unavailable"
    assert result["check_coverage"][0]["local_palette"]["status"] == "checked"


@pytest.mark.parametrize("status", [200, 404])
def test_visual_optional_image_fee_omission_keeps_zero_cost_endpoint_cap(
    visual_files, vision_http, status
):
    from app.visual_review import evaluate_visual

    model, requests = vision_http(status=status)
    del model["pricing"]["image"]
    path = visual_files()
    result = evaluate_visual(path, [], [reference(path)], ["logos"])
    assert result["check_coverage"][0]["status"] == ("checked" if status == 200 else "unavailable")
    posts = [request for request in requests if request.method == "POST"]
    assert len(posts) == 1
    body = json.loads(posts[0].content)
    assert body["provider"]["max_price"] == {"prompt": 0, "completion": 0, "request": 0, "image": 0}
    assert body["provider"]["zdr"] is True
    assert body["provider"]["data_collection"] == "deny"
    assert body["provider"]["allow_fallbacks"] is False


def test_visual_font_advisory_cannot_be_presented_as_exact_identity(visual_files, vision_http):
    from app.visual_review import evaluate_visual

    vision_http([vision_issue(check="colours_fonts", reason="This is exactly FontBrand.")])
    path = visual_files()
    font = {
        **palette_rule(),
        "id": "font-rule",
        "rule_key": "brand_font",
        "value": "Use a serif font",
        "source_excerpt": "Use a serif font",
    }
    result = evaluate_visual(path, [font], [reference(path)], ["colours_fonts"])
    assert result["findings"][0]["status"] == "advisory"
    assert "cannot confirm" in result["findings"][0]["reason"].lower()


def test_visual_invalid_logo_reference_does_not_discard_local_palette(visual_files):
    from app.visual_review import evaluate_visual

    path = visual_files()
    ref = {**reference(path), "sha256": "0" * 64}
    result = evaluate_visual(path, [palette_rule()], [ref], ["colours_fonts", "logos"])
    rows = {row["check"]: row for row in result["check_coverage"]}
    assert rows["colours_fonts"]["status"] == "issues_found"
    assert rows["logos"]["status"] == "unavailable"
    assert result["findings"][0]["origin"] == "deterministic"


@pytest.mark.parametrize("matching_source", [True, False])
def test_visual_reference_can_share_only_its_actual_approved_rule_id(
    visual_files, vision_http, matching_source
):
    from app.visual_review import evaluate_visual

    _, requests = vision_http([vision_issue()])
    path = visual_files()
    ref = reference(path)
    rule = {
        "id": ref["id"],
        "type": "approved_fact",
        "rule_key": "logo_reference",
        "value": ref["source_excerpt"],
        "source_excerpt": ref["source_excerpt"],
        "source_location": ref["source_location"],
        "source_document_id": ref["source_document_id"] if matching_source else "other-source",
    }
    result = evaluate_visual(path, [rule], [ref], ["logos"])
    assert result["check_coverage"][0]["status"] == (
        "issues_found" if matching_source else "unavailable"
    )
    assert len([request for request in requests if request.method == "POST"]) == (
        1 if matching_source else 0
    )
    if matching_source:
        assert result["findings"][0]["evidence"][0]["sha256"] == ref["sha256"]
