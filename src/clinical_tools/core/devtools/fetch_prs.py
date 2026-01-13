"""Fetch Daily Pull Requests."""

import requests  # type: ignore[import-untyped]


def fetch_prs(bit_bucket_url: str, project: str, repo: str, token: str) -> None:
    """
    Fetch Pull Requests.

    Args:
        bit_bucket_url: URL for the BitBucket to fetch PR's from.
        project: Name of the project.
        repo: Name of the repository.
        token: Authorization bearer token to access the repository.
    """
    headers = {"Authorization": f"Bearer {token}"}

    url = f"{bit_bucket_url}/rest/api/1.0/projects/{project}/repos/"

    r = requests.get(url, headers=headers)
    data_repos = r.json()

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
                pr_id = pr["id"]
                title = pr["title"]
                pr_link = (
                    f"{bit_bucket_url}/projects/"
                    f"{project}/repos/{repo['name']})"
                    f"/pull-requests/{pr_id}/overview"
                )

                print(title)
                print(f"[{repo['name']}#{pr_id}]({pr_link})\n")
        else:
            print(f"Expected dict, got {type(repo)}")
