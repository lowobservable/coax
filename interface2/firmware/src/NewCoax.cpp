#include <Arduino.h>

#include <NewCoax.h>

//#define RX_ENABLE_PIN 4
#define RX_RESET_PIN 4
#define RX_ACTIVE_PIN 5
#define RX_ERROR_PIN 6
#define RX_DATA_AVAILABLE_PIN 7
#define RX_READ_PIN 8

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

    //pinMode(RX_ENABLE_PIN, OUTPUT);
    pinMode(RX_RESET_PIN, OUTPUT);
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
    _dataBus.setMode(INPUT);

    _state = Idle;

    //digitalWrite(RX_ENABLE_PIN, HIGH);
}

void NewCoaxReceiver::disable()
{
    //digitalWrite(RX_ENABLE_PIN, LOW);

    _state = Disabled;
}

int NewCoaxReceiver::receive(uint16_t *buffer, size_t bufferSize, uint16_t timeout)
{
    if (_state != Disabled) {
        return ERROR_RX_RECEIVER_ACTIVE;
    }

    _error = 0;
    _buffer = buffer;
    _bufferSize = bufferSize;
    _bufferCount = 0;

    if (digitalRead(RX_DATA_AVAILABLE_PIN) || digitalRead(RX_ERROR_PIN)) {
        reset();
    }

    enable();

    if (timeout > 0) {
        unsigned long startTime = millis();

        while (_state == Idle) {
            // https://www.forward.com.au/pfod/ArduinoProgramming/TimingDelaysInArduino.html#unsigned
            if ((millis() - startTime) > timeout) {
                disable();
                return ERROR_RX_TIMEOUT;
            }
        }
    }

    while (_state != Received) {
        // NOP
    }

    // Copy the count and error then disable.
    uint16_t count = _bufferCount;
    uint16_t error = _error;

    disable();

    // Detect a receiver error.
    if (error > 0) {
        return (-1) * (error + 100);
    }

    // Detect a buffer overflow.
    if (count > bufferSize) {
        return ERROR_RX_OVERFLOW;
    }

    // Unscramble the data.
    for (int index = 0; index < count; index++) {
        buffer[index] = _dataBus.decode(buffer[index]);
    }

    return count;
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

    _bufferCount = 0;
    _state = Receiving;
}

void NewCoaxReceiver::dataAvailableInterrupt()
{
    if (_state != Receiving) {
        return;
    }

    uint16_t word = read();

    if (_bufferCount < _bufferSize) {
        _buffer[_bufferCount++] = word;
    } else {
        _bufferCount = _bufferSize + 1;
    }

    // TODO: this is wrong... but it allows things to settle!
    delayMicroseconds(1);

    if (!digitalRead(RX_ACTIVE_PIN) && !digitalRead(RX_DATA_AVAILABLE_PIN)) {
        _state = Received;
    }
}

void NewCoaxReceiver::errorInterrupt()
{
    _error = _dataBus.decode(read());

    if (_state == Receiving) {
        _state = Received;
    }

    reset();
}

void NewCoaxReceiver::reset()
{
    digitalWrite(RX_RESET_PIN, HIGH);
    delayMicroseconds(1);
    digitalWrite(RX_RESET_PIN, LOW);
}

inline uint16_t NewCoaxReceiver::read()
{
    digitalWrite(RX_READ_PIN, HIGH);

    uint16_t word = _dataBus.read();

    delayMicroseconds(1);

    digitalWrite(RX_READ_PIN, LOW);

    return word;
}

void NewCoaxDataBus::setMode(int mode)
{
    for (int pin = DATA_BUS_START_PIN; pin <= DATA_BUS_END_PIN; pin++) {
        pinMode(pin, mode);
    }
}

inline uint16_t NewCoaxDataBus::read()
{
    return (GPIO6_DR & DATA_BUS_MASK) >> 16;
}

inline void NewCoaxDataBus::write(uint16_t word)
{
    uint32_t bus = (word << 16) & DATA_BUS_MASK;

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
