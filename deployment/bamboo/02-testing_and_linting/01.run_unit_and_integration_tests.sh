#!/usr/bin/env bash

: <<'BAMBOO_CONFIG_DOC'

Task type:
  SSH Task

Task description:
  Run unit and integration tests

Hosts:
  ${bamboo.HOST}

Authentication type:
  Username and password

Username:
  ${bamboo.USER}

Password:
  ${bamboo.PASSWORD}

SSH command:
cd ${bamboo.inject.TESTING_DEPLOYMENT_DIRECTORY}/precision_toolkit/deployment/bamboo/02-testing_and_linting/
bash 01.run_unit_and_integration_tests.sh \
${bamboo.inject.TESTING_DEPLOYMENT_DIRECTORY} \
${bamboo.inject.IMAGE_NAME} \
${bamboo.NEXTFLOW_EXECUTABLE} \
${bamboo.JAVA_EXECUTABLE}

Additional two tasks for this step:

Task type:
  Script

Task description:
  Move test results

Interpreter:
  Shell

Script location:
  Inline

Script body:
cp ${bamboo.inject.TESTING_DEPLOYMENT_DIRECTORY}/precision_toolkit/test_results_unit_standalone.xml ${bamboo.build.working.directory}/test_results_unit_standalone.xml
cp ${bamboo.inject.TESTING_DEPLOYMENT_DIRECTORY}/precision_toolkit/test_results_workflow.xml ${bamboo.build.working.directory}/test_results_workflow.xml

Task type:
  JUnit Parser

Task description:
  Analyze test results

Specify custom results directories:
  *.xml

BAMBOO_CONFIG_DOC

set -euxo pipefail

TESTING_DEPLOYMENT_DIRECTORY="$1"
IMAGE_NAME="$2"
NEXTFLOW_EXECUTABLE="$3"
JAVA_EXECUTABLE="$4"

export PATH="$PATH:${NEXTFLOW_EXECUTABLE}"
export JAVA_HOME="${JAVA_EXECUTABLE}"
export PATH=$JAVA_HOME/bin:$PATH

cd "${TESTING_DEPLOYMENT_DIRECTORY}/precision_toolkit"

# Execute Python unit and standalone tests
uv run pytest tests/standalone/ tests/unit/ --junit-xml=test_results_unit_standalone.xml

# Replace the pointer to the remote image to the local one and run workflow tests with Nextflow pointing to the local image
sed -i 's~container = ".*"~container = "file://'"${TESTING_DEPLOYMENT_DIRECTORY}/precision_toolkit/${IMAGE_NAME}"'"~' nextflow.config

WORKFLOW_THREADS=$(( $(nproc) - 2 ))
if [ "${WORKFLOW_THREADS}" -gt 6 ]; then
  WORKFLOW_THREADS=6
fi
uv run pytest tests/workflow/ --workflow-threads "${WORKFLOW_THREADS}" --ga --symlink --junit-xml=test_results_workflow.xml

chmod a+x "${TESTING_DEPLOYMENT_DIRECTORY}"
chmod a+x "${TESTING_DEPLOYMENT_DIRECTORY}/precision_toolkit"
chmod a+r "${TESTING_DEPLOYMENT_DIRECTORY}/precision_toolkit/"test_results_*.xml
