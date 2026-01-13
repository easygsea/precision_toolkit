"""Integration Tests for Pull Request Fetcher."""

from typing import Any
from unittest.mock import MagicMock, patch

from clinical_tools.core.devtools.fetch_prs import (  # type: ignore[import-not-found]
    fetch_prs,
)


@patch("clinical_tools.core.devtools.fetch_prs.requests.get")
def test_fetch_prs_sequential_auth_flow(mock_get: MagicMock, capsys: Any) -> None:
    """Test the PR fetch function for sequential requests."""
    # 1. Setup: First response is 401 (Fail), Second is 200 (Success)
    mock_fail = MagicMock()
    mock_fail.status_code = 401

    mock_success = MagicMock()
    mock_success.status_code = 200
    mock_success.json.return_value = {"values": []}

    mock_get.side_effect = [mock_fail, mock_success]

    # 2. First Call: Should print Unauthorized
    fetch_prs(bit_bucket_url="http://test", project="P", repo="R", token="BAD_TOKEN")
    out_1 = capsys.readouterr().out
    assert "401" in out_1 or "Unauthorized" in out_1

    # 3. Second Call: Should print No PRs found
    fetch_prs(bit_bucket_url="http://test", project="P", repo="R", token="GOOD_TOKEN")
    out_2 = capsys.readouterr().out
    assert "No pull requests found" in out_2
    assert "401" not in out_2  # Ensure the old error isn't lingering
