"""
coax.interface
~~~~~~~~~~~~~~
"""

from enum import Enum

from .exceptions import ProtocolError

class Interface:
    """3270 coax interface."""

    def __init__(self):
        self.features = set()

    def reset(self):
        """Reset the interface."""
        raise NotImplementedError

    def execute(self, commands, timeout=None):
        """Execute one or more commands."""
        (normalized_commands, has_multiple_commands) = _normalize_commands(commands)

        responses = self._execute(normalized_commands, timeout)

        if has_multiple_commands:
            return responses

        response = responses[0]

        if isinstance(response, BaseException):
            raise response

        return response

    def _execute(self, commands, timeout):
        (outbound_frames, response_lengths) = _pack_outbound_frames(commands)

        inbound_frames = self._transmit_receive(outbound_frames, response_lengths, timeout)

        responses = _unpack_inbound_frames(inbound_frames, commands)

        return responses

    def _transmit_receive(self, outbound_frames, response_lengths, timeout):
        raise NotImplementedError

class InterfaceFeature(Enum):
    """Interface feature."""

    PROTOCOL_3299 = 0x10

class FrameFormat(Enum):
    """3270 coax frame format."""

    WORDS = 1 # 10-bit words
    WORD_DATA = 2 # 10-bit word, 8-bit data words
    DATA = 4 # 8-bit data words

def _is_command(command):
    return hasattr(command, 'pack_outbound_frame') and hasattr(command, 'unpack_inbound_frame')

def _normalize_command(command):
    if _is_command(command):
        return (None, command)

    if not isinstance(command, tuple):
        raise TypeError('Invalid command form')

    if len(command) != 2:
        raise TypeError('Invalid command form')

    if not (command[0] is None or isinstance(command[0], int)):
        raise TypeError('Invalid command form')

    if not _is_command(command[1]):
        raise TypeError('Invalid command form')

    return command

def _normalize_commands(commands):
    try:
        command = _normalize_command(commands)

        return ([command], False)
    except TypeError:
        pass

    try:
        commands = list(commands)
    except TypeError:
        raise TypeError('Commands must be valid command or iterable')

    if not commands:
        raise ValueError('Commands must not be empty')

    return ([_normalize_command(command) for command in commands], True)

def _pack_outbound_frames(commands):
    frames = []
    response_lengths = []

    for (address, command) in commands:
        frame = command.pack_outbound_frame()
        response_length = command.response_length or 1

        frames.append((address, frame))
        response_lengths.append(response_length)

    return (frames, response_lengths)

def _unpack_inbound_frames(frames, commands):
    responses = []

    for (frame, (_, command)) in zip(frames, commands):
        if isinstance(frame, BaseException):
            responses.append(frame)
        else:
            try:
                response = command.unpack_inbound_frame(frame)
            except ProtocolError as error:
                response = error

            responses.append(response)

    return responses
