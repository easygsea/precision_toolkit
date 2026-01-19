#!/usr/bin/env python3
"""
Standalone PR fetching utility script for command line usage.

Usage:
    fetch-pull-requests [--bit_bucket_url <URL_TO_BIT_BUCKET>]
    [--project <PROJECT_NAME>] [--repo <REPO_NAME>] [--token <TOKEN>]

Arguments:
    bit_bucket_url: URL for the BitBucket to fetch PR's from.
    project: Name of the project.
    repo: Name of the repository.
    token: Authorization bearer token to access the repository.
"""

import argparse

from clinical_tools.core.devtools.fetch_pull_requests import fetch_pull_requests


def main() -> None:
    """
    Fetch Pull Requests.

    Args:
        bit_bucket_url: URL for the BitBucket to fetch PR's from.
        project: Name of the project.
        repo: Name of the repository.
        token: Authorization bearer token to access the repository.
    """
    parser = argparse.ArgumentParser(
        description="Fetch today's pull requests.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--bit_bucket_url",
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

    fetch_pull_requests(args.bit_bucket_url, args.project, args.repo, args.token)


if __name__ == "__main__":
    main()
