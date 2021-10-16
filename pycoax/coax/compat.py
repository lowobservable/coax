"""
coax.compat
~~~~~~~~~~~
"""

from .protocol import PollAction, Poll, PollAck, ReadStatus, ReadTerminalId, \
                      ReadExtendedId, ReadAddressCounterHi, ReadAddressCounterLo, \
                      ReadData, ReadMultiple, Reset, LoadControlRegister, \
                      LoadSecondaryControl, LoadMask, LoadAddressCounterHi, \
                      LoadAddressCounterLo, WriteData, Clear, SearchForward, \
                      SearchBackward, InsertByte, StartOperation, DiagnosticReset, \
                      ReadFeatureId, EABReadData, EABLoadMask, EABWriteAlternate, \
                      EABReadMultiple, EABWriteUnderMask, EABReadStatus
from .features import read_feature_ids, parse_features

def poll(interface, action=PollAction.NONE, **kwargs):
    """Execute a POLL command."""
    return interface.execute(Poll(action), **_convert_kwargs(kwargs))

def poll_ack(interface, **kwargs):
    """Execute a POLL_ACK command."""
    return interface.execute(PollAck(), **_convert_kwargs(kwargs))

def read_status(interface, **kwargs):
    """Execute a READ_STATUS command."""
    return interface.execute(ReadStatus(), **_convert_kwargs(kwargs))

def read_terminal_id(interface, **kwargs):
    """Execute a READ_TERMINAL_ID command."""
    return interface.execute(ReadTerminalId(), **_convert_kwargs(kwargs))

def read_extended_id(interface, **kwargs):
    """Execute a READ_EXTENDED_ID command."""
    return interface.execute(ReadExtendedId(), **_convert_kwargs(kwargs))

def read_address_counter_hi(interface, **kwargs):
    """Execute a READ_ADDRESS_COUNTER_HI command."""
    return interface.execute(ReadAddressCounterHi(), **_convert_kwargs(kwargs))

def read_address_counter_lo(interface, **kwargs):
    """Execute a READ_ADDRESS_COUTER_LO command."""
    return interface.execute(ReadAddressCounterLo(), **_convert_kwargs(kwargs))

def read_data(interface, **kwargs):
    """Execute a READ_DATA command."""
    return interface.execute(ReadData(), **_convert_kwargs(kwargs))

def read_multiple(interface, **kwargs):
    """Execute a READ_MULTIPLE command."""
    return interface.execute(ReadMultiple(), **_convert_kwargs(kwargs))

def reset(interface, **kwargs):
    """Execute a RESET command."""
    return interface.execute(Reset(), **_convert_kwargs(kwargs))

def load_control_register(interface, control, **kwargs):
    """Execute a LOAD_CONTROL_REGISTER command."""
    return interface.execute(LoadControlRegister(control), **_convert_kwargs(kwargs))

def load_secondary_control(interface, control, **kwargs):
    """Execute a LOAD_SECONDARY_CONTROL command."""
    return interface.execute(LoadSecondaryControl(control), **_convert_kwargs(kwargs))

def load_mask(interface, mask, **kwargs):
    """Execute a LOAD_MASK command."""
    return interface.execute(LoadMask(mask), **_convert_kwargs(kwargs))

def load_address_counter_hi(interface, address, **kwargs):
    """Execute a LOAD_ADDRESS_COUNTER_HI command."""
    return interface.execute(LoadAddressCounterHi(address), **_convert_kwargs(kwargs))

def load_address_counter_lo(interface, address, **kwargs):
    """Execute a LOAD_ADDRESS_COUNTER_LO command."""
    return interface.execute(LoadAddressCounterLo(address), **_convert_kwargs(kwargs))

def write_data(interface, data, jumbo_write_strategy=None, **kwargs):
    """Execute a WRITE_DATA command."""
    commands = _split_write(WriteData, data, jumbo_write_strategy)

    responses = interface.execute(commands, **_convert_kwargs(kwargs))

    return responses

def clear(interface, pattern, **kwargs):
    """Execute a CLEAR command."""
    return interface.execute(Clear(pattern), **_convert_kwargs(kwargs))

def search_forward(interface, pattern, **kwargs):
    """Execute a SEARCH_FORWARD command."""
    return interface.execute(SearchForward(pattern), **_convert_kwargs(kwargs))

def search_backward(interface, pattern, **kwargs):
    """Execute a SEARCH_BACKWARD command."""
    return interface.execute(SearchBackward(pattern), **_convert_kwargs(kwargs))

def insert_byte(interface, byte, **kwargs):
    """Execute a INSERT_BYTE command."""
    return interface.execute(InsertByte(byte), **_convert_kwargs(kwargs))

def start_operation(interface, **kwargs):
    """Execute a START_OPERATION command."""
    return interface.execute(StartOperation(), **_convert_kwargs(kwargs))

def diagnostic_reset(interface, **kwargs):
    """Execute a DIAGNOSTIC_RESET command."""
    return interface.execute(DiagnosticReset(), **_convert_kwargs(kwargs))

def read_feature_id(interface, feature_address, **kwargs):
    """Execute a READ_FEATURE_ID command."""
    return interface.execute(ReadFeatureId(feature_address), **_convert_kwargs(kwargs))

def get_features(interface, **kwargs):
    """Get the features a terminal supports."""
    commands = read_feature_ids()

    ids = interface.execute(commands, **_convert_kwargs(kwargs))

    return parse_features(ids, commands)

def eab_read_data(interface, feature_address, **kwargs):
    """Execute a EAB_READ_DATA command."""
    return interface.execute(EABReadData(feature_address), **_convert_kwargs(kwargs))

def eab_load_mask(interface, feature_address, mask, **kwargs):
    """Execute a EAB_LOAD_MASK command."""
    return interface.execute(EABLoadMask(feature_address, mask), **_convert_kwargs(kwargs))

def eab_write_alternate(interface, feature_address, data, jumbo_write_strategy=None, **kwargs):
    """Execute a EAB_WRITE_ALTERNATE command."""
    commands = _split_write(lambda data: EABWriteAlternate(feature_address, data), data,
                            jumbo_write_strategy)

    responses = interface.execute(commands, **_convert_kwargs(kwargs))

    return responses

def eab_read_multiple(interface, feature_address, **kwargs):
    """Execute a EAB_READ_MULTIPLE command."""
    return interface.execute(EABReadMultiple(feature_address), **_convert_kwargs(kwargs))

def eab_write_under_mask(interface, feature_address, byte, **kwargs):
    """Execute a EAB_WRITE_UNDER_MASK command."""
    return interface.execute(EABWriteUnderMask(feature_address, byte), **_convert_kwargs(kwargs))

def eab_read_status(interface, feature_address, **kwargs):
    """Execute a EAB_READ_STATUS command."""
    return interface.execute(EABReadStatus(feature_address), **_convert_kwargs(kwargs))

def _convert_kwargs(kwargs):
    if 'receive_timeout' in kwargs:
        kwargs['timeout'] = kwargs['receive_timeout']

        del kwargs['receive_timeout']

    return kwargs

def _chunked(iterable, size):
    for index in range(0, len(iterable), size):
        yield iterable[index:index+size]

def _split_write(constructor, data, jumbo_write_strategy):
    length = 1

    if isinstance(data, tuple):
        length += len(data[0]) * data[1]
    else:
        length += len(data)

    # To avoid breaking a EAB_WRITE_ALTERNATE command the maximum length must be even
    # and the actual data length will be 2 words less...
    max_length = 32

    if jumbo_write_strategy == 'split' and length > max_length:
        if isinstance(data, tuple):
            expanded_data = data[0] * data[1]
        else:
            expanded_data = data

        return [constructor(chunk) for chunk in _chunked(expanded_data, max_length - 2)]

    return constructor(data)
