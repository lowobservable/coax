#!/usr/bin/env python

from common import open_example_serial_interface

from coax import read_status

with open_example_serial_interface() as interface:
    print('READ_STATUS...')

    status = read_status(interface)

    print(status)
