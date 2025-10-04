#!/usr/bin/env bash

: <<'BAMBOO_CONFIG_DOC'

Task type:
  SSH Task

Task description:
  Remove temporary testing directory

Hosts:
  ${bamboo.HOST}

Authentication type:
  Username and password

Username:
  ${bamboo.USER}

Password:
  ${bamboo.PASSWORD}

SSH command:
rm -rfv ${bamboo.inject.TESTING_DEPLOYMENT_DIRECTORY}

BAMBOO_CONFIG_DOC

TESTING_DEPLOYMENT_DIRECTORY="$1"

rm -rfv "${TESTING_DEPLOYMENT_DIRECTORY}"
