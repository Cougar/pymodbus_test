#!/bin/bash
#
# Tested with Python 3.6.10
#

python3 -m venv .venv

. .venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt

python3 test.py

deactivate
