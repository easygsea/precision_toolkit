#!/usr/bin/env bash


export LD_LIBRARY_PATH="${LD_LIBRARY_PATH:-}:/projects/clingenetics/software/tools/python/Python-3.11.7/lib"
export LD_LIBRARY_PATH="${LD_LIBRARY_PATH:-}:/projects/clingenetics/software/tools/python/Python-3.11.7/lib"

TESTING_DEPLOYMENT_DIRECTORY=$1
PYTHON_EXECUTABLE=$2
POETRY_EXECUTABLE=$3

cd "${TESTING_DEPLOYMENT_DIRECTORY}"
# Ensures $@ is empty when calling source to avoid passing in unwanted parameters
shift $#

$PYTHON_EXECUTABLE -m venv .
source bin/activate
pip install --upgrade pip wheel

cd pr_check
"${POETRY_EXECUTABLE}" install
