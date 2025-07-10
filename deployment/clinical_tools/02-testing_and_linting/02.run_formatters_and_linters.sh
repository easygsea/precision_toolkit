#!/usr/bin/env bash

########## BAMBOO INTERFACE CONFIGURATION ############
####       Hosts: gphost14                        ####
######################################################

export LD_LIBRARY_PATH="${LD_LIBRARY_PATH:-}:/projects/clingenetics/software/tools/python/Python-3.11.7/lib"

TESTING_DEVELOPMENT_DIRECTORY=$1

cd "${TESTING_DEVELOPMENT_DIRECTORY}"
source venv/bin/activate
cd clinical_tools

pre-commit run --all-files
