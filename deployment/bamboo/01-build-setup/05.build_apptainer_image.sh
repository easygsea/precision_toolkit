#!/usr/bin/env bash

: <<'BAMBOO_CONFIG_DOC'

Task type:
  SSH Task

Task description:
  Build Apptainer Image

Hosts:
  ${bamboo.HOST_CONTAINER}

Authentication type:
  Username and password

Username:
  ${bamboo.USER}

Password:
  ${bamboo.PASSWORD_CONTAINER}

SSH command:
cd ${bamboo.inject.BUILDING_DEPLOYMENT_DIRECTORY}
bash 05.build_apptainer_image.sh ${bamboo.inject.IMAGE_NAME}

BAMBOO_CONFIG_DOC

set -euxo pipefail

IMAGE_NAME="$1"

rm -rfv "${IMAGE_NAME}"

echo "Building Docker image..."
docker build -t clinical_tools:bamboo -f ./Dockerfile .

echo "Building Apptainer image..."
( while true; do echo "Still building..."; sleep 60; done ) &
KEEPALIVE_PID=$!

sudo apptainer build \
    "${IMAGE_NAME}" \
    docker-daemon://clinical_tools:bamboo

chmod --changes g+w "${IMAGE_NAME}"
kill "${KEEPALIVE_PID}" || true
