#!/usr/bin/env python

import sys
from enum import Enum
import csv

from coax.protocol import Command, is_data_word, unpack_data_word

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

#class CaptureStream:
#    def __init__(self, stream):
#        self.unpacker = Unpacker(stream, raw=False)
#
#        self.from_party = None
#        self.command = None
#
#    def xxx(self):
#        (timestamp, words, errors) = self._read()
#
#        if self.from_party == Party.CONTROLLER:
#            self.from_party = Party.DEVICE
#        elif self.from_party == Party.DEVICE:
#            self.from_party = Party.CONTROLLER
#
#        if errors:
#            pass
#        elif is_command_word(words[0]) and all(is_data_word(word) for word in words[1:]):
#            if self.from_party != Party.CONTROLLER:
#                if self.from_party is not None:
#                    print('something went out of sync')
#
#                self.from_party = Party.CONTROLLER
#
#            self.command = unpack_command_word(words[0])
#            data = unpack_data_words(words[1:])
#
#            if self.command != Command.POLL.value:
#                print('-> ' + format_command(self.command) + ' ' + format_data(data, self.command))
#        elif all(is_data_word(word) for word in words):
#            data = unpack_data_words(words)
#
#            if not (self.command == Command.POLL.value and len(words) == 1 and words[0] == 0):
#                if self.command == Command.POLL.value:
#                    print('do this missing POLL here')
#
#                print('<- ' + format_data(data, self.command))
#        else:
#            # Strange mix of commands and data...
#            pass
#
#    def _read(self):
#        return self.unpacker.unpack()

def main():
    with open(sys.argv[1], 'r') as capture_file:
        reader = csv.reader(capture_file)

        # Skip the header...
        next(reader)

        for line in reader:
            bits = [int(column) for column in line[1:]]

            # Map the sample bits back into a 10-bit word...
            #
            # | Channel | Pin | Bit
            # |       0 |  23 | D11
            # |       1 |  22 | D10
            # |       2 |  21 | D9
            # |       3 |  20 | D8
            # |       4 |  19 | D7
            # |       5 |  18 | D6
            # |       6 |  17 | D5
            # |       7 |  16 | D4
            # |       8 |  15 | D3
            # |       9 |  14 | D2
            word = (bits[9] << 9) | (bits[8] << 8) | (bits[7] << 7) | (bits[6] << 6) | (bits[5] << 5) | (bits[4] << 4) | (bits[3] << 3) | (bits[2] << 2) | (bits[1] << 1) | bits[0]

            # Is it a command word?
            if is_command_word(word):
                print('C: ' + format_command(unpack_command_word(word)))
            else:
                print('D: ' + '{0:02x}'.format(unpack_data_word(word)))

if __name__ == '__main__':
    main()
