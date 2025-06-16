#!/usr/bin/env bash


export LD_LIBRARY_PATH="${LD_LIBRARY_PATH:-}:/projects/clingenetics/software/tools/python/Python-3.11.7/lib"

TESTING_DEPLOYMENT_DIRECTORY=$1

cd "${TESTING_DEPLOYMENT_DIRECTORY}"
source bin/activate
cd pr_check

set +e
pytest --junit-xml=test_results.xml
