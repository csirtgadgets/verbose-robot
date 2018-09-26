#!/bin/bash

export CIF_BOOTSTRAP_TEST=1
export CIF_ANSIBLE_SDIST=/vagrant
export CIF_HUNTER_THREADS=2
export CIF_HUNTER_ADVANCED=1

if [ "${CIF_TOKEN}" == "" ]; then
  CIF_TOKEN=`helpers/token.sh`
fi

export CIF_TOKEN="${CIF_TOKEN}"

time vagrant up
