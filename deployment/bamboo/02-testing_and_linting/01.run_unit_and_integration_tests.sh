#!/usr/bin/env bash

set -euxo pipefail

TESTING_DEPLOYMENT_DIRECTORY="$1"
IMAGE_NAME="$2"
NEXTFLOW_EXECUTABLE="$3"
JAVA_EXECUTABLE="$4"
PYTHON_LIB_DIR="$5"

export PATH="$PATH:${NEXTFLOW_EXECUTABLE}"
export JAVA_HOME="${JAVA_EXECUTABLE}"
export PATH=$JAVA_HOME/bin:$PATH
export LD_LIBRARY_PATH="${LD_LIBRARY_PATH:-}:${PYTHON_LIB_DIR}"

cd "${TESTING_DEPLOYMENT_DIRECTORY}"
source venv/bin/activate
cd clinical_tools/

apptainer exec "${IMAGE_NAME}" pip install pytest pytest-cov pytest-workflow pytest-xdist pyproject-pre-commit

# Executing the python unit and standalone tests inside the container to avoid dependency conflicts with OS
apptainer exec "${IMAGE_NAME}" python -m pytest tests/standalone/ tests/unit/ --junit-xml=test_results_unit_standalone.xml

# Replace the pointer to the remote image to the local one and run workflow tests with Nextflow pointing to the local image
sed -i 's~container = "quay.io/easygsea/clinical_tools:latest"~container = "file://'"${IMAGE_NAME}"'"~' nextflow.config
pytest tests/workflow/ --junit-xml=test_results_workflow.xml

chmod a+x "${TESTING_DEPLOYMENT_DIRECTORY}"
chmod a+x "${TESTING_DEPLOYMENT_DIRECTORY}"/clinical_tools
chmod a+r "${TESTING_DEPLOYMENT_DIRECTORY}"/clinical_tools/test_results_*.xml
