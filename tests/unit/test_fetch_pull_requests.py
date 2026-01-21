"""Unit Tests for Pull Request Fetcher."""

import logging
from types import SimpleNamespace
from typing import Any, NoReturn

import pytest
import requests

from clinical_tools.core.devtools.pr_fetcher import (
    fetch_pull_requests as fetch_pull_requests,
)


def test_fetch_repos_success_no_prs(
    monkeypatch: pytest.MonkeyPatch, caplog: Any
) -> None:
    """Test that correct calls is made for existing repo with no prs."""
    caplog.set_level(logging.INFO)
    # Response for the first call (Fetch Repos)
    repo_response = SimpleNamespace(
        status_code=200,
        json=lambda: {
            "values": [{"slug": "repo-a", "id": 100, "name": "R", "hierarchyId": 123}]
        },
    )

    # Response for the second call (Fetch PRs for repo-a)
    pr_response = SimpleNamespace(status_code=200, json=lambda: {"values": []})

    # Call tracker to manage multiple calls and count them
    responses = [repo_response, pr_response]
    calls = []

    def mock_get(url: str, **kwargs: Any) -> Any:
        calls.append(url)
        return responses.pop(0) if responses else repo_response

    # Apply the monkeypatch
    monkeypatch.setattr(
        "clinical_tools.core.devtools.pr_fetcher.requests.get", mock_get
    )

    # Call the function
    fetch_pull_requests(bitbucket_url="http://fake", project="P", repo="R", token="T")

    assert len(calls) == 2, f"Expected 2 calls, but got {len(calls)}: {calls}"
    assert "repo-a" in calls[1]
    assert "No pull requests found" in caplog.text


def test_fetch_prs_empty_args(caplog: Any) -> None:
    """Test 'INVALID URL' is printed when CLI args are missing."""
    caplog.set_level(logging.WARNING)
    fetch_pull_requests("", "", "", "")

    # Check if the expected "Invalid URL" message was printed
    assert "Invalid URL" in caplog.text


def test_fetch_prs_invalid_args(caplog: Any) -> None:
    """Test 'INVALID URL' is printed when CLI args are invalid."""
    caplog.set_level(logging.WARNING)
    fetch_pull_requests("123", "test", "test", "123")

    # Check if the expected "Invalid URL" message was printed
    assert "Invalid URL" in caplog.text


def test_fetch_repos_success_with_prs(
    monkeypatch: pytest.MonkeyPatch, caplog: Any
) -> None:
    """Test that correct calls is made for repo with prs."""
    caplog.set_level(logging.INFO)
    # Response for the first call (Fetch Repos)
    repo_response = SimpleNamespace(
        status_code=200,
        json=lambda: {
            "values": [
                {"slug": "repo-a", "id": 100, "name": "My_Repo", "hierarchyId": 123}
            ]
        },
    )

    # Response for the second call (Fetch PRs for repo-a)
    pr_response = SimpleNamespace(
        status_code=200,
        json=lambda: {
            "values": [
                {
                    "id": 72,
                    "title": "Valid PR",
                    "fromRef": {"repository": {"name": "My_Repo"}},
                },
            ]
        },
    )

    # Call tracker to manage multiple calls and count them
    responses = [repo_response, pr_response]
    calls = []

    def mock_get(url: str, **kwargs: Any) -> Any:
        calls.append(url)
        return responses.pop(0) if responses else repo_response

    # Apply the monkeypatch
    monkeypatch.setattr(
        "clinical_tools.core.devtools.pr_fetcher.requests.get", mock_get
    )

    fetch_pull_requests(
        bitbucket_url="http://fake", project="P", repo="My_Repo", token="T"
    )

    expected_link = "http://fake/projects/P/repos/My_Repo/pull-requests/72/overview"

    assert len(calls) == 2, f"Expected 2 calls, but got {len(calls)}: {calls}"
    assert "repo-a" in calls[1]
    assert "Valid PR" in caplog.text
    assert f"[My_Repo#72]({expected_link})" in caplog.text


def test_fetch_prs_request_exception(
    monkeypatch: pytest.MonkeyPatch, caplog: Any
) -> None:
    """Test request exception error handling when calling PR fetching function."""
    caplog.set_level(logging.WARNING)
    # Setup: Make the mock "throw" a ConnectionError

    def mock_get_exception(*args: Any, **kwargs: Any) -> NoReturn:
        """Mock function to raise a ConnectionError."""
        raise requests.exceptions.ConnectionError("Connection refused")

    monkeypatch.setattr(requests, "get", mock_get_exception)

    fetch_pull_requests(bitbucket_url="http://fake", project="P", repo="R", token="T")

    # Check if 'except' block caught it and printed the error
    assert (
        "Connection refused" in caplog.text
        and "An error occurred while fetching data" in caplog.text
    )


def test_fetch_prs_missing_fields(monkeypatch: pytest.MonkeyPatch, caplog: Any) -> None:
    """Test print behavior for multiple PR's containing valid/invalid fields."""
    caplog.set_level(logging.INFO)

    # Response for the first call (Fetch Repos)
    repo_response = SimpleNamespace(
        status_code=200,
        json=lambda: {
            "values": [
                {"slug": "my-repo", "id": 100, "name": "My_Repo", "hierarchyId": 123}
            ]
        },
    )

    # Response for the second call (Fetch PRs for repo-a)
    pr_response = SimpleNamespace(
        status_code=200,
        json=lambda: {
            "values": [
                {
                    "id": 72,
                    "title": "Valid PR",
                    "fromRef": {"repository": {"name": "My_Repo"}},
                },
                {
                    "title": "Broken PR"
                },  # Missing required fields such as id and fromRef
            ]
        },
    )

    # Call tracker to manage multiple calls and count them
    responses = [repo_response, pr_response]
    calls = []

    def mock_get(url: str, **kwargs: Any) -> Any:
        calls.append(url)
        return responses.pop(0) if responses else repo_response

    # Apply the monkeypatch
    monkeypatch.setattr(
        "clinical_tools.core.devtools.pr_fetcher.requests.get", mock_get
    )

    fetch_pull_requests(bitbucket_url="http://fake", project="P", repo="", token="T")

    expected_link = "http://fake/projects/P/repos/My_Repo/pull-requests/72/overview"

    assert "Valid PR" in caplog.text
    assert f"[My_Repo#72]({expected_link})" in caplog.text
    assert "my-repo" in calls[1]
    assert "Warning: PR Broken PR is missing fields." in caplog.text
