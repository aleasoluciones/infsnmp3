#!/bin/bash
set -e

nosetests $INTEGRATION_TESTS -s --logging-clear-handlers --processes=16 --process-timeout=50 --with-yanc
NOSE_RETCODE=$?

exit $NOSE_RETCODE
