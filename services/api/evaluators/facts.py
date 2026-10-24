import re
from datetime import date
from decimal import Decimal, InvalidOperation
from uuid import uuid4

from retrieval.approved_sources import evidence


def finding(
    text, quote, start, rule, category, reason, severity="high", status="confirmed_mismatch"
):
    return {
        "id": str(uuid4()),
        "category": category,
        "severity": severity,
        "status": status,
        "quote": quote,
        "start": start,
        "end": start + len(quote),
        "reason": reason,
        "evidence": [evidence(rule)],
        "origin": "deterministic",
        "dismissed": False,
    }


def check_facts(text, rules, as_of=None):
    result = []
    today = as_of or date.today().isoformat()
    rules = applicable_rules(rules, today)
    by_key = {}
    for rule in rules:
        by_key.setdefault((rule["type"], rule["rule_key"]), []).append(rule)
    conflicts = {
        key
        for key, values in by_key.items()
        if len({v["value"].casefold() for v in values}) > 1
        and key[0] in ("approved_fact", "product_name")
    }
    for rule in rules:
        if (rule["type"], rule["rule_key"]) in conflicts:
            issue = finding(
                text,
                text[:100],
                0,
                rule,
                "fact",
                "Applicable approved rules conflict. The owner must clarify precedence.",
                status="conflicting_sources",
            )
            issue["evidence"] = [evidence(r) for r in by_key[(rule["type"], rule["rule_key"])]]
            if not any(
                x["status"] == "conflicting_sources" and x["evidence"] == issue["evidence"]
                for x in result
            ):
                result.append(issue)
            continue
        value = rule["value"]
        if rule["type"] == "prohibited_term":
            for match in re.finditer(
                r"(?<!\w)" + re.escape(value) + r"(?!\w)", text, re.IGNORECASE
            ):
                result.append(
                    finding(
                        text,
                        match.group(),
                        match.start(),
                        rule,
                        "terminology",
                        f"This term is prohibited by the approved rule: {value}",
                    )
                )
        elif rule["type"] == "required_disclaimer" and value not in text:
            result.append(
                finding(
                    text, text[:100], 0, rule, "messaging", f"Missing required wording: {value}"
                )
            )
        elif rule.get("fact") and rule["fact"].get("kind") == "price":
            fact = rule["fact"]
            if fact.get("effective_from", "9999") > today or (
                fact.get("effective_to") and fact["effective_to"] < today
            ):
                continue
            entity, unit, currency = (
                fact.get("entity", ""),
                fact.get("unit", ""),
                fact.get("currency", ""),
            )
            if not entity or not unit or currency not in ("INR", "USD", "EUR", "GBP"):
                continue
            aliases = {
                "INR": r"(?<![\w$])(?:INR\b|Rs\.?(?!\w)|₹)",
                "USD": r"(?<![\w$])(?:USD\b|\$)",
                "EUR": r"(?<![\w$])(?:EUR\b|€)",
                "GBP": r"(?<![\w$])(?:GBP\b|£)",
            }
            for line in re.finditer(r"[^\n]+", text):
                sentence = line.group()
                if currency == "USD" and re.search(
                    r"\b(?:CAD|AUD|NZD|HKD|SGD|CA|AU|NZ|HK|SG|C|A)\s*\$", sentence, re.IGNORECASE
                ):
                    continue

                def bounded(value):
                    return list(
                        re.finditer(
                            r"(?<!\w)" + re.escape(value) + r"(?!\w)", sentence, re.IGNORECASE
                        )
                    )

                if len(bounded(entity)) != 1 or (unit != "item" and len(bounded(unit)) != 1):
                    continue
                # Multiple products/prices or sentence-separated associations are uncertain.
                if any(
                    other.get("fact")
                    and other["fact"].get("entity") != entity
                    and bounded(other["fact"].get("entity", ""))
                    for other in rules
                ):
                    continue
                prices = list(
                    re.finditer(
                        aliases[currency] + r"\s*([0-9]+(?:\.[0-9]{1,2})?)(?![\d,]|\.\d)",
                        sentence,
                        re.IGNORECASE,
                    )
                )
                if len(prices) != 1:
                    continue  # Multiple prices/entities require human interpretation.
                match = prices[0]
                entity_match = bounded(entity)[0]
                between = sentence[
                    min(entity_match.end(), match.end()) : max(entity_match.start(), match.start())
                ]
                if re.search(r"[!?;]|(?<!\d)\.(?!\d)", between):
                    continue
                try:
                    different = Decimal(match.group(1)) != Decimal(str(fact["amount"]))
                except (InvalidOperation, KeyError):
                    continue
                if different:
                    result.append(
                        finding(
                            text,
                            match.group(),
                            line.start() + match.start(),
                            rule,
                            "fact",
                            f"Approved {entity} price for {unit}: {currency} {fact['amount']} (effective {fact['effective_from']}).",
                        )
                    )
    # A lexical risk flag requests evidence; it never declares the claim false.
    risky = re.compile(
        r"[^.!?\n]*(?:\bguarantee\w*|\bcures?\b|\bclinically proven\b|\brisk.free\b)[^.!?\n]*[.!?]?",
        re.IGNORECASE,
    )
    for match in risky.finditer(text):
        quote = match.group().strip()
        if not quote or any(
            quote.casefold() in r["value"].casefold() for r in rules if r["type"] == "approved_fact"
        ):
            continue
        start = match.start() + len(match.group()) - len(match.group().lstrip())
        result.append(
            {
                "id": str(uuid4()),
                "category": "claim",
                "severity": "high",
                "status": "unverified",
                "quote": quote,
                "start": start,
                "end": start + len(quote),
                "reason": "This promotional promise needs supporting evidence. No exact owner-approved claim wording was found; a human must verify it.",
                "evidence": [],
                "origin": "deterministic",
                "dismissed": False,
            }
        )
    return result


def applicable_rules(rules, today=None):
    today = today or date.today().isoformat()
    return [
        r
        for r in rules
        if not r.get("fact")
        or r["fact"].get("kind") != "price"
        or (
            r["fact"].get("effective_from", "9999") <= today
            and (not r["fact"].get("effective_to") or r["fact"]["effective_to"] >= today)
        )
    ]
