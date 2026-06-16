#!/usr/bin/env bash

: <<'BAMBOO_CONFIG_DOC'

Task type:
  SSH Task

Task description:
  Cleanup Images

Hosts:
  ${bamboo.HOST_CONTAINER}

Authentication type:
  Username and password

Username:
  ${bamboo.USER}

Password:
  ${bamboo.PASSWORD_CONTAINER}

SSH command:
  Copy and paste the full code from this script into the Bamboo interface.

BAMBOO_CONFIG_DOC

docker images --format '{{.Repository}}:{{.Tag}}' | grep 'precision_toolkit' | xargs docker rmi
rm -f "${bamboo.BASE_IMAGE_ROOT}"/*.sif
