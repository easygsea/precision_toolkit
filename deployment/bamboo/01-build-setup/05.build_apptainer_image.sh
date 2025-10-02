#!/usr/bin/env bash

set -euxo pipefail

BUILDING_DEPLOYMENT_DIRECTORY="$1"
IMAGE_NAME="$2"

cd "${BUILDING_DEPLOYMENT_DIRECTORY}"

rm -rfv "${IMAGE_NAME}"

docker build -t clinical_tools:bamboo -f ./Dockerfile .

echo "Building apptainer image...."
( while true; do echo "Still building..."; sleep 60; done ) &
KEEPALIVE_PID=$!

sudo apptainer build "${IMAGE_NAME}" docker-daemon://clinical_tools:bamboo
chmod --changes g+w "${IMAGE_NAME}"

kill $KEEPALIVE_PID || true
