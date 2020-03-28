import sys
import time
from serial import Serial

sys.path.append('..')

from coax import SerialInterface, poll, poll_ack

SERIAL_PORT = '/dev/ttyACM0'

def create_serial():
    port = SERIAL_PORT

    print(f'Opening {port}...')

    serial = Serial(port, 115200)

    return serial

def create_interface(serial, reset=True, poll_flush=True):
    print('Sleeping to allow interface time to wake up...')

    time.sleep(3)

    interface = SerialInterface(serial)

    if reset:
        print('Resetting interface...')

        version = interface.reset()

        print(f'Firmware version is {version}')

    if poll_flush:
        print('POLLing...')

        count = 0

        poll_response = poll(interface, receive_timeout=1)

        while poll_response:
            poll_ack(interface)

            count += 1

            poll_response = poll(interface, receive_timeout=1)

        print(f'ACK\'d {count} POLL responses')

    return interface
