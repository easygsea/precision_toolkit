# Deployment scripts

Provided with the repository, there are recommended scripts for testing and linting the code for continuous integration
and continuous development using Apptainer image.

The first three stages - build-setup, testing-and-linting, and build-cleanup - are automated on Bamboo and triggered by
any PUSH to your Clinical Tool Branch on BitBucket.
Deployment is a manual stage and is designed to build the final Apptainer image.

To run the default plan configuration, one has to define the following variables in the Bamboo configuration\
`APPTAINER_IMAGE` - default name of the apptainer image to be built (e.g. clinical_tools_latest.sif)\
`BAMBOO_EXEC_ROOT` - path to the deployment scripts\
`BAMBOO_TMP_ROOT` - path where the repository is cloned to, tested in, and where the virtual environment is stored\
`JAVA_EXECUTABLE` - path to the Java executable, required by Nextflow (e.g. `usr/local/bin/jdk-17.0.2`)\
`NEXTFLOW_EXECUTABLE` - path to the local Nextflow executable\
`PRODUCTION_ROOT` - path where clinical tools are deployed to\
`PYTHON_EXECUTABLE` - path to the Python executable, off of which the virtual environment is created


## CI/CD Agent Instructions
Below are the recommended instructions to launch the scripts saved in the deployment folder.

### Build Setup
- Create Variables File - Local Script\
This script copies the needed variables that are only available on the CI/CD agent, and saves them locally into the
`02.inject_bamboo_variables.txt`
```bash
#!/usr/bin/env bash

set -euxo pipefail

BRANCH_NAME=$1
BAMBOO_TMP_ROOT=$2

CLINICAL_TOOLS_IDENTIFIER="CLINICAL_TOOLS"

UNIQUE_IDENTIFIER="${CLINICAL_TOOLS_IDENTIFIER}_${BRANCH_NAME}"
UNIQUE_IDENTIFIER="${UNIQUE_IDENTIFIER//[.,\/-]/_}"

echo "UNIQUE_IDENTIFIER=${UNIQUE_IDENTIFIER}
TESTING_DEPLOYMENT_DIRECTORY=${BAMBOO_TMP_ROOT}/${UNIQUE_IDENTIFIER}" \
  >> 02.inject_bamboo_variables.txt
cat 02.inject_bamboo_variables.txt
```
- Checkout from BitBucket - SSH Task
```bash
cd ${bamboo.BAMBOO_EXEC_ROOT}
cd 01-build-setup/

bash 03.checkout_from_bitbucket.sh ${bamboo.inject.TESTING_DEPLOYMENT_DIRECTORY} \
${bamboo.planRepository.repositoryUrl} \
${bamboo.planRepository.branchName}
```
  -  Setup Poetry Environment
```bash
cd ${bamboo.BAMBOO_EXEC_ROOT}
cd 01-build-setup/

bash 04.poetry_environment.sh ${bamboo.inject.TESTING_DEPLOYMENT_DIRECTORY} \
${bamboo.PYTHON_EXECUTABLE} \
${bamboo.POETRY_EXECUTABLE}
```
  - Build Apptainer Image
```bash
cd ${bamboo.BAMBOO_EXEC_ROOT}
cd 01-build-setup/

bash 05.build_apptainer_image.sh ${bamboo.inject.TESTING_DEPLOYMENT_DIRECTORY} ${bamboo.APPTAINER_IMAGE}
```
### Run Unit Tests
- Run Tests - SSH Task
```bash
cd ${bamboo.BAMBOO_EXEC_ROOT}
cd 02-testing_and_linting/

bash 01.run_unit_and_integration_tests.sh ${bamboo.inject.TESTING_DEPLOYMENT_DIRECTORY} ${bamboo.APPTAINER_IMAGE} \
    ${bamboo.NEXTFLOW_EXECUTABLE} ${bamboo.JAVA_EXECUTABLE}
```
- Move Test Results - Local Task
```bash
cp ${bamboo.inject.TESTING_DEPLOYMENT_DIRECTORY}/clinical_tools/test_results_unit_standalone.xml ${bamboo.build.working.directory}/test_results_unit_standalone.xml
cp ${bamboo.inject.TESTING_DEPLOYMENT_DIRECTORY}/clinical_tools/test_results_workflow.xml ${bamboo.build.working.directory}/test_results_workflow.xml
```
- Analyze Test Results - JUnit Parser

### Linting
- Run Pre Commit - SSH Task
```bash
cd ${bamboo.BAMBOO_EXEC_ROOT}
cd 02-testing_and_linting/

bash 02.run_formatters_and_linters.sh ${bamboo.inject.TESTING_DEPLOYMENT_DIRECTORY}
```
### Clean Up
- Remove Temporary Directory - SSH Task
```bash
cd ${bamboo.BAMBOO_TMP_ROOT}

rm -rfv ${bamboo.inject.TESTING_DEPLOYMENT_DIRECTORY}
```
### Deployment
This stage is recommended to be manual, especially if the CI/CD agent is running the pipeline every time there is a commit.
The main purpose of this stage is to build the container and copy it to the deployment folder.

- Deploy - SSH Task
```bash
cd ${bamboo.BAMBOO_EXEC_ROOT}
cd 04-deployment/

bash 01-deploy.sh ${bamboo.planRepository.branchName} ${bamboo.planRepository.repositoryUrl} \
    ${bamboo.PRODUCTION_ROOT}
```
