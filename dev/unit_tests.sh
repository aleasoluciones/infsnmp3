#!/bin/bash
set -e

mamba -f progress specs/
RETCODE=$?

exit $RETCODE
