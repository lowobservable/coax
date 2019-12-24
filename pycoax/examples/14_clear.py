#!/usr/bin/env python

import sys
import time
from serial import Serial

sys.path.append('..')

from coax import Interface1, read_address_counter_hi, read_address_counter_lo, read_status, load_address_counter_hi, load_address_counter_lo, write_data, load_mask, clear

print('Opening serial port...')

with Serial('/dev/ttyUSB0', 115200) as serial:
    print('Sleeping to allow interface time to wake up...')

    time.sleep(3)

    interface = Interface1(serial)

    print('Resetting interface...')

    version = interface.reset()

    print(f'Firmware version is {version}')

    load_address_counter_hi(interface, 0)
    load_address_counter_lo(interface, 80)
    write_data(interface, bytes.fromhex('a7 84 8b 8b 8e 33 00 96 8e 91 8b 83 19'))

    input('Press ENTER...')

    load_address_counter_hi(interface, 0)
    load_address_counter_lo(interface, 81)

    load_mask(interface, 0xf0)

    clear(interface, 0x30)

    status = read_status(interface)

    print(status)

    while status.busy:
        status = read_status(interface)

        print(status)

    hi = read_address_counter_hi(interface)
    lo = read_address_counter_lo(interface)

    print(f'hi = {hi}, lo = {lo}')
