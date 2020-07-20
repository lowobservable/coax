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
#include "CoaxTransceiver.h"

NewCoaxDataBus dataBus;
NewCoaxReceiver receiver(dataBus);
NewCoaxTransmitter transmitter(dataBus, receiver);

void CoaxTransceiver::setup()
{
    dataBus.setMode(INPUT, true);

    receiver.begin();
    transmitter.begin();
}

int /* ssize_t */ CoaxTransceiver::transmitReceive(uint16_t *transmitBuffer, size_t transmitBufferCount, uint16_t *receiveBuffer, size_t receiveBufferSize, uint16_t receiveTimeout)
{
    int returnValue = transmitter.transmit(transmitBuffer, transmitBufferCount);

    if (returnValue < 0) {
        return returnValue;
    }

    return receiver.receive(receiveBuffer, receiveBufferSize, receiveTimeout);
}
