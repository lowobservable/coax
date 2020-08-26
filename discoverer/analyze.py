#!/usr/bin/env python

import sys
from enum import Enum

from msgpack import Unpacker

from coax.protocol import Command, is_data_word, unpack_data_words

from display import CHAR_MAP

COMMANDS = { command.value: command.name for command in Command }

# These got removed from the most recent pycoax...
def is_command_word(word):
    return (word & 0x1) == 1

def unpack_command_word(word):
    if not is_command_word(word):
        raise ProtocolError(f'Word does not have command bit set: {word}')

    command = (word >> 2) & 0x1f

    return command

def format_command(command):
    if command in COMMANDS:
        return '<' + COMMANDS[command] + '>'

    return f'<{command:02x}>'

printable_commands = set([Command.WRITE_DATA.value])

def format_data(data, command):
    line = ''

    in_a_printable_stream = False

    for byte in data:
        if command in printable_commands and byte in CHAR_MAP:
            if not in_a_printable_stream:
                line += '\''

            line += CHAR_MAP[byte]

            in_a_printable_stream = True
        else:
            if in_a_printable_stream:
                in_a_printable_stream = False
                line += '\' '

            line += '{0:02x} '.format(byte)

    if in_a_printable_stream:
        line += '\''

    return line.strip()

class Party(Enum):
    CONTROLLER = 1
    DEVICE = 2

class CaptureStream:
    def __init__(self, stream):
        self.unpacker = Unpacker(stream, raw=False)

        self.from_party = None
        self.command = None

    def xxx(self):
        (timestamp, words, errors) = self._read()

        if self.from_party == Party.CONTROLLER:
            self.from_party = Party.DEVICE
        elif self.from_party == Party.DEVICE:
            self.from_party = Party.CONTROLLER

        if errors:
            pass
        elif is_command_word(words[0]) and all(is_data_word(word) for word in words[1:]):
            if self.from_party != Party.CONTROLLER:
                if self.from_party is not None:
                    print('something went out of sync')

                self.from_party = Party.CONTROLLER

            self.command = unpack_command_word(words[0])
            data = unpack_data_words(words[1:])

            if self.command != Command.POLL.value:
                print('-> ' + format_command(self.command) + ' ' + format_data(data, self.command))
        elif all(is_data_word(word) for word in words):
            data = unpack_data_words(words)

            if not (self.command == Command.POLL.value and len(words) == 1 and words[0] == 0):
                if self.command == Command.POLL.value:
                    print('do this missing POLL here')

                print('<- ' + format_data(data, self.command))
        else:
            # Strange mix of commands and data...
            pass

    def _read(self):
        return self.unpacker.unpack()

def main():
    with open(sys.argv[1], 'rb') as capture_file:
        capture_stream = CaptureStream(capture_file)

        while True:
            capture_stream.xxx()

if __name__ == '__main__':
    main()
