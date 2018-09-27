#!/bin/bash

PID=`ps aux | grep supervisord | grep -v grep | awk -F ' ' '{print $2}'`

kill -HUP $PID