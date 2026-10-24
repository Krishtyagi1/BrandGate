from uuid import uuid4

from retrieval.approved_sources import evidence


def verify_findings(proposals, text, rules):
    allowed = {str(rule["id"]): rule for rule in rules}
    verified = []
    for item in proposals:
        quote = item["quote"]
        if quote not in text or text.count(quote) != 1:
            continue  # Ambiguous occurrences cannot be edited by a guessed anchor.
        ids = item["evidence_ids"]
        if any(ref not in allowed for ref in ids) or (not ids and item["category"] != "claim"):
            continue
        sources = [evidence(allowed[ref]) for ref in ids]
        start = text.index(quote)
        verified.append(
            {
                "id": str(uuid4()),
                "category": item["category"],
                "severity": item["severity"],
                "status": "advisory"
                if item["category"] in ("tone", "accessibility")
                else "unverified",
                "quote": quote,
                "start": start,
                "end": start + len(quote),
                "reason": item["reason"],
                "evidence": sources,
                "origin": "ai",
                "dismissed": False,
                "evidence_validation": "Reference and approved excerpt validated. Contextual support requires human judgement.",
            }
        )
    return verified
