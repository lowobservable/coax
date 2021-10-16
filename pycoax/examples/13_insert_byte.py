#!/usr/bin/env python

from common import open_example_serial_interface

from coax import LoadAddressCounterHi, LoadAddressCounterLo, WriteData, InsertByte

with open_example_serial_interface() as interface:
    interface.execute([LoadAddressCounterHi(0), LoadAddressCounterLo(80)])

    interface.execute(WriteData(bytes.fromhex('a7 84 8b 8b 8e 33 00 96 8e 91 8b 83 19')))

    input('Press ENTER...')

    interface.execute([LoadAddressCounterHi(0), LoadAddressCounterLo(81)])

    interface.execute(InsertByte(0xb7))

    input('Press ENTER...')

    interface.execute([LoadAddressCounterHi(0), LoadAddressCounterLo(88)])

    interface.execute(InsertByte(0xb7))
