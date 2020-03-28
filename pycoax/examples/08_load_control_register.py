#!/usr/bin/env python

from common import create_serial, create_interface

from coax import Control, poll, load_address_counter_hi, load_address_counter_lo, write_data, load_control_register

with create_serial() as serial:
    interface = create_interface(serial)

    load_address_counter_hi(interface, 0)
    load_address_counter_lo(interface, 80)

    write_data(interface, bytes.fromhex('a7 84 8b 8b 8e 33 00 96 8e 91 8b 83 19'))

    input('Press ENTER...')

    print('LOAD_CONTROL_REGISTER display_inhibit')

    load_control_register(interface, Control(display_inhibit=True))

    input('Press ENTER...')

    print('LOAD_CONTROL_REGISTER cursor_inhibit')

    load_control_register(interface, Control(cursor_inhibit=True))

    input('Press ENTER...')

    print('LOAD_CONTROL_REGISTER cursor_reverse')

    load_control_register(interface, Control(cursor_reverse=True))

    input('Press ENTER...')

    print('LOAD_CONTROL_REGISTER cursor_blink')

    load_control_register(interface, Control(cursor_blink=True))
