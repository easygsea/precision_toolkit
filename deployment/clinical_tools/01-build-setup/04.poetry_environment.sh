#!/usr/bin/env bash

########## BAMBOO INTERFACE CONFIGURATION ############
####       Hosts: gphost14                        ####
######################################################

set -euxo pipefail

TESTING_DEPLOYMENT_DIRECTORY=$1
PYTHON_EXECUTABLE=$2

cd "${TESTING_DEPLOYMENT_DIRECTORY}"
# Ensures $@ is empty when calling source to avoid passing in unwanted parameters
shift $#

# Activates the virtual environment and installs the packages from the lock file
"${PYTHON_EXECUTABLE}" -m venv venv
source venv/bin/activate
pip install --upgrade pip wheel
pip install poetry==2.0.1

cd clinical_tools/
poetry install --with dev
