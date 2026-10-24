import pytest

from privacy.redaction import redact, restore
from providers.openrouter import ProviderUnavailable, validate_model


def test_free_price_and_schema_guards():
    free = {
        "id": "synthetic/model:free",
        "pricing": {"prompt": "0", "completion": "0"},
        "supported_parameters": ["response_format", "structured_outputs"],
    }
    assert validate_model(free)
    for invalid in (
        {**free, "id": "synthetic/paid"},
        {**free, "pricing": {"prompt": "0.001", "completion": "0"}},
        {**free, "supported_parameters": []},
        {**free, "pricing": {}},
    ):
        with pytest.raises(ProviderUnavailable):
            validate_model(invalid)


def test_redaction_stable_tokens_and_lossless_local_restore():
    original = "Email person@example.com, phone +91 98765 43210. Email person@example.com"
    payload, mapping = redact(original)
    assert "person@example.com" not in payload
    assert "98765" not in payload
    assert restore(payload, mapping) == original
    assert payload.count("[PRIVATE_1]") == 2
    with pytest.raises(ValueError):
        restore(payload + "[PRIVATE_999]", mapping)
