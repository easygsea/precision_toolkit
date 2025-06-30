#!/usr/bin/env bash

####      BAMBOO INTERFACE CONFIGURATION       ####
###    Hosts: gphost14                         ####
###    Authentication type:                    ####
###    Username: <YOUR_USERNAME>               ####
###################################################

set -euxo pipefail

export LD_LIBRARY_PATH="${LD_LIBRARY_PATH:-}:/projects/clingenetics/software/tools/python/Python-3.11.7/lib"

TESTING_DEPLOYMENT_DIRECTORY=$1
PYTHON_EXECUTABLE=$2

cd "${TESTING_DEPLOYMENT_DIRECTORY}"
# Ensures $@ is empty when calling source to avoid passing in unwanted parameters
shift $#

"${PYTHON_EXECUTABLE}" -m venv venv
source venv/bin/activate
pip install --upgrade pip wheel
pip install poetry==2.0.1

cd clinical_tools/
poetry install --with dev
