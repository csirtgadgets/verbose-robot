#!/bin/bash

MACHINE_NAME=verbose-robot

set -e

echo 'giving things a chance to settle...'
sleep 30

echo 'testing connectivity'
docker exec -it verbose-robot cif -d -p

echo 'testing query'
docker exec -it verbose-robot cif --search example.com

echo 'waiting...'
sleep 5

echo 'testing query'
docker exec -it verbose-robot cif --search example.com

echo 'waiting...'
sleep 5

docker exec -it verbose-robot cif --itype ipv4 --tags saerch

docker exec -it verbose-robot cif -q 93.184.216.34

echo 'waiting...'
sleep 5

docker exec -it verbose-robot cif -q 93.184.216.34

declare -a CMDS=(
    "-r /etc/cif/rules/default/openphish.yml -d --client cif --limit 100 --skip-invalid"
    "-r /etc/cif/rules/default/openphish.yml -d --client cif --limit 100 --skip-invalid"
    "-r /etc/cif/rules/default/csirtg.yml -f darknet -d --remember --client cif --limit 100 --skip-invalid"
    "-r /etc/cif/rules/default/csirtg.yml -f uce-urls -d --remember --client cif --limit 100 --skip-invalid"
)

for i in "${CMDS[@]}"; do
    echo "$i"
    docker exec -it ${MACHINE_NAME} csirtg-fm ${i}
done

echo 'waiting 30s... let hunter do their thing...'
sleep 30

declare -a CMDS=(
    "--provider csirtg.io --no-feed --itype url"
    "--provider openphish.com --itype url"
    "--itype ipv4 --tags scanner"
    "--itype ipv4 --tags scanner --days 17"
    #"--itype fqdn --tags search"
    "--itype url --tags uce"
    "--itype url --tags phishing"
    "--itype ipv4 --tags phishing --confidence 2"
    "--itype ipv4 --confidence 1,4 --no-feed -d"
    "--itype fqdn --confidence 1,4 --no-feed -d"
    "--itype fqdn --probability 68,99 --no-feed -d"
    "--indicator csirtg.io --tags malware --submit --confidence 4"
    "-nq csirtg.io"
)

for i in "${CMDS[@]}"; do
    echo "$i"
    docker exec -it ${MACHINE_NAME} cif ${i}
done


echo
echo
echo "testing tokens"

declare -a CMDS=(
    "-d"
    "--user test-write --write --create"
    "--user test-read --read --create"
    "--user test-read-write --write --create --read"
    "-d"
)

for i in "${CMDS[@]}"; do
    echo "$i"
    docker exec -e CIFSDK_CLIENT_HTTP_TRACE=1 -it ${MACHINE_NAME} cif-tokens ${i}
done