#!/usr/bin/env python

from common import open_example_serial_interface

from coax import ReadAddressCounterHi, ReadAddressCounterLo, ReadData, LoadAddressCounterHi, LoadAddressCounterLo, WriteData

with open_example_serial_interface() as interface:
    interface.execute([LoadAddressCounterHi(0), LoadAddressCounterLo(80)])

    interface.execute(WriteData(bytes.fromhex('a7 84 8b 8b 8e 33 00 96 8e 91 8b 83 19')))

    interface.execute([LoadAddressCounterHi(0), LoadAddressCounterLo(81)])

    print('READ_DATA...')

    byte = interface.execute(ReadData())

    print(byte)

    [hi, lo] = interface.execute([ReadAddressCounterHi(), ReadAddressCounterLo()])

    print(f'hi = {hi}, lo = {lo}')
