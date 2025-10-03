# Deployment scripts

Provided with the repository, there are recommended scripts for testing and linting the code for continuous integration
and continuous development using Apptainer image.

The first three stages - build-setup, testing-and-linting, and build-cleanup - are automated on Bamboo and triggered by
any PUSH to your Clinical Tool Branch on BitBucket.
Deployment is a manual stage that promotes a tested build into the operational environment.

To run the default plan configuration, one has to define the following variables in the Bamboo configuration\
`APPTAINER_IMAGE_NAME` - default name of the Apptainer image to be built (e.g. clinical_tools_latest.sif)\
`CONTAINER_BUILD_ROOT` - path where the Docker and Apptainer images are built\
`TEMPORARY_TESTING_ROOT` - path where the repository is cloned to, tested in, and where the virtual environment is stored\
`HOST` -  standard server providing access to testing and deployment directories.\
`HOST_CONTAINER` - server that supports Docker for creating and building images\
`TEMPORARY_IMAGE_ROOT` - path where the image is temporarily stored before being deployed\
`JAVA_EXECUTABLE` - path to the Java executable, required by Nextflow (e.g. `usr/local/bin/jdk-17.0.2`)\
`NEXTFLOW_EXECUTABLE` - path to the local Nextflow executable\
`PASSWORD` - login password for the deployment server, which hosts both deployment and testing directories\
`PASSWORD_CONTAINER` - login password for the server that builds Docker/Apptainer images\
`DEPLOYMENT_ROOT` - path where clinical tools are deployed to\
`PYTHON_EXECUTABLE` - path to the Python executable, off of which the virtual environment is created\
`PYTHON_LIB_DIR` - path to the python libraries\
`USER` - name of the user running the Bamboo plan


## CI/CD Agent Instructions
Below are the recommended instructions to launch the scripts saved in the `bamboo/` folder.

### Build Setup
- Create Variables File - Script Executed on Bamboo\
This script copies the needed variables that are only available on the Bamboo CI/CD agent, and saves them locally into the
`02.inject_bamboo_variables.txt`
```bash
#!/usr/bin/env bash

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
```
- Checkout from BitBucket - Script Executed on Bamboo
```bash
#!/usr/bin/env bash

set -euxo pipefail

TESTING_DEPLOYMENT_DIRECTORY=${bamboo.inject.TESTING_DEPLOYMENT_DIRECTORY}
REPOSITORY_URL=${bamboo.planRepository.repositoryUrl}
BRANCH_NAME=${bamboo.planRepository.branchName}
BUILDING_DEPLOYMENT_DIRECTORY=${bamboo.inject.BUILDING_DEPLOYMENT_DIRECTORY}
HOST_NAME=${bamboo.HOST_CONTAINER}

rm -rfv "${TESTING_DEPLOYMENT_DIRECTORY}"
git clone -b "${BRANCH_NAME}" "${REPOSITORY_URL}" \
  "${TESTING_DEPLOYMENT_DIRECTORY}"/clinical_tools
cd "${TESTING_DEPLOYMENT_DIRECTORY}"/clinical_tools
VERSION=$(sed -nr "s|^version\s*=\s*\"([^\"]+)\"|\1|p" pyproject.toml)
echo "VERSION=${VERSION}" > clinical_tools_version.txt
chmod -R g+w "${TESTING_DEPLOYMENT_DIRECTORY}"

rsync -av README.md pyproject.toml poetry.lock Dockerfile src \
    deployment/bamboo/01-build-setup/05.build_apptainer_image.sh \
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
cd ${bamboo.inject.BUILDING_DEPLOYMENT_DIRECTORY}

bash 05.build_apptainer_image.sh ${bamboo.inject.IMAGE_NAME}
```
  - Transfer Image - SSH Task
```bash
cd ${bamboo.inject.TESTING_DEPLOYMENT_DIRECTORY}
cd clinical_tools/deployment/bamboo/01-build-setup/

bash 06.transfer_image.sh ${bamboo.HOST_CONTAINER} \
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
- Move Test Results - Script Executed on Bamboo
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

bash 02.run_formatters_and_linters.sh ${bamboo.inject.TESTING_DEPLOYMENT_DIRECTORY} ${bamboo.PYTHON_LIB_DIR} ${bamboo.inject.IMAGE_NAME} ${bamboo.TEMPORARY_IMAGE_ROOT}
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
#!/usr/bin/env bash

set -euxo pipefail

# Clone the repository, move it into the deployment folder and build the apptainer image
function clone_and_deploy {
  cd "${PRODUCTION_ROOT}/clinical_tools"
  git clone --branch "${BRANCH_NAME}" "${REPOSITORY_URL}" tmp_dir
  cd tmp_dir
  version=$(get_version)
  if [ -d "${version}" ]; then
    echo "The version has already been deployed"
    exit 1
  else
    cd ..
    mkdir -p "${PRODUCTION_ROOT}/clinical_tools/${version}"
    mv tmp_dir/* "${PRODUCTION_ROOT}/clinical_tools/${version}/"
    cd "${PRODUCTION_ROOT}/clinical_tools/${version}"
    "${PYTHON_EXECUTABLE}" -m venv venv
    source venv/bin/activate
    pip install --upgrade pip wheel
    pip install poetry==2.0.1
    poetry install --with dev
    cp -v "${IMAGE_STORE_ROOT}/${version}/${IMAGE_NAME}" ./"${NEW_IMAGE_NAME}"
    rm -rfv "${IMAGE_STORE_ROOT}/${version}"
    sed -i "s~container = \"quay.io/easygsea/clinical_tools:latest\"~container = \"${PRODUCTION_ROOT}/clinical_tools/${version}/${NEW_IMAGE_NAME}\"~" nextflow.config
    cd "${PRODUCTION_ROOT}/clinical_tools"
    rm -rf main
    mkdir main
    cp -r "${version}"/* main/
  fi
  rm -rf tmp_dir/
}

# Get version defined in the pyproject.toml
function get_version {
  version="$(
    sed --quiet '/^version =/{s/version = "\([^"]\+\)"/\1/;p}' pyproject.toml
  )"
  if [[
    "main" == "${BRANCH_NAME}"
    && ! "${version}" =~ ^[0-9]+(\.[0-9]+){2}$
  ]]; then
    echo "Invalid production version: '${version}'." >&2
    exit 1
  fi
  echo "${version}"
}

function main {
  declare -r \
    BRANCH_NAME=${bamboo.planRepository.branchName}  \
    REPOSITORY_URL=${bamboo.planRepository.repositoryUrl}  \
    PRODUCTION_ROOT=${bamboo.DEPLOYMENT_ROOT} \
    IMAGE_NAME=${bamboo.inject.IMAGE_NAME} \
    PYTHON_EXECUTABLE=${bamboo.PYTHON_EXECUTABLE} \
    IMAGE_STORE_ROOT=${bamboo.TEMPORARY_IMAGE_ROOT} \
    PYTHON_LIB_DIR=${bamboo.PYTHON_LIB_DIR} \
    NEW_IMAGE_NAME=${bamboo.APPTAINER_IMAGE_NAME}

  export LD_LIBRARY_PATH="${LD_LIBRARY_PATH:-}:${PYTHON_LIB_DIR}"

  echo "Deploying branch '${BRANCH_NAME}'..."
  clone_and_deploy
}

main "$@"
```
