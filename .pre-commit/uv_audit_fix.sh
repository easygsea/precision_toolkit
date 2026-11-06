#!/usr/bin/env bash
set -euo pipefail

if uv audit; then
  exit 0
else
  audit_status=$?
fi

if [[ $audit_status -eq 1 ]]; then
  echo ">> Vulnerabilities found. Update the affected package(s) manually, for example:"
  echo ">> uv lock --upgrade-package <package>"
  echo ">> Review uv.lock, run your tests, and rerun uv audit."
  exit 1
fi

exit "$audit_status"
