#!/usr/bin/env python

import sys
import time
from serial import Serial

sys.path.append('..')

from coax import Interface1, poll, poll_ack

print('Opening serial port...')

with Serial('/dev/ttyUSB0', 115200) as serial:
    print('Sleeping to allow interface time to wake up...')

    time.sleep(3)

    interface = Interface1(serial)

    print('Resetting interface...')

    version = interface.reset()

    print(f'Firmware version is {version}')

    print('POLL...')

    poll_response = poll(interface, timeout=5)

    print(poll_response)

    if poll_response:
        print('POLL_ACK...')

        poll_ack(interface)
