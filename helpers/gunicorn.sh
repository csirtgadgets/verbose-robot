#!/bin/bash

gunicorn --worker-class gevent --log-level DEBUG cif.httpd.app:app -b localhost:5000 -k flask_sockets.worker -w 2 --timeout 300 --graceful-timeout 5
