#!/bin/bash
#
# Tested with Python 3.6.10
#

python3 -m venv .venv

. .venv/bin/activate

pip install --upgrade pip
pip install pyserial==3.4 six==1.14.0 tornado==4.5.2 pymodbus==2.4.0

python3 test.py
