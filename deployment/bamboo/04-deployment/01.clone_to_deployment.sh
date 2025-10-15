#!/usr/bin/env bash

: <<'BAMBOO_CONFIG_DOC'

Set deployment as a Manual stage to control testing vs final build.

Task type:
  SSH Task

Task description:
  Deploy clinical_tools

Hosts:
  ${bamboo.HOST}

Authentication type:
  Username and password

Username:
  ${bamboo.USER}

Password:
  ${bamboo.PASSWORD}

SSH command:
  Copy and paste the full code from this script into the Bamboo interface.

BAMBOO_CONFIG_DOC

set -euxo pipefail

# Clone the repository, move it into the deployment folder and build the apptainer image
function clone_and_deploy {
  cd "${DEPLOYMENT_ROOT}/clinical_tools"
  [[ -d tmp_dir ]] && rm -rfv tmp_dir
  git clone --branch "${BRANCH_NAME}" "${REPOSITORY_URL}" tmp_dir
  cd tmp_dir
  version=$(get_version)
  cd ..
  if [[ -d "${version}" ]]; then
    echo "The version has already been deployed"
    exit 1
  else
    version_folder="${DEPLOYMENT_ROOT}/clinical_tools/${version}"
    mkdir -pv "${version_folder}"
    mv tmp_dir/* "${version_folder}/"
    cd "${version_folder}"
    "${PYTHON_EXECUTABLE}" -m venv venv
    source venv/bin/activate
    pip install --upgrade pip wheel
    pip install poetry==2.0.1
    poetry install
    cp -v "${IMAGE_STORE_ROOT}/${version}/${IMAGE_NAME}" ./"${NEW_IMAGE_NAME}"
    sed -i "s~container = \".*\"~container = \"${DEPLOYMENT_ROOT}/clinical_tools/${version}/${NEW_IMAGE_NAME}\"~" nextflow.config    cd "${DEPLOYMENT_ROOT}/clinical_tools"
    chmod --recursive a-w "${version}"
    [[ -d main ]] && chmod --changes --recursive u+w main && rm -rfv main
    mkdir --mode 2750 main
    cp -r "${version}"/* main/
    chmod --changes --recursive a-w main
  fi
  rm -rfv tmp_dir/
  rm -rfv "${IMAGE_STORE_ROOT}/${version}"
}

# Get version defined in the pyproject.toml
function get_version {
  version="$(
    sed --quiet '/^version =/{s/version = "\([^"]\+\)"/\1/;p}' pyproject.toml
  )"
  if [[ ! "${version}" =~ ^[0-9]+(\.[0-9]+){2}$ ]]; then
    echo "Invalid version: '${version}'." >&2
    exit 1
  fi
  echo "${version}"
}

function main {
  declare -r \
    BRANCH_NAME="${1:-${bamboo.planRepository.branchName}}"  \
    REPOSITORY_URL="${2:-${bamboo.planRepository.repositoryUrl}}"  \
    DEPLOYMENT_ROOT="${3:-${bamboo.DEPLOYMENT_ROOT}}" \
    IMAGE_NAME="${4:-${bamboo.inject.IMAGE_NAME}}" \
    PYTHON_EXECUTABLE="${5:-${bamboo.PYTHON_EXECUTABLE}}" \
    IMAGE_STORE_ROOT="${6:-${bamboo.TEMPORARY_IMAGE_ROOT}}" \
    NEW_IMAGE_NAME="${7:-${bamboo.APPTAINER_IMAGE_NAME}}"

  if [[ "${BRANCH_NAME}" != "main" ]]; then
    echo "Deployment is restricted to the 'main' branch only."
    exit 1
  fi

  echo "Deploying branch '${BRANCH_NAME}'..."
  clone_and_deploy
}

main "$@"
