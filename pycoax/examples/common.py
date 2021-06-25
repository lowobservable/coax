import sys
import time
import os
from contextlib import contextmanager

sys.path.append('..')

from coax import open_serial_interface, poll, poll_ack

DEFAULT_SERIAL_PORT = '/dev/ttyACM0'

@contextmanager
def open_example_serial_interface(reset=True, poll_flush=True):
    serial_port = os.environ.get('COAX_PORT', DEFAULT_SERIAL_PORT)

    print(f'Opening {serial_port}...')

    with open_serial_interface(serial_port, reset=False) as interface:
        if reset:
            print('Resetting interface...')

            interface.reset()

            if interface.legacy_firmware_detected:
                print(f'Firmware version is {interface.legacy_firmware_version}')

        if poll_flush:
            print('POLLing...')

            count = 0

            poll_response = poll(interface, receive_timeout=1)

            while poll_response:
                poll_ack(interface)

                count += 1

                poll_response = poll(interface, receive_timeout=1)

            print(f'ACK\'d {count} POLL responses')

        yield interface
