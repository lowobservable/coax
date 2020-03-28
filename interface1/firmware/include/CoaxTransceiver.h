// Copyright (c) 2019, Andrew Kay
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

#define ERROR_TX_RECEIVER_ACTIVE -1
#define ERROR_RX_TIMEOUT -2
#define ERROR_RX_OVERFLOW -3
#define ERROR_RX_RECEIVER -4

class CoaxTransceiver {
public:
    static void setup();
    static int /* ssize_t */ transmitReceive(uint16_t *transmitBuffer, size_t transmitBufferCount, uint16_t *receiveBuffer, size_t receiveBufferSize, uint16_t receiveTimeout);

private:
    static void dataBusSetup();
    static void rxSetup();
    static void txSetup();
    static int /* ssize_t */ transmit(uint16_t *buffer, size_t bufferCount);
    static int /* ssize_t */ receive(uint16_t *buffer, size_t bufferSize, uint16_t timeout);
    static void rxActiveInterrupt();

    static volatile uint8_t rxState;
    static volatile uint16_t *rxBuffer;
    static volatile size_t rxBufferSize;
    static volatile int /* ssize_t */ rxBufferCount;
};
