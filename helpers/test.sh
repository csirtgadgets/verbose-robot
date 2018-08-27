#!/bin/bash

set -e

echo 'giving things a chance to settle...'
sleep 10

echo 'testing connectivity'
curl -v -k https://localhost
sudo -E -u cif cif -d -p

echo 'testing query'
sudo -E -u cif cif  --search example.com

echo 'waiting...'
sleep 5

echo 'testing query'
sudo -E -u cif cif --search example.com

echo 'waiting...'
sleep 5

sudo -E -u cif cif --itype ipv4 --tags saerch

sudo -E -u cif cif -q 93.184.216.34

echo 'waiting...'
sleep 5

sudo -E -u cif cif -q 93.184.216.34

sudo -E -u cif csirtg-fm -r /etc/cif/rules/default/openphish.yml -d --remember --client cif --limit 100 --skip-invalid
sudo -E -u cif csirtg-fm -r /etc/cif/rules/default/openphish.yml -d --remember --client cif --config /etc/cif/csirtg-fm.yml --limit 100 --skip-invalid
sudo -E -u cif csirtg-fm -r /etc/cif/rules/default/csirtg.yml -f darknet -d --remember --client cif --limit 100 --skip-invalid
sudo -E -u cif csirtg-fm -r /etc/cif/rules/default/csirtg.yml -f uce-urls -d --remember --client cif --limit 100 --skip-invalid

echo 'waiting 30s... let hunter do their thing...'
sleep 30

sudo -E -u cif cif --provider csirtg.io

sudo -E -u cif cif --provider openphish.com

sudo -E -u cif cif --itype ipv4 --feed --tags scanner

sudo -E -u cif cif --itype ipv4 --feed --tags scanner --days 17

sudo -E -u cif cif --itype fqdn --feed --tags search

sudo -E -u cif cif --itype url --feed --tags uce

sudo -E -u cif cif --itype url --feed --tags phishing

sudo -E -u cif cif --itype ipv4 --feed --tags phishing --confidence 2

sudo -E -u cif cif --itype ipv4 --confidence 1,6 --no-feed -d

sudo -E -u cif cif --itype fqdn --confidence 1,6 --no-feed -d

echo
echo
echo "testing tokens"

sudo -E -u cif cif-tokens
sudo -E -u cif cif-tokens --user test-write --write --create
sudo -E -u cif cif-tokens --user test-read --read --create
sudo -E -u cif cif-tokens --user test-read-write --write --create --read
sudo -E -u cif CIFSDK_CLIENT_HTTP_TRACE=1 cif-tokens -d
