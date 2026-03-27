#!/usr/bin/env bash

: <<'BAMBOO_CONFIG_DOC'

Task type:
  SSH Task

Task description:
  Transfer Apptainer Image

Hosts:
  ${bamboo.HOST}

Authentication type:
  Username and password

Username:
  ${bamboo.USER}

Password:
  ${bamboo.PASSWORD}

SSH command:
cd ${bamboo.inject.TESTING_DEPLOYMENT_DIRECTORY}/clinical_tools/deployment/bamboo/01-build-setup/
bash 06.transfer_image.sh ${bamboo.HOST_CONTAINER} \
${bamboo.inject.BUILDING_DEPLOYMENT_DIRECTORY} \
${bamboo.inject.IMAGE_NAME} \
${bamboo.inject.TESTING_DEPLOYMENT_DIRECTORY}

BAMBOO_CONFIG_DOC

set -euxo pipefail

HOST_NAME="$1"
BUILDING_DEPLOYMENT_DIRECTORY="$2"
IMAGE_NAME="$3"
TESTING_DEPLOYMENT_DIRECTORY="$4"

scp "${HOST_NAME}":"${BUILDING_DEPLOYMENT_DIRECTORY}"/"${IMAGE_NAME}" \
  "${TESTING_DEPLOYMENT_DIRECTORY}"/clinical_tools
