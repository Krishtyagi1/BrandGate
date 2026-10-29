"""Measured deterministic pixel checks, explicitly separate from AI accuracy.

Run: PYTHONPATH=services/api .venv/bin/python -m evals.local_visual_run
"""

import hashlib
import json
from datetime import UTC, datetime

from app.config import LOCAL, ROOT
from app.visual_review import evaluate_visual
from app.visual_tools import sample_contrast
from PIL import Image

# Labels are literal, independently specified known colour-pair expectations.
# Borderline pairs exercise unrounded AA/large-text threshold decisions.
CONTRAST_CASES = [
    ("black-white", "#000000", "#ffffff", 21, True, True),
    ("white-white", "#ffffff", "#ffffff", 1, False, False),
    ("white-black", "#ffffff", "#000000", 21, True, True),
    ("near-aa-below", "#777777", "#ffffff", 4.48, False, True),
    ("near-aa-above", "#767676", "#ffffff", 4.54, True, True),
    ("low-grey", "#999999", "#ffffff", 2.85, False, False),
    ("near-large-above", "#949494", "#ffffff", 3.03, False, True),
    ("near-large-below", "#959595", "#ffffff", 3.00, False, False),
]
PALETTE_CASES = [
    ("match", "#0000ff", "checked"),
    ("mismatch", "#ff0000", "issues_found"),
    ("neutral", "#ffffff", "checked"),
    ("transparent", (0, 0, 255, 0), "unavailable"),
]


def run_cases(directory):
    directory.mkdir(parents=True, exist_ok=True)
    cases = []
    for name, fg, bg, ratio, normal, large in CONTRAST_CASES:
        image = Image.new("RGB", (40, 20), bg)
        image.paste(fg, (0, 0, 20, 20))
        path = directory / f"contrast-{name}.png"
        image.save(path)
        observed = sample_contrast(path, {"x": 0.25, "y": 0.5}, {"x": 0.75, "y": 0.5})
        expected = {
            "approximate_ratio": ratio,
            "normal_text_threshold_met": normal,
            "large_text_threshold_met": large,
        }
        passed = (
            abs(observed["ratio"] - ratio) < 0.01
            and observed["normal_text_threshold_met"] == normal
            and observed["large_text_threshold_met"] == large
        )
        cases.append(
            {
                "case_id": f"contrast-{name}",
                "check": "sampled_contrast",
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "expected": expected,
                "observed": {
                    k: observed[k]
                    for k in (
                        "ratio",
                        "normal_text_threshold_met",
                        "large_text_threshold_met",
                    )
                },
                "passed": passed,
            }
        )
    rule = {
        "id": "synthetic-blue",
        "type": "approved_fact",
        "rule_key": "brand_palette",
        "value": "Use #0000ff",
        "source_document_id": "synthetic-palette-source",
        "source_excerpt": "Use #0000ff",
        "source_location": "Developer-authored fictional palette rule",
    }
    for name, colour, expected in PALETTE_CASES:
        path = directory / f"palette-{name}.png"
        Image.new("RGBA", (60, 40), colour).save(path)
        observed = evaluate_visual(path, [rule], [], ["colours_fonts"])
        status = observed["check_coverage"][0]["status"]
        cases.append(
            {
                "case_id": f"palette-{name}",
                "check": "dominant_palette",
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "expected": {"status": expected},
                "observed": {
                    "status": status,
                    "findings": len(observed["findings"]),
                    "mode": observed["mode"],
                },
                "passed": status == expected,
            }
        )
    passed = sum(c["passed"] for c in cases)
    return {
        "kind": "Deterministic pixel-check regression benchmark; not model accuracy or human agreement",
        "generated_at": datetime.now(UTC).isoformat(),
        "total": len(cases),
        "passed": passed,
        "failed": len(cases) - passed,
        "expected_rejections": 1,
        "cases": cases,
        "limits": [
            "Twelve simple synthetic pixel fixtures, manually specified expected labels.",
            "Contrast points are supplied; automatic text/background segmentation is not tested.",
            "Palette neutrality is an algorithm scope limitation, not proof of brand compliance.",
            "Transparent-palette rejection is one expected safety result, not a visual detection success.",
            "No model calls, real-person photos, customer assets or independent human labels.",
        ],
    }


def main():
    report = run_cases(LOCAL / "visual-local-eval")
    path = ROOT / "evals/reports/visual-localchecks.json"
    path.write_text(json.dumps(report, indent=2) + "\n")
    manifest = [
        {k: c[k] for k in ("case_id", "check", "sha256", "expected")}
        for c in report["cases"]
    ]
    (ROOT / "evals/fixtures/visual_local_cases.jsonl").write_text(
        "".join(json.dumps(c) + "\n" for c in manifest)
    )
    print(
        json.dumps(
            {
                "report": str(path),
                "total": report["total"],
                "passed": report["passed"],
                "failed": report["failed"],
                "kind": report["kind"],
            },
            indent=2,
        )
    )
    if report["failed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
