import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services/api"))
from agents.review_graph import SYSTEM
from app.review_models import ReviewResponse
from evaluators.evidence import verify_findings
from evaluators.facts import check_facts
from evaluators.rewrites import validate_candidate
from providers import openrouter
from retrieval.approved_sources import evidence
from metrics import match_findings, summarize

parser = argparse.ArgumentParser()
parser.add_argument("--mode", choices=["offline", "live"], default="offline")
parser.add_argument("--suite", choices=["smoke", "benchmark"], default="benchmark")
parser.add_argument("--max-requests", type=int, default=10)
parser.add_argument("--reserve-requests", type=int, default=10)
parser.add_argument("--resume", action="store_true")
args = parser.parse_args()
if not 0 <= args.max_requests <= 10 or args.reserve_requests < 10:
    parser.error("At most 10 requests and a reserve of at least 10 are required.")
cases = [
    json.loads(line)
    for line in (ROOT / "evals/fixtures/synthetic_brand_cases.jsonl")
    .read_text(encoding="utf-8")
    .splitlines()
]
if args.suite == "smoke":
    cases = [c for c in cases if c["id"] in ("FACT01", "CLAIM01", "CLEAN01")]
output = ROOT / f".local/test-results/evaluation-{args.mode}-{args.suite}.json"
output.parent.mkdir(parents=True, exist_ok=True)
old = (
    json.loads(output.read_text()).get("cases", [])
    if args.resume and output.exists()
    else []
)
results = []
attempts = 0
blocked = None
model = None
if args.mode == "live":
    try:
        model = openrouter.selected_model()["id"]
        os.environ["OPENROUTER_MODEL"] = model
    except openrouter.ProviderUnavailable:
        pass
for case in cases:
    fingerprint = hashlib.sha256(json.dumps(case, sort_keys=True).encode()).hexdigest()
    previous = next(
        (
            r
            for r in old
            if r["id"] == case["id"]
            and r.get("fingerprint") == fingerprint
            and r.get("requested_model") == model
            and r["status"] == "passed"
        ),
        None,
    )
    if previous:
        results.append({**previous, "reused": True})
        continue
    result = {
        "id": case["id"],
        "kind": case["kind"],
        "fingerprint": fingerprint,
        "requested_model": model,
        "status": "not_run",
        "counts": None,
        "negative_control": not case.get("expected_issues") and case["kind"] == "clean",
        "reused": False,
    }
    try:
        if args.mode == "live" and blocked:
            result["reason"] = blocked
        elif case["kind"] == "rewrite":
            actual = validate_candidate(case["text"], case["candidate"], case["rules"])
            result.update(
                status="passed"
                if actual["safe"] == case["expected_safe"]
                else "failed",
                assertion="Protected strings, unsupported numbers and risky new claims",
                actual=actual,
            )
        elif args.mode == "offline" and case.get("requires_live"):
            result["reason"] = (
                "Contextual AI evaluation requires a live provider. No mock accuracy is reported."
            )
        else:
            findings = check_facts(case["text"], case["rules"], as_of="2026-10-24")
            if args.mode == "live":
                if attempts >= args.max_requests:
                    result["reason"] = "Invocation request budget exhausted."
                    results.append(result)
                    continue
                quota = openrouter.key_quota()
                if (
                    quota.get("remaining") is not None
                    and quota["remaining"] <= args.reserve_requests
                ):
                    result["reason"] = "Demo quota reserve reached."
                    results.append(result)
                    continue
                attempts += 1
                proposed, metadata = openrouter.complete(
                    SYSTEM,
                    {
                        "content": case["text"],
                        "channel": "general",
                        "approved_sources": [evidence(r) for r in case["rules"]],
                    },
                    ReviewResponse,
                    "evaluation",
                )
                verified = verify_findings(
                    proposed.model_dump()["findings"], case["text"], case["rules"]
                )
                findings += verified
                result["metadata"] = metadata
                result["invalid_model_findings"] = len(proposed.findings) - len(
                    verified
                )
            result["actual_findings"] = findings
            if case.get("metric_excluded"):
                result.update(
                    status="passed"
                    if result.get("invalid_model_findings", 0) == 0
                    else "failed",
                    assertion="Schema and authorised evidence constraints; no tool or approval capability",
                )
            else:
                counts = match_findings(case["expected_issues"], findings)
                result.update(
                    counts=counts,
                    status="passed" if counts["fp"] == counts["fn"] == 0 else "failed",
                )
    except Exception as error:
        result.update(
            status="error",
            reason=str(error)
            if isinstance(error, openrouter.ProviderUnavailable)
            else type(error).__name__,
        )
        if isinstance(error, openrouter.ProviderUnavailable):
            blocked = "Live evaluation stopped after a provider/policy/quota failure. Retry deliberately with --resume."
    results.append(result)
    report = {
        "dataset": "50 developer-labelled synthetic cases; no real materials or independent human feedback",
        "mode": args.mode,
        "suite": args.suite,
        "attempts": attempts,
        "policy_version": openrouter.POLICY_VERSION,
        "prompt_version": "review-v1",
        "summary": summarize(results),
        "cases": results,
    }
    output.write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
report = {
    "dataset": "50 developer-labelled synthetic cases; no real materials or independent human feedback",
    "mode": args.mode,
    "suite": args.suite,
    "attempts": attempts,
    "policy_version": openrouter.POLICY_VERSION,
    "prompt_version": "review-v1",
    "summary": summarize(results),
    "cases": results,
}
output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
print(json.dumps(report["summary"], indent=2))
print(output)
raise SystemExit(1 if any(r["status"] in ("failed", "error") for r in results) else 0)
