# Deployment scripts

Provided with the repository, there are recommended scripts for testing and linting the code for continuous integration
and continuous development using Apptainer image.

The first three stages - build-setup, testing-and-linting, and build-cleanup - are automated on Bamboo and triggered by
any PUSH to your Clinical Tool Branch on BitBucket.
Deployment is a manual stage that promotes a tested build into the production environment.

To run the default plan configuration, one has to define the following variables in the Bamboo configuration\
`APPTAINER_IMAGE` - default name of the Apptainer image to be built (e.g. clinical_tools_latest.sif)\
`BAMBOO_CONTAINERDEV_BUILD_ROOT` - path where the Docker and Apptainer images are built\
`BAMBOO_CONTAINERDEV_BUILD_SCRIPTS` - path to the build scripts\
`BAMBOO_EXEC_ROOT` - path to the deployment scripts\
`BAMBOO_TMP_ROOT` - path where the repository is cloned to, tested in, and where the virtual environment is stored\
`CONTAINERDEV` - server that supports Docker image creation\
`HOST_NAME` - host used for building the image\
`IMAGE_STORE_ROOT` - path where the image is stored before being deployed\
`JAVA_EXECUTABLE` - path to the Java executable, required by Nextflow (e.g. `usr/local/bin/jdk-17.0.2`)\
`NEXTFLOW_EXECUTABLE` - path to the local Nextflow executable\
`PASSWORD` - password for logging into the testing server\
`PASSWORD_CONTAINERDEV` - password for logging into the build server\
`POETRY_EXECUTABLE` - path to the poetry executable\
`PRODUCTION_ROOT` - path where clinical tools are deployed to\
`PYTHON_EXECUTABLE` - path to the Python executable, off of which the virtual environment is created\
`PYTHON_LIB_DIR` - path to the python libraries\
`USER` - name of the user running the Bamboo plan 


## CI/CD Agent Instructions
Below are the recommended instructions to launch the scripts saved in the deployment folder.

### Build Setup
- Create Variables File - Local Script\
This script copies the needed variables that are only available on the CI/CD agent, and saves them locally into the
`02.inject_bamboo_variables.txt`
```bash
#!/usr/bin/env bash

set -euxo pipefail

BRANCH_NAME="$1"
BAMBOO_TMP_ROOT="$2"
BAMBOO_CONTAINERDEV_BUILD_ROOT="$3"
APPTAINER_IMAGE="$4"
BUILD_IDENTIFIER="$5"

CLINICAL_TOOLS_IDENTIFIER="CLINICAL_TOOLS"

UNIQUE_IDENTIFIER="${CLINICAL_TOOLS_IDENTIFIER}_${BRANCH_NAME}"
UNIQUE_IDENTIFIER="${UNIQUE_IDENTIFIER//[.,\/-]/_}"

echo "UNIQUE_IDENTIFIER=${UNIQUE_IDENTIFIER}
TESTING_DEPLOYMENT_DIRECTORY=${BAMBOO_TMP_ROOT}/${UNIQUE_IDENTIFIER}
BUILDING_DEPLOYMENT_DIRECTORY=${BAMBOO_CONTAINERDEV_BUILD_ROOT}/${UNIQUE_IDENTIFIER}
IMAGE_NAME=${APPTAINER_IMAGE}_${BUILD_IDENTIFIER}.sif" \
  > 02.inject_bamboo_variables.txt
cat 02.inject_bamboo_variables.txt
```
- Checkout from BitBucket - Local script
```bash
#!/usr/bin/env bash

set -euxo pipefail

TESTING_DEPLOYMENT_DIRECTORY="$1"
REPOSITORY_URL="$2"
BRANCH_NAME="$3"
BUILDING_DEPLOYMENT_DIRECTORY="$4"
HOST_NAME="$5"

rm -rfv "${TESTING_DEPLOYMENT_DIRECTORY}"
git clone -b "${BRANCH_NAME}" "${REPOSITORY_URL}" \
  "${TESTING_DEPLOYMENT_DIRECTORY}"/clinical_tools
cd "${TESTING_DEPLOYMENT_DIRECTORY}"/clinical_tools
VERSION=$(sed -nr "s|^version\s*=\s*\"([^\"]+)\"|\1|p" pyproject.toml)
echo "VERSION=${VERSION}" > clinical_tools_version.txt
chmod -R g+w "${TESTING_DEPLOYMENT_DIRECTORY}"

rsync -av README.md pyproject.toml poetry.lock Dockerfile src \
  "${HOST_NAME}":"${BUILDING_DEPLOYMENT_DIRECTORY}/"
```
  -  Setup Poetry Environment - SSH Task
```bash
cd ${bamboo.inject.TESTING_DEPLOYMENT_DIRECTORY}
cd clinical_tools/deployment/bamboo/01-build-setup/

bash 04.poetry_environment.sh ${bamboo.inject.TESTING_DEPLOYMENT_DIRECTORY} \
${bamboo.PYTHON_EXECUTABLE} ${bamboo.PYTHON_LIB_DIR}
```
  - Build Apptainer Image - SSH Task
```bash
cd ${bamboo.BAMBOO_CONTAINERDEV_BUILD_SCRIPTS}

bash 05.build_apptainer_image.sh ${bamboo.inject.BUILDING_DEPLOYMENT_DIRECTORY} ${bamboo.inject.IMAGE_NAME}
```
  - Transfer Image - SSH Task
```bash
cd ${bamboo.inject.TESTING_DEPLOYMENT_DIRECTORY}
cd clinical_tools/deployment/bamboo/01-build-setup/

bash 06.transfer_image.sh ${bamboo.CONTAINERDEV} \
${bamboo.inject.BUILDING_DEPLOYMENT_DIRECTORY} \
${bamboo.inject.IMAGE_NAME} \
${bamboo.inject.TESTING_DEPLOYMENT_DIRECTORY}
```
### Run Unit Tests
- Run Tests - SSH Task
```bash
cd ${bamboo.inject.TESTING_DEPLOYMENT_DIRECTORY}
cd clinical_tools/deployment/bamboo/02-testing_and_linting/

bash 01.run_unit_and_integration_tests.sh ${bamboo.inject.TESTING_DEPLOYMENT_DIRECTORY} ${bamboo.inject.IMAGE_NAME} ${bamboo.NEXTFLOW_EXECUTABLE} ${bamboo.JAVA_EXECUTABLE} ${bamboo.PYTHON_LIB_DIR}
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
cd ${bamboo.inject.TESTING_DEPLOYMENT_DIRECTORY}
cd clinical_tools/deployment/bamboo/02-testing_and_linting/
 
bash 02.run_formatters_and_linters.sh ${bamboo.inject.TESTING_DEPLOYMENT_DIRECTORY} ${bamboo.PYTHON_LIB_DIR} ${bamboo.inject.IMAGE_NAME} ${bamboo.IMAGE_STORE_ROOT}
```
### Clean Up
- Remove Testing Directory - SSH Task
```bash
rm -rfv ${bamboo.inject.TESTING_DEPLOYMENT_DIRECTORY}
```
- Remove Build Directory - SSH Task
```bash
rm -rfv ${bamboo.inject.BUILDING_DEPLOYMENT_DIRECTORY}
```
### Deployment
This stage is recommended to be manual, especially if the CI/CD agent is running the pipeline every time there is a commit.
The main purpose of this stage is to build the container and copy it to the deployment folder.

- Deploy - SSH Task
```bash
cd ${bamboo.BAMBOO_EXEC_ROOT}
cd 04-deployment/

bash 01.clone_to_deployment.sh ${bamboo.planRepository.branchName} ${bamboo.planRepository.repositoryUrl} \
    ${bamboo.PRODUCTION_ROOT} ${bamboo.inject.IMAGE_NAME} ${bamboo.PYTHON_EXECUTABLE} \
    ${bamboo.IMAGE_STORE_ROOT} ${bamboo.PYTHON_LIB_DIR} ${bamboo.APPTAINER_IMAGE}
```
