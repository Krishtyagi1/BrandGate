from evaluators.rewrites import validate_candidate


def test_rewrites_protect_links_email_hashtags_and_tokens():
    original = "Visit https://example.com @northstar #Care [PRIVATE_1]"
    assert validate_candidate(
        original, "Explore https://example.com @northstar #Care [PRIVATE_1]", []
    )["safe"]
    assert not validate_candidate(
        original, "Explore https://evil.com @northstar #Care [PRIVATE_1]", []
    )["safe"]
    assert not validate_candidate(
        original, "Visit https://example.com @northstar #Other [PRIVATE_1]", []
    )["safe"]
    assert not validate_candidate(
        original, "Visit https://example.com @northstar #Care [PRIVATE_2]", []
    )["safe"]


def test_new_numbers_and_claims_require_support():
    assert not validate_candidate("Everyday care.", "Everyday care for 100 days.", [])["safe"]
    assert validate_candidate(
        "Price INR 499.", "Price INR 799.", [{"value": "Approved price INR 799"}]
    )["safe"]
    assert not validate_candidate("Gentle care.", "Guaranteed to cure acne.", [])["safe"]


def test_candidate_length_reports_constraint_without_sacrificing_correctness():
    result = validate_candidate("Care today.", "Gentle everyday care. Results vary.", [])
    assert result["safe"] and "could not" in result["length_note"]
