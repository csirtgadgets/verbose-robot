#!/bin/bash

set -e

export CIF_DATA_PATH=/var/lib/cif

#cif-store --token-create-smrt --config /home/cif/smrt.yml
cif-store --token-create-hunter --config-path /home/cif/router.yml

chown cif:cif /home/cif/router.yml