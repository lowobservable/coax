#!/usr/bin/env python

from common import open_example_serial_interface

from coax import Reset

with open_example_serial_interface() as interface:
    print('RESET...')

    interface.execute(Reset())
