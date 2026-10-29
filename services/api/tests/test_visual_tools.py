from io import BytesIO

import pytest
from PIL import Image

from app.config import LOCAL


def test_sampled_contrast_known_ratios_and_transparency(tmp_path):
    from app.visual_tools import sample_contrast

    folder = LOCAL / "test-contrast"
    folder.mkdir(exist_ok=True)
    path = folder / "sample.png"
    image = Image.new("RGBA", (4, 2), "white")
    image.putpixel((0, 0), (0, 0, 0, 255))
    image.putpixel((1, 0), (0, 0, 0, 0))
    image.save(path)
    try:
        result = sample_contrast(path, {"x": 0, "y": 0}, {"x": 0.99, "y": 0.99})
        assert result["ratio"] == 21
        assert result["status"] == "advisory"
        assert result["foreground"] == "#000000"
        assert sample_contrast(path, {"x": 0.99, "y": 0.99}, {"x": 0.99, "y": 0.99})["ratio"] == 1
        with pytest.raises(ValueError, match="transparent"):
            sample_contrast(path, {"x": 0.25, "y": 0}, {"x": 0.99, "y": 0.99})
    finally:
        path.unlink()


def test_contrast_image_access_and_revision_pin(workspace, account):
    owner, org, _ = workspace
    image = BytesIO()
    Image.new("RGB", (10, 10), "white").save(image, format="PNG")
    base = f"/api/organisations/{org}"
    draft = owner.post(
        f"{base}/drafts/upload", files={"file": ("sample.png", image.getvalue(), "image/png")}
    ).json()
    body = {
        "version_id": draft["current_version_id"],
        "foreground": {"x": 0, "y": 0},
        "background": {"x": 0.9, "y": 0.9},
    }
    url = f"{base}/drafts/{draft['id']}/contrast"
    response = owner.post(url, json=body)
    assert response.status_code == 200, response.text
    assert response.json()["ratio"] == 1
    stranger, _, _ = account()
    assert stranger.post(url, json=body).status_code == 404
    from uuid import uuid4

    assert owner.post(url, json={**body, "version_id": str(uuid4())}).status_code == 409
    assert owner.post(url, json={**body, "foreground": {"x": 1, "y": 0}}).status_code == 422


def test_visual_reference_fallback_only_exposes_confirmed_images(workspace, account):
    owner, _, _ = workspace
    example = owner.post("/api/tutorial/example").json()
    base = f"/api/organisations/{example['org_id']}"
    url = f"{base}/drafts/{example['image_draft_id']}/visual-references"
    assert owner.get(url).json()["references"] == []
    knowledge = owner.get(f"{base}/knowledge").json()
    result = owner.post(
        f"{base}/knowledge/confirm",
        json={
            "version_id": example["version_id"],
            "expected_snapshot_id": None,
            "proposal_ids": [p["id"] for p in knowledge["proposals"]],
            "replace_rule_ids": {},
        },
    )
    assert result.status_code == 200, result.text
    refs = owner.get(url).json()
    assert refs["snapshot_id"]
    assert len(refs["references"]) == 1
    assert all("private_path" not in r and r["sha256"] for r in refs["references"])
    stranger, _, _ = account()
    assert stranger.get(url).status_code == 404


def test_visual_benchmark_metrics_exclude_unrun_cases():
    from evals.visual_metrics import agreement

    report = agreement(
        [
            {
                "case_id": "a",
                "expected": ["placement"],
                "observed": ["placement"],
                "status": "evaluated",
            },
            {"case_id": "b", "expected": [], "observed": ["distortion"], "status": "evaluated"},
            {
                "case_id": "c",
                "expected": ["suspected_old_logo"],
                "observed": [],
                "status": "unavailable",
            },
        ]
    )
    assert report["evaluated"] == 2 and report["unrun"] == 1
    assert report["case_agreement"] == 0.5 and report["precision"] == 0.5 and report["recall"] == 1
    assert (
        agreement([{"expected": ["placement"], "status": "unavailable"}])["case_agreement"] is None
    )


def test_sampled_contrast_matches_browser_exif_orientation():
    import hashlib

    from app.visual_review import visual_manifest
    from app.visual_tools import sample_contrast

    folder = LOCAL / "test-contrast-orientation"
    folder.mkdir(exist_ok=True)
    path = folder / "rotated.jpg"
    image = Image.new("RGB", (40, 20), "white")
    for x in range(20):
        for y in range(20):
            image.putpixel((x, y), (0, 0, 0))
    orientation = image.getexif()
    orientation[274] = 6
    image.save(path, quality=100, subsampling=0, exif=orientation)
    sha = hashlib.sha256(path.read_bytes()).hexdigest()
    try:
        result = sample_contrast(path, {"x": 0.5, "y": 0.1}, {"x": 0.5, "y": 0.9}, sha)
        assert result["ratio"] == pytest.approx(21, abs=0.01)
        assert result["image_sha256"] == sha
        manifest = visual_manifest({"private_path": str(path), "sha256": sha}, [], [])
        assert manifest["candidate"]["width"] == 20 and manifest["candidate"]["height"] == 40
    finally:
        path.unlink()
