"""Fetch Daily Pull Requests."""

import logging

import requests  
from requests.exceptions import (  
    MissingSchema,
    RequestException,
)

logging.basicConfig(format="%(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)


def fetch_pull_requests(
    bit_bucket_url: str, project: str, repo: str, token: str
) -> None:
    """
    Fetch Pull Requests.

    Args:
        bit_bucket_url: URL for the BitBucket to fetch PR's from.
        project: Name of the project.
        repo: Name of the repository.
        token: Authorization bearer token to access the repository.
    """
    base_api_url = f"{bit_bucket_url}/rest/api/1.0/projects/{project}/repos"

    try:
        headers = {"Authorization": f"Bearer {token}"}
        repo_response = requests.get(base_api_url, headers=headers)

        if repo_response.status_code == 200:
            repositories = repo_response.json().get("values", [])
            print("reps: ", repositories)
            all_prs = []

            for repo_data in repositories:
                if not isinstance(repo_data, dict):
                    continue

                if repo and repo_data.get("name") != repo:
                    continue

                repo_slug = repo_data.get("slug")
                pr_url = f"{base_api_url}/{repo_slug}/pull-requests"

                pr_response = requests.get(pr_url, headers=headers)

                if pr_response.status_code == 200:
                    pull_requests = pr_response.json().get("values", [])
                    print("\n\npull reqs: ", pull_requests)

                    for pr in pull_requests:
                        repo_name_context = (
                            pr.get("fromRef", {}).get("repository", {}).get("name")
                        )

                        all_prs.append(
                            {
                                "pr_data": pr,
                                "repo_name": repo_name_context or repo_data.get("name"),
                            }
                        )
                else:
                    logging.warning(
                        f"Failed to fetch PRs for {repo_slug}:{pr_response.status_code}"
                    )

            if all_prs:
                for item in all_prs:
                    pr = item["pr_data"]
                    r_name = item["repo_name"]

                    pr_id = pr.get("id")
                    title = pr.get("title")

                    if pr_id is None or title is None:
                        logging.warning(
                            f"Warning: PR {title or 'Unknown'} is missing fields."
                        )
                        continue

                    pr_link = (
                        f"{bit_bucket_url}/projects/{project}/repos/{r_name}"
                        f"/pull-requests/{pr_id}/overview"
                    )
                    logging.info(title)
                    logging.info(f"[{r_name}#{pr_id}]({pr_link})\n")
            else:
                logging.info("No pull requests found.")
        else:
            logging.warning(
                f"Repo request failed with status code {repo_response.status_code}"
            )

    except MissingSchema as e:
        logging.error(f"Invalid URL: '{base_api_url}': {str(e)}")
    except RequestException as e:
        logging.error(f"An error occurred while fetching data: {str(e)}")
