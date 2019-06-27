#!/usr/bin/env python

import sys
import time
from serial import Serial

sys.path.append('..')

from coax import Interface1

print('Opening serial port...')

with Serial('/dev/ttyUSB0', 115200) as serial:
    print('Sleeping to allow interface time to wake up...')

    time.sleep(3)

    interface = Interface1(serial)

    print('Resetting interface...')

    version = interface.reset()

    print(f'Firmware version is {version}')

    for n in range(10):
        print(f'Writing line {n + 1}...')

        address = ((7 + n) * 80) + 80

        interface.offload_write(b'\x80', address=address, repeat=n)
