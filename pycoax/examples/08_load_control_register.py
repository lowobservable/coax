#!/usr/bin/env python

from common import open_example_serial_interface

from coax import Control, LoadAddressCounterHi, LoadAddressCounterLo, WriteData, LoadControlRegister

with open_example_serial_interface() as interface:
    interface.execute([LoadAddressCounterHi(0), LoadAddressCounterLo(80)])

    interface.execute(WriteData(bytes.fromhex('a7 84 8b 8b 8e 33 00 96 8e 91 8b 83 19')))

    input('Press ENTER...')

    print('LOAD_CONTROL_REGISTER display_inhibit')

    interface.execute(LoadControlRegister(Control(display_inhibit=True)))

    input('Press ENTER...')

    print('LOAD_CONTROL_REGISTER cursor_inhibit')

    interface.execute(LoadControlRegister(Control(cursor_inhibit=True)))

    input('Press ENTER...')

    print('LOAD_CONTROL_REGISTER cursor_reverse')

    interface.execute(LoadControlRegister(Control(cursor_reverse=True)))

    input('Press ENTER...')

    print('LOAD_CONTROL_REGISTER cursor_blink')

    interface.execute(LoadControlRegister(Control(cursor_blink=True)))
