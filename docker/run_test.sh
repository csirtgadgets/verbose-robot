#!/bin/bash

set -e

DOCKER_CONFIGS="$(pwd)"

if [[ "${CIF_TOKEN}" == "" ]]; then
    CIF_TOKEN=`head -n 25000 /dev/urandom | openssl dgst -sha256`
    echo "CIF_TOKEN Generated"
else
    echo "Using existing ENV CIF_TOKEN"
fi

echo ""
echo "${CIF_TOKEN}"
echo ""

C=$(docker run -e CSIRTG_TOKEN="${CSIRTG_TOKEN}" -e CIF_TOKEN="${CIF_TOKEN}" -e CIF_HUNTER_ADVANCED=1 -e CIF_HUNTER_THREADS=2 -e CIF_HUNTER_TRACE=1 -it -d -p 5000:5000 --name verbose-robot --memory 2g --memory-swap 4g -v "${DOCKER_CONFIGS}"/geo/:/var/lib/GeoIP/ csirtgadgets/verbose-robot)

bash docker/test.sh

if [[ -z ${NO_AUTO_REMOVE} ]]; then
    echo 'shutting down in 90s'
    sleep 90
    docker rm -f verbose-robot
else
    echo "done"
fi
