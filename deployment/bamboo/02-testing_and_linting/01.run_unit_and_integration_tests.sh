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
cd ${bamboo.inject.TESTING_DEPLOYMENT_DIRECTORY}
cd clinical_tools/deployment/bamboo/02-testing_and_linting/
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
cp ${bamboo.inject.TESTING_DEPLOYMENT_DIRECTORY}/clinical_tools/test_results_unit_standalone.xml ${bamboo.build.working.directory}/test_results_unit_standalone.xml
cp ${bamboo.inject.TESTING_DEPLOYMENT_DIRECTORY}/clinical_tools/test_results_workflow.xml ${bamboo.build.working.directory}/test_results_workflow.xml

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

cd "${TESTING_DEPLOYMENT_DIRECTORY}"
source venv/bin/activate
cd clinical_tools/

# Executing the python unit and standalone tests
pytest tests/standalone/ tests/unit/ --junit-xml=test_results_unit_standalone.xml

# Replace the pointer to the remote image to the local one and run workflow tests with Nextflow pointing to the local image
sed -i 's~container = "quay.io/easygsea/clinical_tools:latest"~container = "file://'"${IMAGE_NAME}"'"~' nextflow.config
pytest tests/workflow/ --junit-xml=test_results_workflow.xml

chmod a+x "${TESTING_DEPLOYMENT_DIRECTORY}"
chmod a+x "${TESTING_DEPLOYMENT_DIRECTORY}"/clinical_tools
chmod a+r "${TESTING_DEPLOYMENT_DIRECTORY}"/clinical_tools/test_results_*.xml
