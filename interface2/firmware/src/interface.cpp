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

#include <cstdio>
#include <cstring>

#include <machine/endian.h>

#include "stm32l4xx_hal.h"

#include "config.h"
#include "coax.h"
#include "indicators.h"
#include "message.h"
#include "debug.h"
#include "version.h"

#include "interface.h"

void sendErrorMessage(uint8_t code, const char *description)
{
    uint8_t message[2 + 62 + 1] = { 0x02, code };
    size_t count = 2;

    if (description != NULL) {
        strncpy(reinterpret_cast<char *>(message + 2), description, 62);

        count += strlen(description);
    }

    MessageSender::send(message, count);
}

Interface::Interface(Coax &coax, Indicators &indicators) :
    _coax(coax),
    _indicators(indicators)
{
    _coax.setTXProtocol(CoaxProtocol::_3270);
    _coax.setRXProtocol(CoaxProtocol::_3270);
    _coax.setParity(CoaxParity::Even);
}

void Interface::handleMessage(uint8_t *buffer, size_t bufferCount)
{
    if (bufferCount < 4) {
        sendErrorMessage(ERROR_INVALID_MESSAGE, "HANDLE_MESSAGE_BUFFER_COUNT_4");
        return;
    }

    size_t count = (buffer[0] << 8) | buffer[1];

    if (bufferCount - 4 != count) {
        sendErrorMessage(ERROR_INVALID_MESSAGE, "HANDLE_MESSAGE_BUFFER_COUNT_MISMATCH");
        return;
    }

    if (count < 1) {
        sendErrorMessage(ERROR_INVALID_MESSAGE, "HANDLE_COMMAND_BUFFER_COUNT_1");
        return;
    }

    uint8_t command = buffer[2];

    if (command == COMMAND_RESET) {
        handleReset(buffer + 3, count - 1);
    } else if (command == COMMAND_TRANSMIT_RECEIVE) {
        Debug::setMarker(0);
        handleTransmitReceive(buffer + 3, count - 1);
        Debug::resetMarker(0);
    } else if (command == COMMAND_INFO) {
        handleInfo(buffer + 3, count - 1);
    } else if (command == COMMAND_TEST) {
        handleTest(buffer + 3, count - 1);
    } else if (command == COMMAND_DFU) {
        handleDFU(buffer + 3, count - 1);
    } else if (command == COMMAND_SNOOPIE_REPORT) {
        handleSnoopieReport(buffer + 3, count - 1);
    } else {
        sendErrorMessage(ERROR_UNKNOWN_COMMAND, NULL);
    }
}

void Interface::handleError(MessageReceiverError error)
{
    if (error == MESSAGE_RECEIVER_ERROR_TIMEOUT) {
        sendErrorMessage(ERROR_MESSAGE_TIMEOUT, NULL);
    } else {
        Debug::trap(401, "error = %d", error);
    }
}

void Interface::handleReset(uint8_t *buffer, size_t bufferCount)
{
    _coax.reset();

    uint8_t response[] = { 0x01, 0x32, 0x70 };

    MessageSender::send(response, 3);
}

void Interface::handleTransmitReceive(uint8_t *buffer, size_t bufferCount)
{
    if (bufferCount < 6) {
        sendErrorMessage(ERROR_INVALID_MESSAGE, "HANDLE_TXRX_BUFFER_COUNT_6");
        return;
    }

    uint16_t *transmitBuffer = reinterpret_cast<uint16_t *>(buffer + 2);
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
        uint8_t *source = reinterpret_cast<uint8_t *>(transmitBuffer) + (transmitRepeatOffset * 2);
        uint8_t *destination = reinterpret_cast<uint8_t *>(transmitBuffer) + (transmitBufferCount * 2);

        uint16_t sourceCount = transmitBufferCount - transmitRepeatOffset;

        size_t length = sourceCount * 2;

        for (int index = 1; index < transmitRepeatCount; index++) {
            memcpy(destination, source, length);

            transmitBufferCount += sourceCount;

            destination += length;
        }
    }

    if (transmitBuffer[0] & 0x8000) {
        _coax.setTXProtocol(CoaxProtocol::_3299);
    } else {
        _coax.setTXProtocol(CoaxProtocol::_3270);
    }

    int transmitCount = _coax.transmit(transmitBuffer, transmitBufferCount);

    if (transmitCount < 0) {
        Debug::trap(402, "error = %d", transmitCount);

        _indicators.error();

        // Convert the error to legacy interface error for compatability.
        if (transmitCount == COAX_ERROR_TX_RECEIVER_ACTIVE) {
            sendErrorMessage(101, NULL);
        } else {
            sendErrorMessage(105, NULL);
        }

        return;
    }

    _indicators.tx();

    uint16_t *receiveBuffer = reinterpret_cast<uint16_t *>(buffer + 2);

    int receiveCount = _coax.receive(receiveBuffer, receiveBufferSize, receiveTimeout);

    if (receiveCount < 0) {
        Debug::trap(403, "error = %d", receiveCount);

        // vvv
        snoopieTeamAway();
        // ^^^

        _indicators.error();

        // Convert the error to legacy interface error for compatability.
        if (receiveCount == COAX_ERROR_RX_LOSS_OF_MID_BIT_TRANSITION) {
            sendErrorMessage(104, "Loss of mid bit transition");
        } else if (receiveCount == COAX_ERROR_RX_PARITY) {
            sendErrorMessage(104, "Parity error");
        } else if (receiveCount == COAX_ERROR_RX_INVALID_END_SEQUENCE) {
            sendErrorMessage(104, "Invalid end sequence");
        } else {
            sendErrorMessage(104, NULL);
        }

        return;
    }

    // Convert timeout to legacy interface error for compatability.
    if (receiveCount == 0) {
        sendErrorMessage(102, NULL);
        return;
    }

    _indicators.rx();

    // Send the response message.
    buffer[1] = 0x01;

    MessageSender::send(buffer + 1, 1 + (receiveCount * 2));
}

void Interface::handleInfo(uint8_t *buffer, size_t bufferCount)
{
    if (bufferCount < 1) {
        sendErrorMessage(ERROR_INVALID_MESSAGE, "HANDLE_INFO_BUFFER_COUNT_1");
        return;
    }

    uint8_t query = buffer[0];

    if (query == INFO_SUPPORTED_QUERIES) {
        buffer[0] = 0x01;
        buffer[1] = INFO_SUPPORTED_QUERIES;
        buffer[2] = INFO_HARDWARE_TYPE;
        buffer[3] = INFO_FIRMWARE_VERSION;
        buffer[4] = INFO_MESSAGE_BUFFER_SIZE;
        buffer[5] = INFO_FEATURES;

        MessageSender::send(buffer, 6);
    } else if (query == INFO_HARDWARE_TYPE) {
        buffer[0] = 0x01;

        int length = snprintf(reinterpret_cast<char *>(buffer + 1), 64, "interface2");

        MessageSender::send(buffer, length + 1);
    } else if (query == INFO_FIRMWARE_VERSION) {
        buffer[0] = 0x01;

        int length = snprintf(reinterpret_cast<char *>(buffer + 1), 64,
                "%d.%d.%d (build %s)", VERSION_MAJOR, VERSION_MINOR, VERSION_PATCH,
                FIRMWARE_BUILD_WHAT);

        MessageSender::send(buffer, length + 1);
    } else if (query == INFO_MESSAGE_BUFFER_SIZE) {
        buffer[0] = 0x01;

        uint32_t size = __htonl(MESSAGE_BUFFER_SIZE);

        memcpy(buffer + 1, &size, sizeof(uint32_t));

        MessageSender::send(buffer, 5);
    } else if (query == INFO_FEATURES) {
        buffer[0] = 0x01;
        buffer[1] = FEATURE_PROTOCOL_3299;

        MessageSender::send(buffer, 2);
    } else {
        sendErrorMessage(ERROR_INVALID_MESSAGE, "HANDLE_INFO_UNKNOWN_QUERY");
        return;
    }
}

void Interface::handleTest(uint8_t *buffer, size_t bufferCount)
{
    if (bufferCount < 1) {
        sendErrorMessage(ERROR_INVALID_MESSAGE, "HANDLE_TEST_BUFFER_COUNT_1");
        return;
    }

    uint8_t test = buffer[0];

    if (test == TEST_SUPPORTED_TESTS) {
        buffer[0] = 0x01;
        buffer[1] = TEST_SUPPORTED_TESTS;

        MessageSender::send(buffer, 2);
    } else {
        sendErrorMessage(ERROR_INVALID_MESSAGE, "HANDLE_TEST_UNKNOWN_TEST");
        return;
    }
}

extern void resetToBootloader();

void Interface::handleDFU(uint8_t *buffer, size_t bufferCount)
{
    buffer[0] = 0x01;

    MessageSender::send(buffer, 1);

    // Wait before resetting to allow the response to be sent.
    HAL_Delay(1000);

    resetToBootloader();
}

uint16_t snoopieBuffer[256];
uint8_t snoopieWriteIndex;

void Interface::snoopieTeamAway()
{
    printf("\r\n\r\nSNOOPIE +++\r\n");

    _coax.snoopie((uint16_t *) &snoopieBuffer, 256, &snoopieWriteIndex);

    printf("writeIndex = %d\r\n", snoopieWriteIndex);

    for (size_t index = 0; index < 256; index++) {
        uint16_t counter = (snoopieBuffer[index] & 0xfff0) >> 4;
        uint8_t probes = snoopieBuffer[index] & 0x0f;

        printf("%d %d\r\n", counter, probes);
    }

    printf("SNOOPIE ---\r\n");
}

void Interface::handleSnoopieReport(uint8_t *buffer, size_t bufferCount)
{
    buffer[0] = 0x01;
    buffer[1] = snoopieWriteIndex;

    memcpy(buffer + 2, &snoopieBuffer, 256 * sizeof(uint16_t));

    MessageSender::send(buffer, 2 + (256 * sizeof(uint16_t)));
}
