import pytest

from app.hosting import prepare_environment


def test_additional_hostname_allows_saves_without_accepting_other_origins(workspace, monkeypatch):
    owner, org, _ = workspace
    monkeypatch.setattr(
        "app.main.WEB_ORIGINS",
        frozenset(
            {
                "https://buildgate.velox0.com",
                "https://brandgate.velox0.com",
            }
        ),
        raising=False,
    )
    for origin in ("https://buildgate.velox0.com", "https://brandgate.velox0.com"):
        result = owner.post(
            f"/api/organisations/{org}/drafts",
            json={"text": "Synthetic alias check"},
            headers={"Origin": origin},
        )
        assert result.status_code == 201, result.text
    for origin in (
        "https://evil.example",
        "https://brandgate.velox0.com.evil.example",
        "http://brandgate.velox0.com",
        "null",
    ):
        assert (
            owner.post(
                f"/api/organisations/{org}/drafts",
                json={"text": "Rejected"},
                headers={"Origin": origin},
            ).status_code
            == 403
        )
    assert (
        owner.post(
            f"/api/organisations/{org}/drafts",
            json={"text": "Rejected"},
            headers={"Origin": "https://brandgate.velox0.com", "X-Inkloom-CSRF": ""},
        ).status_code
        == 403
    )


@pytest.mark.parametrize(
    "alias",
    [
        "*",
        "https://*.velox0.com",
        "http://brandgate.velox0.com",
        "https://brandgate.velox0.com/path",
        "https://user:password@brandgate.velox0.com",
        "https://brandgate.velox0.com?x=1",
        "https://brandgate.velox0.com#part",
        "https://brandgate.velox0.com:bad",
    ],
)
def test_hosted_rejects_unsafe_additional_origins(alias):
    from test_hosted_startup import hosted_env

    with pytest.raises(ValueError, match="origin"):
        prepare_environment(hosted_env(WEB_ADDITIONAL_ORIGINS=alias))


def test_exact_additional_origins_preserve_primary_and_deduplicate():
    from app.web_origins import allowed_web_origins

    assert allowed_web_origins(
        "https://buildgate.velox0.com",
        " https://brandgate.velox0.com,https://brandgate.velox0.com ",
    ) == frozenset({"https://buildgate.velox0.com", "https://brandgate.velox0.com"})
    assert allowed_web_origins("http://127.0.0.1:3000", "") == frozenset({"http://127.0.0.1:3000"})
