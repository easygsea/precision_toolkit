#!/usr/bin/env bash

set -euxo pipefail

TESTING_DEPLOYMENT_DIRECTORY=$1
PYTHON_EXECUTABLE=$2
PYTHON_LIB_DIR=$3

export LD_LIBRARY_PATH="${LD_LIBRARY_PATH:-}:${PYTHON_LIB_DIR}"

cd "${TESTING_DEPLOYMENT_DIRECTORY}"
# Ensures $@ is empty when calling source to avoid passing in unwanted parameters
shift $#

# Activates the virtual environment and installs the packages from the lock file
"${PYTHON_EXECUTABLE}" -m venv venv
chmod -R g+w venv/
source venv/bin/activate
pip install --upgrade pip wheel
pip install poetry==2.0.1

cd clinical_tools/
poetry install --with dev
