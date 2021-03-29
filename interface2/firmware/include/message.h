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

enum MessageReceiverError {
    MESSAGE_RECEIVER_ERROR_DATA_OVERFLOW,
    MESSAGE_RECEIVER_ERROR_MESSAGE_OVERFLOW,
    MESSAGE_RECEIVER_ERROR_TIMEOUT
};

enum MessageReceiverState {
    MESSAGE_RECEIVER_STATE_WAIT_START,
    MESSAGE_RECEIVER_STATE_DATA,
    MESSAGE_RECEIVER_STATE_ESCAPE,
    MESSAGE_RECEIVER_STATE_AVAILABLE,
    MESSAGE_RECEIVER_STATE_DATA_OVERFLOW,
    MESSAGE_RECEIVER_STATE_MESSAGE_OVERFLOW
};

class MessageReceiver
{
public:
    MessageReceiver(volatile uint8_t *buffer, size_t bufferSize,
            void (*messageCallback)(const uint8_t *, size_t),
            void (*errorCallback)(MessageReceiverError));

    void load(const uint8_t *buffer, size_t bufferCount);
    bool dispatch();

private:
    uint32_t _timeout;
    volatile uint32_t _lastReceiveTime;
    volatile uint8_t *_buffer;
    size_t _bufferSize;
    volatile size_t _bufferCount;
    volatile MessageReceiverState _state;
    void (*_messageCallback)(const uint8_t *, size_t);
    void (*_errorCallback)(MessageReceiverError);
};

class MessageSender
{
public:
    static bool send(const uint8_t *buffer, size_t bufferCount);
};
