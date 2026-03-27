#!/usr/bin/env bash

: <<'BAMBOO_CONFIG_DOC'

Task type:
  Script

Task description:
  Create Variables File

Interpreter:
  Shell

Script location:
  Inline

Arguments:
  ${bamboo.planRepository.branchName} ${bamboo.TEMPORARY_TESTING_ROOT} ${bamboo.CONTAINER_BUILD_ROOT} ${bamboo.APPTAINER_IMAGE_NAME} ${bamboo.buildResultKey}

Script body:
  Copy and paste the full code from this script into the Bamboo interface.

BAMBOO_CONFIG_DOC

set -euxo pipefail

BRANCH_NAME="$1"
TEMPORARY_TESTING_ROOT="$2"
CONTAINER_BUILD_ROOT="$3"
APPTAINER_IMAGE_NAME="$4"
BUILD_IDENTIFIER="$5"

CLINICAL_TOOLS_IDENTIFIER="CLINICAL_TOOLS"

UNIQUE_IDENTIFIER="${CLINICAL_TOOLS_IDENTIFIER}_${BRANCH_NAME}"
UNIQUE_IDENTIFIER="${UNIQUE_IDENTIFIER//[.,\/-]/_}"

echo "UNIQUE_IDENTIFIER=${UNIQUE_IDENTIFIER}
TESTING_DEPLOYMENT_DIRECTORY=${TEMPORARY_TESTING_ROOT}/${UNIQUE_IDENTIFIER}
BUILDING_DEPLOYMENT_DIRECTORY=${CONTAINER_BUILD_ROOT}/${UNIQUE_IDENTIFIER}
IMAGE_NAME=${APPTAINER_IMAGE_NAME}_${BUILD_IDENTIFIER}.sif" \
  >> 02.inject_bamboo_variables.txt
cat 02.inject_bamboo_variables.txt
