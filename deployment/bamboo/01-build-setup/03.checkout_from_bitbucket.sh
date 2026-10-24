#!/usr/bin/env bash

: <<'BAMBOO_CONFIG_DOC'

Task type:
  SSH Task

Task description:
  Checkout from BitBucket

Hosts:
  ${bamboo.HOST}

Authentication type:
  Username and password

Username:
  ${bamboo.USER}

Password:
  ${bamboo.PASSWORD}

SSH command:
  Copy and paste the full code from this script into the Bamboo interface.

BAMBOO_CONFIG_DOC

set -euxo pipefail

# Bamboo substitutes these tokens before Bash parses the SSH task.
# shellcheck disable=SC2016
TESTING_DEPLOYMENT_DIRECTORY='${bamboo.inject.TESTING_DEPLOYMENT_DIRECTORY}'
# shellcheck disable=SC2016
REPOSITORY_URL='${bamboo.planRepository.repositoryUrl}'
# shellcheck disable=SC2016
BRANCH_NAME='${bamboo.planRepository.branchName}'
# shellcheck disable=SC2016
BUILDING_DEPLOYMENT_DIRECTORY='${bamboo.inject.BUILDING_DEPLOYMENT_DIRECTORY}'
# shellcheck disable=SC2016
HOST_NAME='${bamboo.HOST_CONTAINER}'

rm -rfv "${TESTING_DEPLOYMENT_DIRECTORY}"
git clone -b "${BRANCH_NAME}" "${REPOSITORY_URL}" \
  "${TESTING_DEPLOYMENT_DIRECTORY}/precision_toolkit"
cd "${TESTING_DEPLOYMENT_DIRECTORY}/precision_toolkit"
BRANCH_NAME="${BRANCH_NAME}" .pre-commit/validate_branch_name.sh
VERSION=$(sed -nr "s|^version\s*=\s*\"([^\"]+)\"|\1|p" pyproject.toml)
echo "VERSION=${VERSION}" >precision_toolkit_version.txt
chmod -R g+w "${TESTING_DEPLOYMENT_DIRECTORY}"

rsync -av README.md pyproject.toml uv.lock Dockerfile apptainer.def src \
  deployment/bamboo/01-build-setup/05.build_apptainer_image.sh \
  "${HOST_NAME}":"${BUILDING_DEPLOYMENT_DIRECTORY}/"
