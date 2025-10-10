# Bitbucket to GitHub Synchronization

This documentation provides instructions to set up automatic synchronization from a Bitbucket repository to a GitHub repository using GitHub Actions.

## Overview

Synchronization methods supported:
- Scheduled sync: Runs on a schedule via GitHub Actions
- Manual sync: Triggered on demand from the GitHub Actions UI

> **Note:** This setup syncs the `main` branch and tags from Bitbucket to GitHub. It can be adapted as needed.

## Prerequisites

- You have Admin access on both Bitbucket and GitHub repositories.
- Bitbucket username and App Password with appropriate permissions.
- GitHub repository with Actions enabled.

## Setup Steps

### 1. Create Bitbucket App Password

1. In Bitbucket, navigate to Manage account → HTTP access tokens → Create token.
   - Token name: `GitHub Sync`
   - Project permissions: `Project read`
   - Repository permissions: `Repository read`
3. Copy the generated app password.

### 2. Configure GitHub Repository Secrets

In GitHub, go to your repo → Settings → Secrets and variables → Actions:

Define these secrets:

- `BITBUCKET_REPO_URL`
  The Bitbucket HTTPS URL, without username/password.
  Example:
  ```
  bitbucket.org/yourworkspace/yourrepo.git
  ```

- `BITBUCKET_USER`
  Your Bitbucket username.
  Example:
  ```
  your.bitbucket.user
  ```

- `BITBUCKET_TOKEN`
  The Bitbucket App Password created above.

> **Tip:** For even more secure setups, rotate your app password frequently.

### 3. Review and (Optionally) Edit the Workflow

The main workflow is in: `.github/workflows/sync-from-bitbucket.yml`.

**Key workflow logic:**
- Runs on a schedule
- Also runs on manual trigger (from Actions tab)
- Checks out the current GitHub branch
- Adds Bitbucket remote using the secrets (`BITBUCKET_USER` and `BITBUCKET_TOKEN`)
- Fetches Bitbucket `main` branch and tags
- Pushes updates and tags to GitHub, with force for safety

---

## Test Manual Sync

1. Go to GitHub → Actions → "Sync Bitbucket to GitHub"
2. Click "Run workflow"
3. Observe logs; you should see fetch and push operations.

---

See [GitHub Actions documentation](https://docs.github.com/en/actions) for more help.
