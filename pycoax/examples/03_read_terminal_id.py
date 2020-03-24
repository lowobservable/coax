#!/usr/bin/env python

from common import create_serial, create_interface

from coax import read_terminal_id

with create_serial() as serial:
    interface = create_interface(serial)

    print('READ_TERMINAL_ID...')

    terminal_id = read_terminal_id(interface)

    print(terminal_id)
