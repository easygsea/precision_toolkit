#!/usr/bin/env bash

set -euxo pipefail

IMAGE_NAME="$1"

rm -rfv "${IMAGE_NAME}"

docker build -t clinical_tools:bamboo -f ./Dockerfile .

echo "Building apptainer image...."
( while true; do echo "Still building..."; sleep 60; done ) &
KEEPALIVE_PID=$!

sudo apptainer build "${IMAGE_NAME}" docker-daemon://clinical_tools:bamboo
chmod --changes g+w "${IMAGE_NAME}"

kill $KEEPALIVE_PID || true
