#!/usr/bin/env bash

: <<'BAMBOO_CONFIG_DOC'

Task type:
  SSH Task

Hosts:
  ${bamboo.HOST_CONTAINER}

Authentication type:
  Username and password

Username:
  ${bamboo.USER}

Password:
  ${bamboo.PASSWORD_CONTAINER}

BAMBOO_CONFIG_DOC

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
