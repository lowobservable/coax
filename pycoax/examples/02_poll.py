#!/usr/bin/env python

from common import open_example_serial_interface

from coax import poll, poll_ack

with open_example_serial_interface(poll_flush=False) as interface:
    print('POLL...')

    poll_response = poll(interface, receive_timeout=5)

    print(poll_response)

    if poll_response:
        print('POLL_ACK...')

        poll_ack(interface)
