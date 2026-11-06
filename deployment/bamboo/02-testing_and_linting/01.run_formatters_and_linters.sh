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
cd ${bamboo.inject.TESTING_DEPLOYMENT_DIRECTORY}/precision_toolkit/deployment/bamboo/02-testing_and_linting/
bash 01.run_formatters_and_linters.sh \
${bamboo.inject.TESTING_DEPLOYMENT_DIRECTORY} \
${bamboo.inject.IMAGE_NAME} \
${bamboo.TEMPORARY_IMAGE_ROOT} \
${bamboo.NEXTFLOW_EXECUTABLE} \
${bamboo.JAVA_EXECUTABLE}

BAMBOO_CONFIG_DOC

set -euxo pipefail

TESTING_DEPLOYMENT_DIRECTORY="$1"
IMAGE_NAME="$2"
IMAGE_STORE_ROOT="$3"
NEXTFLOW_EXECUTABLE="$4"
JAVA_EXECUTABLE="$5"

export PATH="$PATH:${NEXTFLOW_EXECUTABLE}"
export JAVA_HOME="${JAVA_EXECUTABLE}"
export PATH=$JAVA_HOME/bin:$PATH

cd "${TESTING_DEPLOYMENT_DIRECTORY}/precision_toolkit"

uv run pre-commit run --all-files

VERSION=$(sed 's/^VERSION=//' precision_toolkit_version.txt)
rsync -av "${IMAGE_NAME}" "${IMAGE_STORE_ROOT}/${VERSION}/"
