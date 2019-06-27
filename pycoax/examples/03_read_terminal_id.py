#!/usr/bin/env python

import sys
import time
from serial import Serial

sys.path.append('..')

from coax import Interface1, read_terminal_id

print('Opening serial port...')

with Serial('/dev/ttyUSB0', 115200) as serial:
    print('Sleeping to allow interface time to wake up...')

    time.sleep(3)

    interface = Interface1(serial)

    print('Resetting interface...')

    version = interface.reset()

    print(f'Firmware version is {version}')

    print('READ_TERMINAL_ID...')

    terminal_id = read_terminal_id(interface)

    print(terminal_id)
