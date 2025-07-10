#!/usr/bin/env bash

set -euxo pipefail

TESTING_DEVELOPMENT_DIRECTORY=$1

cd "${TESTING_DEVELOPMENT_DIRECTORY}"
source venv/bin/activate
cd clinical_tools

pre-commit run --all-files
