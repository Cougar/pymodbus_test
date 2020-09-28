import functools

import serial

from tornado.ioloop import IOLoop
from tornado.iostream import StreamClosedError
import tornado.web
import time

from pymodbus.client.asynchronous import schedulers

from pymodbus.client.asynchronous.tcp import AsyncModbusTCPClient
#from pymodbus.client.asynchronous.serial import AsyncModbusSerialClient
from pymodbus_async.client.asynchronous.serial import AsyncModbusSerialClient

from pymodbus.exceptions import ConnectionException, ModbusIOException
from pymodbus.register_read_message import ReadHoldingRegistersResponse
from pymodbus.pdu import ExceptionResponse

import logging
FORMAT = ('%(asctime)-15s %(levelname)-8s %(threadName)-15s'
        '%(pathname)s:%(lineno)d %(module)s.%(funcName)s(): %(message)s')
logging.basicConfig(format=FORMAT)
log = logging.getLogger()
log.setLevel(logging.DEBUG)
log.setLevel(logging.ERROR)

UNIT = 0x01

def stats_inc(f):
    def wrapper(self, *args):
        self._stats[f.__name__] = self._stats.get(f.__name__, 0) + 1
        return f(self, *args)
    return wrapper

class ModBusRunner:
    def __init__(self, client_name, ModbusClient, register_list, timeout=3, **kwargs):
        self._stats = {}
        self.client_name = client_name
        self._ModbusClient = ModbusClient
        self._kwargs = kwargs
        self._client = None
        self._protocol = None
        self._register = self._get_next_register(register_list)
        self._timeout = timeout
        self._timeout_callback = None
        self._connect()

    def _connect(self):
        self._event_loop, self._future = self._ModbusClient(schedulers.IO_LOOP, **self._kwargs)
        self._future.add_done_callback(self._on_connect)

    def run(self):
        self._send_request()

    def _get_next_register(self, register_list):
        while True:
            for register in register_list:
                yield register

    @stats_inc
    def _send_request(self):
        register = next(self._register)
        log.debug('_send_request(%d)', register)
        try:
            self._client.read_holding_registers(register, 1, unit=UNIT).add_done_callback(functools.partial(self._on_done, register))
        except StreamClosedError as ex:
            log.error(ex)
            self._connect()
        except Exception as ex:
            log.error(ex)
        self._timeout_callback = IOLoop.current().call_later(self._timeout, self._on_timeout)
        log.debug('+++ timeout set: %s', self._timeout_callback)

    def _on_connect(self, future):
        log.debug('_on_connect()')
        log.info("Client connected")
        try:
            res = future.result()
            log.error("RES: %s", res)
        except serial.serialutil.SerialException as ex:
            log.error(ex)
            return
#       except FileNotFoundError as ex:
#           log.error(ex)
#           return
        except Exception as ex:
            log.exception(ex)
        try:
            exp = future.exception()
            if exp:
                log.exception(exp)
            else:
                self._client = future.result()
                self.run()
        except Exception as ex:
            log.exception(ex)

    @stats_inc
    def _on_done(self, register, f):
        IOLoop.current().remove_timeout(self._timeout_callback)
        log.debug('_on_done(%d)', register)
        exc = f.exception()
        if exc:
            log.error(exc)
#           return
        else:
            self._print(register, f.result())
        self._send_request()

    @stats_inc
    def _on_timeout(self):
        log.warning("%s: TIMEOUT reading registers (%s, %s)", self, self._client, self._protocol)
        self._send_request()

    def _print(self, register, value):
        if isinstance(value, ExceptionResponse):
            log.error("ExceptionResponse: %s (%d)", value, register)
            return
        if hasattr(value, "bits"):
            t = value.bits
        elif hasattr(value, "registers"):
            t = value.registers
        else:
            t = value
        log.info("Printing %d: -- {}".format(t), register)
        print(f"{self.client_name!s:8}: {register} = {t}")

    def __str__(self):
        strings = []
        strings.append(str(self.client_name)+':')
        strings.append('-----')
        for k, v in self._stats.items():
            strings.append(f"{k}: {v}")
        return '\n'.join(strings)+'\n'

    def __del__(self):
        log.debug('__del__()')
        if self._client:
            self._client.close()
        if self._protocol:
            self._protocol.stop()

class WebHandler(tornado.web.RequestHandler):
    def __init__(self, *args, **kwargs):
        self._runners = kwargs.pop('runners')
        self.start_time = kwargs.pop('start')
        super().__init__(*args, **kwargs)

    def get(self, *args, **kwargs):
        self.set_header("Content-Type", "text/plain; charset=utf-8")
        for runner in self._runners:
            self.write(str(runners[runner]))
            self.write('\n\n')
        time_elapsed = int(time.time() - self.start_time)
        self.write(f"start time: {self.start_time}\n")
        self.write(f"time elapsed: {time_elapsed} sec\n")
        self.finish()

if __name__ == "__main__":
    runners = {}
    IOLoop.configure('tornado.platform.epoll.EPollIOLoop')
#   ModBusRunner('local', AsyncModbusTCPClient, [8, 10], host='127.0.0.1', port=5020)
    runners['tcp'] = ModBusRunner('tcp', AsyncModbusTCPClient, [149, 150, 257, 498, 499, 999], host='10.0.0.13', port=502, timeout=1)
    runners['serial'] = ModBusRunner('serial', AsyncModbusSerialClient, [149, 150, 257, 498, 499, 999], method='rtu', port='/dev/ttyUSB2', baudrate=19200, parity='E', timeout=1)

    app = tornado.web.Application([
        (r'/.*', WebHandler, {"start": int(time.time()), "runners": runners})
        ])
    app.listen(8000)
    IOLoop.instance().start()
