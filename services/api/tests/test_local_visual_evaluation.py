import shutil
from uuid import uuid4

from app.config import LOCAL


def test_local_pixel_benchmark_checks_known_labels_and_transparent_rejection():
    from evals.local_visual_run import run_cases

    folder = LOCAL / "test-local-eval" / uuid4().hex
    try:
        report = run_cases(folder)
        assert report["total"] == 12 and report["passed"] == 12
        assert report["expected_rejections"] == 1
        assert (
            next(c for c in report["cases"] if c["case_id"] == "contrast-black-white")["observed"][
                "ratio"
            ]
            == 21
        )
        assert (
            next(c for c in report["cases"] if c["case_id"] == "contrast-near-aa-below")[
                "observed"
            ]["normal_text_threshold_met"]
            is False
        )
        assert (
            next(c for c in report["cases"] if c["case_id"] == "palette-mismatch")["observed"][
                "status"
            ]
            == "issues_found"
        )
    finally:
        if folder.exists():
            shutil.rmtree(folder)


def test_local_benchmark_reports_engine_errors_instead_of_passing(monkeypatch):
    from evals import local_visual_run

    def wrong(*args, **kwargs):
        return {"ratio": 21, "normal_text_threshold_met": True, "large_text_threshold_met": True}

    monkeypatch.setattr(local_visual_run, "sample_contrast", wrong)
    folder = LOCAL / "test-local-eval" / uuid4().hex
    try:
        report = local_visual_run.run_cases(folder)
        assert report["failed"] > 0
        assert (
            next(c for c in report["cases"] if c["case_id"] == "contrast-white-white")["passed"]
            is False
        )
    finally:
        if folder.exists():
            shutil.rmtree(folder)
