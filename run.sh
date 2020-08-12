#!/bin/bash
#
# Tested with Python 3.6.10
#

python3 -m venv .venv

. .venv/bin/activate

pip install pyserial==3.4 six==1.14.0 tornado==4.5.2

# clone pymodbus 2.3.0 and patch its name to pymodbus230
test -d pymodbus_riptideio || git clone https://github.com/riptideio/pymodbus pymodbus_riptideio
cp -r pymodbus_riptideio/pymodbus pymodbus230
find pymodbus230/ -name '*.py' -print0 | xargs -0 -n 1 sed -i 's/\(from\|import\) pymodbus\./\1 pymodbus230./'

# clone pymodbus 1.2.0 python3 branch and patch its name to pymodbus120
test -d pymodbus_droid4control || git clone --branch python3 https://github.com/droid4control/pymodbus pymodbus_droid4control
cp -r pymodbus_droid4control/pymodbus pymodbus120
find pymodbus120/ -name '*.py' -print0 | xargs -0 -n 1 sed -i 's/\(from\|import\) pymodbus\./\1 pymodbus120./'

# clone pymodbus_async for 1.2.0 and patch its name to pymodbus120_async
test -d pymodbus_async || git clone https://github.com/droid4control/pymodbus_async pymodbus_async
cp -r pymodbus_async pymodbus120_async
find pymodbus120_async/ -name '*.py' -print0 | xargs -0 -n 1 sed -i 's/\(from\|import\) pymodbus\./\1 pymodbus120./'

python3 test.py
