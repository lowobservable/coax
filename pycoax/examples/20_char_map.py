#!/usr/bin/env python

from common import open_example_serial_interface

from coax import Control, read_address_counter_hi, read_address_counter_lo, load_address_counter_hi, load_address_counter_lo, write_data, load_control_register

DIGIT_MAP = [0x20, 0x21, 0x22, 0x23, 0x24, 0x25, 0x26, 0x27, 0x28, 0x29, 0x80, 0x81, 0x82, 0x83, 0x84, 0x85]

with open_example_serial_interface() as interface:
    load_control_register(interface, Control(cursor_inhibit=True))

    load_address_counter_hi(interface, 0)
    load_address_counter_lo(interface, 80)

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

    write_data(interface, buffer)

    # Status Line
    load_address_counter_hi(interface, 7)
    load_address_counter_lo(interface, 48)

    buffer = b''

    for hi in range(12, 16):
        buffer += bytes([DIGIT_MAP[hi]]) + (b'\x00' * 15)

    buffer += b'\x00' * 16

    for hi in range(12, 16):
        for lo in range(0, 16):
            buffer += bytes([DIGIT_MAP[lo]])

    write_data(interface, buffer)

    load_address_counter_hi(interface, 0)
    load_address_counter_lo(interface, 0)

    buffer = bytes(range(0xc0, 0xff + 1))

    write_data(interface, buffer)
