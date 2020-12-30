Start Python docker container (optional):

```
docker run -ti --device /dev/ttyUSB2 -p 8000:8000 python:3.6.2 bash
```

Run script (in contianer):

```
git clone https://github.com/Cougar/pymodbus_test.git --branch=pymodbus-2.5.0rc2
cd pymodbus_test
./run.sh
```

You can see stats if you open http://127.0.0.1:8000/

Note: if using different serial port, change it in docker command line and in the end of `test.py` script
