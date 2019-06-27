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

#define COMMAND_RESET 0x01
#define COMMAND_EXECUTE 0x02
#define COMMAND_EXECUTE_OFFLOAD 0x03

#define ERROR_INVALID_MESSAGE 1
#define ERROR_UNKNOWN_COMMAND 2
#define ERROR_UNKNOWN_OFFLOAD_COMMAND 3

#define UNPACK_DATA_WORD(w) (uint8_t) ((w >> 2) & 0xff)

void handleResetCommand(uint8_t *buffer, int bufferCount) {
  uint8_t response[] = { 0x01, 0x00, 0x00, 0x01 };
  
  sendMessage(response, 4);
}

void handleExecuteCommand(uint8_t *buffer, int bufferCount) {
  if (bufferCount < 6) {
    sendErrorMessage(ERROR_INVALID_MESSAGE);
    return;
  }
  
  uint16_t commandWord = (buffer[0] << 8) | buffer[1];
  uint16_t receiveCount = (buffer[2] << 8) | buffer[3];
  uint16_t timeout = (buffer[4] << 8) | buffer[5];

  uint8_t *dataBuffer = buffer + 6;
  uint16_t dataBufferCount = bufferCount - 6;

  uint16_t *receiveBuffer = (uint16_t *) (buffer + 2);
  
  bufferCount = CoaxTransceiver::transmitReceive(commandWord, dataBuffer, dataBufferCount, receiveBuffer, receiveCount, timeout);

  if (bufferCount < 0) {
    sendErrorMessage(100 + ((-1) * bufferCount));
    return;
  }

  // Send the response message.
  buffer[1] = 0x01;
  
  bufferCount = 1 + (bufferCount * 2);

  sendMessage(buffer + 1, bufferCount);
}

void handleExecuteOffloadCommand(uint8_t *buffer, int bufferCount) {
  if (bufferCount < 1) {
    sendErrorMessage(ERROR_INVALID_MESSAGE);
    return;
  }

  uint8_t command = buffer[0];

  if (command == 0x01) {
    handleOffloadLoadAddressCounter(buffer + 1, bufferCount - 1);
  } else if (command == 0x02) {
    handleOffloadWrite(buffer + 1, bufferCount - 1);
  } else {
    sendErrorMessage(ERROR_UNKNOWN_OFFLOAD_COMMAND);
  }
}

void handleOffloadLoadAddressCounter(uint8_t *buffer, int bufferCount) {
  uint16_t response;
  
  if (bufferCount < 2) {
    sendErrorMessage(ERROR_INVALID_MESSAGE);
    return;
  }

  uint8_t hi = buffer[0];
  uint8_t lo = buffer[1];
  
  // TODO: error handling...
  CoaxTransceiver::transmitReceive(/* LOAD_ADDRESS_COUNTER_HI */ 0x11, &hi, 1, &response, 1, 0);
  CoaxTransceiver::transmitReceive(/* LOAD_ADDRESS_COUNTER_LO */ 0x51, &lo, 1, &response, 1, 0);

  // Send the response message.
  uint8_t message[] = { 0x01 };
  
  sendMessage(message, 1);
}

void handleOffloadWrite(uint8_t *buffer, int bufferCount) {
  uint16_t response;
  
  if (bufferCount < 5) {
    sendErrorMessage(ERROR_INVALID_MESSAGE);
    return;
  }

  uint8_t addressHi = buffer[0];
  uint8_t addressLo = buffer[1];
  bool restoreOriginalAddress = buffer[2];
  uint16_t repeatCount = (buffer[3] << 8) | buffer[4];

  uint8_t *dataBuffer = buffer + 5;
  uint16_t dataBufferCount = bufferCount - 5;
  
  if (dataBufferCount < 1) {
    sendErrorMessage(ERROR_INVALID_MESSAGE);
    return;
  }

  // Repeat the provided data if applicable.
  if (repeatCount > 0) {
    uint16_t dataBufferIndex = dataBufferCount;

    for (int repeatIndex = 0; repeatIndex < repeatCount; repeatIndex++) {
      for (int index = 0; index < dataBufferCount; index++) {
        dataBuffer[dataBufferIndex++] = dataBuffer[index];
      }
    }

    dataBufferCount *= (repeatCount + 1);
  }
  
  // Store original address if applicable.
  uint8_t originalAddressHi;
  uint8_t originalAddressLo;

  if (restoreOriginalAddress) {
    CoaxTransceiver::transmitReceive(/* READ_ADDRESS_COUNTER_HI */ 0x15, NULL, 0, &response, 1, 0);

    originalAddressHi = UNPACK_DATA_WORD(response);

    CoaxTransceiver::transmitReceive(/* READ_ADDRESS_COUNTER_LO */ 0x55, NULL, 0, &response, 1, 0);
    
    originalAddressLo = UNPACK_DATA_WORD(response);
  }

  // Move to start address if applicable.
  if (!(addressHi == 0xff && addressLo == 0xff)) {
    CoaxTransceiver::transmitReceive(/* LOAD_ADDRESS_COUNTER_HI */ 0x11, &addressHi, 1, &response, 1, 0);
    CoaxTransceiver::transmitReceive(/* LOAD_ADDRESS_COUNTER_LO */ 0x51, &addressLo, 1, &response, 1, 0);
  }

  // Write buffer.
  CoaxTransceiver::transmitReceive(/* WRITE_DATA */ 0x31, dataBuffer, dataBufferCount, &response, 1, 0);

  // Restore original address if applicable.
  if (restoreOriginalAddress) {
    CoaxTransceiver::transmitReceive(/* LOAD_ADDRESS_COUNTER_HI */ 0x11, &originalAddressHi, 1, &response, 1, 0);
    CoaxTransceiver::transmitReceive(/* LOAD_ADDRESS_COUNTER_LO */ 0x51, &originalAddressLo, 1, &response, 1, 0);
  }

  // Send the response message.
  uint8_t message[] = { 0x01 };
  
  sendMessage(message, 1);
}

void handleMessage(uint8_t *buffer, int bufferCount) {
  if (bufferCount < 1) {
    sendErrorMessage(ERROR_INVALID_MESSAGE);
    return;
  }

  uint8_t command = buffer[0];

  if (command == COMMAND_RESET) {
    handleResetCommand(buffer + 1, bufferCount - 1);
  } else if (command == COMMAND_EXECUTE) {
    handleExecuteCommand(buffer + 1, bufferCount - 1);
  } else if (command == COMMAND_EXECUTE_OFFLOAD) {
    handleExecuteOffloadCommand(buffer + 1, bufferCount - 1);
  } else {
    sendErrorMessage(ERROR_UNKNOWN_COMMAND);
  }
}

#define FRAME_END 0xc0
#define FRAME_ESCAPE 0xdb
#define FRAME_ESCAPE_END 0xdc
#define FRAME_ESCAPE_ESCAPE 0xdd

enum {
  WAIT_START,
  DATA,
  ESCAPE
} frameState;

#define FRAME_BUFFER_SIZE (25 * 80) + 32

uint8_t frameBuffer[FRAME_BUFFER_SIZE];
int frameBufferCount = 0;

void handleFrame(uint8_t *buffer, int bufferCount) {
  if (bufferCount < 4) {
    sendErrorMessage(ERROR_INVALID_MESSAGE);
    return;
  }

  int count = (buffer[0] << 8) | buffer[1];

  if (bufferCount - 4 != count) {
    sendErrorMessage(ERROR_INVALID_MESSAGE);
    return;
  }

  handleMessage(buffer + 2, count);
}

void sendMessage(uint8_t *buffer, int bufferCount) {
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

void sendErrorMessage(uint8_t code) {
  uint8_t message[] = { 0x02, code };
  
  sendMessage(message, 2);
}

void setup() {
  // Configure serial port and state machine.
  Serial.begin(115200);

  frameState = WAIT_START;

  while (Serial.available() > 0) {
    Serial.read();
  }
  
  // Configure the transceiver.
  CoaxTransceiver::setup();
}

void loop() {
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
