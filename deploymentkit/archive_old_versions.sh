#!/bin/bash

ARCHIVE_DB=$1
DB=/var/lib/cif/cifv4.db

if [ -d /usr/local/lib/python3.6/dist-packages ]; then
    echo 'removing old cif|cifsdk files..'
    rm -rf `find /usr | egrep "(verbose-robot-)+"`

    if [ "$ARCHIVE_DB" == "1" ]; then
      if [ -f "$DB" ]; then
        echo "archiving old cif db"
        mv "$DB" "$DB.old"
      fi
    fi
fi