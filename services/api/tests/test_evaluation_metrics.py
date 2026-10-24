import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "evals"))
from metrics import match_findings, summarize


def test_one_prediction_cannot_match_two_labels():
    gold = {"category": "fact", "status": "confirmed_mismatch", "start": 2, "end": 8}
    assert match_findings([gold, gold], [gold]) == {"tp": 1, "fp": 0, "fn": 1}


def test_errors_and_not_run_remain_visible_in_metrics():
    result = summarize(
        [
            {"status": "passed", "counts": {"tp": 1, "fp": 0, "fn": 0}},
            {"status": "error", "counts": None},
            {"status": "not_run", "counts": None},
        ]
    )
    assert result["total_cases"] == 3 and result["errors"] == 1 and result["not_run"] == 1
    assert result["measured_cases"] == 1
