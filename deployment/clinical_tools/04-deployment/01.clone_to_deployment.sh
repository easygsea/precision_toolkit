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
    apptainer build "${APPTAINER_IMAGE}" apptainer.def
    sed -i "s~container = \"quay.io/easygsea/clinical_tools:latest\"~container = \"${PRODUCTION_ROOT}/clinical_tools/${version}/${APPTAINER_IMAGE}\"~" nextflow.config
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
    BRANCH_NAME="$1"  \
    REPOSITORY_URL="$2"  \
    PRODUCTION_ROOT="$3" \
    APPTAINER_IMAGE="$4" \
    PYTHON_EXECUTABLE="$5"
  echo "Deploying branch '${BRANCH_NAME}'..."
  clone_and_deploy
}

main "$@"
