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

#include "pins.h"

#include "indicators.h"

#define LED_GPIO_Port GPIOB

Indicators::Indicators()
{
    _status = INDICATORS_STATUS_UNKNOWN;

    _txState = 0;
    _rxState = 0;
    _errorState = 0;
}

void Indicators::init()
{
    // Configure GPIO.
    __HAL_RCC_GPIOB_CLK_ENABLE();

    HAL_GPIO_WritePin(LED_GPIO_Port, LED_STATUS_Pin | LED_TX_Pin | LED_RX_Pin | LED_ERROR_Pin, GPIO_PIN_RESET);

    GPIO_InitTypeDef gpioInit = { 0 };

    gpioInit.Pin = LED_STATUS_Pin | LED_TX_Pin | LED_RX_Pin | LED_ERROR_Pin;
    gpioInit.Mode = GPIO_MODE_OUTPUT_PP;
    gpioInit.Pull = GPIO_NOPULL;
    gpioInit.Speed = GPIO_SPEED_FREQ_LOW;

    HAL_GPIO_Init(LED_GPIO_Port, &gpioInit);

    // Set initial GPIO state.
    HAL_GPIO_WritePin(LED_GPIO_Port, LED_STATUS_Pin | LED_TX_Pin | LED_RX_Pin | LED_ERROR_Pin, GPIO_PIN_SET);
}

void Indicators::setStatus(IndicatorsStatus status)
{
    _status = status;

    if (_status == INDICATORS_STATUS_CONFIGURING) {
        HAL_GPIO_WritePin(LED_GPIO_Port, LED_STATUS_Pin, GPIO_PIN_SET);

        HAL_GPIO_WritePin(LED_GPIO_Port, LED_TX_Pin | LED_RX_Pin | LED_ERROR_Pin, GPIO_PIN_RESET);
    } else if (_status == INDICATORS_STATUS_RUNNING) {
        HAL_GPIO_WritePin(LED_GPIO_Port, LED_STATUS_Pin, GPIO_PIN_SET);
    }
}

void Indicators::tx()
{
    if (_txState == 0) {
        _txState = 2;
    }
}

void Indicators::rx()
{
    if (_rxState == 0) {
        _rxState = 2;
    }
}

void Indicators::error()
{
    if (_errorState == 0) {
        _errorState = 2;
    }
}

void Indicators::update()
{
    if (_status == INDICATORS_STATUS_CONFIGURING) {
        HAL_GPIO_TogglePin(LED_GPIO_Port, LED_STATUS_Pin);
    }

    if (_txState > 0) {
        HAL_GPIO_WritePin(LED_GPIO_Port, LED_TX_Pin, _txState == 2 ? GPIO_PIN_SET : GPIO_PIN_RESET);

        _txState--;
    } else {
        HAL_GPIO_WritePin(LED_GPIO_Port, LED_TX_Pin, GPIO_PIN_RESET);
    }

    if (_rxState > 0) {
        HAL_GPIO_WritePin(LED_GPIO_Port, LED_RX_Pin, _rxState == 2 ? GPIO_PIN_SET : GPIO_PIN_RESET);

        _rxState--;
    } else {
        HAL_GPIO_WritePin(LED_GPIO_Port, LED_RX_Pin, GPIO_PIN_RESET);
    }

    if (_errorState > 0) {
        HAL_GPIO_WritePin(LED_GPIO_Port, LED_ERROR_Pin, _errorState == 2 ? GPIO_PIN_SET : GPIO_PIN_RESET);

        _errorState--;
    } else {
        HAL_GPIO_WritePin(LED_GPIO_Port, LED_ERROR_Pin, GPIO_PIN_RESET);
    }
}
