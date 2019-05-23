#!/bin/bash

set -e

#docker rm -f verbose-robot
docker build --rm=true --force-rm=true -t csirtgadgets/verbose-robot .
