#!/bin/bash

set -e

echo 'installing ansible...'
sudo pip install 'cryptography>=1.5' 'ansible>=2.6,<2.7'

# test to see if we've linked this in development
# install by default in production
if [ ! -e roles/csirtgadgets.cifv4 ]; then
  ansible-galaxy install csirtgadgets.cifv4,0.0a2
fi

echo 'running ansible...'
ansible-playbook -i "localhost," -c local site.yml -vv
