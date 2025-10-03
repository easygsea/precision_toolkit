#!/usr/bin/env bash

: <<'BAMBOO_CONFIG_DOC'

Task type:
  SSH Task

Hosts:
  ${bamboo.HOST}

Authentication type:
  Username and password

Username:
  ${bamboo.USER}

Password:
  ${bamboo.PASSWORD}

BAMBOO_CONFIG_DOC

TESTING_DEPLOYMENT_DIRECTORY="$1"

rm -rfv "${TESTING_DEPLOYMENT_DIRECTORY}"
