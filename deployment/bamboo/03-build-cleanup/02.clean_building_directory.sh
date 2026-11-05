#!/usr/bin/env bash

: <<'BAMBOO_CONFIG_DOC'

Task type:
  SSH Task

Task description:
  Remove temporary image build directory

Hosts:
  ${bamboo.HOST_CONTAINER}

Authentication type:
  Username and password

Username:
  ${bamboo.USER}

Password:
  ${bamboo.PASSWORD_CONTAINER}

SSH command:
rm -rfv ${bamboo.inject.BUILDING_DEPLOYMENT_DIRECTORY}

BAMBOO_CONFIG_DOC

BUILDING_DEPLOYMENT_DIRECTORY="$1"

rm -rfv "${BUILDING_DEPLOYMENT_DIRECTORY}"
