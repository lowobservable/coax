#!/usr/bin/env python

from common import open_example_serial_interface

with open_example_serial_interface(reset=False, poll_flush=False) as interface:
    print('Resetting interface...')

    interface.reset()

    if interface.legacy_firmware_detected:
        print(f'Firmware version is {interface.legacy_firmware_version}')
