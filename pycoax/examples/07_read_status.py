#!/usr/bin/env python

from common import open_example_serial_interface

from coax import ReadStatus

with open_example_serial_interface() as interface:
    print('READ_STATUS...')

    status = interface.execute(ReadStatus())

    print(status)
