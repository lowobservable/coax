#!/usr/bin/env python

from common import open_example_serial_interface

from coax import ReadAddressCounterHi, ReadAddressCounterLo, LoadAddressCounterHi, LoadAddressCounterLo, WriteData, Data

with open_example_serial_interface() as interface:
    print('LOAD_ADDRESS_COUNTER_HI and LO...')

    interface.execute([LoadAddressCounterHi(0), LoadAddressCounterLo(80)])

    print('WRITE_DATA...')

    interface.execute(WriteData(bytes.fromhex('a7 84 8b 8b 8e 33 00 96 8e 91 8b 83 19')))

    print('READ_ADDRESS_COUNTER_HI and LO...')

    [hi, lo] = interface.execute([ReadAddressCounterHi(), ReadAddressCounterLo()])

    print(f'hi = {hi:02x}, lo = {lo:02x}')

    print('WRITE_DATA (repeat twice)...')

    interface.execute(WriteData((bytes.fromhex('a7 84 8b 8b 8e 33 00 96 8e 91 8b 83 19'), 2)))

    print('Unaccompanied data after WRITE_DATA...')

    interface.execute(Data(bytes.fromhex('33 00 80 8d 83 00 92 8e 8c 84 00 94 8d 80 82 82 8e 8c 8f 80 8d 88 84 83 00 83 80 93 80')))
