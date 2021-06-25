#!/usr/bin/env python

from common import open_example_serial_interface

from coax import reset

with open_example_serial_interface() as interface:
    print('RESET...')

    reset(interface)
