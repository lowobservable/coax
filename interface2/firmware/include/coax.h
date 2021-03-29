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

#define COAX_ERROR_TX_RECEIVER_ACTIVE -1
#define COAX_ERROR_TX_UNDERFLOW -2

#define COAX_ERROR_RX_LOSS_OF_MID_BIT_TRANSITION -1
#define COAX_ERROR_RX_PARITY -2
#define COAX_ERROR_RX_INVALID_END_SEQUENCE -4
#define COAX_ERROR_RX_OVERFLOW -8
#define COAX_ERROR_RX_UNKNOWN -513

#define COAX_ERROR_NOT_INITIALIZED -1024

enum class CoaxParity
{
    Odd = 0,
    Even = 1
};

class SPICoaxTransceiver;

class Coax
{
public:
    Coax(SPICoaxTransceiver &spiCoaxTransceiver, CoaxParity parity,
            volatile uint16_t *buffer, size_t bufferSize);

    bool init();

    void reset();

    int transmit(const uint16_t *buffer, size_t bufferCount);
    int receive(uint16_t *buffer, size_t bufferSize, uint16_t timeout);

    void handleInterrupt();

private:
    SPICoaxTransceiver &_spiCoaxTransceiver;
    CoaxParity _parity;

    bool _isInitialized;

    volatile enum {
        COAX_INTERRUPT_STATE_IDLE,
        COAX_INTERRUPT_STATE_DISABLED,
        COAX_INTERRUPT_STATE_RECEIVING,
        COAX_INTERRUPT_STATE_RECEIVED,
        COAX_INTERRUPT_STATE_ERROR
    } _interruptState = COAX_INTERRUPT_STATE_DISABLED;

    volatile uint16_t *_buffer;
    size_t _bufferSize;
    volatile size_t _bufferCount = 0;
    volatile int _error = 0;
};

#define COAX_REGISTER_STATUS 0x1
#define COAX_REGISTER_STATUS_RX_ERROR 0x40
#define COAX_REGISTER_STATUS_RX_ACTIVE 0x20
#define COAX_REGISTER_STATUS_TX_COMPLETE 0x08
#define COAX_REGISTER_STATUS_TX_ACTIVE 0x04

#define COAX_REGISTER_CONTROL 0x2
#define COAX_REGISTER_CONTROL_LOOPBACK 0x01
#define COAX_REGISTER_CONTROL_TX_PARITY 0x08
#define COAX_REGISTER_CONTROL_RX_PARITY 0x40

#define COAX_REGISTER_DEVICE_ID 0xf

class SPICoaxTransceiver
{
public:
    SPICoaxTransceiver();

    bool init();

    void reset();

    uint8_t readRegister(uint8_t index);
    void writeRegister(uint8_t index, uint8_t value, uint8_t mask);

    int transmit(const uint16_t *buffer, size_t bufferCount);
    int receive(uint16_t *buffer, size_t bufferSize);

    void setLoopback(bool loopback);
    void setTXParity(CoaxParity parity);
    void setRXParity(CoaxParity parity);

    inline bool isTXComplete()
    {
        return readRegister(COAX_REGISTER_STATUS) & COAX_REGISTER_STATUS_TX_COMPLETE;
    }

    inline bool isRXActive()
    {
        return readRegister(COAX_REGISTER_STATUS) & COAX_REGISTER_STATUS_RX_ACTIVE;
    };

private:
    void spiTransfer(const uint8_t *transmitBuffer, uint8_t *receiveBuffer, size_t count);
};
