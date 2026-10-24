def match_findings(expected, actual):
    """One-to-one overlap matching; one prediction cannot satisfy two labels."""
    used = set()
    matched = 0
    for gold in expected:
        for index, predicted in enumerate(actual):
            if index in used:
                continue
            if (
                predicted["category"] != gold["category"]
                or predicted["status"] != gold["status"]
            ):
                continue
            if gold.get("rule_id") and gold["rule_id"] not in {
                r["id"] for r in predicted.get("evidence", [])
            }:
                continue
            overlap = max(
                0,
                min(gold["end"], predicted["end"])
                - max(gold["start"], predicted["start"]),
            )
            if (
                overlap
                / max(
                    1,
                    min(
                        gold["end"] - gold["start"],
                        predicted["end"] - predicted["start"],
                    ),
                )
                < 0.5
            ):
                continue
            used.add(index)
            matched += 1
            break
    return {"tp": matched, "fp": len(actual) - matched, "fn": len(expected) - matched}


def summarize(results):
    measured = [r for r in results if r.get("counts") is not None]
    tp = sum(r["counts"]["tp"] for r in measured)
    fp = sum(r["counts"]["fp"] for r in measured)
    fn = sum(r["counts"]["fn"] for r in measured)
    negatives = [r for r in measured if r.get("negative_control")]
    return {
        "total_cases": len(results),
        "passed": sum(r["status"] == "passed" for r in results),
        "failed": sum(r["status"] == "failed" for r in results),
        "measured_cases": len(measured),
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "issue_precision": tp / (tp + fp) if tp + fp else None,
        "issue_recall": tp / (tp + fn) if tp + fn else None,
        "negative_control_cases": len(negatives),
        "negative_cases_with_false_positive": sum(
            r["counts"]["fp"] > 0 for r in negatives
        ),
        "not_run": sum(r["status"] == "not_run" for r in results),
        "errors": sum(r["status"] == "error" for r in results),
        "scope": "Metrics cover executed labelled cases only; not overall model accuracy.",
    }
