"""Unit Tests for Pull Request Fetcher."""

from typing import Any
from unittest.mock import MagicMock, patch

import requests  # type: ignore[import-untyped]

from clinical_tools.core.devtools.fetch_prs import (  # type: ignore[import-not-found]
    fetch_prs,
)


@patch("clinical_tools.core.devtools.fetch_prs.requests.get")
def test_fetch_prs_success(mock_get: MagicMock) -> None:
    """Test the mock function gets called."""
    # 1. Setup the Mock
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "values": [{"slug": "repo-a", "id": 100, "title": "Beta", "name": "Alpha"}]
    }
    mock_get.return_value = mock_response

    # 2. Call the function
    fetch_prs(bit_bucket_url="http://fake", project="P", repo="R", token="T")

    # 3. Assertions
    assert mock_get.called


def test_fetch_prs_empty_args(capsys: Any) -> None:
    """Test 'INVALID URL' is printed when CLI args are missing."""
    fetch_prs("", "", "", "")

    captured = capsys.readouterr()

    # Check if the expected "Invalid URL" message was printed
    assert "Invalid URL" in captured.out


def test_fetch_prs_invalid_args(capsys: Any) -> None:
    """Test 'INVALID URL' is printed when CLI args are invalid."""
    fetch_prs("123", "test", "test", "123")

    captured = capsys.readouterr()

    # Check if the expected "Invalid URL" message was printed
    assert "Invalid URL" in captured.out


@patch("clinical_tools.core.devtools.fetch_prs.requests.get")
def test_fetch_prs_none_found(mock_get: MagicMock, capsys: Any) -> None:
    """Test valid url but no pull requests returned."""
    # Setup the Mock for a successful connection but empty data
    mock_response = MagicMock()
    mock_response.status_code = 200
    # Simulating the structure of a standard API response with no items
    mock_response.json.return_value = {"values": []}
    mock_get.return_value = mock_response

    # Call the function with a "valid" looking URL
    fetch_prs(bit_bucket_url="http://fake", project="P", repo="R", token="T")

    captured = capsys.readouterr()

    assert "No pull requests found" in captured.out


@patch("clinical_tools.core.devtools.fetch_prs.requests.get")
def test_fetch_prs_request_exception(mock_get: MagicMock, capsys: Any) -> None:
    """Test request exception error handling when calling PR fetching function."""
    # Setup: Make the mock "throw" a ConnectionError
    mock_get.side_effect = requests.exceptions.ConnectionError("Connection refused")

    fetch_prs(bit_bucket_url="http://fake", project="P", repo="R", token="T")

    captured = capsys.readouterr()

    # Check if 'except' block caught it and printed the error
    assert "An error occurred while fetching data" in captured.out
    assert "Connection refused" in captured.out


@patch("clinical_tools.core.devtools.fetch_prs.requests.get")
def test_fetch_prs_missing_fields(mock_get: MagicMock, capsys: Any) -> None:
    """Test print behavior for multiple PR's containing valid/invalid fields."""
    # Setup Mock: One good PR, one broken PR
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "values": [
            {"slug": "repo-a", "id": 100, "title": "Valid PR", "name": "Alpha"},
            {"slug": "repo-a", "name": "Alpha"},
        ]
    }
    mock_get.return_value = mock_response

    fetch_prs(bit_bucket_url="http://fake", project="P", repo="R", token="T")

    captured = capsys.readouterr()

    # Check that it processed the valid one
    assert "Valid PR" in captured.out
    # Check that it handled the missing field gracefully
    assert "Warning" in captured.out and "missing expected fields" in captured.out
