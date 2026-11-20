#!/bin/bash

set -euo pipefail

INPUT=$(cat)
if ! COMMAND=$(printf '%s' "$INPUT" | jq -er '
  if (.tool_input | type) == "object" then
    .tool_input.command
  elif (.toolArgs | type) == "string" then
    (.toolArgs | fromjson).command
  else
    error("missing shell command")
  end
'); then
  echo "BLOCKED: Copilot hook received an invalid shell-command payload." >&2
  exit 2
fi

DANGEROUS_PATTERNS=(
  "git push"
  "git reset --hard"
  "git clean -fd"
  "git clean -f"
  "git branch -D"
  "git checkout \."
  "git restore \."
)

for pattern in "${DANGEROUS_PATTERNS[@]}"; do
  if echo "$COMMAND" | grep -qE "$pattern"; then
    echo "BLOCKED: '$COMMAND' matches dangerous pattern '$pattern'. The user has prevented you from doing this." >&2
    exit 2
  fi
done

exit 0
