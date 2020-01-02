#!/bin/bash

set -e

#docker stop verbose-robot
#docker rm verbose-robot
#docker image remove csirtgadgets/verbose-robot

rm -rf dist/*
python3 setup.py sdist

docker build --rm=true --force-rm=true -t csirtgadgets/verbose-robot:latest -f docker/Dockerfile .
