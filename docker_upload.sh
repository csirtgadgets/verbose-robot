#!/bin/bash

set -e

VERSION=4.0.0a3

docker tag csirtgadgets/verbose-robot:latest csirtgadgets/verbose-robot:${VERSION}
docker push csirtgadgets/verbose-robot:latest
docker push csirtgadgets/verbose-robot:${VERSION}
