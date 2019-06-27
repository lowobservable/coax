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
//    36    |   PC1        | D2              |   10    |   14
//    37    |   PC0        | D3              |    9    |   15
//    29    |   PA7        | D4              |    8    |   16
//    28    |   PA6        | D5              |    7    |   17
//    27    |   PA5        | D6              |    6    |   18
//    26    |   PA4        | D7              |    5    |   19
//    25    |   PA3        | D8              |    4    |   20
//    24    |   PA2        | D9              |    3    |   21
//    23    |   PA1        | D10             |    2    |   22
//    22    |   PA0        | D11             |    1    |   23
// --------- -------------- ----------------- --------- ---------
//     8    |   PH5 0x20   | REGISTER LOAD   |   23    |
//     9    |   PH6 0x40   | REGISTERS FULL  |   22    |
//    10    |              | AUTO RESPONSE   |   21    |
//    11    |              | EVEN/ODD PARITY |   18    |
//    12    |   PB6 0x40   | PARITY CONTROL  |   19    |
// --------- -------------- ----------------- --------- ---------
//    18*   |   PD3 0x08   | RECEIVER ACTIVE |         |    7
//     2    |   PE4 0x10   | DATA AVAILABLE  |         |   10
//     3    |   PE5 0x20   | ERROR           |         |    8
//     4    |              | DATA CONTROL    |         |    5
//     5    |   PE3 0x08   | REGISTER READ   |         |    9
//     6    |   PH3 0x08   | OUTPUT CONTROL  |         |   11
//     7    |   PH4 0x10   | OUTPUT ENABLE   |         |   13
//
// * - Interrupt capable pin

#define TX_REGISTER_LOAD_PIN 8
#define TX_REGISTERS_FULL_PIN 9
#define TX_AUTO_RESPONSE_PIN 10
#define TX_EVEN_ODD_PARITY_PIN 11
#define TX_PARITY_CONTROL_PIN 12

#define RX_ACTIVE_PIN 18
#define RX_DATA_AVAILABLE_PIN 2
#define RX_ERROR_PIN 3
#define RX_DATA_CONTROL_PIN 4
#define RX_REGISTER_READ_PIN 5
#define RX_OUTPUT_CONTROL_PIN 6
#define RX_OUTPUT_ENABLE_PIN 7

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

static int /* ssize_t */ CoaxTransceiver::transmitReceive(uint16_t commandWord, uint8_t *dataBuffer, size_t dataBufferCount, uint16_t *receiveBuffer, size_t receiveBufferSize, uint16_t timeout) {
  int returnValue = transmit(commandWord, dataBuffer, dataBufferCount);

  if (returnValue < 0) {
    return returnValue;
  }

  return receive(receiveBuffer, receiveBufferSize, timeout);
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

static int /* ssize_t */ CoaxTransceiver::transmit(uint16_t commandWord, uint8_t *dataBuffer, size_t dataCount) {
  // Ensure receiver is inactive.
  if (rxState != RX_STATE_DISABLED) {
    return ERROR_TX_RECEIVER_ACTIVE;
  }
  
  if ((PIND & 0x8) == 0x8) {
    return ERROR_TX_RECEIVER_ACTIVE;
  }

  // Disable interrupts.
  noInterrupts();

  // Disable receiver output.
  PORTH &= ~0x10; // RX Output Enable - Low (Disable)

  // Configure data bus for output.
  DDRA = B11111111;
  DDRC = B00000011;

  // Send command word - we make an assumption here that TX_REGISTERS_FULL is not set.
  PORTC = (PINC & 0xfc) | ((commandWord >> 8) & 0x3);
  PORTA = commandWord & 0xff;

  PORTH &= ~0x20; // TX Register Load - Low (Load)
  PORTH |=  0x20; // TX Register Load - High

  // Send data - offload parity computation to DP8340.
  if (dataCount > 0) {
    // Enable transmitter parity calculation.
    PORTB &= ~0x40; // TX Parity Control - Low
    
    for (int index = 0; index < dataCount; index++) {
      // Wait while TX Registers Full is high.
      while ((PINH & 0x40) == 0x40) {
        NOP;
      }
      
      uint8_t data = dataBuffer[index];

      PORTC = (PINC & 0xfc) | ((data >> 6) & 0x3);
      PORTA = (data << 2);

      PORTH &= ~0x20; // TX Register Load - Low (Load)
      PORTH |=  0x20; // TX Register Load - High
    }

    // Disable transmitter parity calculation.
    PORTB |= 0x40; // TX Parity Control - High
  }

  // Configure data bus for input.
  DDRA = B00000000;
  DDRC = B00000000;

  // Enable receiver output.
  PORTH |= 0x10; // RX Output Enable - High (Enable)

  // Enable interrupts.
  interrupts();

  return dataCount;
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
    while ((PINE & 0x30) == 0) {
      NOP;
    }
    
    if (/* ERROR */ (PINE & 0x20) == 0x20) {
      mask = 0x20;
            
      PORTH &= ~0x8; // Output Control - Low (Error)
      PORTE &= ~0x8; // Register Read - Low

      // Read and mark as error.
      data = (((PINC & 0x3) | 0x80) << 8) | PINA;

      PORTE |= 0x8; // Register Read - High
      PORTH |= 0x8; // Output Control - High (Data)
    } else if (/* DATA AVAILABLE */ (PINE & 0x10) == 0x10) {
      mask = 0x10;
      
      PORTE &= ~0x8; // Register Read - Low

      // Read.
      data = ((PINC & 0x3) << 8) | PINA;
     
      PORTE |= 0x8; // Register Read - High
    }
    
    if (rxBufferCount >= rxBufferSize) {
      rxBufferCount = ERROR_RX_OVERFLOW;
      goto EXIT;
    }
    
    rxBuffer[rxBufferCount++] = data;

    while ((PINE & mask) == mask) {
      NOP;
    }
  } while ((PIND & 0x8) == 0x8);

EXIT:
  rxState = RX_STATE_RECEIVED;
}
