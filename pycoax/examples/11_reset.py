#!/usr/bin/env python

from common import create_serial, create_interface

from coax import reset

with create_serial() as serial:
    interface = create_interface(serial)

    print('RESET...')

    reset(interface)
