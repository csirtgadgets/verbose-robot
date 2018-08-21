#!/bin/bash

set -e 

kill -KILL `ps aux | grep python3 | grep 'cifv4' | awk -F ' ' '{print $2}'`
