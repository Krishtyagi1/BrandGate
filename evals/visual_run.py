"""Generate fictional geometry-only fixtures; optionally probe strict free vision.

Run PYTHONPATH=services/api .venv/bin/python -m evals.visual_run [--live] [--limit 4].
No real persons, customer assets, paid routes or weaker privacy fallback.
"""

import argparse
import hashlib
import json
from datetime import UTC, datetime

from app.config import LOCAL, ROOT
from app.visual_review import evaluate_visual
from PIL import Image, ImageDraw
from providers.openrouter import ProviderUnavailable
from providers.vision import selected_vision_model

from .visual_metrics import agreement


def fixtures():
    directory = LOCAL / "visual-eval"
    directory.mkdir(exist_ok=True)
    logo = Image.new("RGB", (80, 60), "white")
    pen = ImageDraw.Draw(logo)
    pen.polygon([(8, 52), (40, 8), (72, 52)], fill="#164c91")
    pen.rectangle((32, 35, 48, 52), fill="white")
    reference = directory / "approved.png"
    logo.save(reference)
    description = "Approved fictional Northstar mark is a blue triangular arch, with original 4:3 bounding-box proportions. Place its top-left corner at (20,20) pixels. Do not stretch. The old blue circle mark is obsolete and prohibited. White background."
    ref = {
        "id": "approved-logo",
        "label": "Approved fictional Northstar mark",
        "private_path": str(reference),
        "sha256": hashlib.sha256(reference.read_bytes()).hexdigest(),
        "source_document_id": "synthetic-source",
        "source_location": "Synthetic logo sheet, image 1",
        "source_excerpt": description,
    }
    cases = []
    for format, size in [
        ("banner", (900, 300)),
        ("poster", (480, 640)),
        ("website", (960, 540)),
    ]:
        for variant, expected in [
            ("correct", []),
            ("old", ["suspected_old_logo"]),
            ("placement", ["placement"]),
            ("distortion", ["distortion"]),
        ]:
            image = Image.new("RGB", size, "white")
            mark = logo
            if variant == "old":
                mark = Image.new("RGB", (80, 60), "white")
                ImageDraw.Draw(mark).ellipse((18, 8, 62, 52), fill="#164c91")
            if variant == "distortion":
                mark = logo.resize((160, 60))
            position = (
                (size[0] - 100, size[1] - 80) if variant == "placement" else (20, 20)
            )
            image.paste(mark, position)
            ImageDraw.Draw(image).text(
                (24, 130),
                "Fictional Northstar / synthetic review fixture",
                fill="#162841",
            )
            path = directory / f"{format}-{variant}.png"
            image.save(path)
            cases.append(
                {
                    "case_id": f"{format}-{variant}",
                    "format": format,
                    "expected": expected,
                    "path": str(path),
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                    "label_basis": "Developer-labelled explicit geometry; no independent human study.",
                }
            )
    return ref, cases


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--limit", type=int, choices=range(1, 9), default=4)
    args = parser.parse_args()
    ref, cases = fixtures()
    model, reason = None, "Live inference was not requested."
    if args.live:
        try:
            model = selected_vision_model()["id"]
            reason = "Run limit reached; remaining cases unrun."
        except ProviderUnavailable as error:
            reason = str(error)
    outputs = []
    stop = model is None
    for index, case in enumerate(cases):
        item = {k: v for k, v in case.items() if k != "path"}
        item.update(
            status="unavailable" if stop else "unrun", observed=[], reason=reason
        )
        if not stop and index < args.limit:
            result = evaluate_visual(case["path"], [], [ref], ["logos"])
            if result["mode"] == "live":
                item.update(
                    status="evaluated",
                    observed=sorted(
                        {
                            f.get("issue_type", "reference_difference")
                            for f in result["findings"]
                        }
                    ),
                    metadata=result["metadata"],
                    reason=None,
                )
            else:
                stop = True
                reason = (
                    result.get("error")
                    or "Vision unavailable; manual comparison required."
                )
                item.update(status="unavailable", reason=reason)
        outputs.append(item)
    report = {
        "generated_at": datetime.now(UTC).isoformat(),
        "kind": "Synthetic developer-labelled vision benchmark; not an independent human agreement study",
        "live_requested": args.live,
        "model": model,
        "metrics": agreement(outputs),
        "cases": outputs,
        "limits": [
            "Twelve simple geometry fixtures; no natural backgrounds or real brand assets.",
            "Labels authored by the fixture developer, not independent raters.",
            "No accuracy estimate for unavailable or unrun cases.",
            "Fallback: inspect approved references side by side; separate reviewer records the final judgement.",
        ],
    }
    path = ROOT / "evals/reports/visual-round3.json"
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(report, indent=2) + "\n")
    # Versioned manifest contains no private machine paths or image payloads.
    (ROOT / "evals/fixtures/visual_cases.jsonl").write_text(
        "".join(
            json.dumps({k: v for k, v in case.items() if k != "path"}) + "\n"
            for case in cases
        )
    )
    print(
        json.dumps(
            {
                "report": str(path),
                "model": model,
                "reason": reason,
                "metrics": report["metrics"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
