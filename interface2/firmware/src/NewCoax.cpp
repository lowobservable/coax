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

#include <Arduino.h>

#include "NewCoax.h"

#define RESET_PIN 5 // -> FPGA 6

#define TX_ACTIVE_PIN 3 // -> FPGA 3
#define TX_LOAD_PIN 6 // -> FPGA 7
#define TX_FULL_PIN 7 // -> FPGA 8

#define RX_ENABLE_PIN 8 // -> FPGA 9
#define RX_ACTIVE_PIN 9 // -> FPGA 10
#define RX_ERROR_PIN 10 // -> FPGA 11
#define RX_DATA_AVAILABLE_PIN 11 // -> FPGA 12
#define RX_READ_PIN 12 // -> FPGA 13

#define DATA_BUS_START_PIN 14
#define DATA_BUS_END_PIN 23
#define DATA_BUS_MASK 0x0fcf0000

static NewCoaxReceiver *receiver = NULL;

void rxActiveInterrupt()
{
    if (receiver == NULL) {
        return;
    }

    receiver->activeInterrupt();
}

void rxErrorInterrupt()
{
    if (receiver == NULL) {
        return;
    }

    receiver->errorInterrupt();
}

void rxDataAvailableInterrupt()
{
    if (receiver == NULL) {
        return;
    }

    receiver->dataAvailableInterrupt();
}

void NewCoaxReceiver::begin()
{
    receiver = this;

    pinMode(RESET_PIN, OUTPUT);

    pinMode(RX_ENABLE_PIN, OUTPUT);
    pinMode(RX_ACTIVE_PIN, INPUT);
    pinMode(RX_ERROR_PIN, INPUT);
    pinMode(RX_DATA_AVAILABLE_PIN, INPUT);
    pinMode(RX_READ_PIN, OUTPUT);

    attachInterrupt(digitalPinToInterrupt(RX_ACTIVE_PIN), rxActiveInterrupt, RISING);
    attachInterrupt(digitalPinToInterrupt(RX_ERROR_PIN), rxErrorInterrupt, RISING);
    attachInterrupt(digitalPinToInterrupt(RX_DATA_AVAILABLE_PIN), rxDataAvailableInterrupt, RISING);
}

void NewCoaxReceiver::enable()
{
    _dataBus.setMode(INPUT, false);

    _state = Idle;

    digitalWrite(RX_ENABLE_PIN, HIGH);
}

void NewCoaxReceiver::disable()
{
    digitalWrite(RX_ENABLE_PIN, LOW);

    _state = Disabled;
}

#define FRAME_END 0xc0
#define FRAME_ESCAPE 0xdb
#define FRAME_ESCAPE_END 0xdc
#define FRAME_ESCAPE_ESCAPE 0xdd

inline void slipWrite(uint8_t value)
{
    if (value == FRAME_END) {
        Serial.write(FRAME_ESCAPE);
        Serial.write(FRAME_ESCAPE_END);
    } else if (value == FRAME_ESCAPE) {
        Serial.write(FRAME_ESCAPE);
        Serial.write(FRAME_ESCAPE_ESCAPE);
    } else {
        Serial.write(value);
    }
}

inline void slipWrite(uint16_t value)
{
    // Byte order consistent with original interface...
    slipWrite((uint8_t) (value & 0xff));
    slipWrite((uint8_t) ((value >> 8) & 0xff));
}

inline void slipWrite(uint32_t value)
{
    slipWrite((uint8_t) (value & 0xff));
    slipWrite((uint8_t) ((value >> 8) & 0xff));
    slipWrite((uint8_t) ((value >> 16) & 0xff));
    slipWrite((uint8_t) ((value >> 24) & 0xff));
}

void NewCoaxReceiver::activeInterrupt()
{
    if (_state != Idle) {
        return;
    }

    // Flush any old data.
    if (digitalRead(RX_DATA_AVAILABLE_PIN)) {
        read();
    }

    Serial.write(FRAME_END);

    slipWrite(millis());

    _state = Receiving;
}

void NewCoaxReceiver::dataAvailableInterrupt()
{
    if (_state != Receiving) {
        return;
    }

    uint16_t word = read();

    slipWrite(word);

    // TODO: this is wrong... but it allows things to settle!
    delayMicroseconds(1);

    if (!digitalRead(RX_ACTIVE_PIN) && !digitalRead(RX_DATA_AVAILABLE_PIN)) {
        Serial.write(FRAME_END);

        _state = Idle;
    }
}

void NewCoaxReceiver::errorInterrupt()
{
    if (_state != Receiving) {
        return;
    }

    uint16_t error = 0x8000 | _dataBus.read();

    slipWrite(error);

    reset();
}

void NewCoaxReceiver::reset()
{
    digitalWrite(RESET_PIN, HIGH);
    delayMicroseconds(1);
    digitalWrite(RESET_PIN, LOW);
}

inline uint16_t NewCoaxReceiver::read()
{
    digitalWrite(RX_READ_PIN, HIGH);

    uint16_t word = _dataBus.read();

    delayMicroseconds(1);

    digitalWrite(RX_READ_PIN, LOW);

    return word;
}

void NewCoaxDataBus::setMode(uint8_t mode, bool force)
{
    if (mode == _mode && !force) {
        return;
    }

    for (int pin = DATA_BUS_START_PIN; pin <= DATA_BUS_END_PIN; pin++) {
        pinMode(pin, mode);
    }

    _mode = mode;
}

inline uint16_t NewCoaxDataBus::read()
{
    return decode((GPIO6_DR & DATA_BUS_MASK) >> 16);
}

inline void NewCoaxDataBus::write(uint16_t word)
{
    uint32_t bus = (encode(word) << 16) & DATA_BUS_MASK;

    GPIO6_DR_SET = bus;
    GPIO6_DR_CLEAR = ~bus;
}

inline uint16_t NewCoaxDataBus::encode(uint16_t word)
{
    return ((word & 0x0020) >> 5)
           | ((word & 0x0010) >> 3)
           | (word & 0x0300)
           | ((word & 0x0003) << 2)
           | ((word & 0x0008) << 3)
           | ((word & 0x00c0) << 4)
           | ((word & 0x0004) << 5);
}

inline uint16_t NewCoaxDataBus::decode(uint16_t word)
{
    return ((word & 0x0080) >> 5)
           | ((word & 0x0c00) >> 4)
           | ((word & 0x0040) >> 3)
           | ((word & 0x000c) >> 2)
           | (word & 0x0300)
           | ((word & 0x0002) << 3)
           | ((word & 0x0001) << 5);
}
