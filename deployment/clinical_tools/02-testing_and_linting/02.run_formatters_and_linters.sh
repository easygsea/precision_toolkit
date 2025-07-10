#!/usr/bin/env bash

########## BAMBOO INTERFACE CONFIGURATION ############
####       Hosts: gphost14                        ####
######################################################

set -euxo pipefail

TESTING_DEVELOPMENT_DIRECTORY=$1

cd "${TESTING_DEVELOPMENT_DIRECTORY}"
source venv/bin/activate
cd clinical_tools

pre-commit run --all-files
