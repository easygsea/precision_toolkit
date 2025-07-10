#!/usr/bin/env bash

########## BAMBOO INTERFACE CONFIGURATION ############
####       Hosts: gphost14                        ####
######################################################

set -euxo pipefail

TESTING_DEPLOYMENT_DIRECTORY=$1
REPOSITORY_URL=$2
BRANCH_NAME=$3

rm -rfv "${TESTING_DEPLOYMENT_DIRECTORY}"
git clone -b "${BRANCH_NAME}" "${REPOSITORY_URL}" \
  "${TESTING_DEPLOYMENT_DIRECTORY}"/clinical_tools
cd "${TESTING_DEPLOYMENT_DIRECTORY}"/clinical_tools
VERSION=$(sed -nr "s|^version\s*=\s*\"([^\"]+)\"|\1|p" pyproject.toml)
echo "VERSION=${VERSION}" > clinical_tools_version.txt
