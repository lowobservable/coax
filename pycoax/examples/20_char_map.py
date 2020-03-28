#!/usr/bin/env python

from common import create_serial, create_interface

from coax import read_address_counter_hi, read_address_counter_lo, load_address_counter_hi, load_address_counter_lo, write_data

DIGIT_MAP = [0x20, 0x21, 0x22, 0x23, 0x24, 0x25, 0x26, 0x27, 0x28, 0x29, 0x80, 0x81, 0x82, 0x83, 0x84, 0x85]

with create_serial() as serial:
    interface = create_interface(serial)

    print('LOAD_ADDRESS_COUNTER_HI...')

    load_address_counter_hi(interface, 0)

    print('LOAD_ADDRESS_COUNTER_LO...')

    load_address_counter_lo(interface, 80)

    print('WRITE_DATA...')

    buffer = b'\x00' * 3

    # Header Row
    for lo in range(16):
        buffer += bytes([DIGIT_MAP[lo]]) + (b'\x00' * 3)

    buffer += b'\x00' * 13

    # Rows
    for hi in range(16):
        buffer += bytes([DIGIT_MAP[hi]]) + (b'\x00' * 2)

        for lo in range(16):
            buffer += bytes([(hi << 4) | lo]) + b'\x32\xc0\x00'

        buffer += b'\x00' * 13

    buffer += b'\x00' * 560

    write_data(interface, buffer)
