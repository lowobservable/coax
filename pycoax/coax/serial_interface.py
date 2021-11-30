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

from .interface import Interface, InterfaceFeature, FrameFormat
from .protocol import pack_data_word
from .exceptions import InterfaceError, InterfaceTimeout, ReceiveError, ReceiveTimeout

class SerialInterface(Interface):
    """Serial attached 3270 coax interface."""

    def __init__(self, serial):
        if serial is None:
            raise ValueError('Serial port is required')

        super().__init__()

        self.serial = serial

        self.slip_serial = SlipSerial(self.serial)

        self.legacy_firmware_detected = None
        self.legacy_firmware_version = None

    def reset(self):
        """Reset the interface."""
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
            self.legacy_firmware_version = f'{major}.{minor}.{patch}'
        else:
            raise InterfaceError(f'Invalid reset response: {message}')

        # Query features, if this is not a legacy firmware.
        if not self.legacy_firmware_detected:
            try:
                self.features = self._get_features()
            except InterfaceError:
                pass

    def enter_dfu_mode(self):
        """Enter device firmware upgrade mode."""
        message = bytes([0xf2])

        self._write_message(message)

        message = self._read_message()

        if message[0] != 0x01:
            raise _convert_error(message)

    def _get_features(self):
        """Get interface features."""
        message = bytes([0xf0, 0x07])

        self._write_message(message)

        message = self._read_message()

        if message[0] != 0x01:
            raise _convert_error(message)

        known_feature_values = {feature.value for feature in InterfaceFeature}

        features = {InterfaceFeature(value) for value in message[1:] if value in known_feature_values}

        return features

    def _transmit_receive(self, outbound_frames, response_lengths, timeout):
        if len(response_lengths) != len(outbound_frames):
            raise ValueError('Response lengths length must equal outbound frames length')

        if any(address is not None for (address, _) in outbound_frames) and InterfaceFeature.PROTOCOL_3299 not in self.features:
            raise NotImplementedError('Interface does not support 3299 protocol')

        # Pack all messages before sending.
        timeout_milliseconds = self._calculate_timeout_milliseconds(timeout)

        messages = [_pack_transmit_receive_message(address, frame, response_length, timeout_milliseconds)
                    for ((address, frame), response_length) in zip(outbound_frames, response_lengths)]

        responses = []

        for message in messages:
            self._write_message(message)

            message = self._read_message()

            if message[0] == 0x01:
                response = _unpack_transmit_receive_response(message[1:])
            else:
                error = _convert_error(message)

                if not isinstance(error, (ReceiveError, ReceiveTimeout)):
                    raise error

                response = error

            responses.append(response)

        return responses

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
    """Opens serial port and initializes serial attached 3270 coax interface."""
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

def _pack_transmit_receive_message(address, frame, response_length, timeout_milliseconds):
    message = bytes([0x06])

    repeat_count = 0
    repeat_offset = 0
    bytes_ = bytearray()

    if frame[0] == FrameFormat.WORDS:
        if isinstance(frame[1], tuple):
            repeat_count = frame[1][1]

            for word in frame[1][0]:
                bytes_ += struct.pack('<H', word)
        else:
            for word in frame[1]:
                bytes_ += struct.pack('<H', word)
    elif frame[0] == FrameFormat.WORD_DATA:
        bytes_ += struct.pack('<H', frame[1])

        if len(frame) > 2:
            if isinstance(frame[2], tuple):
                repeat_offset = 1
                repeat_count = frame[2][1]

                for byte in frame[2][0]:
                    bytes_ += struct.pack('<H', pack_data_word(byte))
            else:
                for byte in frame[2]:
                    bytes_ += struct.pack('<H', pack_data_word(byte))
    elif frame[0] == FrameFormat.DATA:
        if isinstance(frame[1], tuple):
            repeat_count = frame[1][1]

            for byte in frame[1][0]:
                bytes_ += struct.pack('<H', pack_data_word(byte))
        else:
            for byte in frame[1]:
                bytes_ += struct.pack('<H', pack_data_word(byte))

    if address is not None:
        if address < 0 or address > 63:
            raise ValueError('Address must be between 0 and 63')

        if repeat_count > 0:
            repeat_offset += 1

        bytes_ = struct.pack('<H', 0x8000 | address) + bytes_

    message += struct.pack('>H', (repeat_offset << 15) | repeat_count)
    message += bytes_
    message += struct.pack('>HH', response_length, timeout_milliseconds)

    return message

def _unpack_transmit_receive_response(bytes_):
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
