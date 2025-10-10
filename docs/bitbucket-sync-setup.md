# Bitbucket to GitHub Synchronization

This document explains how to set up automatic synchronization between your Bitbucket repository and GitHub repository.

## Overview

The synchronization system consists of:
- **Scheduled sync**: Runs every hour to check for changes
- **Webhook sync**: Triggers immediately when changes are pushed to Bitbucket
- **Manual sync**: Can be triggered manually from GitHub Actions

## Setup Instructions

### 1. Prerequisites

- GitHub CLI (`gh`) installed and authenticated
- Access to both Bitbucket and GitHub repositories
- Admin permissions on both repositories

### 2. Quick Setup

Run the setup script:
```bash
./scripts/setup-bitbucket-sync.sh
```

### 3. Manual Setup

#### Step 1: Configure GitHub Secrets

Go to your GitHub repository → Settings → Secrets and variables → Actions

Add these secrets:

**BITBUCKET_REPO_URL**
```
https://username:app_password@bitbucket.org/workspace/repository.git
```

Replace:
- `username`: Your Bitbucket username
- `app_password`: Bitbucket App Password (not your regular password)
- `workspace`: Your Bitbucket workspace/team name
- `repository`: Your repository name

**BITBUCKET_WEBHOOK_SECRET** (optional but recommended)
```
# Generate with: openssl rand -hex 32
your_random_secret_string
```

#### Step 2: Create Bitbucket App Password

1. Go to Bitbucket → Personal settings → App passwords
2. Create new app password with permissions:
   - Repositories: Read
   - Webhooks: Read and write
3. Copy the generated password

#### Step 3: Configure Bitbucket Webhook

1. Go to your Bitbucket repository → Repository settings → Webhooks
2. Add webhook with these settings:

**Basic Settings:**
- Title: `GitHub Sync`
- URL: `https://api.github.com/repos/YOUR_GITHUB_USERNAME/YOUR_REPO_NAME/dispatches`
- Events: `Repository push`, `Tag push`

**Advanced Settings:**
- Secret: Use the `BITBUCKET_WEBHOOK_SECRET` value
- Skip certificate verification: No

**Webhook Payload:**
```json
{
  "event_type": "bitbucket-push",
  "client_payload": {
    "ref": "${ref}",
    "tag": "${tag}"
  }
}
```

## How It Works

### Scheduled Sync (Every Hour)
- Runs automatically every hour
- Fetches all branches and tags from Bitbucket
- Compares with GitHub and syncs any differences
- Handles new branches, updated branches, and new tags

### Webhook Sync (Immediate)
- Triggers when you push to Bitbucket
- Immediately syncs the specific branch or tag that was pushed
- Faster than scheduled sync for immediate updates

### Manual Sync
- Can be triggered from GitHub Actions tab
- Useful for testing or forcing a sync
- Supports force sync option to sync even when no changes detected

## Workflow Files

### `.github/workflows/sync-from-bitbucket.yml`
- Main synchronization workflow
- Runs on schedule and manual trigger
- Syncs all branches and tags

### `.github/workflows/bitbucket-webhook-sync.yml`
- Webhook-triggered workflow
- Syncs specific branch/tag that triggered the webhook
- Faster response to changes

## Testing

### Test Manual Sync
1. Go to GitHub → Actions → "Sync from Bitbucket"
2. Click "Run workflow"
3. Check the logs for any errors

### Test Webhook Sync
1. Make a change in Bitbucket
2. Push the change
3. Check GitHub Actions for the webhook-triggered workflow
4. Verify the change appears in GitHub

### Test Branch Sync
1. Create a new branch in Bitbucket
2. Push some changes to that branch
3. Check if the branch appears in GitHub
4. Verify the changes are synced

### Test Tag Sync
1. Create a tag in Bitbucket
2. Push the tag
3. Check if the tag appears in GitHub

## Troubleshooting

### Common Issues

**Authentication Errors**
- Verify the `BITBUCKET_REPO_URL` secret is correct
- Check that the App Password has the right permissions
- Ensure the URL format includes username and password

**Webhook Not Triggering**
- Check the webhook URL is correct
- Verify the webhook secret matches
- Check Bitbucket webhook logs for errors

**Branches Not Syncing**
- Check if the branch exists on Bitbucket
- Verify the branch name doesn't contain special characters
- Check GitHub Actions logs for specific errors

**Tags Not Syncing**
- Ensure tags are pushed to Bitbucket (not just created locally)
- Check if tags already exist on GitHub
- Verify tag names don't conflict

### Debug Commands

Check current remotes:
```bash
git remote -v
```

Check branches:
```bash
git branch -a
```

Check tags:
```bash
git tag -l
```

Test Bitbucket access:
```bash
git ls-remote https://username:password@bitbucket.org/workspace/repo.git
```

## Security Considerations

- Use App Passwords instead of regular passwords
- Store secrets securely in GitHub Secrets
- Use webhook secrets to verify webhook authenticity
- Regularly rotate App Passwords
- Monitor webhook logs for suspicious activity

## Advanced Configuration

### Custom Sync Schedule
Edit `.github/workflows/sync-from-bitbucket.yml`:
```yaml
schedule:
  - cron: '0 */6 * * *'  # Every 6 hours
```

### Selective Branch Sync
Modify the workflow to only sync specific branches:
```yaml
# In the sync all branches step
if [[ "$branch" == "main" || "$branch" == "develop" ]]; then
  # Sync this branch
fi
```

### Custom Webhook Events
Add more webhook events in Bitbucket:
- Pull request events
- Issue events
- Custom events

## Support

If you encounter issues:
1. Check the GitHub Actions logs
2. Verify all secrets are correctly configured
3. Test with manual sync first
4. Check Bitbucket webhook logs
5. Review this documentation

For additional help, check the GitHub Actions documentation or Bitbucket webhook documentation.
