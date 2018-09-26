#!/bin/bash

set -e

export CIF_ANSIBLE_SDIST=$CIF_ANSIBLE_SDIST
export CIF_HUNTER_THREADS=$CIF_HUNTER_THREADS
export CIF_HUNTER_ADVANCED=$CIF_HUNTER_ADVANCED

echo 'installing the basics'
sudo apt-get update && apt-get install -y build-essential python-dev python2.7 python-pip python-dev aptitude \
    python-pip libffi-dev libssl-dev software-properties-common

bash ../ansible.sh

if [[ "$CIF_BOOTSTRAP_TEST" -eq '1' ]]; then
    bash ../test.sh
fi
