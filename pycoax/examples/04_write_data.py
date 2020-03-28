#!/usr/bin/env python

from common import create_serial, create_interface

from coax import read_address_counter_hi, read_address_counter_lo, load_address_counter_hi, load_address_counter_lo, write_data

with create_serial() as serial:
    interface = create_interface(serial)

    print('LOAD_ADDRESS_COUNTER_HI...')

    load_address_counter_hi(interface, 0)

    print('LOAD_ADDRESS_COUNTER_LO...')

    load_address_counter_lo(interface, 80)

    print('WRITE_DATA...')

    write_data(interface, bytes.fromhex('a7 84 8b 8b 8e 33 00 96 8e 91 8b 83 19'))

    print('READ_ADDRESS_COUNTER_HI...')

    hi = read_address_counter_hi(interface)

    print('READ_ADDRESS_COUNTER_LO...')

    lo = read_address_counter_lo(interface)

    print(f'hi = {hi:02x}, lo = {lo:02x}')

    print('WRITE_DATA (repeat twice)...')

    write_data(interface, (bytes.fromhex('a7 84 8b 8b 8e 33 00 96 8e 91 8b 83 19'), 2))
