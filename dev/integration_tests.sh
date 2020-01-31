#!/bin/bash
set -e

trap "docker stop -t 0 snmpsimd; docker rm snmpsimd; exit" SIGHUP SIGINT SIGTERM ERR
docker-compose -f dev/infsnmp3_devdocker/docker-compose.yml up -d
sleep 5
nosetests $INTEGRATION_TESTS -s --logging-clear-handlers --processes=16 --process-timeout=50 --with-yanc
NOSE_RETCODE=$?
docker-compose -f dev/infsnmp3_devdocker/docker-compose.yml down
exit $NOSE_RETCODE
