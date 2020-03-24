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
           
// Arduino Mega pins...
//
//  Arduino   Arduino Port        Label        DP8340N   DP8341N 
//    Pin       and Mask                         Pin       Pin
// ---------|--------------|-----------------|---------|---------
//     7    |              | EVEN/ODD PARITY |   18    |
//     6    |   PH3 0x08   | PARITY CONTROL  |   19    |
//     5    |              | AUTO RESPONSE   |   21    |
//     4    |   PG5 0x20   | REGISTERS FULL  |   22    |
//     3    |   PE5 0x20   | REGISTER LOAD   |   23    |
// ---------.--------------.-----------------.---------.---------
//     2    |              | DATA CONTROL    |         |    5
//    14    |   PJ1 0x02   | ERROR           |         |    8
//    15    |   PJ0 0x01   | DATA AVAILABLE  |         |   10
//    16    |   PH1 0x02   | REGISTER READ   |         |    9
//    17    |   PH0 0x01   | OUTPUT CONTROL  |         |   11
//    18*   |   PD3 0x08   | RECEIVER ACTIVE |         |    7
//    19    |   PD2 0x04   | OUTPUT ENABLE   |         |   13
// ---------.--------------.-----------------.---------.---------
//    22    |   PA0        | D11             |    1    |   23
//    23    |   PA1        | D10             |    2    |   22
//    24    |   PA2        | D9              |    3    |   21
//    25    |   PA3        | D8              |    4    |   20
//    26    |   PA4        | D7              |    5    |   19
//    27    |   PA5        | D6              |    6    |   18
//    28    |   PA6        | D5              |    7    |   17
//    29    |   PA7        | D4              |    8    |   16
//    36    |   PC1        | D2              |   10    |   14
//    37    |   PC0        | D3              |    9    |   15
//
// * - Interrupt capable pin

#define TX_EVEN_ODD_PARITY_PIN 7
#define TX_PARITY_CONTROL_PIN 6
#define TX_AUTO_RESPONSE_PIN 5
#define TX_REGISTERS_FULL_PIN 4
#define TX_REGISTER_LOAD_PIN 3

#define RX_DATA_CONTROL_PIN 2
#define RX_ERROR_PIN 14
#define RX_DATA_AVAILABLE_PIN 15
#define RX_REGISTER_READ_PIN 16
#define RX_OUTPUT_CONTROL_PIN 17
#define RX_ACTIVE_PIN 18
#define RX_OUTPUT_ENABLE_PIN 19

#define RX_STATE_DISABLED 0
#define RX_STATE_WAITING 1
#define RX_STATE_RECEIVING 2
#define RX_STATE_RECEIVED 3

static volatile uint8_t CoaxTransceiver::rxState;
static volatile uint16_t *CoaxTransceiver::rxBuffer;
static volatile size_t CoaxTransceiver::rxBufferSize;
static volatile int /* ssize_t */ CoaxTransceiver::rxBufferCount;

#define NOP __asm__("nop\n\t")

static void CoaxTransceiver::setup() {
  // Configure data bus.
  dataBusSetup();

  // Configure receiver (DP8341N).
  rxSetup();

  // Configure transmitter (DP8340N).
  txSetup();
}

static int /* ssize_t */ CoaxTransceiver::transmitReceive(uint16_t *transmitBuffer, size_t transmitBufferCount, uint16_t *receiveBuffer, size_t receiveBufferSize, uint16_t receiveTimeout) {
  int returnValue = transmit(transmitBuffer, transmitBufferCount);

  if (returnValue < 0) {
    return returnValue;
  }

  return receive(receiveBuffer, receiveBufferSize, receiveTimeout);
}

static void CoaxTransceiver::dataBusSetup() {
  DDRA = B00000000;
  DDRC = B00000000;
}

static void CoaxTransceiver::rxSetup() {
  // Data Control - Amplifier Inputs
  pinMode(RX_DATA_CONTROL_PIN, OUTPUT);
  
  digitalWrite(RX_DATA_CONTROL_PIN, HIGH);

  // Register Read
  pinMode(RX_REGISTER_READ_PIN, OUTPUT);

  digitalWrite(RX_REGISTER_READ_PIN, HIGH);

  // Output Control - Data
  pinMode(RX_OUTPUT_CONTROL_PIN, OUTPUT);

  digitalWrite(RX_OUTPUT_CONTROL_PIN, HIGH);

  // Output Enable - Active
  pinMode(RX_OUTPUT_ENABLE_PIN, OUTPUT);

  digitalWrite(RX_OUTPUT_ENABLE_PIN, HIGH);

  // Receiver Active
  pinMode(RX_ACTIVE_PIN, INPUT);

  attachInterrupt(digitalPinToInterrupt(RX_ACTIVE_PIN), rxActiveInterrupt, RISING);

  // Data Available
  pinMode(RX_DATA_AVAILABLE_PIN, INPUT);

  // Error
  pinMode(RX_ERROR_PIN, INPUT); 
}

static void CoaxTransceiver::txSetup() {
  // Register Load
  pinMode(TX_REGISTER_LOAD_PIN, OUTPUT);

  digitalWrite(TX_REGISTER_LOAD_PIN, HIGH);
  
  // Auto Response - Data
  pinMode(TX_AUTO_RESPONSE_PIN, OUTPUT);

  digitalWrite(TX_AUTO_RESPONSE_PIN, HIGH);
  
  // Even/Odd Parity - Even
  pinMode(TX_EVEN_ODD_PARITY_PIN, OUTPUT);

  digitalWrite(TX_EVEN_ODD_PARITY_PIN, HIGH);

  // Parity Control - Data
  pinMode(TX_PARITY_CONTROL_PIN, OUTPUT);

  digitalWrite(TX_PARITY_CONTROL_PIN, HIGH);

  // Registers Full
  pinMode(TX_REGISTERS_FULL_PIN, INPUT);
}

static int /* ssize_t */ CoaxTransceiver::transmit(uint16_t *buffer, size_t bufferCount) {
  // Ensure receiver is inactive.
  if (rxState != RX_STATE_DISABLED) {
    return ERROR_TX_RECEIVER_ACTIVE;
  }
  
  if (/* RECEIVER ACTIVE */ (PIND & 0x8) == 0x8) {
    return ERROR_TX_RECEIVER_ACTIVE;
  }

  // Disable interrupts.
  noInterrupts();

  // Disable receiver output.
  PORTD &= ~0x04; // RX Output Enable - Low (Disable)

  // Configure data bus for output.
  DDRA = B11111111;
  DDRC = B00000011;

  // Transmit.
  for (int index = 0; index < bufferCount; index++) {
    uint16_t data = buffer[index];
    
    // Wait while TX Registers Full is high.
    while ((PING & 0x20) == 0x20) {
      NOP;
    }

    PORTC = (PINC & 0xfc) | ((data >> 8) & 0x3);
    PORTA = data & 0xff;

    PORTE &= ~0x20; // TX Register Load - Low (Load)
    PORTE |= 0x20; // TX Register Load - High
  }

  // Configure data bus for input.
  DDRA = B00000000;
  DDRC = B00000000;

  // Enable receiver output.
  PORTD |= 0x04; // RX Output Enable - High (Enable)

  // Enable interrupts.
  interrupts();

  return bufferCount;
}

static int /* ssize_t */ CoaxTransceiver::receive(uint16_t *buffer, size_t bufferSize, uint16_t timeout) {
  rxBuffer = buffer;
  rxBufferSize = bufferSize;

  rxState = RX_STATE_WAITING;
  
  if (timeout > 0) {
    unsigned long startTime = millis();
    
    while (rxState == RX_STATE_WAITING) {
      // https://www.forward.com.au/pfod/ArduinoProgramming/TimingDelaysInArduino.html#unsigned
      if ((millis() - startTime) > timeout) {
        rxState = RX_STATE_DISABLED;
        return ERROR_RX_TIMEOUT;
      }
    }
  }
  
  while (rxState != RX_STATE_RECEIVED) {
    NOP;
  }

  rxState = RX_STATE_DISABLED;

  return rxBufferCount;
}

static void CoaxTransceiver::rxActiveInterrupt() {
  uint16_t data;
  uint8_t mask;
  
  if (rxState == RX_STATE_DISABLED) {
    return;
  }

  rxState = RX_STATE_RECEIVING;

  rxBufferCount = 0;

  do {
    while (/* ERROR or DATA AVAILABLE */ (PINJ & 0x03) == 0) {
      NOP;
    }
    
    if (/* ERROR */ (PINJ & 0x02) == 0x02) {
      mask = 0x02;
            
      PORTH &= ~0x01; // Output Control - Low (Error)
      PORTH &= ~0x02; // Register Read - Low

      // Read and mark as error.
      data = (((PINC & 0x3) | 0x80) << 8) | PINA;

      PORTH |= 0x02; // Register Read - High
      PORTH |= 0x01; // Output Control - High (Data)
    } else if (/* DATA AVAILABLE */ (PINJ & 0x01) == 0x01) {
      mask = 0x01;
      
      PORTH &= ~0x02; // Register Read - Low

      // Read.
      data = ((PINC & 0x3) << 8) | PINA;
     
      PORTH |= 0x02; // Register Read - High
    }
    
    if (rxBufferCount >= rxBufferSize) {
      rxBufferCount = ERROR_RX_OVERFLOW;
      goto EXIT;
    }
    
    rxBuffer[rxBufferCount++] = data;

    while ((PINJ & mask) == mask) {
      NOP;
    }
  } while (/* RECEIVER ACTIVE */ (PIND & 0x8) == 0x8);

EXIT:
  rxState = RX_STATE_RECEIVED;
}
