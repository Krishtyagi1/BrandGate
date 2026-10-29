"""Agreement on developer-labelled synthetic images; unavailable is never a pass."""


def agreement(cases):
    measured = [case for case in cases if case["status"] == "evaluated"]
    tp = fp = fn = exact = 0
    for case in measured:
        expected, observed = set(case["expected"]), set(case["observed"])
        tp += len(expected & observed)
        fp += len(observed - expected)
        fn += len(expected - observed)
        exact += expected == observed
    return {
        "total": len(cases),
        "evaluated": len(measured),
        "unrun": len(cases) - len(measured),
        "case_agreement": exact / len(measured) if measured else None,
        "precision": tp / (tp + fp) if tp + fp else None,
        "recall": tp / (tp + fn) if tp + fn else None,
        "true_positive_types": tp,
        "false_positive_types": fp,
        "missed_types": fn,
    }
