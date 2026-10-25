#!/usr/bin/env bash
set -euo pipefail

if uv audit; then
  exit 0
fi

echo ">> Vulnerabilities found, upgrading uv.lock..."
uv lock --upgrade || {
  echo ">> uv lock --upgrade failed"
  exit 1
}

if uv audit; then
  echo ">> uv.lock upgraded and audit is clean."
  echo ">> Review the diff, run your tests, then: git add uv.lock && commit again."
else
  echo ">> Still vulnerable after upgrading. Either no fix exists yet, or the fix"
  echo ">> is newer than exclude-newer days. Exempt it with exclude-newer-package."
fi
exit 1
