#!/usr/bin/env bash

: <<'BAMBOO_CONFIG_DOC'

Task type:
  SSH Task

Task description:
  Create Virtual Environment

Hosts:
  ${bamboo.HOST}

Authentication type:
  Username and password

Username:
  ${bamboo.USER}

Password:
  ${bamboo.PASSWORD}

SSH command:
cd ${bamboo.inject.TESTING_DEPLOYMENT_DIRECTORY}
cd clinical_tools/deployment/bamboo/01-build-setup/
bash 04.create_virtual_environment.sh \
${bamboo.inject.TESTING_DEPLOYMENT_DIRECTORY} \
${bamboo.PYTHON_EXECUTABLE}

BAMBOO_CONFIG_DOC

set -euxo pipefail

TESTING_DEPLOYMENT_DIRECTORY="$1"
PYTHON_EXECUTABLE="$2"

cd "${TESTING_DEPLOYMENT_DIRECTORY}/clinical_tools"
# Ensures $@ is empty when calling source to avoid passing in unwanted parameters
shift $#

# Install the package from the lock file
uv venv --python "${PYTHON_EXECUTABLE}"
chmod -R g+w .venv/
uv sync --group dev
uv run pre-commit install
