#!/usr/bin/env bash

: <<'BAMBOO_CONFIG_DOC'

Task type:
  SSH Task

Hosts:
  ${bamboo.HOST}

Authentication type:
  Username and password

Username:
  ${bamboo.USER}

Password:
  ${bamboo.PASSWORD}

BAMBOO_CONFIG_DOC

set -euxo pipefail

TESTING_DEVELOPMENT_DIRECTORY="$1"
PYTHON_LIB_DIR="$2"
IMAGE_NAME="$3"
IMAGE_STORE_ROOT="$4"

export LD_LIBRARY_PATH="${LD_LIBRARY_PATH:-}:${PYTHON_LIB_DIR}"

cd "${TESTING_DEVELOPMENT_DIRECTORY}"
source venv/bin/activate
cd clinical_tools

pre-commit run --all-files

VERSION=$(sed 's/^VERSION=//' clinical_tools_version.txt)
rsync -av "${IMAGE_NAME}" "${IMAGE_STORE_ROOT}/${VERSION}/"
