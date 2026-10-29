"""Static-image evaluation only. Authorised caller supplies approved snapshot data.

No persistence, approval or consent side effects occur here. The authenticated
review route must pin this input manifest in its explicit outbound preview.
"""

import base64
import hashlib
import re
import warnings
from collections import Counter
from io import BytesIO
from pathlib import Path
from uuid import uuid4

from PIL import Image, ImageOps, UnidentifiedImageError

from app.config import LOCAL
from providers import vision
from providers.openrouter import ProviderUnavailable
from retrieval.approved_sources import evidence

VISUAL_CHECKS = {"colours_fonts", "logos", "accessibility"}
HEX = re.compile(r"#[0-9a-fA-F]{6}\b|#[0-9a-fA-F]{3}\b")


def _path(value):
    path = Path(value)
    path = (path if path.is_absolute() else LOCAL / path).resolve()
    if not path.is_relative_to(LOCAL.resolve()) or not path.is_file():
        raise ValueError("Image is not available in private local storage.")
    return path


def _image(value, expected_hash=None):
    path = _path(value)
    if path.suffix.lower() not in (".png", ".jpg", ".jpeg"):
        raise ValueError("Only static PNG/JPEG images are supported; video is unsupported.")
    if path.stat().st_size > 5_000_000:
        raise ValueError("Image exceeds the 5 MB supported size.")
    raw = path.read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    if expected_hash is not None and sha != expected_hash:
        raise ValueError("Image changed after its approved snapshot or preview.")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(BytesIO(raw)) as original:
                if original.format not in ("PNG", "JPEG") or getattr(original, "n_frames", 1) != 1:
                    raise ValueError("Only static PNG/JPEG images are supported.")
                if original.width * original.height > 16_000_000:
                    raise ValueError("Image exceeds the supported pixel limit.")
                original.load()
                # Browsers honour JPEG EXIF rotation/mirroring. Sampling and
                # region dimensions must use that same displayed coordinate grid.
                # Original bytes and their consent/reference hashes stay unchanged.
                image = ImageOps.exif_transpose(original).convert("RGBA")
                mime = "image/png" if original.format == "PNG" else "image/jpeg"
    except (
        OSError,
        UnidentifiedImageError,
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
    ):
        raise ValueError("Image could not be safely decoded.") from None
    return (
        {"sha256": sha, "width": image.width, "height": image.height, "mime_type": mime},
        image,
        raw,
    )


def _reference(ref):
    if not all(
        ref.get(key)
        for key in (
            "id",
            "label",
            "private_path",
            "sha256",
            "source_document_id",
            "source_location",
        )
    ):
        raise ValueError("Approved visual reference lacks immutable source evidence.")
    if not (ref.get("source_excerpt") or ref.get("value")):
        raise ValueError("Approved visual reference lacks its source description.")
    meta, image, raw = _image(ref["private_path"], ref["sha256"])
    safe = {
        "id": str(ref["id"]),
        "label": ref["label"],
        **meta,
        "source_document_id": str(ref["source_document_id"]),
        "source_location": ref["source_location"],
        "source_excerpt": ref.get("source_excerpt") or ref["value"],
    }
    return safe, image, raw


def visual_manifest(candidate_version, snapshot_rules, references):
    """Safe preview identity; no private paths, credentials or raw image bytes.

    candidate_version requires private_path (or original_path/file_ref), with
    optional id and sha256/artifact_sha256. References have the _reference shape.
    The caller provides authenticated download URLs separately.
    """
    candidate, _, _ = _image(
        candidate_version.get("private_path")
        or candidate_version.get("original_path")
        or candidate_version.get("file_ref"),
        candidate_version.get("artifact_sha256") or candidate_version.get("sha256"),
    )
    return {
        "candidate": {"id": str(candidate_version.get("id", "candidate")), **candidate},
        "references": [_reference(ref)[0] for ref in references],
        "rule_ids": sorted(str(rule["id"]) for rule in snapshot_rules),
        "disclosure": "Original candidate and listed reference images are sent unredacted only after explicit preview and consent. Image text is not protected by text redaction.",
    }


def _coverage(check, status, reason, **extra):
    return {"check": check, "status": status, "reason": reason, **extra}


def _finding(reason, sources, origin, region=None):
    return {
        "id": str(uuid4()),
        "category": "visual",
        "severity": "medium",
        "status": "advisory",
        "quote": "Image appearance",
        "start": 0,
        "end": 0,
        "reason": reason,
        "evidence": sources,
        "origin": origin,
        "dismissed": False,
        **({"region": region} if region else {}),
    }


def _rgb(code):
    code = code.lstrip("#")
    if len(code) == 3:
        code = "".join(char * 2 for char in code)
    return tuple(int(code[index : index + 2], 16) for index in (0, 2, 4))


def _palette(image, rules):
    supported = []
    colours = set()
    for rule in rules:
        if not rule.get("source_document_id") or not rule.get("source_excerpt"):
            continue
        # A model-proposed value is never authority for a hex absent in its
        # literal approved source excerpt.
        values = {_rgb(code) for code in HEX.findall(rule.get("value", ""))}
        literal = {_rgb(code) for code in HEX.findall(rule["source_excerpt"])}
        if values and values <= literal:
            colours.update(values)
            supported.append(rule)
    if not supported:
        return [], None
    sample = image.copy()
    sample.thumbnail((128, 128), Image.Resampling.LANCZOS)
    opaque = [pixel[:3] for pixel in sample.get_flattened_data() if pixel[3] >= 230]
    if not opaque:
        return [], _coverage(
            "colours_fonts",
            "unavailable",
            "No opaque pixels for a deterministic dominant palette check. Fonts were not checked.",
        )
    counts = Counter(tuple(round(component / 16) * 16 for component in pixel) for pixel in opaque)
    mismatches = []
    for rgb, count in counts.most_common(8):
        # Ignore low-area details, neutral backgrounds and antialiasing. This
        # describes a palette observation, not a logo/whole-image compliance test.
        if count / len(opaque) < 0.1 or max(rgb) - min(rgb) < 24:
            continue
        if all(
            sum((left - right) ** 2 for left, right in zip(rgb, approved)) > 48**2
            for approved in colours
        ):
            mismatches.append("#" + "".join(f"{min(component, 255):02x}" for component in rgb))
    findings = []
    if mismatches:
        findings.append(
            _finding(
                "Dominant non-neutral sampled colours "
                + ", ".join(mismatches)
                + " differ from the approved source palette. Photographs/backgrounds may legitimately differ; a human must interpret this observation.",
                [evidence(rule) for rule in supported],
                "deterministic",
            )
        )
    return findings, _coverage(
        "colours_fonts",
        "issues_found" if findings else "checked",
        "Deterministic dominant palette only: opaque pixels sampled to 128px, colours covering at least 10%, neutral backgrounds excluded, RGB tolerance 48. Exact fonts, logo identity and full brand compliance were not checked.",
        scope="dominant_palette_only",
    )


def evaluate_visual(
    candidate_path: Path,
    rules: list,
    references: list,
    requested_checks: list[str],
    usage_callback=None,
) -> dict:
    """Evaluate only. Caller already verified tenant, snapshot, preview and consent."""
    checks = list(dict.fromkeys(check for check in requested_checks if check in VISUAL_CHECKS))
    result = {"findings": [], "check_coverage": [], "mode": "local"}
    try:
        candidate, image, raw = _image(candidate_path)
    except (ValueError, TypeError):
        status = (
            "unsupported"
            if Path(candidate_path).suffix.lower() not in (".png", ".jpg", ".jpeg")
            else "unavailable"
        )
        result["check_coverage"] = [
            _coverage(
                check,
                status,
                "Candidate image is unavailable or unsupported; only private static PNG/JPEG images can be evaluated.",
            )
            for check in checks
        ]
        return result
    if not checks:
        return result
    reference_error = None
    try:
        if len(references) > 4:
            raise ValueError(
                "At most four approved image references can be compared in one bounded review."
            )
        resolved = [_reference(ref) for ref in references]
        if len({ref[0]["id"] for ref in resolved}) != len(resolved):
            raise ValueError("Duplicate visual reference identity.")
    except (ValueError, TypeError):
        resolved = []
        reference_error = (
            "At most four approved image references can be compared in one review. This collection exceeds the limit; visual comparison was not performed."
            if len(references) > 4
            else "Approved visual reference failed private-path, hash or source validation. No visual pass was recorded."
        )
    pending = []
    coverage = {}
    palette_row = None
    if "colours_fonts" in checks:
        findings, row = _palette(image, rules)
        result["findings"].extend(findings)
        palette_row = row
        font_guidance = any(
            "font" in (str(r.get("rule_key", "")) + " " + str(r.get("value", ""))).lower()
            for r in rules
        )
        if row:
            coverage["colours_fonts"] = row
        if font_guidance:
            pending.append("colours_fonts")
        elif not row:
            coverage["colours_fonts"] = _coverage(
                "colours_fonts",
                "source_missing",
                "No approved literal palette or font guidance was supplied.",
            )
    if "logos" in checks:
        pending.append("logos")
    if "accessibility" in checks:
        access_rules = [
            r
            for r in rules
            if "accessib" in str(r.get("rule_key", "")).lower()
            or "contrast" in str(r.get("value", "")).lower()
        ]
        coverage["accessibility"] = _coverage(
            "accessibility",
            "unsupported" if access_rules else "source_missing",
            "Pixel-only accessibility certification and reliable text/background contrast are unsupported; use text accessibility checks and human review."
            if access_rules
            else "No approved accessibility guidance was supplied.",
        )
    if pending and not resolved:
        for check in pending:
            coverage[check] = _coverage(
                check,
                "unavailable" if reference_error else "source_missing",
                reference_error
                or "No approved image reference was supplied for this visual comparison.",
            )
            if check == "colours_fonts" and palette_row:
                coverage[check]["local_palette"] = palette_row
        pending = []
    if pending:
        safe_refs = [ref[0] for ref in resolved]
        source_map = {str(rule["id"]): evidence(rule) for rule in rules}
        for ref in safe_refs:
            backed_rule = source_map.get(ref["id"])
            if backed_rule and (
                backed_rule["source_document_id"] != ref["source_document_id"]
                or backed_rule["excerpt"] != ref["source_excerpt"]
            ):
                result["error"] = "Visual rule/reference identity collision."
                for check in pending:
                    coverage[check] = _coverage(check, "unavailable", result["error"])
                result["check_coverage"] = [coverage[check] for check in checks]
                return result
            source_map[ref["id"]] = {
                "id": ref["id"],
                "type": "visual_reference",
                "rule_key": ref["label"],
                "value": ref["source_excerpt"],
                "excerpt": ref["source_excerpt"],
                "location": ref["source_location"],
                "source_document_id": ref["source_document_id"],
                "sha256": ref["sha256"],
            }
        images = [
            "data:" + candidate["mime_type"] + ";base64," + base64.b64encode(raw).decode("ascii")
        ]
        images += [
            "data:" + ref[0]["mime_type"] + ";base64," + base64.b64encode(ref[2]).decode("ascii")
            for ref in resolved
        ]
        payload = {
            "candidate": candidate,
            "references": safe_refs,
            "rules": list(source_map.values()),
            "requested_checks": pending,
        }
        try:
            parsed, metadata = vision.evaluate(payload, images, usage_callback)
            proposals = parsed.model_dump()["findings"]
            if any(
                item["check"] not in pending
                or any(ref not in source_map for ref in item["evidence_ids"])
                for item in proposals
            ):
                raise ProviderUnavailable(
                    "Vision returned unknown check or evidence references. No visual pass was recorded."
                )
            for item in proposals:
                reason = item["reason"]
                if item["check"] == "colours_fonts":
                    reason = "A visual style difference may exist relative to the cited guidance. Pixels cannot confirm an exact font family; a human should compare the typography with the approved reference."
                issue = _finding(
                    reason, [source_map[ref] for ref in item["evidence_ids"]], "ai", item["region"]
                )
                issue["severity"] = item["severity"]
                issue["issue_type"] = item["issue_type"]
                if item["check"] == "accessibility":
                    issue["category"] = "accessibility"
                result["findings"].append(issue)
            result["metadata"] = metadata
            result["mode"] = "live"
            for check in pending:
                has_issues = any(p["check"] == check for p in proposals) or (
                    check == "colours_fonts"
                    and palette_row
                    and palette_row["status"] == "issues_found"
                )
                coverage[check] = _coverage(
                    check,
                    "issues_found" if has_issues else "checked",
                    "Real free vision compared candidate with approved reference images. Subjective advisory only; exact font identity and exhaustive visual compliance require human review.",
                    scope="advisory_reference_comparison",
                )
                if check == "colours_fonts" and palette_row:
                    coverage[check]["local_palette"] = palette_row
        except ProviderUnavailable as error:
            result["error"] = str(error)
            result["mode"] = "partial" if palette_row else "unavailable"
            for check in pending:
                coverage[check] = _coverage(check, "unavailable", str(error))
                if check == "colours_fonts" and palette_row:
                    coverage[check]["local_palette"] = palette_row
    result["check_coverage"] = [coverage[check] for check in checks]
    return result
