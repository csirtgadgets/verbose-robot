#!/bin/bash

set -e

VERSION="$1"

docker tag csirtgadgets/verbose-robot:latest csirtgadgets/verbose-robot:${VERSION}
docker push csirtgadgets/verbose-robot:latest
docker push csirtgadgets/verbose-robot:${VERSION}
