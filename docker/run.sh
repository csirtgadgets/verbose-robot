#!/bin/bash

set -e

if [ "${CIF_TOKEN}" == "" ]; then
    CIF_TOKEN=`head -n 25000 /dev/urandom | openssl dgst -sha256`
    echo "CIF_TOKEN Generated"
else
    echo "Using existing ENV CIF_TOKEN"
fi

echo ""
echo "${CIF_TOKEN}"
echo ""

docker run \
  -e CIF_TOKEN="${CIF_TOKEN}" \
  -e MAXMIND_USER_ID="${MAXMIND_USER_ID}" \
  -e MAXMIND_LICENSE_KEY="${MAXMIND_LICENSE_KEY}" \
  -it -p 5000:5000 --name verbose-robot --memory 2g --memory-swap 4g csirtgadgets/verbose-robot:latest