Run Python docker container:

docker run -ti --device /dev/ttyUSB2 python:3.6.2 bash

Run script on contianer:

git clone https://github.com/Cougar/pymodbus_test.git
cd pymodbus_test
./run.sh
