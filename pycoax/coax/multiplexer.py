"""
coax.multiplexer
~~~~~~~~~~~~~~~~
"""

PORT_MAP_3299 = [
    # The 3299-2 port numbers appear to be LSB first
    0b000000,
    0b100000,
    0b010000,
    0b110000,
    0b001000,
    0b101000,
    0b011000,
    0b111000
]

def get_device_address(port):
    if port < 0 or port > 7:
        raise ValueError('Port must be between 0 and 7')

    return PORT_MAP_3299[port]
