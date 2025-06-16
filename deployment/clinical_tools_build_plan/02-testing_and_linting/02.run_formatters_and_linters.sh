#!/usr/bin/env bash


export LD_LIBRARY_PATH="${LD_LIBRARY_PATH:-}:/projects/clingenetics/software/tools/python/Python-3.11.7/lib"

TESTING_DEVELOPMENT_DIRECTORY=$1

cd "${TESTING_DEVELOPMENT_DIRECTORY}"
source bin/activate
cd pr_check

pre-commit run --all-files
