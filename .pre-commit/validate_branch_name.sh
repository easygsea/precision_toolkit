#!/usr/bin/env bash
set -euo pipefail

readonly TICKET='CDI-[0-9]+'
readonly VERSION='v(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)'
readonly DESCRIPTION='[A-Za-z0-9]+([_-][A-Za-z0-9]+)*'

PATTERN="^((improvement|bugfix|feature)/${TICKET}\.${DESCRIPTION}"
PATTERN+="|release/${VERSION}\.${TICKET}"
PATTERN+="|hotfix/${VERSION}\.${TICKET}\.${DESCRIPTION})$"
readonly PATTERN

branch="${BRANCH_NAME:-$(git rev-parse --abbrev-ref HEAD)}"

if [[ "${branch}" == 'HEAD' ]]; then
  exit 0
fi

if [[ "${branch}" =~ ${PATTERN} ]]; then
  exit 0
fi

echo "ERROR: Invalid branch name: '${branch}'" >&2
printf '%s\n' \
  'Expected one of these branch naming patterns:' \
  ' improvement/CDI-<ticket>.<description>' \
  ' bugfix/CDI-<ticket>.<description>' \
  ' feature/CDI-<ticket>.<description>' \
  ' release/v<major>.<minor>.<patch>.CDI-<ticket>' \
  ' hotfix/v<major>.<minor>.<patch>.CDI-<ticket>.<description>' \
  '' \
  'Descriptions must use lowercase letters, digits, underscores, or hyphens.' \
  'Example: feature/CDI-123.add_login_page' >&2
exit 1
