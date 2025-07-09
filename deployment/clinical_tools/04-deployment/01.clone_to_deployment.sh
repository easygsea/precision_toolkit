#!/usr/bin/env bash

####      BAMBOO INTERFACE CONFIGURATION       ####
###    Hosts: dragen02                         ####
###################################################

set -euxo pipefail

export LD_LIBRARY_PATH="${LD_LIBRARY_PATH:-}:/projects/clingenetics/software/tools/python/Python-3.11.7/lib"

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
    rm -rf tmp_dir/
    cd "${PRODUCTION_ROOT}/clinical_tools/${version}"
    apptainer build clinical_tools.sif apptainer.def
  fi

}

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
    PRODUCTION_ROOT="$3"
  echo "Deploying branch '${BRANCH_NAME}'..."
  clone_and_deploy
}

main "$@"
