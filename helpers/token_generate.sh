#!/bin/bash

set -e

CIF_TOKEN=`head -n 25000 /dev/urandom | openssl dgst -sha256 | awk -F ' ' '{print $2}'`
if [ "${CIF_TOKEN}" == "" ]; then
  export CIF_TOKEN=`head -n 25000 /dev/urandom | openssl dgst -sha256`
fi

echo ${CIF_TOKEN}