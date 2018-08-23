#!/bin/bash

CIF_TOKEN=`head -n 25000 /dev/urandom | openssl dgst -sha256`

echo "CIF Token Generated:"
echo ""
echo "${CIF_TOKEN}"
echo ""

C=$(docker run -e CIF_TOKEN="${CIF_TOKEN}" -it -d -p 5000:5000 --name verbose-robot --memory 2g --memory-swap 4g csirtgadgets/verbose-robot)

echo "Getting a shell into the container..."
docker exec -it $C /bin/bash
