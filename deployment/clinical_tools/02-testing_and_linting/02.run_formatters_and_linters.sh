#!/usr/bin/env bash

set -euxo pipefail

TESTING_DEVELOPMENT_DIRECTORY=$1
PYTHON_LIB_DIR=$2

export LD_LIBRARY_PATH="${LD_LIBRARY_PATH:-}:${PYTHON_LIB_DIR}"

cd "${TESTING_DEVELOPMENT_DIRECTORY}"
source venv/bin/activate
cd clinical_tools

pre-commit run --all-files
