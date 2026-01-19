"""Integration Tests for Pull Request Fetcher."""

import logging
from typing import Any
from unittest.mock import MagicMock, patch

from clinical_tools.core.devtools.fetch_pull_requests import (  # noqa: E501
    fetch_pull_requests as fetch_pull_requests,
)


@patch("clinical_tools.core.devtools.fetch_pull_requests.requests.get")
def test_fetch_prs_sequential_auth_flow(mock_get: MagicMock, caplog: Any) -> None:
    """Test the PR fetch function for sequential requests."""
    caplog.set_level(logging.INFO)

    # 1. Setup: First response is 401 (Fail), Second is 200 (Success)
    mock_fail = MagicMock()
    mock_fail.status_code = 401

    mock_success = MagicMock()
    mock_success.status_code = 200
    mock_success.json.return_value = {"values": []}

    mock_get.side_effect = [mock_fail, mock_success]

    # 2. First Call: Should print Unauthorized
    fetch_pull_requests(
        bit_bucket_url="http://test", project="P", repo="R", token="BAD_TOKEN"
    )
    assert "401" in caplog.text or "Request failed with status code" in caplog.text

    caplog.clear()

    # 3. Second Call: Should print No PRs found
    fetch_pull_requests(
        bit_bucket_url="http://test", project="P", repo="R", token="GOOD_TOKEN"
    )
    assert "No pull requests found" in caplog.text
    assert "401" not in caplog.text  # Ensure the old error isn't lingering
