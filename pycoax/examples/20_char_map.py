#!/usr/bin/env python

from common import open_example_serial_interface

from coax import Control, LoadAddressCounterHi, LoadAddressCounterLo, WriteData, LoadControlRegister

DIGIT_MAP = [0x20, 0x21, 0x22, 0x23, 0x24, 0x25, 0x26, 0x27, 0x28, 0x29, 0x80, 0x81, 0x82, 0x83, 0x84, 0x85]

with open_example_serial_interface() as interface:
    interface.execute(LoadControlRegister(Control(cursor_inhibit=True)))

    interface.execute([LoadAddressCounterHi(0), LoadAddressCounterLo(80)])

    buffer = b'\x00' * 4

    # Header Row
    for lo in range(16):
        buffer += bytes([0x2f, DIGIT_MAP[lo]]) + (b'\x00' * 2)

    buffer += b'\x00' * 12

    # Rows
    for hi in range(16):
        buffer += bytes([DIGIT_MAP[hi], 0x2f]) + (b'\x00' * 2)

        for lo in range(16):
            if hi < 12:
                buffer += bytes([0x00, (hi << 4) | lo, 0xc0, 0x00])
            else:
                buffer += bytes([(hi << 4) | lo, 0x32, 0xc0, 0x00])

        buffer += b'\x00' * 12

    buffer += b'\x00' * 560

    interface.execute(WriteData(buffer))

    # Status Line
    interface.execute([LoadAddressCounterHi(7), LoadAddressCounterLo(48)])

    buffer = b''

    for hi in range(12, 16):
        buffer += bytes([DIGIT_MAP[hi]]) + (b'\x00' * 15)

    buffer += b'\x00' * 16

    for hi in range(12, 16):
        for lo in range(0, 16):
            buffer += bytes([DIGIT_MAP[lo]])

    interface.execute(WriteData(buffer))

    interface.execute([LoadAddressCounterHi(0), LoadAddressCounterLo(0)])

    buffer = bytes(range(0xc0, 0xff + 1))

    interface.execute(WriteData(buffer))
