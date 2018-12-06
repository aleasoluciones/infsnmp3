#!/bin/bash

python setup.py develop
pip install pip --upgrade
pip install -r requirements.txt --upgrade
pip install -r requirements-dev.txt --upgrade