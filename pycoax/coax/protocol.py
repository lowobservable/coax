"""
coax.protocol
~~~~~~~~~~~~~
"""

from enum import Enum

from .exceptions import ProtocolError
from .parity import odd_parity

class Command(Enum):
    """Terminal command."""

    # Read Commands
    POLL = 0x01
    POLL_ACK = 0x11
    READ_STATUS = 0x0d
    READ_TERMINAL_ID = 0x09
    READ_EXTENDED_ID = 0x07
    READ_ADDRESS_COUNTER_HI = 0x05
    READ_ADDRESS_COUNTER_LO = 0x15
    READ_DATA = 0x03
    READ_MULTIPLE = 0x0b

    # Write Commands
    RESET = 0x02
    LOAD_CONTROL_REGISTER = 0x0a
    LOAD_SECONDARY_CONTROL = 0x1a
    LOAD_MASK = 0x16
    LOAD_ADDRESS_COUNTER_HI = 0x04
    LOAD_ADDRESS_COUNTER_LO = 0x14
    WRITE_DATA = 0x0c
    CLEAR = 0x06
    SEARCH_FORWARD = 0x10
    SEARCH_BACKWARD = 0x12
    INSERT_BYTE = 0x0e
    START_OPERATION = 0x08
    DIAGNOSTIC_RESET = 0x1c

class PollResponse:
    """Terminal POLL response."""

    @staticmethod
    def is_power_on_reset_complete(value):
        """Is the response word a power on reset complete response?"""
        return value == 0xa

    @staticmethod
    def is_keystroke(value):
        """Is the response word a keystroke response?"""
        return ((value & 0x2) == 0x2) and ((value & 0x1) == 0)

    def __init__(self, value):
        self.value = value

class PowerOnResetCompletePollResponse(PollResponse):
    """Terminal power-on-reset complete poll response."""

    def __init__(self, value):
        if not PollResponse.is_power_on_reset_complete(value):
            raise ValueError('Invalid POR poll response')

        super().__init__(value)

class KeystrokePollResponse(PollResponse):
    """Terminal keystroke poll response."""

    def __init__(self, value):
        if not PollResponse.is_keystroke(value):
            raise ValueError('Invalid keystroke poll response')

        super().__init__(value)

        self.scan_code = (value >> 2) & 0xff

class TerminalId:
    """Terminal model and keyboard."""

    def __init__(self, value):
        if (value & 0x1) != 0:
            raise ValueError('Invalid terminal identifier')

        self.value = value

        self.model = (value & 0x0e) >> 1
        self.keyboard = (value & 0xf0) >> 4

def poll(interface, **kwargs):
    """Execute a POLL command."""
    response = _execute_read_command(interface, Command.POLL, allow_trta_response=True,
                                     unpack_data_words=False, **kwargs)

    if response is None:
        return None

    word = response[0]

    if PollResponse.is_power_on_reset_complete(word):
        return PowerOnResetCompletePollResponse(word)

    if PollResponse.is_keystroke(word):
        return KeystrokePollResponse(word)

    return PollResponse(word)

def poll_ack(interface, **kwargs):
    """Execute a POLL_ACK command."""
    _execute_write_command(interface, Command.POLL_ACK, **kwargs)

def read_status(interface):
    """Execute a READ_STATUS command."""
    raise NotImplementedError

def read_terminal_id(interface, **kwargs):
    """Execute a READ_TERMINAL_ID command."""
    response = _execute_read_command(interface, Command.READ_TERMINAL_ID, **kwargs)

    return TerminalId(response[0])

def read_extended_id(interface, **kwargs):
    """Execute a READ_EXTENDED_ID command."""
    return _execute_read_command(interface, Command.READ_EXTENDED_ID, 4,
                                 allow_trta_response=True, **kwargs)

def read_address_counter_hi(interface, **kwargs):
    """Execute a READ_ADDRESS_COUNTER_HI command."""
    return _execute_read_command(interface, Command.READ_ADDRESS_COUNTER_HI, **kwargs)[0]

def read_address_counter_lo(interface, **kwargs):
    """Execute a READ_ADDRESS_COUTER_LO command."""
    return _execute_read_command(interface, Command.READ_ADDRESS_COUNTER_LO, **kwargs)[0]

def read_data(interface):
    """Execute a READ_DATA command."""
    raise NotImplementedError

def read_multiple(interface):
    """Execute a READ_MULTIPLE command."""
    raise NotImplementedError

def reset(interface):
    """Execute a RESET command."""
    raise NotImplementedError

def load_control_register(interface):
    """Execute a LOAD_CONTROL_REGISTER command."""
    raise NotImplementedError

def load_secondary_control(interface):
    """Execute a LOAD_SECONDARY_CONTROL command."""
    raise NotImplementedError

def load_mask(interface):
    """Execute a LOAD_MASK command."""
    raise NotImplementedError

def load_address_counter_hi(interface, address, **kwargs):
    """Execute a LOAD_ADDRESS_COUNTER_HI command."""
    _execute_write_command(interface, Command.LOAD_ADDRESS_COUNTER_HI, bytes([address]), **kwargs)

def load_address_counter_lo(interface, address, **kwargs):
    """Execute a LOAD_ADDRESS_COUNTER_LO command."""
    _execute_write_command(interface, Command.LOAD_ADDRESS_COUNTER_LO, bytes([address]), **kwargs)

def write_data(interface, data, **kwargs):
    """Execute a WRITE_DATA command."""
    _execute_write_command(interface, Command.WRITE_DATA, data, **kwargs)

def clear(interface):
    """Execute a CLEAR command."""
    raise NotImplementedError

def search_forward(interface):
    """Execute a SEARCH_FORWARD command."""
    raise NotImplementedError

def search_backward(interface):
    """Execute a SEARCH_BACKWARD command."""
    raise NotImplementedError

def insert_byte(interface):
    """Execute a INSERT_BYTE command."""
    raise NotImplementedError

def start_operation(interface):
    """Execute a START_OPERATION command."""
    raise NotImplementedError

def diagnostic_reset(interface):
    """Execute a DIAGNOSTIC_RESET command."""
    raise NotImplementedError

def _execute_read_command(interface, command, response_length=1,
                          allow_trta_response=False, trta_value=None,
                          unpack_data_words=True, **kwargs):
    """Execute a standard read command."""
    command_word = _pack_command_word(command)

    response = interface.execute(command_word, response_length=response_length, **kwargs)

    if allow_trta_response and len(response) == 1 and response[0] == 0:
        return trta_value

    if len(response) != response_length:
        raise ProtocolError(f'Expected {response_length} word {command.name} response')

    return _unpack_data_words(response) if unpack_data_words else response

def _execute_write_command(interface, command, data=None, **kwargs):
    """Execute a standard write command."""
    command_word = _pack_command_word(command)

    response = interface.execute(command_word, data, **kwargs)

    if len(response) != 1:
        raise ProtocolError(f'Expected 1 word {command.name} response')

    if response[0] != 0:
        raise ProtocolError('Expected TR/TA response')

def _pack_command_word(command, address=0):
    """Pack a command and address into a 10-bit command word for the interface."""
    return (address << 7) | (command.value << 2) | 0x1

def _unpack_data_words(words):
    """Unpack the data bytes from 10-bit data words, performs parity checking."""
    return bytes([_unpack_data_word(word) for word in words])

def _unpack_data_word(word):
    """Unpack the data byte from a 10-bit data word, performs parity checking."""
    if not (word & 0x1) == 0x0:
        raise ProtocolError('Word does not have data bit set')

    byte = (word >> 2) & 0xff
    parity = (word >> 1) & 0x1

    if not odd_parity(byte) == parity:
        raise ProtocolError('Parity error')

    return byte
