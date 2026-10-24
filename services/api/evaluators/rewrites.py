import re
from collections import Counter

PROTECTED = re.compile(
    r"https?://[^\s<>]+|\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b|(?<!\w)[#@][\w]+|\[PRIVATE_\d+\]"
)
NUMBERS = re.compile(r"\b\d+(?:\.\d+)?\b")


def validate_candidate(original, candidate, rules):
    reason = ""
    if Counter(PROTECTED.findall(original)) != Counter(PROTECTED.findall(candidate)):
        reason = "A protected link, email, mention, hashtag or private token changed."
    old_numbers = set(NUMBERS.findall(original))
    approved_numbers = set(NUMBERS.findall(" ".join(r["value"] for r in rules)))
    if set(NUMBERS.findall(candidate)) - old_numbers - approved_numbers:
        reason = "The correction introduces an unsupported number."
    risky = re.compile(r"(?i)\b(guaranteed|cure|cures|100%|risk.free|clinically proven)\b")
    approved = " ".join(r["value"] for r in rules).casefold()
    if any(
        m.group().casefold() not in original.casefold() and m.group().casefold() not in approved
        for m in risky.finditer(candidate)
    ):
        reason = "The correction introduces an unsupported promotional claim."
    for r in rules:
        if (
            r.get("type") == "required_disclaimer"
            and r["value"] in original
            and r["value"] not in candidate
        ):
            reason = "Required wording was removed."
    before = len(original.split())
    after = len(candidate.split())
    matches = before == after if before <= 30 else abs(after - before) <= max(1, before * 0.1)
    note = f"{before} → {after} words. " + (
        "Length target retained."
        if matches
        else "The length target could not be met; factual and safety constraints take priority."
    )
    return {"safe": not reason, "reason": reason, "length_note": note}
