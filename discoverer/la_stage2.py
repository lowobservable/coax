#!/usr/bin/env python

import sys
from enum import Enum

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

def format_data(data, command):
    return ' '.join(['{0:02x}'.format(byte) for byte in data])

def main():
    command = None
    data = None

    for line in sys.stdin:
        line = line.strip()

        if line.startswith('[') and line.endswith(']'):
            words = [int(word) for word in line[1:-1].split(',')]

            if is_command_word(words[0]) and all(is_data_word(word) for word in words[1:]):
                command = unpack_command_word(words[0])
                data = unpack_data_words(words[1:])

                if command != Command.POLL.value:
                    print('-> ' + format_command(command) + ' ' + format_data(data, command))
            elif all(is_data_word(word) for word in words):
                data = unpack_data_words(words)

                if not (command == Command.POLL.value and len(words) == 1 and words[0] == 0):
                    # Okay, perhaps the POLL was interesting so lets print it here.
                    if command == Command.POLL.value:
                        print('-> ' + format_command(command))


                    print('?? ' + format_data(data, command))
            else:
                # Strange mix of commands and data...
                print('!! ' + str(words))

if __name__ == '__main__':
    main()
