# pycoax

Python IBM 3270 coaxial interface library.

## Usage

You will need to build an [interface](../interface1) and connect it to your computer.

Install using `pip`:

```
pip install pycoax
```

Assuming your interface is connected to `/dev/ttyACM0` and you have a CUT type terminal connected to the interface, you can do something like this:

```
import time
from serial import Serial
from coax import SerialInterface, poll, poll_ack, load_address_counter_hi, \
                 load_address_counter_lo, write_data, ReceiveTimeout

with Serial('/dev/ttyACM0', 115200) as serial:
    # Give the interface time to wake up...
    time.sleep(3)

    # Initialize and reset the interface.
    interface = SerialInterface(serial)

    firmware_version = interface.reset()

    print(f'Firmware version is {firmware_version}')

    # Wait for a terminal to attach...
    poll_response = None
    attached = False

    while not attached:
        try:
            poll_response = poll(interface, receive_timeout=1)

            if poll_response:
                print(poll_response)

                poll_ack(interface)

            attached = True
        except ReceiveTimeout:
            print('.')

            time.sleep(1)

    # Poll the terminal until status is empty.
    while poll_response:
        poll_response = poll(interface)

        if poll_response:
            print(poll_response)

            poll_ack(interface)

    # Move the cursor to top-left cell of a 80 column display.
    load_address_counter_hi(interface, 0)
    load_address_counter_lo(interface, 80)

    # Write a secret message.
    write_data(interface, bytes.fromhex('a1 84 00 92 94 91 84 00 93 8e 00 83 91 88 8d 8a 00 98 8e 94 91 00 ae 95 80 8b 93 88 8d 84'))
```

See [examples](examples) for complete examples.
