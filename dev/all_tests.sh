#!/bin/bash

dev/unit_tests.sh &&\
dev/regression_tests.sh &&\
dev/integration_tests.sh
