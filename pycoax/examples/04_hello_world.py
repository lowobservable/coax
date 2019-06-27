#!/usr/bin/env python

import sys
import time
from serial import Serial

sys.path.append('..')

from coax import Interface1, read_address_counter_hi, read_address_counter_lo, load_address_counter_hi, load_address_counter_lo, write_data

print('Opening serial port...')

with Serial('/dev/ttyUSB0', 115200) as serial:
    print('Sleeping to allow interface time to wake up...')

    time.sleep(3)

    interface = Interface1(serial)

    print('Resetting interface...')

    version = interface.reset()

    print(f'Firmware version is {version}')

    print('LOAD_ADDRESS_COUNTER_HI...')

    load_address_counter_hi(interface, 0)

    print('LOAD_ADDRESS_COUNTER_LO...')

    load_address_counter_lo(interface, 80)

    print('WRITE_DATA...')

    write_data(interface, bytes.fromhex('a7 84 8b 8b 8e 33 00 96 8e 91 8b 83 19'))

    print('READ_ADDRESS_COUNTER_HI...')

    hi = read_address_counter_hi(interface)

    print('READ_ADDRESS_COUNTER_LO...')

    lo = read_address_counter_lo(interface)

    print(f'hi = {hi:02x}, lo = {lo:02x}')
