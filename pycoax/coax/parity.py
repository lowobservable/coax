"""
coax.parity
~~~~~~~~~~~

Single byte parity computation
"""

# From http://p-nand-q.com/python/algorithms/math/bit-parity.html
def _parallel_swar(i):
    i = i - ((i >> 1) & 0x55555555)
    i = (i & 0x33333333) + ((i >> 2) & 0x33333333)
    i = (((i + (i >> 4)) & 0x0F0F0F0F) * 0x01010101) >> 24
    return int(i % 2)

_PARITY_LOOKUP = [_parallel_swar(i) for i in range(256)]

def even_parity(byte):
    """Compute even parity"""
    if byte < 0 or byte > 255:
        raise ValueError('Input must be between 0 and 255')

    return _PARITY_LOOKUP[byte]

def odd_parity(byte):
    """Compute odd parity"""
    return int(not even_parity(byte))
