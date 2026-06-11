#!/usr/bin/env python3
"""
Standalone PR fetching utility script for command line usage.

Usage:
    fetch-pull-requests --bitbucket_url <URL_TO_BITBUCKET>
    --project <PROJECT_NAME> [--repo <REPO_NAME>] --token <TOKEN>

Arguments:
    bitbucket_url: URL for the BitBucket to fetch PR's from.
    project: Name of the project.
    repo: Name of the repository.
    token: Authorization bearer token to access the repository.

Example:
    fetch-pull-requests --bitbucket_url "https://svn.test.ca/bitbucket"
    --project "projects" --repo "project1" --token "${TOKEN}"
"""

import argparse

from precision_toolkit.core.devtools.pull_request_fetcher import fetch_pull_requests


def main() -> None:
    """Fetch Pull Requests."""
    parser = argparse.ArgumentParser(
        description="Fetch today's pull requests.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--bitbucket_url",
        type=str,
        required=True,
        help="URL for the BitBucket to fetch PR's from.",
    )
    parser.add_argument(
        "--project",
        type=str,
        required=True,
        help="Name of the project.",
    )
    parser.add_argument(
        "--repo",
        type=str,
        help="Optional name of the repository.",
    )
    parser.add_argument(
        "--token",
        type=str,
        required=True,
        help="Authorization bearer token to access the repository.",
    )

    args = parser.parse_args()

    fetch_pull_requests(args.bitbucket_url, args.project, args.repo, args.token)


if __name__ == "__main__":
    main()
