#!/usr/bin/env bash

########## BAMBOO INTERFACE CONFIGURATION ############
####       Hosts: dragen02                        ####
######################################################


set -euxo pipefail

TESTING_DEPLOYMENT_DIRECTORY=$1
IMAGE_NAME=$2

cd "${TESTING_DEPLOYMENT_DIRECTORY}"/clinical_tools

apptainer build "${IMAGE_NAME}" apptainer.def
