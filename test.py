import functools
from tornado.ioloop import IOLoop

from pymodbus230.client.asynchronous import schedulers
from pymodbus230.client.asynchronous.tcp import AsyncModbusTCPClient

from pymodbus120_async.client import AsyncModbusSerialClient, AsyncErrorResponse
from pymodbus120.exceptions import ConnectionException, ModbusIOException
from pymodbus120.register_read_message import ReadHoldingRegistersResponse

import logging
FORMAT = ('%(asctime)-15s %(threadName)-15s'
          ' %(levelname)-8s %(module)-15s:%(lineno)-8s %(message)s')
logging.basicConfig(format=FORMAT)
log = logging.getLogger()
log.setLevel(logging.WARNING)

UNIT = 0x01

class CommonModBusRunner:
    def __init__(self, client_name, ModbusClient, register_list, timeout=3, **kwargs):
        self.client_name = client_name
        self._client = None
        self._protocol = None
        self._register = self._get_next_register(register_list)
        self._timeout = timeout
        self._timeout_callback = None

    def run(self):
        self._send_request()

    def _get_next_register(self, register_list):
        while True:
            for register in register_list:
                yield register

    def _on_timeout(self):
        log.warning("%s: TIMEOUT reading registers (%s, %s)", self, self._client, self._protocol)
        self._send_request()

    def _print(self, register, value):
        if hasattr(value, "bits"):
            t = value.bits
        elif hasattr(value, "registers"):
            t = value.registers
        else:
            t = value
        log.info("Printing %d: -- {}".format(t), register)
        print(f"{self!s:8}: {register} = {t}")

    def __str__(self):
        return str(self.client_name)

    def __del__(self):
        log.debug('__del__()')
        if self._client:
            self._client.close()
        if self._protocol:
            self._protocol.stop()


class ModBusRunner(CommonModBusRunner):
    def __init__(self, client_name, ModbusClient, register_list, timeout=3, **kwargs):
        super().__init__(client_name, ModbusClient, register_list, timeout, **kwargs)
        self._protocol, future = ModbusClient(schedulers.IO_LOOP, **kwargs)
        future.add_done_callback(self._on_connect)

    def _send_request(self):
        register = next(self._register)
        log.debug('_send_request(%d)', register)
        self._timeout_callback = IOLoop.current().call_later(self._timeout, self._on_timeout)
        log.debug('+++ timeout set: %s', self._timeout_callback)
        try:
            self._client.read_holding_registers(register, 1, unit=UNIT).add_done_callback(functools.partial(self._on_done, register))
        except tornado.iostream.StreamClosedError as ex:
            log.error(ex)

    def _on_connect(self, future):
        log.debug('_on_connect()')
        log.info("Client connected")
        exp = future.exception()
        if exp:
            log.error(exp)
        else:
            self._client = future.result()
            self.run()

    def _on_done(self, register, f):
        log.debug('_on_done(%d)', register)
        exc = f.exception()
        if exc:
            log.debug(exc)
        else:
            self._print(register, f.result())
        log.debug('--- remove_timeout()')
        IOLoop.current().remove_timeout(self._timeout_callback)
        self._send_request()


class ModBusRunner120(CommonModBusRunner):
    def __init__(self, client_name, ModbusClient, register_list, timeout=3, **kwargs):
        super().__init__(client_name, ModbusClient, register_list, timeout, **kwargs)
        self._client = ModbusClient(**kwargs)
        self.run()

    def _send_request(self):
        register = next(self._register)
        log.debug('_send_request(%d)', register)
        self._timeout_callback = IOLoop.current().call_later(self._timeout, self._on_timeout)
        log.debug('+++ timeout set: %s', self._timeout_callback)
        try:
            self._client.read_holding_registers(register, 1, unit=UNIT).addCallback(functools.partial(self._on_done, register))
        except tornado.iostream.StreamClosedError as ex:
            log.error(ex)

    def _on_done(self, register, f):
        log.debug('_on_done(%d)', register)
        if isinstance(f, ReadHoldingRegistersResponse):
            self._print(register, f.registers)
        elif isinstance(f, AsyncErrorResponse):
            log.error("AsyncErrorResponse error_code = %d", f.error_code)
        else:
            log.error("Unknown error: register: %s, f: %s", register, f)
        log.debug('--- remove_timeout()')
        IOLoop.current().remove_timeout(self._timeout_callback)
        self._send_request()


if __name__ == "__main__":
    IOLoop.configure('tornado.platform.epoll.EPollIOLoop')
#   ModBusRunner('local', AsyncModbusTCPClient, [8, 10], host='127.0.0.1', port=5020)
    ModBusRunner('tcp', AsyncModbusTCPClient, [149, 150, 257, 498, 499], host='192.168.1.151', port=502)
    ModBusRunner120('serial', AsyncModbusSerialClient, [149, 150, 257, 498, 499], method='rtu', port='/dev/ttyUSB2', baudrate=19200, parity='E')
    IOLoop.instance().start()
