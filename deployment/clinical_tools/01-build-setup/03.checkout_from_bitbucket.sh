#!/usr/bin/env bash

set -euxo pipefail

TESTING_DEPLOYMENT_DIRECTORY=$1
REPOSITORY_URL=$2
BRANCH_NAME=$3
BUILDING_DEPLOYMENT_DIRECTORY=$4
HOST_NAME=$5

rm -rfv "${TESTING_DEPLOYMENT_DIRECTORY}"
git clone -b "${BRANCH_NAME}" "${REPOSITORY_URL}" \
  "${TESTING_DEPLOYMENT_DIRECTORY}"/clinical_tools
cd "${TESTING_DEPLOYMENT_DIRECTORY}"/clinical_tools
VERSION=$(sed -nr "s|^version\s*=\s*\"([^\"]+)\"|\1|p" pyproject.toml)
echo "VERSION=${VERSION}" > clinical_tools_version.txt

scp -r README.md pyproject.toml poetry.lock apptainer.def src \
  "${HOST_NAME}":"${BUILDING_DEPLOYMENT_DIRECTORY}"