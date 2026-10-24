from evaluators.evidence import verify_findings
from evaluators.facts import check_facts


def rule(kind, value, **extra):
    return {
        "id": "rule-1",
        "type": kind,
        "value": value,
        "rule_key": "synthetic",
        "scope_channel": "global",
        "source_excerpt": None,
        "source_location": None,
        **extra,
    }


def test_price_requires_entity_currency_date_and_unit():
    policy = [
        rule(
            "approved_fact",
            "Cloudberry costs INR 799 per 150ml",
            fact={
                "kind": "price",
                "entity": "Cloudberry",
                "amount": "799",
                "currency": "INR",
                "unit": "150ml",
                "effective_from": "2026-01-01",
            },
        )
    ]
    assert (
        check_facts("Cloudberry 150ml costs INR 499.", policy)[0]["status"] == "confirmed_mismatch"
    )
    assert check_facts("Cloudberry 150ml costs INR 799.", policy) == []
    assert check_facts("Other product 150ml costs INR 499.", policy) == []
    assert check_facts("Cloudberry 50ml costs INR 499.", policy) == []
    assert check_facts("Cloudberry 150ml costs USD 499.", policy) == []


def test_terms_disclaimers_and_clean_control():
    rules = [
        rule("prohibited_term", "miracle"),
        rule("required_disclaimer", "Results vary.", id="rule-2"),
    ]
    findings = check_facts("A miracle.", rules)
    assert len(findings) == 2
    assert all(x["evidence"] for x in findings)
    assert check_facts("Everyday care. Results vary.", rules) == []


def test_price_does_not_match_partial_entities_units_or_foreign_dollars():
    policy = [
        rule(
            "approved_fact",
            "Pro costs USD 10 per month",
            fact={
                "kind": "price",
                "entity": "Pro",
                "amount": "10",
                "currency": "USD",
                "unit": "month",
                "effective_from": "2026-01-01",
            },
        )
    ]
    for text in (
        "Professional services cost USD 500 per month.",
        "Pro costs USD 500 per monthly package.",
        "Pro costs CAD$500 per month.",
        "Pro costs A$500 per month.",
        "Pro costs CAD $500 per month.",
        "Pro is our software. Services cost USD 500 per month.",
    ):
        assert check_facts(text, policy) == [], text
    assert check_facts("Pro costs USD 500 per month.", policy)[0]["status"] == "confirmed_mismatch"


def test_fake_evidence_and_wrong_quote_rejected_and_claims_remain_unverified():
    rules = [rule("approved_fact", "Cloudberry is a cleanser.")]
    proposal = {
        "category": "claim",
        "severity": "high",
        "quote": "Cures acne",
        "reason": "Unsupported claim",
        "evidence_ids": ["fake"],
    }
    assert verify_findings([proposal], "Cures acne", rules) == []
    proposal["evidence_ids"] = ["rule-1"]
    found = verify_findings([proposal], "Cures acne", rules)
    assert found[0]["status"] == "unverified"
    assert found[0]["evidence"][0]["id"] == "rule-1"
    assert verify_findings([proposal], "Everyday care", rules) == []
