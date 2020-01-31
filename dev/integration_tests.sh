#!/bin/bash
set -e

IS_SNMPSIM_CONTAINER_RUNNING=$(docker inspect -f '{{.State.Running}}' infsnmp3_devdocker_snmpsim_1)

if [[ $IS_SNMPSIM_CONTAINER_RUNNING == "false" ]]; then
    echo "Please start the dev dependencies before running the integration tests."
    exit 1
fi

nosetests $INTEGRATION_TESTS -s --logging-clear-handlers --processes=16 --process-timeout=50 --with-yanc
NOSE_RETCODE=$?

exit $NOSE_RETCODE
