// Copyright (c) 2020, Andrew Kay
//
// Permission to use, copy, modify, and/or distribute this software for any
// purpose with or without fee is hereby granted, provided that the above
// copyright notice and this permission notice appear in all copies.
//
// THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
// WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
// MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
// ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
// WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
// ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
// OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

#pragma once

#include <cstdint>
#include <cstddef>

#include "coax.h"
#include "indicators.h"

#define COMMAND_RESET 0x01
#define COMMAND_TRANSMIT_RECEIVE 0x06
#define COMMAND_INFO 0xf0
#define COMMAND_TEST 0xf1
#define COMMAND_DFU 0xf2

#define INFO_SUPPORTED_QUERIES 0x01
#define INFO_HARDWARE_TYPE 0x02
#define INFO_HARDWARE_REVISION 0x03
#define INFO_HARDWARE_SERIAL 0x04
#define INFO_FIRMWARE_VERSION 0x05
#define INFO_MESSAGE_BUFFER_SIZE 0x06
#define INFO_FEATURES 0x07

#define TEST_SUPPORTED_TESTS 0x01

#define ERROR_INVALID_MESSAGE 1
#define ERROR_UNKNOWN_COMMAND 2
#define ERROR_MESSAGE_TIMEOUT 3

class Interface
{
public:
    Interface(Coax &coax, Indicators &indicators);

    void handleMessage(uint8_t *buffer, size_t bufferCount);
    void handleError(MessageReceiverError error);

private:
    Coax &_coax;
    Indicators &_indicators;

    void handleReset(uint8_t *buffer, size_t bufferCount);
    void handleTransmitReceive(uint8_t *buffer, size_t bufferCount);
    void handleInfo(uint8_t *buffer, size_t bufferCount);
    void handleTest(uint8_t *buffer, size_t bufferCount);
    void handleDFU(uint8_t *buffer, size_t bufferCount);
};
