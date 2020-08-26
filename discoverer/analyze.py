#!/usr/bin/env python

import sys

from msgpack import Unpacker

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

def format_command(word):
    if word in COMMANDS:
        return COMMANDS[word]

    return word

def main():
    command = None

    with open(sys.argv[1], 'rb') as capture_file:
        unpacker = Unpacker(capture_file, raw=False)

        for (timestamp, words, errors) in unpacker:
            if errors:
                print('E')
            else:
                line = ''

                is_single_data_word = (len(words) == 1 and is_data_word(words[0]))
                is_trta = (len(words) == 0 and words[0] == 0)

                for word in words:
                    if is_command_word(word):
                        command = unpack_command_word(word)

                        if command in COMMANDS:
                            line += '<' + COMMANDS[command] + '> '
                        else:
                            line += f'<{word:04x}> '
                    elif is_data_word(word):
                        data = unpack_data_word(word)

                        if command == Command.WRITE_DATA.value and data in CHAR_MAP:
                            line += CHAR_MAP[data]
                        else:
                            line += f'{data:02x} '
                    else:
                        line += f'[{word:04x}] '

                # Hide POLLs and TRTAs
                if command != Command.POLL.value and not is_trta:
                    print(line)

if __name__ == '__main__':
    main()
