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
from coax import open_serial_interface, Poll, PollAck, LoadAddressCounterHi, \
                 LoadAddressCounterLo, WriteData, ReceiveTimeout

with open_serial_interface('/dev/ttyACM0') as interface:
    # Wait for a terminal to attach...
    poll_response = None
    attached = False

    while not attached:
        try:
            poll_response = interface.execute(Poll(), timeout=1)

            if poll_response:
                print(poll_response)

                interface.execute(PollAck())

            attached = True
        except ReceiveTimeout:
            print('.')

            time.sleep(1)

    # Poll the terminal until status is empty.
    while poll_response:
        poll_response = interface.execute(Poll())

        if poll_response:
            print(poll_response)

            interface.execute(Poll())

    # Move the cursor to top-left cell of a 80 column display.
    interface.execute([LoadAddressCounterHi(0), LoadAddressCounterLo(80)])

    # Write a secret message.
    interface.execute(WriteData(bytes.fromhex('a1 84 00 92 94 91 84 00 93 8e 00 83 91 88 8d 8a 00 98 8e 94 91 00 ae 95 80 8b 93 88 8d 84')))
```

See [examples](examples) for complete examples.
