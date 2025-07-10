#!/usr/bin/env bash

set -euxo pipefail

TESTING_DEPLOYMENT_DIRECTORY=$1
APPTAINER_IMAGE=$2
NEXTFLOW_EXECUTABLE=$3
JAVA_EXECUTABLE=$4

export PATH="$PATH:${NEXTFLOW_EXECUTABLE}"
export JAVA_HOME="${JAVA_EXECUTABLE}"
export PATH=$JAVA_HOME/bin:$PATH

cd "${TESTING_DEPLOYMENT_DIRECTORY}"
source venv/bin/activate
cd clinical_tools/

# Executing the python unit and standalone tests inside the container to avoid dependency conflicts with OS
apptainer exec "${APPTAINER_IMAGE}" python -m pytest tests/standalone/ tests/unit/ --junit-xml=test_results_unit_standalone.xml

# Replace the pointer to the remote image to the local one and run workflow tests with Nextflow pointing to the local image
sed -i 's~container = "quay.io/easygsea/clinical_tools:latest"~container = "file://'"${APPTAINER_IMAGE}"'"~' nextflow.config
pytest tests/workflow/ --junit-xml=test_results_workflow.xml
