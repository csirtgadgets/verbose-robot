#!/bin/bash

set -e

head -n 25000 /dev/urandom | openssl dgst -sha256
