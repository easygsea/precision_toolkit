#!/usr/bin/env bash

: <<'BAMBOO_CONFIG_DOC'

Task type:
  SSH Task

Task description:
  Run pre commit

Hosts:
  ${bamboo.HOST}

Authentication type:
  Username and password

Username:
  ${bamboo.USER}

Password:
  ${bamboo.PASSWORD}

SSH command:
cd ${bamboo.inject.TESTING_DEPLOYMENT_DIRECTORY}/clinical_tools/deployment/bamboo/02-testing_and_linting/
bash 02.run_formatters_and_linters.sh \
${bamboo.inject.TESTING_DEPLOYMENT_DIRECTORY} \
${bamboo.inject.IMAGE_NAME} \
${bamboo.TEMPORARY_IMAGE_ROOT}

BAMBOO_CONFIG_DOC

set -euxo pipefail

TESTING_DEVELOPMENT_DIRECTORY="$1"
IMAGE_NAME="$2"
IMAGE_STORE_ROOT="$3"

cd "${TESTING_DEVELOPMENT_DIRECTORY}/clinical_tools"

uv run pre-commit run --all-files

VERSION=$(sed 's/^VERSION=//' clinical_tools_version.txt)
rsync -av "${IMAGE_NAME}" "${IMAGE_STORE_ROOT}/${VERSION}/"
