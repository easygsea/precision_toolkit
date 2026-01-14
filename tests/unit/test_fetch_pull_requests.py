"""Unit Tests for Pull Request Fetcher."""

import logging
from typing import Any
from unittest.mock import MagicMock, patch

import requests  # type: ignore[import-untyped]

from clinical_tools.core.devtools.fetch_pull_requests import (  # type: ignore[import-not-found] # noqa: E501
    fetch_prs as fetch_prs,
)


@patch("clinical_tools.core.devtools.fetch_pull_requests.requests.get")
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


def test_fetch_prs_empty_args(caplog: Any) -> None:
    """Test 'INVALID URL' is printed when CLI args are missing."""
    caplog.set_level(logging.WARNING)
    fetch_prs("", "", "", "")

    # Check if the expected "Invalid URL" message was printed
    assert "Invalid URL" in caplog.text


def test_fetch_prs_invalid_args(caplog: Any) -> None:
    """Test 'INVALID URL' is printed when CLI args are invalid."""
    caplog.set_level(logging.WARNING)
    fetch_prs("123", "test", "test", "123")

    # Check if the expected "Invalid URL" message was printed
    assert "Invalid URL" in caplog.text


@patch("clinical_tools.core.devtools.fetch_pull_requests.requests.get")
def test_fetch_prs_none_found(mock_get: MagicMock, caplog: Any) -> None:
    """Test valid url but no pull requests returned."""
    caplog.set_level(logging.INFO)
    # Setup the Mock for a successful connection but empty data
    mock_response = MagicMock()
    mock_response.status_code = 200
    # Simulating the structure of a standard API response with no items
    mock_response.json.return_value = {"values": []}
    mock_get.return_value = mock_response

    # Call the function with a "valid" looking URL
    fetch_prs(bit_bucket_url="http://fake", project="P", repo="R", token="T")

    assert "No pull requests found" in caplog.text


@patch("clinical_tools.core.devtools.fetch_pull_requests.requests.get")
def test_fetch_prs_request_exception(mock_get: MagicMock, caplog: Any) -> None:
    """Test request exception error handling when calling PR fetching function."""
    caplog.set_level(logging.WARNING)
    # Setup: Make the mock "throw" a ConnectionError
    mock_get.side_effect = requests.exceptions.ConnectionError("Connection refused")

    fetch_prs(bit_bucket_url="http://fake", project="P", repo="R", token="T")

    # Check if 'except' block caught it and printed the error
    assert "An error occurred while fetching data" in caplog.text
    assert "Connection refused" in caplog.text


@patch("clinical_tools.core.devtools.fetch_pull_requests.requests.get")
def test_fetch_prs_missing_fields(mock_get: MagicMock, caplog: Any) -> None:
    """Test print behavior for multiple PR's containing valid/invalid fields."""
    caplog.set_level(logging.INFO)
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

    # Check that it processed the valid one
    assert "Valid PR" in caplog.text
    # Check that it handled the missing field gracefully
    assert "Warning" in caplog.text and "missing expected fields" in caplog.text
