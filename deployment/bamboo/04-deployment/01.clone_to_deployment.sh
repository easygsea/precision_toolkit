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
  git clone --branch "${BRANCH_NAME}" "${REPOSITORY_URL}" tmp_dir
  cd tmp_dir
  version=$(get_version)
  if [ -d "${version}" ]; then
    echo "The version has already been deployed"
    exit 1
  else
    cd ..
    mkdir -p "${DEPLOYMENT_ROOT}/clinical_tools/${version}"
    mv tmp_dir/* "${DEPLOYMENT_ROOT}/clinical_tools/${version}/"
    cd "${DEPLOYMENT_ROOT}/clinical_tools/${version}"
    "${PYTHON_EXECUTABLE}" -m venv venv
    source venv/bin/activate
    pip install --upgrade pip wheel
    pip install poetry==2.0.1
    poetry install --with dev
    cp -v "${IMAGE_STORE_ROOT}/${version}/${IMAGE_NAME}" ./"${NEW_IMAGE_NAME}"
    rm -rfv "${IMAGE_STORE_ROOT}/${version}"
    sed -i "s~container = \"quay.io/easygsea/clinical_tools:latest\"~container = \"${DEPLOYMENT_ROOT}/clinical_tools/${version}/${NEW_IMAGE_NAME}\"~" nextflow.config
    cd "${DEPLOYMENT_ROOT}/clinical_tools"
    if [[ "${BRANCH_NAME}" == "main" ]]; then
      rm -rf main
      mkdir main
      cp -r "${version}"/* main/
    fi
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
    BRANCH_NAME="${1:-${bamboo.planRepository.branchName}}"  \
    REPOSITORY_URL="${2:-${bamboo.planRepository.repositoryUrl}}"  \
    DEPLOYMENT_ROOT="${3:-${bamboo.DEPLOYMENT_ROOT}}" \
    IMAGE_NAME="${4:-${bamboo.inject.IMAGE_NAME}}" \
    PYTHON_EXECUTABLE="${5:-${bamboo.PYTHON_EXECUTABLE}}" \
    IMAGE_STORE_ROOT="${6:-${bamboo.TEMPORARY_IMAGE_ROOT}}" \
    NEW_IMAGE_NAME="${7:-${bamboo.APPTAINER_IMAGE_NAME}}"

  # If NEW_IMAGE_NAME does not end with .sif, add the .sif suffix
  if [[ "${NEW_IMAGE_NAME}" != *.sif ]]; then
    NEW_IMAGE_NAME="${NEW_IMAGE_NAME}.sif"
  fi

  echo "Deploying branch '${BRANCH_NAME}'..."
  clone_and_deploy
}

main "$@"
