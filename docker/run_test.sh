#!/bin/bash

CIF_TOKEN=`head -n 25000 /dev/urandom | openssl dgst -sha256`

echo "CIF Token Generated:"
echo ""
echo "${CIF_TOKEN}"
echo ""

C=$(docker run -e CIF_DOCKER_TEST=1 -e CIF_TOKEN="${CIF_TOKEN}" -e CIF_HUNTER_ADVANCED=1 -e CIF_HUNTER_THREADS=2 -e CIF_HUNTER_TRACE=1 -it -d -p 5000:5000 --name verbose-robot --memory 2g --memory-swap 4g csirtgadgets/verbose-robot)

docker exec -it $C /home/cif/test.sh
