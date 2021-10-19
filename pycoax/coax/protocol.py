"""
coax.protocol
~~~~~~~~~~~~~
"""

from enum import Enum

from .interface import FrameFormat
from .parity import odd_parity
from .exceptions import ProtocolError

class Command(Enum):
    """Terminal command."""

    # Base
    POLL = 0x01
    POLL_ACK = 0x11
    READ_STATUS = 0x0d
    READ_TERMINAL_ID = 0x09
    READ_EXTENDED_ID = 0x07
    READ_ADDRESS_COUNTER_HI = 0x05
    READ_ADDRESS_COUNTER_LO = 0x15
    READ_DATA = 0x03
    READ_MULTIPLE = 0x0b

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

    # Feature
    READ_FEATURE_ID = 0x07

    # EAB Feature
    EAB_READ_DATA = 0x03
    EAB_LOAD_MASK = 0x06
    EAB_WRITE_ALTERNATE = 0x0a
    EAB_READ_MULTIPLE = 0x0b
    EAB_WRITE_UNDER_MASK = 0x0c
    EAB_READ_STATUS = 0x0d

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
            raise ValueError(f'Invalid POR poll response: {value}')

        super().__init__(value)

class KeystrokePollResponse(PollResponse):
    """Terminal keystroke poll response."""

    def __init__(self, value):
        if not PollResponse.is_keystroke(value):
            raise ValueError(f'Invalid keystroke poll response: {value}')

        super().__init__(value)

        self.scan_code = (value >> 2) & 0xff

    def __repr__(self):
        return f'<KeystrokePollResponse scan_code={self.scan_code}>'

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

class TerminalType(Enum):
    """Terminal type."""

    CUT = 1
    DFT = 2

class TerminalId:
    """Terminal model and keyboard."""

    _MODEL_MAP = {
        0b010: 2,
        0b011: 3,
        0b111: 4,
        0b110: 5
    }

    def __init__(self, value):
        self.value = value

        if (value & 0x1) == 0:
            self.type = TerminalType.CUT

            model = (value & 0x0e) >> 1

            if model not in TerminalId._MODEL_MAP:
                raise ValueError(f'Invalid model: {model}')

            self.model = TerminalId._MODEL_MAP[model]
            self.keyboard = (value & 0xf0) >> 4
        elif value == 1:
            self.type = TerminalType.DFT
            self.model = None
            self.keyboard = None
        else:
            raise ValueError(f'Invalid terminal identifier: {value}')

    def __repr__(self):
        return (f'<TerminalId type={self.type.name}, model={self.model}, '
                f'keyboard={self.keyboard}>')

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
        return int(bool(self.big))

    def __repr__(self):
        return f'<SecondaryControl big={self.big}>'

class ReadCommand:
    """Base class for read commands."""

    response_length = None

    def pack_outbound_frame(self):
        raise NotImplementedError

    def unpack_inbound_frame(self, words):
        raise NotImplementedError

class WriteCommand:
    """Base class for write commands."""

    response_length = 1

    def pack_outbound_frame(self):
        raise NotImplementedError

    def unpack_inbound_frame(self, words):
        if not is_tt_ar(words):
            raise ProtocolError(f'Expected TT/AR response: {words}')

class Poll(ReadCommand):
    """POLL command."""

    response_length = 1

    def __init__(self, action=PollAction.NONE):
        self.action = action

    def pack_outbound_frame(self):
        command_word = (self.action.value << 8) | pack_command_word(Command.POLL)

        return (FrameFormat.WORD_DATA, command_word)

    def unpack_inbound_frame(self, words):
        if is_tt_ar(words):
            return None

        if len(words) != 1:
            raise ProtocolError(f'Expected 1 word POLL response: {words}')

        word = words[0]

        if PollResponse.is_power_on_reset_complete(word):
            return PowerOnResetCompletePollResponse(word)

        if PollResponse.is_keystroke(word):
            return KeystrokePollResponse(word)

        return PollResponse(word)

class PollAck(WriteCommand):
    """POLL_ACK command."""

    def pack_outbound_frame(self):
        command_word = pack_command_word(Command.POLL_ACK)

        return (FrameFormat.WORD_DATA, command_word)

class ReadStatus(ReadCommand):
    """READ_STATUS command."""

    response_length = 1

    def pack_outbound_frame(self):
        command_word = pack_command_word(Command.READ_STATUS)

        return (FrameFormat.WORD_DATA, command_word)

    def unpack_inbound_frame(self, words):
        if len(words) != 1:
            raise ProtocolError(f'Expected 1 word READ_STATUS response: {words}')

        return Status(unpack_data_word(words[0]))

class ReadTerminalId(ReadCommand):
    """READ_TERMINAL_ID command."""

    response_length = 1

    def pack_outbound_frame(self):
        command_word = pack_command_word(Command.READ_TERMINAL_ID)

        return (FrameFormat.WORD_DATA, command_word)

    def unpack_inbound_frame(self, words):
        if len(words) != 1:
            raise ProtocolError(f'Expected 1 word READ_TERMINAL_ID response: {words}')

        return TerminalId(unpack_data_word(words[0]))

class ReadExtendedId(ReadCommand):
    """READ_EXTENDED_ID command."""

    response_length = 4

    def pack_outbound_frame(self):
        command_word = pack_command_word(Command.READ_EXTENDED_ID)

        return (FrameFormat.WORD_DATA, command_word)

    def unpack_inbound_frame(self, words):
        if is_tt_ar(words):
            return None

        if len(words) != 4:
            raise ProtocolError(f'Expected 4 word READ_EXTENDED_ID response: {words}')

        return unpack_data_words(words)

class ReadAddressCounterHi(ReadCommand):
    """READ_ADDRESS_COUNTER_HI command."""

    response_length = 1

    def pack_outbound_frame(self):
        command_word = pack_command_word(Command.READ_ADDRESS_COUNTER_HI)

        return (FrameFormat.WORD_DATA, command_word)

    def unpack_inbound_frame(self, words):
        if len(words) != 1:
            raise ProtocolError(f'Expected 1 word READ_ADDRESS_COUNTER_HI response: {words}')

        return unpack_data_word(words[0])

class ReadAddressCounterLo(ReadCommand):
    """READ_ADDRESS_COUNTER_LO command."""

    response_length = 1

    def pack_outbound_frame(self):
        command_word = pack_command_word(Command.READ_ADDRESS_COUNTER_LO)

        return (FrameFormat.WORD_DATA, command_word)

    def unpack_inbound_frame(self, words):
        if len(words) != 1:
            raise ProtocolError(f'Expected 1 word READ_ADDRESS_COUNTER_LO response: {words}')

        return unpack_data_word(words[0])

class ReadData(ReadCommand):
    """READ_DATA command."""

    response_length = 1

    def pack_outbound_frame(self):
        command_word = pack_command_word(Command.READ_DATA)

        return (FrameFormat.WORD_DATA, command_word)

    def unpack_inbound_frame(self, words):
        if len(words) != 1:
            raise ProtocolError(f'Expected 1 word READ_DATA response: {words}')

        return unpack_data_word(words[0])

class ReadMultiple(ReadCommand):
    """READ_MULTIPLE command."""

    response_length = 32

    def pack_outbound_frame(self):
        command_word = pack_command_word(Command.READ_MULTIPLE)

        return (FrameFormat.WORD_DATA, command_word)

    def unpack_inbound_frame(self, words):
        if len(words) == 0:
            raise ProtocolError(f'Expected 1 or more word READ_MULTIPLE response: {words}')

        return unpack_data_words(words)

class Reset(WriteCommand):
    """RESET command."""

    def pack_outbound_frame(self):
        command_word = pack_command_word(Command.RESET)

        return (FrameFormat.WORD_DATA, command_word)

class LoadControlRegister(WriteCommand):
    """LOAD_CONTROL_REGISTER command."""

    def __init__(self, control):
        self.control = control

    def pack_outbound_frame(self):
        command_word = pack_command_word(Command.LOAD_CONTROL_REGISTER)

        return (FrameFormat.WORD_DATA, command_word, [self.control.value])

class LoadSecondaryControl(WriteCommand):
    """LOAD_SECONDARY_CONTROL command."""

    def __init__(self, control):
        self.control = control

    def pack_outbound_frame(self):
        command_word = pack_command_word(Command.LOAD_SECONDARY_CONTROL)

        return (FrameFormat.WORD_DATA, command_word, [self.control.value])

class LoadMask(WriteCommand):
    """LOAD_MASK command."""

    def __init__(self, mask):
        self.mask = mask

    def pack_outbound_frame(self):
        command_word = pack_command_word(Command.LOAD_MASK)

        return (FrameFormat.WORD_DATA, command_word, [self.mask])

class LoadAddressCounterHi(WriteCommand):
    """LOAD_ADDRESS_COUNTER_HI command."""

    def __init__(self, address):
        if address < 0 or address > 255:
            raise ValueError('Address is out of range')

        self.address = address

    def pack_outbound_frame(self):
        command_word = pack_command_word(Command.LOAD_ADDRESS_COUNTER_HI)

        return (FrameFormat.WORD_DATA, command_word, [self.address])

class LoadAddressCounterLo(WriteCommand):
    """LOAD_ADDRESS_COUNTER_LO command."""

    def __init__(self, address):
        if address < 0 or address > 255:
            raise ValueError('Address is out of range')

        self.address = address

    def pack_outbound_frame(self):
        command_word = pack_command_word(Command.LOAD_ADDRESS_COUNTER_LO)

        return (FrameFormat.WORD_DATA, command_word, [self.address])

class WriteData(WriteCommand):
    """WRITE_DATA command."""

    def __init__(self, data):
        self.data = data

    def pack_outbound_frame(self):
        command_word = pack_command_word(Command.WRITE_DATA)

        return (FrameFormat.WORD_DATA, command_word, self.data)

class Clear(WriteCommand):
    """CLEAR command."""

    def __init__(self, pattern):
        self.pattern = pattern

    def pack_outbound_frame(self):
        command_word = pack_command_word(Command.CLEAR)

        return (FrameFormat.WORD_DATA, command_word, [self.pattern])

class SearchForward(WriteCommand):
    """SEARCH_FORWARD command."""

    def __init__(self, pattern):
        self.pattern = pattern

    def pack_outbound_frame(self):
        command_word = pack_command_word(Command.SEARCH_FORWARD)

        return (FrameFormat.WORD_DATA, command_word, [self.pattern])

class SearchBackward(WriteCommand):
    """SEARCH_BACKWARD command."""

    def __init__(self, pattern):
        self.pattern = pattern

    def pack_outbound_frame(self):
        command_word = pack_command_word(Command.SEARCH_BACKWARD)

        return (FrameFormat.WORD_DATA, command_word, [self.pattern])

class InsertByte(WriteCommand):
    """INSERT_BYTE command."""

    def __init__(self, byte):
        self.byte = byte

    def pack_outbound_frame(self):
        command_word = pack_command_word(Command.INSERT_BYTE)

        return (FrameFormat.WORD_DATA, command_word, [self.byte])

class StartOperation(WriteCommand):
    """START_OPERATION command."""

    def pack_outbound_frame(self):
        raise NotImplementedError

    def unpack_inbound_frame(self, words):
        raise NotImplementedError

class DiagnosticReset(WriteCommand):
    """DIAGNOSTIC_RESET command."""

    def pack_outbound_frame(self):
        raise NotImplementedError

    def unpack_inbound_frame(self, words):
        raise NotImplementedError

class ReadFeatureId(ReadCommand):
    """READ_FEATURE_ID command."""

    response_length = 1

    def __init__(self, feature_address):
        self.feature_address = feature_address

    def pack_outbound_frame(self):
        command_word = pack_command_word(Command.READ_FEATURE_ID, self.feature_address)

        return (FrameFormat.WORD_DATA, command_word)

    def unpack_inbound_frame(self, words):
        if is_tt_ar(words):
            return None

        if len(words) != 1:
            raise ProtocolError(f'Expected 1 word READ_FEATURE_ID response: {words}')

        return unpack_data_word(words[0])

class EABReadData(ReadCommand):
    """EAB_READ_DATA command."""

    response_length = 1

    def __init__(self, feature_address):
        self.feature_address = feature_address

    def pack_outbound_frame(self):
        command_word = pack_command_word(Command.EAB_READ_DATA, self.feature_address)

        return (FrameFormat.WORD_DATA, command_word)

    def unpack_inbound_frame(self, words):
        if len(words) != 1:
            raise ProtocolError(f'Expected 1 word EAB_READ_DATA response: {words}')

        return unpack_data_words(words)

class EABLoadMask(WriteCommand):
    """EAB_LOAD_MASK command."""

    def __init__(self, feature_address, mask):
        self.feature_address = feature_address
        self.mask = mask

    def pack_outbound_frame(self):
        command_word = pack_command_word(Command.EAB_LOAD_MASK, self.feature_address)

        return (FrameFormat.WORD_DATA, command_word, [self.mask])

class EABWriteAlternate(WriteCommand):
    """EAB_WRITE_ALTERNATE command."""

    def __init__(self, feature_address, data):
        self.feature_address = feature_address
        self.data = data

    def pack_outbound_frame(self):
        command_word = pack_command_word(Command.EAB_WRITE_ALTERNATE, self.feature_address)

        return (FrameFormat.WORD_DATA, command_word, self.data)

class EABReadMultiple(ReadCommand):
    """EAB_READ_MULTIPLE command."""

    response_length = 32

    def __init__(self, feature_address):
        self.feature_address = feature_address

    def pack_outbound_frame(self):
        command_word = pack_command_word(Command.EAB_READ_MULTIPLE, self.feature_address)

        return (FrameFormat.WORD_DATA, command_word)

    def unpack_inbound_frame(self, words):
        return unpack_data_words(words)

class EABWriteUnderMask(WriteCommand):
    """EAB_WRITE_UNDER_MASK command."""

    def __init__(self, feature_address, byte):
        self.feature_address = feature_address
        self.byte = byte

    def pack_outbound_frame(self):
        command_word = pack_command_word(Command.EAB_WRITE_UNDER_MASK, self.feature_address)

        return (FrameFormat.WORD_DATA, command_word, [self.byte])

class EABReadStatus(ReadCommand):
    """EAB_READ_STATUS command."""

    response_length = 1

    def __init__(self, feature_address):
        self.feature_address = feature_address

    def pack_outbound_frame(self):
        command_word = pack_command_word(Command.EAB_READ_STATUS, self.feature_address)

        return (FrameFormat.WORD_DATA, command_word)

    def unpack_inbound_frame(self, words):
        if len(words) != 1:
            raise ProtocolError(f'Expected 1 word EAB_READ_STATUS response: {words}')

        return unpack_data_word(words[0])

class Data(WriteCommand):
    """Unaccompanied data."""

    def __init__(self, data):
        self.data = data

    def pack_outbound_frame(self):
        return (FrameFormat.DATA, self.data)

def pack_command_word(command, feature_address=None):
    """Pack a command into a 10-bit command word."""
    if feature_address is not None and (feature_address < 2 or feature_address > 15):
        raise ValueError(f'Invalid feature address: {feature_address}')

    return (feature_address << 6 if feature_address is not None else 0) | (command.value << 2) | 0x1

def pack_data_word(byte, set_parity=True):
    """Pack a data byte into a 10-bit data word."""
    parity = odd_parity(byte) if set_parity else 0

    return (byte << 2) | (parity << 1)

def is_tt_ar(words):
    """Is the word a TT/AR (transmission turnaround / auto response)?"""
    return len(words) == 1 and words[0] == 0

def is_data_word(word):
    """Is data word bit set?"""
    return (word & 0x1) == 0

def unpack_data_word(word, check_parity=False):
    """Unpack the data byte from a 10-bit data word."""
    if not is_data_word(word):
        raise ProtocolError(f'Word does not have data bit set: {word}')

    byte = (word >> 2) & 0xff
    parity = (word >> 1) & 0x1

    if check_parity and parity != odd_parity(byte):
        raise ProtocolError(f'Parity error: {word}')

    return byte

def pack_data_words(bytes_, set_parity=True):
    """Pack data bytes into 10-bit data words."""
    return [pack_data_word(byte, set_parity=set_parity) for byte in bytes_]

def unpack_data_words(words, check_parity=False):
    """Unpack the data bytes from 10-bit data words."""
    return bytes([unpack_data_word(word, check_parity=check_parity) for word in words])
