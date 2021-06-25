"""
coax.serial_interface
~~~~~~~~~~~~~~~~~~~~~
"""

import time
import os
import struct
from copy import copy
from contextlib import contextmanager
from serial import Serial
from sliplib import SlipWrapper, ProtocolError

from .interface import Interface
from .exceptions import InterfaceError, InterfaceTimeout, ReceiveError, ReceiveTimeout

class SerialInterface(Interface):
    def __init__(self, serial):
        if serial is None:
            raise ValueError('Serial port is required')

        self.serial = serial

        self.slip_serial = SlipSerial(self.serial)

        self.legacy_firmware_detected = None
        self.legacy_firmware_version = None

    def reset(self):
        original_serial_timeout = self.serial.timeout

        self.serial.timeout = 5

        self.serial.reset_input_buffer()

        self._write_message(bytes([0x01]))

        try:
            message = self._read_message()
        finally:
            self.serial.timeout = original_serial_timeout

            self.serial.reset_input_buffer()

        if message[0] != 0x01:
            raise _convert_error(message)

        if message[1:] == b'\x32\x70':
            self.legacy_firmware_detected = False
            self.legacy_firmware_version = None
        elif len(message) == 4:
            (major, minor, patch) = struct.unpack('BBB', message[1:])

            self.legacy_firmware_detected = True
            self.legacy_firmware_version = '{}.{}.{}'.format(major, minor, patch)
        else:
            raise InterfaceError(f'Invalid reset response: {message}')

    def transmit_receive(self, transmit_words, transmit_repeat_count=None,
                         transmit_repeat_offset=1, receive_length=None,
                         receive_timeout=None):
        timeout_milliseconds = self._calculate_timeout_milliseconds(receive_timeout)

        message = bytes([0x06])

        message += _pack_transmit_header(transmit_repeat_count, transmit_repeat_offset)
        message += _pack_transmit_data(transmit_words)
        message += _pack_receive_header(receive_length, timeout_milliseconds)

        self._write_message(message)

        message = self._read_message()

        if message[0] != 0x01:
            raise _convert_error(message)

        return _unpack_receive_data(message[1:])

    def enter_dfu_mode(self):
        message = bytes([0xf2])

        self._write_message(message)

        message = self._read_message()

        if message[0] != 0x01:
            raise _convert_error(message)

    def _calculate_timeout_milliseconds(self, timeout):
        milliseconds = 0

        if timeout:
            if self.serial.timeout and timeout > self.serial.timeout:
                raise ValueError('Timeout cannot be greater than serial timeout')

            milliseconds = int(timeout * 1000)

        return milliseconds

    def _read_message(self):
        try:
            message = self.slip_serial.recv_msg()
        except ProtocolError:
            raise InterfaceError('SLIP protocol error')

        if len(message) < 4:
            raise InterfaceError(f'Invalid response message: {message}')

        (length,) = struct.unpack('>H', message[:2])

        if length != len(message) - 4:
            raise InterfaceError('Response message length mismatch')

        if length < 1:
            raise InterfaceError('Empty response message')

        return message[2:-2]

    def _write_message(self, message):
        self.slip_serial.send_msg(struct.pack('>H', len(message)) + message +
                                  struct.pack('>H', 0))

@contextmanager
def open_serial_interface(serial_port, reset=True):
    with Serial(serial_port, 115200) as serial:
        serial.reset_input_buffer()
        serial.reset_output_buffer()

        # Allow the interface firmware time to start, this is only required for the
        # original Arduino Mega based interface.
        if 'COAX_FAST_START' not in os.environ:
            time.sleep(3)

        interface = SerialInterface(serial)

        if reset:
            interface.reset()

        yield interface

def _pack_transmit_header(repeat_count, repeat_offset):
    repeat = ((repeat_offset << 15) | repeat_count) if repeat_count else 0

    return struct.pack('>H', repeat)

def _pack_transmit_data(words):
    bytes_ = bytearray()

    for word in words:
        bytes_ += struct.pack('<H', word)

    return bytes_

def _pack_receive_header(length, timeout_milliseconds):
    return struct.pack('>HH', length or 0, timeout_milliseconds)

def _unpack_receive_data(bytes_):
    return [(hi << 8) | lo for (lo, hi) in zip(bytes_[::2], bytes_[1::2])]

ERROR_MAP = {
    1: InterfaceError('Invalid request message'),
    2: InterfaceError('Unknown command'),

    101: InterfaceError('Receiver active'),
    102: ReceiveTimeout(),
    103: ReceiveError('Receiver buffer overflow'),
    104: ReceiveError('Receiver error')
}

def _convert_error(message):
    if message[0] != 0x02:
        return InterfaceError(f'Invalid response: {message}')

    if len(message) < 2:
        return InterfaceError(f'Invalid error response: {message}')

    if message[1] in ERROR_MAP:
        error = copy(ERROR_MAP[message[1]])

        # Append description if included.
        if len(message) > 2:
            description = message[2:].decode('ascii')

            if error.args:
                error.args = (f'{error.args[0]}: {description}', *error.args[1:])
            else:
                error.args = (description,)

        return error

    return InterfaceError(f'Unknown error: {message[1]}')

class SlipSerial(SlipWrapper):
    """sliplib wrapper for pySerial."""

    def send_bytes(self, packet):
        """Sends a packet over the serial port."""
        self.stream.write(packet)
        self.stream.flush()

    def recv_bytes(self):
        """Receive data from the serial port."""
        if self.stream.closed:
            return b''

        count = self.stream.in_waiting

        if count:
            return self.stream.read(count)

        byte = self.stream.read(1)

        if byte == b'':
            raise InterfaceTimeout()

        return byte
