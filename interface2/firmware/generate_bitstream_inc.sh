#!/bin/bash

BITSTREAM=../fpga/rtl/top.bin

if [ ! -f $BITSTREAM ]; then
    echo "Bitstream '$BITSTREAM' not found." >&2
    exit 1
fi

if [ ! $BITSTREAM -nt "src/bitstream.inc" ]; then
    echo "Bitstream '$BITSTREAM' is not newer than generated include file, skipping." >&2
    exit
fi

xxd -i $BITSTREAM | tail -n +2 | head -n -2 > src/bitstream.inc
