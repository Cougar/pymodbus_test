Run Python docker container:

docker run -ti --device /dev/ttyUSB2 python:3.6.2 bash

Run script on contianer:

git clone https://github.com/Cougar/pymodbus_test.git --recurse-submodules --branch=pymodbus-2.5.0rc2
cd pymodbus_test
./run.sh
