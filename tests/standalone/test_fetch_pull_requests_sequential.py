"""Integration Tests for Pull Request Fetcher."""

import logging
from types import SimpleNamespace
from typing import Any

import pytest

from clinical_tools.core.devtools.pr_fetcher import (
    fetch_pull_requests as fetch_pull_requests,
)


def test_fetch_prs_sequential_auth_flow(
    monkeypatch: pytest.MonkeyPatch, caplog: Any
) -> None:
    """Test the PR fetch function for sequential requests."""
    caplog.set_level(logging.INFO)

    # Setup: First response is 401 (Fail), Second is 200 (Success)
    mock_fail = SimpleNamespace(status_code=401)
    mock_success = SimpleNamespace(status_code=200, json=lambda: {"values": []})

    responses = iter([mock_fail, mock_success])

    def mock_get(*args: Any, **kwargs: Any) -> Any:
        return next(responses)

    # Apply the monkeypatch
    monkeypatch.setattr(
        "clinical_tools.core.devtools.pr_fetcher.requests.get", mock_get
    )

    # First Call: Should print Unauthorized
    fetch_pull_requests(
        bitbucket_url="http://test", project="P", repo="R", token="BAD_TOKEN"
    )
    assert "401" in caplog.text or "Request failed with status code" in caplog.text

    caplog.clear()

    # Second Call: Should print No PRs found
    fetch_pull_requests(
        bitbucket_url="http://test", project="P", repo="R", token="GOOD_TOKEN"
    )
    assert "No pull requests found" in caplog.text
    assert "401" not in caplog.text  # Ensure the old error isn't lingering
