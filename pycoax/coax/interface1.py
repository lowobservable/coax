"""
coax.interface1
~~~~~~~~~~~~~~~
"""

from enum import Flag
import itertools
import struct
from sliplib import SlipWrapper, ProtocolError

from .exceptions import InterfaceError, InterfaceTimeout, ReceiveError, ReceiveTimeout

class Interface1:
    """A serial attached Arduino interface using the National Semiconductor
    DP8340 and DP8341.
    """

    def __init__(self, serial):
        if serial is None:
            raise ValueError('Serial port is required')

        self.serial = serial

        self.slip_serial = SlipSerial(self.serial)

    def reset(self):
        """Reset the interface."""
        original_serial_timeout = self.serial.timeout

        self.serial.reset_input_buffer()

        self._write_message(b'\x01')

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

    def execute(self, command_word, data=None, response_length=1, timeout=None):
        """Executes a command.

        :param command_word: the command to execute
        :param data: optional bytearray containing command data
        :param response_length: the expected response length
        :param timeout: optional timeout in seconds
        """
        timeout_milliseconds = 0

        if timeout:
            if self.serial.timeout and timeout > self.serial.timeout:
                raise ValueError('Timeout cannot be greater than serial timeout')

            timeout_milliseconds = int(timeout * 1000)

        message = struct.pack(">BHHH", 0x02, command_word, response_length,
                              timeout_milliseconds)

        if data is not None:
            message += data

        self._write_message(message)

        message = self._read_message()

        if message[0] != 0x01:
            raise _convert_error(message)

        response_bytes = message[1:]

        response_words = [(hi << 8) | lo for (lo, hi) in zip(response_bytes[::2],
                                                             response_bytes[1::2])]

        # Handle any receiver (DP8341) errors that are included in the response words.
        error_words = [word for word in response_words if (word & 0x8000) == 0x8000]

        if error_words:
            raise _convert_receiver_errors(error_words)

        return response_words

    def offload_load_address_counter(self, address):
        """Executes a combined LO and HI address counter load.

        :param address: the address
        """
        parameters = struct.pack(">H", address)

        self._execute_offload(0x01, parameters)

    def offload_write(self, data, address=None, restore_original_address=False, repeat=0):
        """Executes a complex write operation.

        :param data: the data
        :param address: optional address to load before WRITE_DATA command
        :param restore_original_address: restore the original data after write
        :param repeat: repeat the data
        """
        parameters = struct.pack(">HBH", 0xffff if address is None else address,
                                 0x01 if restore_original_address else 0x00,
                                 repeat) + data

        self._execute_offload(0x02, parameters)

    def _execute_offload(self, command, parameters=None):
        """Executes an offloaded command."""
        message = struct.pack("BB", 0x03, command)

        if parameters:
            message += parameters

        self._write_message(message)

        message = self._read_message()

        if message[0] != 0x01:
            raise _convert_error(message)

    def _read_message(self):
        try:
            message = self.slip_serial.recv_msg()
        except ProtocolError:
            raise InterfaceError('SLIP protocol error')

        if len(message) < 4:
            raise InterfaceError('Invalid response message')

        (length,) = struct.unpack(">H", message[:2])

        if length != len(message) - 4:
            raise InterfaceError('Response message length mismatch')

        if length < 1:
            raise InterfaceError('Empty response message')

        return message[2:-2]

    def _write_message(self, message):
        self.slip_serial.send_msg(struct.pack(">H", len(message)) + message + struct.pack(">H", 0))

ERROR_MAP = {
    1: InterfaceError('Invalid request message'),
    2: InterfaceError('Unknown command'),
    3: InterfaceError('Unknown offload command'),

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

class ReceiverErrorCode(Flag):
    """Receiver (DP8341) error code."""
    DATA_OVERFLOW = 0x01
    PARITY = 0x02
    TRANSMIT_CHECK_CONDITIONS = 0x04
    INVALID_ENDING_SEQUENCE = 0x08
    MID_BID_TRANSITION = 0x10
    STARTING_SEQUENCE = 0x20
    RECEIVER_DISABLED = 0x40

def _parse_receiver_error(word):
    return [code for code in ReceiverErrorCode if code & ReceiverErrorCode(word & 0x7f)]

def _convert_receiver_errors(words):
    codes = set(itertools.chain.from_iterable([_parse_receiver_error(word) for word
                                               in words]))

    message = 'Receiver ' + ', '.join([code.name for code in codes]) + ' error'

    raise ReceiveError(message)

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
