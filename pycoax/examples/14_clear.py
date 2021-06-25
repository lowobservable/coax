#!/usr/bin/env python

from common import open_example_serial_interface

from coax import read_address_counter_hi, read_address_counter_lo, read_status, load_address_counter_hi, load_address_counter_lo, write_data, load_mask, clear

with open_example_serial_interface() as interface:
    load_address_counter_hi(interface, 0)
    load_address_counter_lo(interface, 80)

    write_data(interface, bytes.fromhex('a7 84 8b 8b 8e 33 00 96 8e 91 8b 83 19'))

    input('Press ENTER...')

    load_address_counter_hi(interface, 0)
    load_address_counter_lo(interface, 81)

    load_mask(interface, 0xf0)

    clear(interface, 0x30)

    status = read_status(interface)

    print(status)

    while status.busy:
        status = read_status(interface)

        print(status)

    hi = read_address_counter_hi(interface)
    lo = read_address_counter_lo(interface)

    print(f'hi = {hi}, lo = {lo}')
