#!/usr/bin/env python

import sys
from collections import namedtuple
import struct

from more_itertools import partition
from serial import Serial
from sliplib import ProtocolError
import msgpack

from coax.serial_interface import SlipSerial, _unpack_receive_data

Packet = namedtuple('Packet', ['timestamp', 'words', 'errors'])

class TapException(Exception):
    pass

class NewCoaxTap:
    def __init__(self, serial_port):
        self.serial = Serial(serial_port, 115200)

        self.slip_serial = SlipSerial(self.serial)

    def enable(self):
        self.serial.write(b'e')
        self.serial.flush()

    def read(self):
        try:
            message = self.slip_serial.recv_msg()
        except ProtocolError:
            raise TapException('SLIP protocol error')

        if len(message) < 6:
            raise TapException('Invalid message received, must be at least 6 bytes')

        if len(message) % 2 != 0:
            raise TapException('Invalid message received, must be even length')

        timestamp = struct.unpack('<I', message[0:4])[0]

        words = _unpack_receive_data(message[4:])

        errors = []
        data = []

        for word in words:
            if word & 0x8000:
                errors.append(word & 0x7fff)
            else:
                data.append(word)

        if errors:
            sys.stdout.write('E')

        return Packet(timestamp, data, errors)

tap = NewCoaxTap(sys.argv[1])

capture_file = open(sys.argv[2], 'wb')

# Start capture.
tap.enable()

# Process packets.
packet_count = 0
need_newline = False

while True:
    try:
        packet = tap.read()
    except TapException as error:
        if need_newline:
            print()

        print(f'ERROR: {error}')

        need_newline = False
        continue

    capture_file.write(msgpack.packb(packet, use_bin_type=True))

    if packet_count % 10 == 0:
        sys.stdout.write('.')
        sys.stdout.flush()
        
        need_newline = True

    packet_count += 1
