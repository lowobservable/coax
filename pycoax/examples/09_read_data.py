#!/usr/bin/env python

from common import create_serial, create_interface

from coax import read_address_counter_hi, read_address_counter_lo, read_data, load_address_counter_hi, load_address_counter_lo, write_data

with create_serial() as serial:
    interface = create_interface(serial)

    load_address_counter_hi(interface, 0)
    load_address_counter_lo(interface, 80)

    write_data(interface, bytes.fromhex('a7 84 8b 8b 8e 33 00 96 8e 91 8b 83 19'))

    load_address_counter_hi(interface, 0)
    load_address_counter_lo(interface, 81)

    print('READ_DATA...')

    print(read_data(interface))

    hi = read_address_counter_hi(interface)
    lo = read_address_counter_lo(interface)

    print(f'hi = {hi}, lo = {lo}')
