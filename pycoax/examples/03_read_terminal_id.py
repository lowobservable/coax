#!/usr/bin/env python

from common import open_example_serial_interface

from coax import ReadTerminalId

with open_example_serial_interface() as interface:
    print('READ_TERMINAL_ID...')

    terminal_id = interface.execute(ReadTerminalId())

    print('{0:02X}'.format(terminal_id.value))
    print(terminal_id)
