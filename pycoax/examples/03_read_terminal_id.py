#!/usr/bin/env python

from common import open_example_serial_interface

from coax import read_terminal_id

with open_example_serial_interface() as interface:
    print('READ_TERMINAL_ID...')

    terminal_id = read_terminal_id(interface)

    print(terminal_id)
