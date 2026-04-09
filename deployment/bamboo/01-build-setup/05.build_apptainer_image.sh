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
bash 05.build_apptainer_image.sh ${bamboo.inject.IMAGE_NAME} ${bamboo.BASE_IMAGE_ROOT}

BAMBOO_CONFIG_DOC

set -euxo pipefail

IMAGE_NAME="$1"
BASE_IMAGE_ROOT="$2"

chmod -R a+rx "$PWD"
rm -rfv "${IMAGE_NAME}"

CONFIG_HASH=$(cat Dockerfile pyproject.toml uv.lock | sha256sum | cut -c1-16)
DOCKER_TAG="clinical_tools:${CONFIG_HASH}"
BASE_IMAGE="${BASE_IMAGE_ROOT}/${CONFIG_HASH}_base.sif"

# Only rebuild base images if config hash is new
if ! docker image inspect "${DOCKER_TAG}" &>/dev/null; then
    sed -i '/^# Install project source/,/^    rm -rf dist\/ \/root\/.cache$/d' Dockerfile
    echo "Building Docker image..."
    docker build -t "${DOCKER_TAG}" -f ./Dockerfile .
fi

if [[ ! -f "${BASE_IMAGE}" ]]; then
    echo "Building base Apptainer image..."
    ( while true; do echo "Still building..."; sleep 60; done ) &
    KEEPALIVE_PID=$!
    sudo apptainer build "${BASE_IMAGE}" "docker-daemon://${DOCKER_TAG}"
    kill "${KEEPALIVE_PID}" || true
fi

# Point .def at the correct base SIF
sed -i "s|^From:.*|From: ${BASE_IMAGE}|" apptainer.def

echo "Building Apptainer image..."
( while true; do echo "Still building..."; sleep 60; done ) &
KEEPALIVE_PID=$!
sudo apptainer build "${IMAGE_NAME}" apptainer.def
kill "${KEEPALIVE_PID}" || true
