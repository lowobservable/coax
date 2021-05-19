#!/usr/bin/env python

import sys

from common import create_serial, create_interface

from coax import read_terminal_id, load_address_counter_hi, load_address_counter_lo, \
                 read_data, read_multiple

with create_serial() as serial:
    interface = create_interface(serial)

    print('READ_TERMINAL_ID...')

    terminal_id = read_terminal_id(interface)

    print(terminal_id)

    if terminal_id.type != TerminalType.DFT:
        sys.exit('Uh, I was expecting a DFT-type terminal')

    # Step 1...
    print('Step 1')

    load_address_counter_hi(interface, 0x00)
    load_address_counter_lo(interface, 0x0c)

    if read_data(interface) != 0x02:
        sys.exit('1.1 - I was expecting 0x02')

    if read_data(interface) != 0x00:
        sys.exit('1.2 - I was expecting 0x00')

    if read_data(interface) != 0x00:
        sys.exit('1.3 - I was expecting 0x00')

    if read_data(interface) != 0x00:
        sys.exit('1.4 - I was expecting 0x00')

    # Step 2...
    print('Step 2')

    load_address_counter_hi(interface, 0x00)
    load_address_counter_lo(interface, 0x0c)

    if read_multiple(interface) != bytes.fromhex('02 00 00 00'):
        sys.exit('2.1 - I was expecting [0x02 0x00 0x00 0x00]')

    if read_multiple(interface) != bytes.fromhex('10 00 00 00'):
        sys.exit('2.2 - I was expecting [0x10 0x00 0x00 0x00]')

    # Step 3...
    print('Step 3')

    # ...
