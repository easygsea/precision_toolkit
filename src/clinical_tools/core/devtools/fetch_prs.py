import requests

BITBUCKET_URL = "<YOUR URL HERE>"
PROJECT = "<YOUR PROJECT HERE>"
REPO = "<YOUR REPO HERE>"
TOKEN = "<YOUR TOKEN HERE>"

headers = {"Authorization": f"Bearer {TOKEN}"}

url = f"{BITBUCKET_URL}/rest/api/1.0/projects/{PROJECT}/repos/"

r = requests.get(url, headers=headers)
data_repos = r.json()

for repo in data_repos['values']:
    url = f"{BITBUCKET_URL}/rest/api/1.0/projects/{PROJECT}/repos/{repo['slug']}/pull-requests"

    r = requests.get(url, headers=headers)
    data = r.json()

    for pr in data["values"]:
        pr_id = pr["id"]
        title = pr["title"]
        state = pr["state"]
        pr_link = f"{BITBUCKET_URL}/projects/{PROJECT}/repos/{repo['name']}/pull-requests/{pr_id}/overview"

        print(title)
        print(f"[{repo['name']}#{pr_id}]({pr_link})\n")