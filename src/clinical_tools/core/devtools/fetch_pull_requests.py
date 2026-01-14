"""Fetch Daily Pull Requests."""

import logging

import requests  # type: ignore[import-untyped]
from requests.exceptions import (  # type: ignore[import-untyped]
    MissingSchema,
    RequestException,
)

logging.basicConfig(format="%(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)


def fetch_prs(bit_bucket_url: str, project: str, repo: str, token: str) -> None:
    """
    Fetch Pull Requests.

    Args:
        bit_bucket_url: URL for the BitBucket to fetch PR's from.
        project: Name of the project.
        repo: Name of the repository.
        token: Authorization bearer token to access the repository.
    """
    url = f"{bit_bucket_url}/rest/api/1.0/projects/{project}/repos/"

    try:
        headers = {"Authorization": f"Bearer {token}"}
        r = requests.get(url, headers=headers)

        if r.status_code == 200:
            data_repos = r.json()
            repositories = data_repos.get("values", [])

            if repositories:
                for repo in data_repos["values"]:
                    if isinstance(repo, dict):
                        url = (
                            f"{bit_bucket_url}/rest"
                            f"/api/1.0/projects/{project}"
                            f"/repos/{repo['slug']}/pull-requests"
                        )

                        r = requests.get(url, headers=headers)
                        data = r.json()

                        for pr in data["values"]:
                            pr_id = pr.get("id", "Unknown ID")
                            title = pr.get("title", "No Title Provided")

                            if "id" not in pr or "title" not in pr:
                                logging.warning(
                                    f"Warning: PR {title} with ID: {pr_id}"
                                    "is missing expected fields."
                                )
                            else:
                                pr_link = (
                                    f"{bit_bucket_url}/projects/"
                                    f"{project}/repos/{repo['name']}"
                                    f"/pull-requests/{pr_id}/overview"
                                )
                                logging.info(title)
                                logging.info(f"[{repo['name']}#{pr_id}]({pr_link})\n")
                    else:
                        logging.warning(f"Expected dict, got {type(repo)}")
            else:
                logging.info("No pull requests found")
        else:
            logging.warning(f"Request failed with status code {r.status_code}")
    except MissingSchema as e:
        logging.error(f"Invalid URL: '{url}': {str(e)}")
    except RequestException as e:
        logging.error(f"An error occurred while fetching data: {str(e)}")
