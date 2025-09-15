#!/usr/bin/env bash

set -euxo pipefail

BUILDING_DEPLOYMENT_DIRECTORY=$1
APPTAINER_IMAGE=$2

cd "${BUILDING_DEPLOYMENT_DIRECTORY}"

sudo apptainer build "${APPTAINER_IMAGE}" apptainer.def