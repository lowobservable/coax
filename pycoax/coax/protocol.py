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

class PollAction(Enum):
    """Terminal POLL action."""

    NONE = 0x0
    ALARM = 0x2
    ENABLE_KEYBOARD_CLICKER = 0x3
    DISABLE_KEYBOARD_CLICKER = 0x1

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

class Status:
    """Terminal status."""

    def __init__(self, value):
        self.value = value

        self.monocase = bool(value & 0x80)
        self.busy = not bool(value & 0x20)
        self.feature_error = bool(value & 0x04)
        self.operation_complete = bool(value & 0x02)

    def __repr__(self):
        return (f'<Status monocase={self.monocase}, busy={self.busy}, '
                f'feature_error={self.feature_error}, '
                f'operation_complete={self.operation_complete}>')

class TerminalId:
    """Terminal model and keyboard."""

    _MODEL_MAP = {
        0b010: 2,
        0b011: 3,
        0b111: 4,
        0b110: 5
    }

    def __init__(self, value):
        if (value & 0x1) != 0:
            raise ValueError('Invalid terminal identifier')

        self.value = value

        model = (value & 0x0e) >> 1

        if model not in TerminalId._MODEL_MAP:
            raise ValueError('Invalid model')

        self.model = TerminalId._MODEL_MAP[model]
        self.keyboard = (value & 0xf0) >> 4

    def __repr__(self):
        return f'<TerminalId model={self.model}, keyboard={self.keyboard}>'

class Control:
    """Terminal control register."""

    def __init__(self, step_inhibit=False, display_inhibit=False, cursor_inhibit=False,
                 cursor_reverse=False, cursor_blink=False):
        self.step_inhibit = step_inhibit
        self.display_inhibit = display_inhibit
        self.cursor_inhibit = cursor_inhibit
        self.cursor_reverse = cursor_reverse
        self.cursor_blink = cursor_blink

    @property
    def value(self):
        value = bool(self.step_inhibit) << 4
        value |= bool(self.display_inhibit) << 3
        value |= bool(self.cursor_inhibit) << 2
        value |= bool(self.cursor_reverse) << 1
        value |= bool(self.cursor_blink)

        return value

    def __repr__(self):
        return (f'<Control step_inhibit={self.step_inhibit}>, '
                f'display_inhibit={self.display_inhibit}, '
                f'cursor_inhibit={self.cursor_inhibit}, '
                f'cursor_reverse={self.cursor_reverse}, '
                f'cursor_blink={self.cursor_blink}>')

class SecondaryControl:
    """Terminal secondary control register."""

    def __init__(self, big=False):
        self.big = big

    @property
    def value(self):
        return bool(self.big) | 0

    def __repr__(self):
        return f'<SecondaryControl big={self.big}>'

def poll(interface, action=PollAction.NONE, **kwargs):
    """Execute a POLL command."""
    command_word = (action.value << 8) | pack_command_word(Command.POLL)

    response = _execute_read_command(interface, command_word, allow_trta_response=True,
                                     unpack=False, **kwargs)

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
    command_word = pack_command_word(Command.POLL_ACK)

    _execute_write_command(interface, command_word, **kwargs)

def read_status(interface, **kwargs):
    """Execute a READ_STATUS command."""
    command_word = pack_command_word(Command.READ_STATUS)

    response = _execute_read_command(interface, command_word, **kwargs)

    return Status(response[0])

def read_terminal_id(interface, **kwargs):
    """Execute a READ_TERMINAL_ID command."""
    command_word = pack_command_word(Command.READ_TERMINAL_ID)

    response = _execute_read_command(interface, command_word, **kwargs)

    return TerminalId(response[0])

def read_extended_id(interface, **kwargs):
    """Execute a READ_EXTENDED_ID command."""
    command_word = pack_command_word(Command.READ_EXTENDED_ID)

    return _execute_read_command(interface, command_word, 4, allow_trta_response=True,
                                 **kwargs)

def read_address_counter_hi(interface, **kwargs):
    """Execute a READ_ADDRESS_COUNTER_HI command."""
    command_word = pack_command_word(Command.READ_ADDRESS_COUNTER_HI)

    return _execute_read_command(interface, command_word, **kwargs)[0]

def read_address_counter_lo(interface, **kwargs):
    """Execute a READ_ADDRESS_COUTER_LO command."""
    command_word = pack_command_word(Command.READ_ADDRESS_COUNTER_LO)

    return _execute_read_command(interface, command_word, **kwargs)[0]

def read_data(interface, **kwargs):
    """Execute a READ_DATA command."""
    command_word = pack_command_word(Command.READ_DATA)

    return _execute_read_command(interface, command_word, **kwargs)

def read_multiple(interface, **kwargs):
    """Execute a READ_MULTIPLE command."""
    command_word = pack_command_word(Command.READ_MULTIPLE)

    return _execute_read_command(interface, command_word, 32,
                                 validate_response_length=False, **kwargs)

def reset(interface, **kwargs):
    """Execute a RESET command."""
    command_word = pack_command_word(Command.RESET)

    _execute_write_command(interface, command_word, **kwargs)

def load_control_register(interface, control, **kwargs):
    """Execute a LOAD_CONTROL_REGISTER command."""
    command_word = pack_command_word(Command.LOAD_CONTROL_REGISTER)

    _execute_write_command(interface, command_word, bytes([control.value]), **kwargs)

def load_secondary_control(interface, control, **kwargs):
    """Execute a LOAD_SECONDARY_CONTROL command."""
    command_word = pack_command_word(Command.LOAD_SECONDARY_CONTROL)

    _execute_write_command(interface, command_word, bytes([control.value]), **kwargs)

def load_mask(interface, mask, **kwargs):
    """Execute a LOAD_MASK command."""
    command_word = pack_command_word(Command.LOAD_MASK)

    _execute_write_command(interface, command_word, bytes([mask]), **kwargs)

def load_address_counter_hi(interface, address, **kwargs):
    """Execute a LOAD_ADDRESS_COUNTER_HI command."""
    command_word = pack_command_word(Command.LOAD_ADDRESS_COUNTER_HI)

    _execute_write_command(interface, command_word, bytes([address]), **kwargs)

def load_address_counter_lo(interface, address, **kwargs):
    """Execute a LOAD_ADDRESS_COUNTER_LO command."""
    command_word = pack_command_word(Command.LOAD_ADDRESS_COUNTER_LO)

    _execute_write_command(interface, command_word, bytes([address]), **kwargs)

def write_data(interface, data, **kwargs):
    """Execute a WRITE_DATA command."""
    command_word = pack_command_word(Command.WRITE_DATA)

    _execute_write_command(interface, command_word, data, **kwargs)

def clear(interface, pattern, **kwargs):
    """Execute a CLEAR command."""
    command_word = pack_command_word(Command.CLEAR)

    _execute_write_command(interface, command_word, bytes([pattern]), **kwargs)

def search_forward(interface, pattern, **kwargs):
    """Execute a SEARCH_FORWARD command."""
    command_word = pack_command_word(Command.SEARCH_FORWARD)

    _execute_write_command(interface, command_word, bytes([pattern]), **kwargs)

def search_backward(interface, pattern, **kwargs):
    """Execute a SEARCH_BACKWARD command."""
    command_word = pack_command_word(Command.SEARCH_BACKWARD)

    _execute_write_command(interface, command_word, bytes([pattern]), **kwargs)

def insert_byte(interface, byte, **kwargs):
    """Execute a INSERT_BYTE command."""
    command_word = pack_command_word(Command.INSERT_BYTE)

    _execute_write_command(interface, command_word, bytes([byte]), **kwargs)

def start_operation(interface):
    """Execute a START_OPERATION command."""
    raise NotImplementedError

def diagnostic_reset(interface):
    """Execute a DIAGNOSTIC_RESET command."""
    raise NotImplementedError

def pack_command_word(command):
    """Pack a command into a 10-bit command word."""
    return (command.value << 2) | 0x1

def is_command_word(word):
    """Is command word bit set?"""
    return (word & 0x1) == 1

def unpack_command_word(word):
    """Unpack a 10-bit command word."""
    if not is_command_word(word):
        raise ProtocolError('Word does not have command bit set')

    command = (word >> 2) & 0x1f

    return Command(command)

def pack_data_word(byte, set_parity=True):
    """Pack a data byte into a 10-bit data word."""
    parity = odd_parity(byte) if set_parity else 0

    return (byte << 2) | (parity << 1)

def is_data_word(word):
    """Is data word bit set?"""
    return (word & 0x1) == 0

def unpack_data_word(word, check_parity=False):
    """Unpack the data byte from a 10-bit data word."""
    if not is_data_word(word):
        raise ProtocolError('Word does not have data bit set')

    byte = (word >> 2) & 0xff
    parity = (word >> 1) & 0x1

    if check_parity and parity != odd_parity(byte):
        raise ProtocolError('Parity error')

    return byte

def pack_data_words(bytes_, set_parity=True):
    """Pack data bytes into 10-bit data words."""
    return [pack_data_word(byte, set_parity=set_parity) for byte in bytes_]

def unpack_data_words(words, check_parity=False):
    """Unpack the data bytes from 10-bit data words."""
    return bytes([unpack_data_word(word, check_parity=check_parity) for word in words])

def _execute_read_command(interface, command_word, response_length=1,
                          validate_response_length=True, allow_trta_response=False,
                          trta_value=None, unpack=True, **kwargs):
    """Execute a standard read command."""
    response = interface.transmit_receive([command_word], receive_length=response_length,
                                          **kwargs)

    if allow_trta_response and len(response) == 1 and response[0] == 0:
        return trta_value

    if validate_response_length and len(response) != response_length:
        command = unpack_command_word(command_word)

        raise ProtocolError(f'Expected {response_length} word {command.name} response')

    return unpack_data_words(response) if unpack else response

def _execute_write_command(interface, command_word, data=None, **kwargs):
    """Execute a standard write command."""
    data_words = []
    transmit_repeat_count = None

    if isinstance(data, tuple):
        data_words = pack_data_words(data[0])
        transmit_repeat_count = data[1]
    elif data is not None:
        data_words = pack_data_words(data)

    response = interface.transmit_receive([command_word, *data_words],
                                          transmit_repeat_count,
                                          receive_length=1, **kwargs)

    if len(response) != 1:
        command = unpack_command_word(command_word)

        raise ProtocolError(f'Expected 1 word {command.name} response')

    if response[0] != 0:
        raise ProtocolError('Expected TR/TA response')
