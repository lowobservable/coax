#!/usr/bin/env python

from common import create_serial, create_interface

from coax import read_status

with create_serial() as serial:
    interface = create_interface(serial)

    print('READ_STATUS...')

    status = read_status(interface)

    print(status)
