"""
coax.serial_interface
~~~~~~~~~~~~~~~~~~~~~
"""

import struct
from sliplib import SlipWrapper, ProtocolError

from .interface import Interface
from .exceptions import InterfaceError, InterfaceTimeout, ReceiveError, ReceiveTimeout

class SerialInterface(Interface):
    def __init__(self, serial):
        if serial is None:
            raise ValueError('Serial port is required')

        self.serial = serial

        self.slip_serial = SlipSerial(self.serial)

    def reset(self):
        original_serial_timeout = self.serial.timeout

        self.serial.reset_input_buffer()

        self._write_message(bytes([0x01]))

        self.serial.timeout = 5

        try:
            message = self._read_message()
        finally:
            self.serial.timeout = original_serial_timeout

        if message[0] != 0x01:
            raise _convert_error(message)

        if len(message) != 4:
            raise InterfaceError('Invalid reset response')

        (major, minor, patch) = struct.unpack('BBB', message[1:])

        return '{}.{}.{}'.format(major, minor, patch)

    def transmit(self, words, repeat_count=None, repeat_offset=1):
        message = bytes([0x02])

        message += _pack_transmit_header(repeat_count, repeat_offset)
        message += _pack_transmit_data(words)

        self._write_message(message)

        message = self._read_message()

        if message[0] != 0x01:
            raise _convert_error(message)

    def receive(self, length=None, timeout=None):
        timeout_milliseconds = self._calculate_timeout_milliseconds(timeout)

        message = bytes([0x04])

        message += _pack_receive_header(length, timeout_milliseconds)

        self._write_message(message)

        message = self._read_message()

        if message[0] != 0x01:
            raise _convert_error(message)

        return _unpack_receive_data(message[1:])

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
            raise InterfaceError('Invalid response message')

        (length,) = struct.unpack('>H', message[:2])

        if length != len(message) - 4:
            raise InterfaceError('Response message length mismatch')

        if length < 1:
            raise InterfaceError('Empty response message')

        return message[2:-2]

    def _write_message(self, message):
        self.slip_serial.send_msg(struct.pack('>H', len(message)) + message +
                                  struct.pack('>H', 0))

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
    103: ReceiveError('Receiver buffer overflow')
}

def _convert_error(message):
    if message[0] != 0x02:
        return InterfaceError('Invalid response')

    if len(message) < 2:
        return InterfaceError('Invalid error response')

    if message[1] in ERROR_MAP:
        return ERROR_MAP[message[1]]

    return InterfaceError('Unknown error')

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
