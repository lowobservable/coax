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

#include <cstring>

#include "stm32l4xx_ll_spi.h"

#include "pins.h"
#include "debug.h"

#include "coax.h"

Coax::Coax(SPICoaxTransceiver &spiCoaxTransceiver, volatile uint16_t *buffer,
        size_t bufferSize) :
    _spiCoaxTransceiver(spiCoaxTransceiver),
    _txProtocol(CoaxProtocol::_3270),
    _rxProtocol(CoaxProtocol::_3270),
    _parity(CoaxParity::Even),
    _buffer(buffer),
    _bufferSize(bufferSize)
{
    _isInitialized = false;
}

bool Coax::init()
{
    _isInitialized = false;

    _interruptState = COAX_INTERRUPT_STATE_DISABLED;

    if (!_spiCoaxTransceiver.init()) {
        return false;
    }

    _spiCoaxTransceiver.setTXProtocol(_txProtocol);
    _spiCoaxTransceiver.setTXParity(_parity);

    _spiCoaxTransceiver.setRXProtocol(_rxProtocol);
    _spiCoaxTransceiver.setRXParity(_parity);

    _isInitialized = true;

    return _isInitialized;
}

void Coax::reset()
{
    if (!_isInitialized) {
        return;
    }

    _interruptState = COAX_INTERRUPT_STATE_DISABLED;

    _spiCoaxTransceiver.reset();

    _spiCoaxTransceiver.setTXProtocol(_txProtocol);
    _spiCoaxTransceiver.setTXParity(_parity);

    _spiCoaxTransceiver.setRXProtocol(_rxProtocol);
    _spiCoaxTransceiver.setRXParity(_parity);
}

void Coax::setTXProtocol(CoaxProtocol protocol)
{
    if (!_isInitialized) {
        _txProtocol = protocol;
        return;
    }

    if (_txProtocol == protocol) {
        return;
    }

    _spiCoaxTransceiver.setTXProtocol(protocol);

    _txProtocol = protocol;
}

void Coax::setRXProtocol(CoaxProtocol protocol)
{
    if (!_isInitialized) {
        _rxProtocol = protocol;
        return;
    }

    if (_rxProtocol == protocol) {
        return;
    }

    _spiCoaxTransceiver.setRXProtocol(protocol);

    _rxProtocol = protocol;
}

void Coax::setParity(CoaxParity parity)
{
    if (!_isInitialized) {
        _parity = parity;
        return;
    }

    if (_parity == parity) {
        return;
    }

    _spiCoaxTransceiver.setTXParity(parity);
    _spiCoaxTransceiver.setRXParity(parity);

    _parity = parity;
}

int Coax::transmit(const uint16_t *buffer, size_t bufferCount)
{
    if (!_isInitialized) {
        return COAX_ERROR_NOT_INITIALIZED;
    }

    uint8_t status = _spiCoaxTransceiver.readRegister(COAX_REGISTER_STATUS);

    if (status & COAX_REGISTER_STATUS_RX_ACTIVE) {
        return COAX_ERROR_TX_RECEIVER_ACTIVE;
    }

    if (status & COAX_REGISTER_STATUS_RX_ERROR) {
        Debug::trap(101);

        _spiCoaxTransceiver.reset();
    }

    _interruptState = COAX_INTERRUPT_STATE_IDLE;

    return _spiCoaxTransceiver.transmit(buffer, bufferCount);
}

int Coax::receive(uint16_t *buffer, size_t bufferSize, uint16_t timeout)
{
    if (!_isInitialized) {
        return COAX_ERROR_NOT_INITIALIZED;
    }

    if (timeout > 0) {
        uint32_t startTime = HAL_GetTick();

        while (_interruptState == COAX_INTERRUPT_STATE_IDLE) {
            // https://www.forward.com.au/pfod/ArduinoProgramming/TimingDelaysInArduino.html#unsigned
            if ((HAL_GetTick() - startTime) > timeout) {
                return 0;
            }
        }
    }

uint32_t startTime = HAL_GetTick();

    while (!(_interruptState == COAX_INTERRUPT_STATE_RECEIVED || _interruptState == COAX_INTERRUPT_STATE_ERROR)) {
if ((HAL_GetTick() - startTime) > 1000) {
    Debug::trap(102);
}
    }

    int count = 0;

    if (_interruptState == COAX_INTERRUPT_STATE_RECEIVED) {
        count = _bufferCount > bufferSize ? bufferSize : _bufferCount;

        memcpy(buffer, const_cast<uint16_t *>(_buffer), count * sizeof(uint16_t));

        // TODO: we should be able to manipulate _buffer and not change the state
        // to allow multiple calls to this method to read a large message... but
        // that is not necessary right now
    } else if (_interruptState == COAX_INTERRUPT_STATE_ERROR) {
        Debug::trap(103, "error = %d", _error);

        count = (-1) * _error;
    }

    _interruptState = COAX_INTERRUPT_STATE_IDLE;

    return count;
}

void Coax::handleInterrupt()
{
    if (!_isInitialized) {
        Debug::trap(104);
        return;
    }

    if (_interruptState != COAX_INTERRUPT_STATE_IDLE) {
        Debug::trap(105, "state = %d", _interruptState);
        return;
    }

    _interruptState = COAX_INTERRUPT_STATE_RECEIVING;

    int error = 0;

    uint16_t *buffer = const_cast<uint16_t *>(_buffer);
    size_t bufferSize = _bufferSize;
    int bufferCount = 0;

    bool isActive;
    int count;

    do {
        // Determine if the receiver is active before reading from the FIFO to
        // avoid a race condition where the FIFO is empty, the receiver is
        // active but is inactive by the time we check the status.
        isActive = _spiCoaxTransceiver.isRXActive();

        // TODO: need to somehow handle an overflow detection here...

        count = _spiCoaxTransceiver.receive(buffer, bufferSize);

        if (count < 0) {
            error = (-1) * count;
            break;
        }

        bufferCount += count;

        buffer += count;
        bufferSize -= count;
    } while (isActive || count == static_cast<int>(bufferSize));

    if (error != 0) {
        _bufferCount = 0;
        _error = error;

        _interruptState = COAX_INTERRUPT_STATE_ERROR;
    } else {
        _bufferCount = bufferCount;
        _error = 0;

        _interruptState = COAX_INTERRUPT_STATE_RECEIVED;
    }
}

#define COAX_COMMAND_READ_REGISTER 0x2
#define COAX_COMMAND_WRITE_REGISTER 0x3
#define COAX_COMMAND_TX 0x4
#define COAX_COMMAND_RX 0x5
#define COAX_COMMAND_RESET 0xff

#define NOP asm volatile("nop\n\t")
#define ATOMIC_BLOCK_START __disable_irq()
#define ATOMIC_BLOCK_END __enable_irq()

SPICoaxTransceiver::SPICoaxTransceiver()
{
}

bool SPICoaxTransceiver::init()
{
    // Configure GPIO.
    __HAL_RCC_GPIOA_CLK_ENABLE();
    __HAL_RCC_GPIOB_CLK_ENABLE();

    HAL_GPIO_WritePin(GPIOA, ICE40_CS_Pin | COAX_RESET_Pin, GPIO_PIN_RESET);

    GPIO_InitTypeDef gpioInit = { 0 };

    gpioInit.Pin = ICE40_CS_Pin | COAX_RESET_Pin;
    gpioInit.Mode = GPIO_MODE_OUTPUT_PP;
    gpioInit.Pull = GPIO_NOPULL;
    gpioInit.Speed = GPIO_SPEED_FREQ_LOW;

    HAL_GPIO_Init(GPIOA, &gpioInit);

    gpioInit.Pin = COAX_IRQ_Pin;
    gpioInit.Mode = GPIO_MODE_IT_RISING;
    gpioInit.Pull = GPIO_NOPULL;

    HAL_GPIO_Init(GPIOB, &gpioInit);

    HAL_NVIC_SetPriority(EXTI0_IRQn, 0, 0);
    HAL_NVIC_EnableIRQ(EXTI0_IRQn);

    // Set initial GPIO state.
    HAL_GPIO_WritePin(GPIOA, ICE40_CS_Pin, GPIO_PIN_SET);
    HAL_GPIO_WritePin(GPIOA, COAX_RESET_Pin, GPIO_PIN_RESET);

    // Configure SPI.
    __HAL_RCC_SPI1_CLK_ENABLE();

    gpioInit.Pin = ICE40_SCK_Pin | ICE40_SDI_Pin | ICE40_SDO_Pin;
    gpioInit.Mode = GPIO_MODE_AF_PP;
    gpioInit.Alternate = GPIO_AF5_SPI1;
    gpioInit.Pull = GPIO_NOPULL;
    gpioInit.Speed = GPIO_SPEED_FREQ_VERY_HIGH;

    HAL_GPIO_Init(GPIOA, &gpioInit);

    LL_SPI_InitTypeDef spiInit = { 0 };

    spiInit.TransferDirection = LL_SPI_FULL_DUPLEX;
    spiInit.Mode = LL_SPI_MODE_MASTER;
    spiInit.DataWidth = LL_SPI_DATAWIDTH_8BIT;
    spiInit.ClockPolarity = LL_SPI_POLARITY_LOW;
    spiInit.ClockPhase = LL_SPI_PHASE_1EDGE;
    spiInit.NSS = LL_SPI_NSS_SOFT;
    spiInit.BaudRate = LL_SPI_BAUDRATEPRESCALER_DIV8;
    spiInit.BitOrder = LL_SPI_MSB_FIRST;
    spiInit.CRCCalculation = LL_SPI_CRCCALCULATION_DISABLE;
    spiInit.CRCPoly = 7;

    LL_SPI_Init(SPI1, &spiInit);

    LL_SPI_SetStandard(SPI1, LL_SPI_PROTOCOL_MOTOROLA);
    LL_SPI_DisableNSSPulseMgt(SPI1);
    LL_SPI_SetRxFIFOThreshold(SPI1, LL_SPI_RX_FIFO_TH_QUARTER);

    LL_SPI_Enable(SPI1);

    // Release hardware reset.
    HAL_GPIO_WritePin(GPIOA, COAX_RESET_Pin, GPIO_PIN_SET);

    uint8_t deviceId = readRegister(COAX_REGISTER_DEVICE_ID);

    if (deviceId != 0xa5) {
        return false;
    }

    reset();

    setLoopback(false);

    setTXParity(CoaxParity::Even);
    setRXParity(CoaxParity::Even);

    return true;
}

void SPICoaxTransceiver::reset()
{
    uint8_t transmitBuffer[1] = { COAX_COMMAND_RESET };

    ATOMIC_BLOCK_START;
    LL_GPIO_ResetOutputPin(ICE40_CS_GPIO_Port, ICE40_CS_Pin);

    spiTransfer(transmitBuffer, NULL, 1);

    LL_GPIO_SetOutputPin(ICE40_CS_GPIO_Port, ICE40_CS_Pin);
    ATOMIC_BLOCK_END;
}

uint8_t SPICoaxTransceiver::readRegister(uint8_t index)
{
    uint8_t transmitBuffer[2] = { (uint8_t) (COAX_COMMAND_READ_REGISTER | (index << 4)), 0x00 };
    uint8_t receiveBuffer[2];

    ATOMIC_BLOCK_START;
    LL_GPIO_ResetOutputPin(ICE40_CS_GPIO_Port, ICE40_CS_Pin);

    spiTransfer(transmitBuffer, receiveBuffer, 2);

    LL_GPIO_SetOutputPin(ICE40_CS_GPIO_Port, ICE40_CS_Pin);
    ATOMIC_BLOCK_END;

    return receiveBuffer[1];
}

void SPICoaxTransceiver::writeRegister(uint8_t index, uint8_t value, uint8_t mask)
{
    uint8_t transmitBuffer[3] = { (uint8_t) (COAX_COMMAND_WRITE_REGISTER | (index << 4)), mask, value };

    ATOMIC_BLOCK_START;
    LL_GPIO_ResetOutputPin(ICE40_CS_GPIO_Port, ICE40_CS_Pin);

    spiTransfer(transmitBuffer, NULL, 3);

    LL_GPIO_SetOutputPin(ICE40_CS_GPIO_Port, ICE40_CS_Pin);
    ATOMIC_BLOCK_END;
}

int SPICoaxTransceiver::transmit(const uint16_t *buffer, size_t bufferCount)
{
    uint8_t transmitBuffer[2] = { COAX_COMMAND_TX };
    uint8_t receiveBuffer[2];

    size_t count = 0;
    int error = 0;

    ATOMIC_BLOCK_START;
    LL_GPIO_ResetOutputPin(ICE40_CS_GPIO_Port, ICE40_CS_Pin);

    spiTransfer(transmitBuffer, NULL, 1);

    do {
        transmitBuffer[0] = (buffer[count] >> 8) & 0x03;
        transmitBuffer[1] = buffer[count] & 0xff;

        spiTransfer(transmitBuffer, receiveBuffer, 2);

        uint8_t value = receiveBuffer[1];

        if (value == 0) {
            count++;
        } else if (value == 0x81) {
            // Overflow... we'll just try again.
            continue;
        } else if (value == 0x82) {
            error = COAX_ERROR_TX_UNDERFLOW;
            break;
        }
    } while (count < bufferCount);

    LL_GPIO_SetOutputPin(ICE40_CS_GPIO_Port, ICE40_CS_Pin);
    ATOMIC_BLOCK_END;

    if (error != 0) {
        return error;
    }

    while (!isTXComplete()) {
        NOP;
    }

    return count;
}

int SPICoaxTransceiver::receive(uint16_t *buffer, size_t bufferSize)
{
    uint8_t transmitBuffer[2] = { COAX_COMMAND_RX };
    uint8_t receiveBuffer[2];

    size_t count = 0;
    int error = 0;

    ATOMIC_BLOCK_START;
    LL_GPIO_ResetOutputPin(ICE40_CS_GPIO_Port, ICE40_CS_Pin);

    spiTransfer(transmitBuffer, NULL, 1);

    transmitBuffer[0] = 0x00;
    transmitBuffer[1] = 0x00;

    do {
        spiTransfer(transmitBuffer, receiveBuffer, 2);

        uint16_t value = (receiveBuffer[0] << 8) | receiveBuffer[1];

        if (value & 0x8000) {
            error = (-1) * (value & 0x03ff);

            if (error == 0) {
                Debug::trap(106);

                error = COAX_ERROR_RX_UNKNOWN;
            }

            break;
        } else if (value & 0x4000) {
            break;
        }

        // TODO: can this ever happen... I don't think so now the loop has
        // been rewritten.
        if (count >= bufferSize) {
            Debug::trap(107);
            break;
        }

        buffer[count] = value & 0x03ff;

        count++;
    } while (count < bufferSize);

    LL_GPIO_SetOutputPin(ICE40_CS_GPIO_Port, ICE40_CS_Pin);
    ATOMIC_BLOCK_END;

    if (error != 0) {
        return error;
    }

    return count;
}

void SPICoaxTransceiver::setLoopback(bool loopback)
{
    writeRegister(COAX_REGISTER_CONTROL, loopback ? COAX_REGISTER_CONTROL_LOOPBACK : 0, COAX_REGISTER_CONTROL_LOOPBACK);
}

void SPICoaxTransceiver::setTXProtocol(CoaxProtocol protocol)
{
    writeRegister(COAX_REGISTER_CONTROL, protocol == CoaxProtocol::_3299 ? COAX_REGISTER_CONTROL_TX_PROTOCOL : 0, COAX_REGISTER_CONTROL_TX_PROTOCOL);
}

void SPICoaxTransceiver::setTXParity(CoaxParity parity)
{
    writeRegister(COAX_REGISTER_CONTROL, parity == CoaxParity::Even ? COAX_REGISTER_CONTROL_TX_PARITY : 0, COAX_REGISTER_CONTROL_TX_PARITY);
}

void SPICoaxTransceiver::setRXProtocol(CoaxProtocol protocol)
{
    writeRegister(COAX_REGISTER_CONTROL, protocol == CoaxProtocol::_3299 ? COAX_REGISTER_CONTROL_RX_PROTOCOL : 0, COAX_REGISTER_CONTROL_RX_PROTOCOL);
}

void SPICoaxTransceiver::setRXParity(CoaxParity parity)
{
    writeRegister(COAX_REGISTER_CONTROL, parity == CoaxParity::Even ? COAX_REGISTER_CONTROL_RX_PARITY : 0, COAX_REGISTER_CONTROL_RX_PARITY);
}

void SPICoaxTransceiver::spiTransfer(const uint8_t *transmitBuffer,
        uint8_t *receiveBuffer, size_t count)
{
    // TODO: flush, or confirm TX ready?

    for (size_t index = 0; index < count; index++) {
        while (!(SPI1->SR & SPI_SR_TXE)) {
            NOP;
        }

        LL_SPI_TransmitData8(SPI1, transmitBuffer[index]);

        while (!LL_SPI_IsActiveFlag_RXNE(SPI1)) {
            NOP;
        }

        uint8_t value = LL_SPI_ReceiveData8(SPI1);

        if (receiveBuffer != NULL) {
            receiveBuffer[index] = value;
        }
    }
}
