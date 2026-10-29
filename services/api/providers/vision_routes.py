"""Public metadata preflight only. No prompts, pixels, keys or inference calls."""

import json
import time
from datetime import UTC, datetime
from urllib.parse import quote

import httpx

from providers import openrouter

MAX_CANDIDATES = 16


def _read(client, path, deadline=None):
    deadline = deadline if deadline is not None else time.monotonic() + 30
    try:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise ValueError("Metadata phase deadline exceeded")
        with client.stream("GET", openrouter.BASE + path, timeout=min(10, remaining)) as response:
            response.raise_for_status()
            content = bytearray()
            for chunk in response.iter_bytes():
                if time.monotonic() > deadline or len(content) + len(chunk) > 5_000_000:
                    raise ValueError("Metadata exceeds its time or byte budget")
                content.extend(chunk)
        body = json.loads(content)
        if not isinstance(body, dict) or "data" not in body:
            raise ValueError("Metadata has no data field")
        return body["data"]
    except (httpx.HTTPError, ValueError, TypeError):
        raise openrouter.ProviderUnavailable(
            "Could not verify published vision endpoint metadata. No image was sent."
        ) from None


def _identity(endpoint):
    if not isinstance(endpoint, dict):
        return None
    fields = tuple(endpoint.get(k) for k in ("model_id", "tag", "provider_name"))
    return fields if all(isinstance(v, str) and v for v in fields) else None


def inspect_routes():
    report = {
        "checked_at": datetime.now(UTC).isoformat(),
        "status": "blocked",
        "candidates": [],
        "omitted_candidates": 0,
        "notice": "Published metadata only, not a successful inference test. Zero-price/privacy/schema routing, owner consent and outbound preview remain required. No image or company source is sent by this check.",
    }
    candidates = []
    try:
        for model in openrouter.get_models():
            if not isinstance(model, dict):
                continue
            try:
                openrouter.validate_vision_model(model)
                if model["id"].endswith(":free"):
                    candidates.append(model)
            except (openrouter.ProviderUnavailable, TypeError, ValueError, AttributeError):
                continue
        candidates.sort(key=lambda m: m["id"])
        report["omitted_candidates"] = max(0, len(candidates) - MAX_CANDIDATES)
        if not candidates:
            report["reason"] = "No free model advertises image input and JSON schema support."
            return report
        with openrouter.client() as client:
            deadline = time.monotonic() + 30
            zdr = _read(client, "/endpoints/zdr", deadline)
            if not isinstance(zdr, list):
                raise openrouter.ProviderUnavailable(
                    "Could not verify the published zero-retention endpoint list. No image was sent."
                )
            identities = {key for e in zdr if (key := _identity(e)) is not None}
            for model in candidates[:MAX_CANDIDATES]:
                row = {"model": model["id"], "eligible": False, "endpoints": []}
                try:
                    data = _read(
                        client, "/models/" + quote(model["id"], safe="/:") + "/endpoints", deadline
                    )
                    if not isinstance(data, dict) or not isinstance(data.get("endpoints"), list):
                        raise openrouter.ProviderUnavailable(
                            "Model endpoint metadata is unavailable or malformed."
                        )
                    for endpoint in data["endpoints"]:
                        identity = _identity(endpoint)
                        if (
                            identity is None
                            or identity[0] != model["id"]
                            or identity not in identities
                        ):
                            continue
                        # A model's aggregated capabilities cannot establish the
                        # capabilities or price of this specific endpoint.
                        candidate = {
                            **model,
                            "pricing": endpoint.get("pricing", {}),
                            "supported_parameters": endpoint.get("supported_parameters", []),
                        }
                        if (
                            not isinstance(candidate["pricing"], dict)
                            or not isinstance(candidate["supported_parameters"], list)
                            or not all(
                                isinstance(p, str) for p in candidate["supported_parameters"]
                            )
                        ):
                            continue
                        try:
                            openrouter.validate_vision_model(candidate)
                        except openrouter.ProviderUnavailable:
                            continue
                        row["endpoints"].append({"provider": identity[2], "tag": identity[1]})
                    row["eligible"] = bool(row["endpoints"])
                    row["reason"] = (
                        "A published zero-retention endpoint advertises free pricing and schema support; inference is not yet verified."
                        if row["eligible"]
                        else "No published zero-retention endpoint also satisfies free pricing and JSON schema requirements."
                    )
                except openrouter.ProviderUnavailable as error:
                    row["reason"] = str(error)
                report["candidates"].append(row)
        if any(row["eligible"] for row in report["candidates"]):
            report["status"] = "candidate_available"
        report["reason"] = (
            "A candidate passed metadata preflight; runtime policy still decides availability."
            if report["status"] == "candidate_available"
            else "No verified free zero-retention vision endpoint is currently available. Use manual comparison with approved references."
        )
    except openrouter.ProviderUnavailable as error:
        report["status"] = "unavailable"
        report["reason"] = str(error)
    return report
