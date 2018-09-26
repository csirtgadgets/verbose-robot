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

C=$(docker run -e CIF_TOKEN="${CIF_TOKEN}" -it -d -p 5000:5000 --name verbose-robot --memory 2g --memory-swap 4g csirtgadgets/verbose-robot)

docker exec -it verbose-robot apt-get install htop tcpdump curl vim mlocate git

echo "Getting a shell into the container..."
docker exec -it $C /bin/bash
