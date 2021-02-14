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

#include <Arduino.h>

#include "CoaxTransceiver.h"

#define FRAME_END 0xc0
#define FRAME_ESCAPE 0xdb
#define FRAME_ESCAPE_END 0xdc
#define FRAME_ESCAPE_ESCAPE 0xdd

enum {
    WAIT_START,
    DATA,
    ESCAPE
} frameState;

#define FRAME_BUFFER_SIZE ((25 * 80) * 2) + 32

uint8_t frameBuffer[FRAME_BUFFER_SIZE];
int frameBufferCount = 0;

#define ERROR_INVALID_MESSAGE 1
#define ERROR_UNKNOWN_COMMAND 2

void sendMessage(uint8_t *buffer, int bufferCount)
{
    Serial.write((char) FRAME_END);

    // Write the length.
    Serial.write((char) bufferCount >> 8);
    Serial.write((char) bufferCount);

    for (int index = 0; index < bufferCount; index++) {
        if (buffer[index] == FRAME_END) {
            Serial.write((char) FRAME_ESCAPE);
            Serial.write((char) FRAME_ESCAPE_END);
        } else if (buffer[index] == FRAME_ESCAPE) {
            Serial.write((char) FRAME_ESCAPE);
            Serial.write((char) FRAME_ESCAPE_ESCAPE);
        } else {
            Serial.write((char) buffer[index]);
        }
    }

    // Write the placeholder for checksum.
    Serial.write((char) 0x00);
    Serial.write((char) 0x00);

    Serial.write((char) FRAME_END);

    Serial.flush();
}

void sendErrorMessage(uint8_t code, const char *description)
{
    uint8_t message[2 + 62 + 1] = { 0x02, code };
    int count = 2;

    if (description != NULL) {
        strncpy((char *) (message + 2), description, 62);

        count += strlen(description);
    }

    sendMessage(message, count);
}

#define COMMAND_RESET 0x01
#define COMMAND_TRANSMIT_RECEIVE 0x06

void handleResetCommand(uint8_t *buffer, int bufferCount)
{
    uint8_t response[] = { 0x01, 0x00, 0x00, 0x01 };

    sendMessage(response, 4);
}

void handleTransmitReceiveCommand(uint8_t *buffer, int bufferCount)
{
    if (bufferCount < 6) {
        sendErrorMessage(ERROR_INVALID_MESSAGE, "HANDLE_TXRX_BUFFER_COUNT_6");
        return;
    }

    uint16_t *transmitBuffer = (uint16_t *) (buffer + 2);
    uint16_t transmitBufferCount = (bufferCount - 6) / 2;

    uint16_t transmitRepeatCount = ((buffer[0] << 8) | buffer[1]) & 0x7fff;
    uint16_t transmitRepeatOffset = buffer[0] >> 7;

    uint16_t receiveBufferSize = (buffer[bufferCount - 4] << 8) | buffer[bufferCount - 3];
    uint16_t receiveTimeout = (buffer[bufferCount - 2] << 8) | buffer[bufferCount - 1];

    if (transmitBufferCount < 1) {
        sendErrorMessage(ERROR_INVALID_MESSAGE, "HANDLE_TXRX_TX_BUFFER_COUNT_1");
        return;
    }

    // Expand the provided data if applicable.
    if (transmitRepeatCount > 1) {
        uint8_t *source = ((uint8_t *) transmitBuffer) + (transmitRepeatOffset * 2);
        uint8_t *destination = ((uint8_t *) transmitBuffer) + (transmitBufferCount * 2);

        uint16_t sourceCount = transmitBufferCount - transmitRepeatOffset;

        size_t length = sourceCount * 2;

        for (int index = 1; index < transmitRepeatCount; index++) {
            memcpy(destination, source, length);

            transmitBufferCount += sourceCount;

            destination += length;
        }
    }

    uint16_t *receiveBuffer = (uint16_t *) (buffer + 2);

    bufferCount = CoaxTransceiver::transmitReceive(transmitBuffer, transmitBufferCount, receiveBuffer, receiveBufferSize, receiveTimeout);

    if (bufferCount < 0) {
        sendErrorMessage(100 + ((-1) * bufferCount), NULL);
        return;
    }

    // Send the response message.
    buffer[1] = 0x01;

    bufferCount = 1 + (bufferCount * 2);

    sendMessage(buffer + 1, bufferCount);
}

void handleMessage(uint8_t *buffer, int bufferCount)
{
    if (bufferCount < 1) {
        sendErrorMessage(ERROR_INVALID_MESSAGE, "HANDLE_MESSAGE_BUFFER_COUNT_1");
        return;
    }

    uint8_t command = buffer[0];

    if (command == COMMAND_RESET) {
        handleResetCommand(buffer + 1, bufferCount - 1);
    } else if (command == COMMAND_TRANSMIT_RECEIVE) {
        handleTransmitReceiveCommand(buffer + 1, bufferCount - 1);
    } else {
        sendErrorMessage(ERROR_UNKNOWN_COMMAND, NULL);
    }
}

void handleFrame(uint8_t *buffer, int bufferCount)
{
    if (bufferCount < 4) {
        sendErrorMessage(ERROR_INVALID_MESSAGE, "HANDLE_FRAME_BUFFER_COUNT_4");
        return;
    }

    int count = (buffer[0] << 8) | buffer[1];

    if (bufferCount - 4 != count) {
        sendErrorMessage(ERROR_INVALID_MESSAGE, "HANDLE_FRAME_BUFFER_COUNT_MISMATCH");
        return;
    }

    handleMessage(buffer + 2, count);
}

void setup()
{
    // Configure serial port and state machine.
    Serial.begin(115200);

    frameState = WAIT_START;

    while (Serial.available() > 0) {
        Serial.read();
    }

    // Configure the transceiver.
    CoaxTransceiver::setup();
}

void loop()
{
    if (Serial.available() > 0) {
        uint8_t byte = Serial.read();

        if (frameState == WAIT_START) {
            if (byte == FRAME_END) {
                frameState = DATA;
            }
        } else if (frameState == DATA) {
            if (byte == FRAME_END) {
                if (frameBufferCount > 0) {
                    handleFrame(frameBuffer, frameBufferCount);
                }

                frameBufferCount = 0;
                frameState = WAIT_START;
            } else if (byte == FRAME_ESCAPE) {
                frameState = ESCAPE;
            } else {
                // TODO: overflow...
                frameBuffer[frameBufferCount++] = byte;
            }
        } else if (frameState == ESCAPE) {
            if (byte == FRAME_ESCAPE_END) {
                // TODO: overflow...
                frameBuffer[frameBufferCount++] = FRAME_END;
            } else if (byte == FRAME_ESCAPE_ESCAPE) {
                // TODO: overflow...
                frameBuffer[frameBufferCount++] = FRAME_ESCAPE;
            }

            frameState = DATA;
        }
    }
}
