#!/usr/bin/env python

from common import create_serial, create_interface

from coax import poll, poll_ack

with create_serial() as serial:
    interface = create_interface(serial, poll_flush=False)

    print('POLL...')

    poll_response = poll(interface, receive_timeout=5)

    print(poll_response)

    if poll_response:
        print('POLL_ACK...')

        poll_ack(interface)
