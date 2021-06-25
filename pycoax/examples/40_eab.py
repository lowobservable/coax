#!/usr/bin/env python

import sys
from itertools import chain

from common import open_example_serial_interface

from coax import Feature, get_features, load_address_counter_hi, load_address_counter_lo, write_data, eab_write_alternate, eab_load_mask

def eab_alternate_zip(regen_buffer, eab_buffer):
    return bytes(chain(*zip(regen_buffer, eab_buffer)))

with open_example_serial_interface() as interface:
    features = get_features(interface)

    if Feature.EAB not in features:
        sys.exit('No EAB feature found.')

    eab_address = features[Feature.EAB]

    print(f'EAB feature found at address {eab_address}')

    # Protected Normal
    load_address_counter_hi(interface, 0)
    load_address_counter_lo(interface, 80)

    regen_buffer = bytes.fromhex('e0 08 00 af 91 8e 93 84 82 93 84 83 00 ad 8e 91 8c 80 8b 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 09')

    write_data(interface, regen_buffer)

    # Protected Intense
    load_address_counter_hi(interface, 0)
    load_address_counter_lo(interface, 160)

    regen_buffer = bytes.fromhex('e8 08 00 af 91 8e 93 84 82 93 84 83 00 a8 8d 93 84 8d 92 84 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 09')

    write_data(interface, regen_buffer)

    # Normal EFA
    load_address_counter_hi(interface, 1)
    load_address_counter_lo(interface, 64)

    regen_buffer = bytes.fromhex('e0 08 00 ad 8e 91 8c 80 8b 00 a4 a5 a0 00 00 00 00 00 00 00 00 00 00 b7 bf 00 a1 bf 00 b1 bf 00 ac bf 00 a6 bf 00 a2 bf 00 b8 bf 00 b6 bf 00 00 09 e0')
    eab_buffer = bytes.fromhex('00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 08 00 00 10 00 00 18 00 00 20 00 00 28 00 00 30 00 00 38 00 00 00 00 00')

    eab_write_alternate(interface, eab_address, eab_alternate_zip(regen_buffer, eab_buffer))

    # Blink EFA
    load_address_counter_hi(interface, 1)
    load_address_counter_lo(interface, 144)

    regen_buffer = bytes.fromhex('e0 08 00 a1 8b 88 8d 8a 00 a4 a5 a0 00 00 00 00 00 00 00 00 00 00 00 b7 bf 00 a1 bf 00 b1 bf 00 ac bf 00 a6 bf 00 a2 bf 00 b8 bf 00 b6 bf 00 00 09 e0')
    eab_buffer = bytes.fromhex('40 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 08 00 00 10 00 00 18 00 00 20 00 00 28 00 00 30 00 00 38 00 00 00 00 00')

    eab_write_alternate(interface, eab_address, eab_alternate_zip(regen_buffer, eab_buffer))

    # Reverse EFA
    load_address_counter_hi(interface, 1)
    load_address_counter_lo(interface, 224)

    regen_buffer = bytes.fromhex('e0 08 00 b1 84 95 84 91 92 84 00 a4 a5 a0 00 00 00 00 00 00 00 00 00 b7 bf 00 a1 bf 00 b1 bf 00 ac bf 00 a6 bf 00 a2 bf 00 b8 bf 00 b6 bf 00 00 09 e0')
    eab_buffer = bytes.fromhex('80 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 08 00 00 10 00 00 18 00 00 20 00 00 28 00 00 30 00 00 38 00 00 00 00 00')

    eab_write_alternate(interface, eab_address, eab_alternate_zip(regen_buffer, eab_buffer))

    # Underline EFA
    load_address_counter_hi(interface, 2)
    load_address_counter_lo(interface, 48)

    regen_buffer = bytes.fromhex('e0 08 00 b4 8d 83 84 91 8b 88 8d 84 00 a4 a5 a0 00 00 00 00 00 00 00 b7 bf 00 a1 bf 00 b1 bf 00 ac bf 00 a6 bf 00 a2 bf 00 b8 bf 00 b6 bf 00 00 09 e0')
    eab_buffer = bytes.fromhex('c0 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 08 00 00 10 00 00 18 00 00 20 00 00 28 00 00 30 00 00 38 00 00 00 00 00')

    eab_write_alternate(interface, eab_address, eab_alternate_zip(regen_buffer, eab_buffer))
