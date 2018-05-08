#!/bin/bash
docker stop verbose-robot
docker rm verbose-robot
docker build --rm=true --force-rm=true -t csirtgadgets/verbose-robot .