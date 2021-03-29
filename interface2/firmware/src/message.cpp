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

#include "stm32l4xx_hal.h"

#include "usbd_cdc_if.h"

#include "debug.h"

#include "message.h"

#define MESSAGE_END 0xc0
#define MESSAGE_ESCAPE 0xdb
#define MESSAGE_ESCAPE_END 0xdc
#define MESSAGE_ESCAPE_ESCAPE 0xdd

MessageReceiver::MessageReceiver(volatile uint8_t *buffer, size_t bufferSize,
        void (*messageCallback)(const uint8_t *, size_t),
        void (*errorCallback)(MessageReceiverError)) :
    _buffer(buffer),
    _bufferSize(bufferSize),
    _messageCallback(messageCallback),
    _errorCallback(errorCallback)
{
    _timeout = 1000;
    _lastReceiveTime = -1;

    _bufferCount = 0;
    _state = MESSAGE_RECEIVER_STATE_WAIT_START;
}

void MessageReceiver::load(const uint8_t *buffer, size_t bufferCount)
{
    _lastReceiveTime = HAL_GetTick();

    for (size_t index = 0; index < bufferCount; index++) {
        uint8_t byte = buffer[index];

        if (_state == MESSAGE_RECEIVER_STATE_WAIT_START) {
            if (byte == MESSAGE_END) {
                _bufferCount = 0;
                _state = MESSAGE_RECEIVER_STATE_DATA;
            }
        } else if (_state == MESSAGE_RECEIVER_STATE_DATA) {
            if (byte == MESSAGE_END) {
                if (_bufferCount > 0) {
                    _state = MESSAGE_RECEIVER_STATE_AVAILABLE;
                } else {
                    _state = MESSAGE_RECEIVER_STATE_WAIT_START;
                }
            } else if (byte == MESSAGE_ESCAPE) {
                _state = MESSAGE_RECEIVER_STATE_ESCAPE;
            } else {
                if (_bufferCount < _bufferSize) {
                    _buffer[_bufferCount++] = byte;
                } else {
                    _state = MESSAGE_RECEIVER_STATE_DATA_OVERFLOW;
                }
            }
        } else if (_state == MESSAGE_RECEIVER_STATE_ESCAPE) {
            if (byte == MESSAGE_ESCAPE_END) {
                if (_bufferCount < _bufferSize) {
                    _buffer[_bufferCount++] = MESSAGE_END;
                    _state = MESSAGE_RECEIVER_STATE_DATA;
                } else {
                    _state = MESSAGE_RECEIVER_STATE_DATA_OVERFLOW;
                }
            } else if (byte == MESSAGE_ESCAPE_ESCAPE) {
                if (_bufferCount < _bufferSize) {
                    _buffer[_bufferCount++] = MESSAGE_ESCAPE;
                    _state = MESSAGE_RECEIVER_STATE_DATA;
                } else {
                    _state = MESSAGE_RECEIVER_STATE_DATA_OVERFLOW;
                }
            } else {
                _state = MESSAGE_RECEIVER_STATE_WAIT_START;
            }
        } else if (_state == MESSAGE_RECEIVER_STATE_AVAILABLE) {
            _state = MESSAGE_RECEIVER_STATE_MESSAGE_OVERFLOW;
        }
    }
}

bool MessageReceiver::dispatch()
{
    if (_state == MESSAGE_RECEIVER_STATE_AVAILABLE || _state == MESSAGE_RECEIVER_STATE_MESSAGE_OVERFLOW) {
        // In the case of a message overflow the message is still valid.
        _messageCallback(const_cast<uint8_t *>(_buffer), _bufferCount);

        // A message overflow could occur during the above callback.
        if (_state == MESSAGE_RECEIVER_STATE_MESSAGE_OVERFLOW) {
            _errorCallback(MESSAGE_RECEIVER_ERROR_MESSAGE_OVERFLOW);
        }
    } else if (_state == MESSAGE_RECEIVER_STATE_DATA_OVERFLOW) {
        _errorCallback(MESSAGE_RECEIVER_ERROR_DATA_OVERFLOW);
    } else {
        if (_state != MESSAGE_RECEIVER_STATE_WAIT_START) {
            uint32_t lastReceiveTime = _lastReceiveTime;
            uint32_t time = HAL_GetTick();

            if (time - lastReceiveTime > _timeout) {
                Debug::trap(201, "state = %d, lastReceiveTime = %d, time = %d", _state, lastReceiveTime, time);

                _state = MESSAGE_RECEIVER_STATE_WAIT_START;

                _errorCallback(MESSAGE_RECEIVER_ERROR_TIMEOUT);
            }
        }

        return false;
    }

    _state = MESSAGE_RECEIVER_STATE_WAIT_START;

    return true;
}

extern USBD_HandleTypeDef hUsbDeviceFS;

HAL_StatusTypeDef transmit(const uint8_t *buffer, size_t bufferCount, uint32_t timeout)
{
    if (hUsbDeviceFS.dev_state != USBD_STATE_CONFIGURED) {
        return HAL_ERROR;
    }

    USBD_CDC_HandleTypeDef *cdc = reinterpret_cast<USBD_CDC_HandleTypeDef *>(hUsbDeviceFS.pClassData);

    uint32_t startTime = HAL_GetTick();

    while (cdc->TxState != 0) {
        if (timeout != HAL_MAX_DELAY) {
            if (HAL_GetTick() - startTime > timeout || timeout == 0) {
                return HAL_TIMEOUT;
            }
        }
    }

    HAL_StatusTypeDef status = (HAL_StatusTypeDef) CDC_Transmit_FS(const_cast<uint8_t *>(buffer), bufferCount);

    if (status != HAL_OK) {
        return status;
    }

    startTime = HAL_GetTick();

    while (cdc->TxState != 0) {
        if (timeout != HAL_MAX_DELAY) {
            if (HAL_GetTick() - startTime > timeout || timeout == 0) {
                return HAL_TIMEOUT;
            }
        }
    }

    return HAL_OK;
}

inline size_t encode(uint8_t *buffer, size_t size, uint8_t byte)
{
    if (byte == MESSAGE_END || byte == MESSAGE_ESCAPE) {
        if (size < 2) {
            return 0;
        }

        buffer[0] = MESSAGE_ESCAPE;

        if (byte == MESSAGE_END)
            buffer[1] = MESSAGE_ESCAPE_END;
        else if (byte == MESSAGE_ESCAPE)
            buffer[1] = MESSAGE_ESCAPE_ESCAPE;

        return 2;
    }

    if (size < 1) {
        return 0;
    }

    buffer[0] = byte;

    return 1;
}

#define PACKET_SIZE 64

// In order to simplify the breaking up of a message into multiple packets we reserve
// space at the end of every packet for the footer and end symbol. If the packet
// contained a real checksum in the footer then this would be at worst case 5 to
// allow for the encoding.
#define RESERVED 3

bool MessageSender::send(const uint8_t *buffer, size_t bufferCount)
{
    uint8_t packet[PACKET_SIZE];

    size_t packetCount = 0;
    size_t remainingPacketSize = PACKET_SIZE - RESERVED;

    // Start the message and encode the header, we assume that there is space for the header.
    packet[packetCount++] = MESSAGE_END;

    remainingPacketSize--;

    size_t count = encode(&packet[packetCount], remainingPacketSize, (u_int8_t) (bufferCount >> 8));

    packetCount += count;
    remainingPacketSize -= count;

    count = encode(&packet[packetCount], remainingPacketSize, (u_int8_t) bufferCount);

    packetCount += count;
    remainingPacketSize -= count;

    // Encode the data, once the packet size has been reached transmit the packet.
    size_t index = 0;

    while (index < bufferCount) {
        count = encode(&packet[packetCount], remainingPacketSize, buffer[index]);

        if (count > 0) {
            index++;
        }

        packetCount += count;
        remainingPacketSize -= count;

        // Transmit the packet and begin a new packet.
        if (count == 0 || remainingPacketSize == 0) {
            if (transmit(packet, packetCount, 1000) != HAL_OK) {
                return false;
            }

            packetCount = 0;
            remainingPacketSize = PACKET_SIZE - RESERVED;
        }
    }

    // Add the footer (space has been reserved), end the message and transmit the packet.
    packet[packetCount++] = 0;
    packet[packetCount++] = 0;
    packet[packetCount++] = MESSAGE_END;

    if (!transmit(packet, packetCount, 1000)) {
        return false;
    }

    return true;
}
