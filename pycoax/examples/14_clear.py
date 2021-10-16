#!/usr/bin/env python

from common import open_example_serial_interface

from coax import ReadAddressCounterHi, ReadAddressCounterLo, ReadStatus, LoadAddressCounterHi, LoadAddressCounterLo, WriteData, LoadMask, Clear

with open_example_serial_interface() as interface:
    # Clear the entire screen, except status line.
    interface.execute([LoadAddressCounterHi(0), LoadAddressCounterLo(80), LoadMask(0x00), Clear(0x00)])

    status = interface.execute(ReadStatus())

    print(status)

    while status.busy:
        status = interface.execute(ReadStatus())

        print(status)

    input('Press ENTER...')

    # Write something...
    interface.execute([LoadAddressCounterHi(0), LoadAddressCounterLo(80)])

    interface.execute(WriteData(bytes.fromhex('a7 84 8b 8b 8e 33 00 96 8e 91 8b 83 19')))

    input('Press ENTER...')

    interface.execute([LoadAddressCounterHi(0), LoadAddressCounterLo(81), LoadMask(0xf0), Clear(0x30)])

    status = interface.execute(ReadStatus())

    print(status)

    while status.busy:
        status = interface.execute(ReadStatus())

        print(status)

    [hi, lo] = interface.execute([ReadAddressCounterHi(), ReadAddressCounterLo()])

    print(f'hi = {hi}, lo = {lo}')
