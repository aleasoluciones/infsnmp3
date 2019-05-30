#!/bin/bash
set -e

mamba -f progress regression_specs/
RETCODE=$?

exit $RETCODE
