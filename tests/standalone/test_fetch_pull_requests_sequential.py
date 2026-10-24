"""Integration Tests for Pull Request Fetcher."""

import logging
from types import SimpleNamespace

import pytest

from precision_toolkit.core.devtools.pull_request_fetcher import (
    fetch_pull_requests,
)


def test_fetch_prs_sequential_auth_flow(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """Test pull request fetcher sequential authentication flow."""
    caplog.set_level(logging.INFO)

    mock_fail = SimpleNamespace(status_code=401)
    mock_success = SimpleNamespace(status_code=200, json=lambda: {"values": []})

    responses = iter([mock_fail, mock_success])

    def mock_get(*args: object, **kwargs: object) -> SimpleNamespace:
        return next(responses)

    monkeypatch.setattr(
        "precision_toolkit.core.devtools.pull_request_fetcher.requests.get", mock_get
    )

    fetch_pull_requests(
        bitbucket_url="http://test", project="P", repo="R", token="BAD_TOKEN"
    )
    assert "401" in caplog.text or "Request failed with status code" in caplog.text

    caplog.clear()

    fetch_pull_requests(
        bitbucket_url="http://test", project="P", repo="R", token="GOOD_TOKEN"
    )
    assert "No pull requests found" in caplog.text
    assert "401" not in caplog.text
