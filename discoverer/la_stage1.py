#!/usr/bin/env python

import sys
import csv

def output_words(words):
    print(words)

def main():
    reader = csv.reader(sys.stdin)

    # Skip the header...
    next(reader)

    previous_data_available = None
    previous_receiver_active = None

    words = []

    for line in reader:
        data_available = bool(int(line[11]))
        receiver_active = bool(int(line[12]))

        if receiver_active and not previous_receiver_active:
            if words:
                output_words(words)

            words = []

        if data_available and not previous_data_available:
            bits = [int(column) for column in line[1:11]]

            word = (bits[9] << 9) | (bits[8] << 8) | (bits[7] << 7) | (bits[6] << 6) | (bits[5] << 5) | (bits[4] << 4) | (bits[3] << 3) | (bits[2] << 2) | (bits[1] << 1) | bits[0]

            words.append(word)

        previous_data_available = data_available
        previous_receiver_active = receiver_active

    if words:
        output_words(words)

if __name__ == '__main__':
    main()
