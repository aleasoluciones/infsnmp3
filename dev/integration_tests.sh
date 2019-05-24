#!/bin/bash
set -e

trap "docker stop -t 0 snmpsimd; docker rm snmpsimd; exit" SIGHUP SIGINT SIGTERM ERR
docker build -t snmpsimd .
docker run -d --name snmpsimd -v /etc/localtime:/etc/localtime:ro -v $(pwd)/integration_tests/snmpsim/simulated_data/:/simulated_data -p 1161:1161/udp snmpsimd
sleep 5
nosetests $INTEGRATION_TESTS -s --logging-clear-handlers --processes=16 --process-timeout=50 --with-yanc
NOSE_RETCODE=$?
docker stop -t 0 snmpsimd
docker rm snmpsimd
exit $NOSE_RETCODE
