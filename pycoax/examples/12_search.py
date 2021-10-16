#!/usr/bin/env python

from common import open_example_serial_interface

from coax import ReadAddressCounterHi, ReadAddressCounterLo, ReadStatus, LoadAddressCounterHi, LoadAddressCounterLo, WriteData, LoadMask, SearchForward, SearchBackward

with open_example_serial_interface() as interface:
    interface.execute([LoadAddressCounterHi(0), LoadAddressCounterLo(80)])

    interface.execute(WriteData(bytes.fromhex('a7 84 8b 8b 8e 33 00 96 8e 91 8b 83 19')))

    interface.execute([LoadAddressCounterHi(0), LoadAddressCounterLo(81)])

    interface.execute(LoadMask(0xff))

    interface.execute(SearchForward(0x83))

    status = interface.execute(ReadStatus())

    print(status)

    while status.busy:
        status = interface.execute(ReadStatus())

        print(status)

    [hi, lo] = interface.execute([ReadAddressCounterHi(), ReadAddressCounterLo()])

    print(f'hi = {hi}, lo = {lo}')

    interface.execute(SearchBackward(0x84))

    status = interface.execute(ReadStatus())

    print(status)

    while status.busy:
        status = interface.execute(ReadStatus())

        print(status)

    [hi, lo] = interface.execute([ReadAddressCounterHi(), ReadAddressCounterLo()])

    print(f'hi = {hi}, lo = {lo}')

    interface.execute(LoadMask(0xf0))

    interface.execute(SearchForward(0x30))

    status = interface.execute(ReadStatus())

    print(status)

    while status.busy:
        status = interface.execute(ReadStatus())

        print(status)

    [hi, lo] = interface.execute([ReadAddressCounterHi(), ReadAddressCounterLo()])

    print(f'hi = {hi}, lo = {lo}')
