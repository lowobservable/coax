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

#include "ice40.h"

ICE40::ICE40()
{
    _isConfigured = false;
}

inline void clock()
{
    LL_GPIO_ResetOutputPin(ICE40_SCK_GPIO_Port, ICE40_SCK_Pin);

    for (int index = 0; index < 4; index++) {
        asm volatile("nop\n\t");
    }

    LL_GPIO_SetOutputPin(ICE40_SCK_GPIO_Port, ICE40_SCK_Pin);
}

bool ICE40::configure(const uint8_t *bitstream, size_t bitstreamCount)
{
    _isConfigured = false;

    // Configure GPIO.
    __HAL_RCC_GPIOA_CLK_ENABLE();
    __HAL_RCC_GPIOB_CLK_ENABLE();

    HAL_GPIO_WritePin(GPIOA, ICE40_CS_Pin | ICE40_SCK_Pin | ICE40_SDI_Pin, GPIO_PIN_RESET);
    HAL_GPIO_WritePin(GPIOB, ICE40_CRESET_Pin, GPIO_PIN_RESET);

    GPIO_InitTypeDef gpioInit = { 0 };

    gpioInit.Pin = ICE40_CS_Pin | ICE40_SCK_Pin | ICE40_SDI_Pin;
    gpioInit.Mode = GPIO_MODE_OUTPUT_PP;
    gpioInit.Pull = GPIO_NOPULL;
    gpioInit.Speed = GPIO_SPEED_FREQ_LOW;

    HAL_GPIO_Init(GPIOA, &gpioInit);

    gpioInit.Pin = ICE40_CRESET_Pin;
    gpioInit.Mode = GPIO_MODE_OUTPUT_PP;
    gpioInit.Pull = GPIO_NOPULL;
    gpioInit.Speed = GPIO_SPEED_FREQ_LOW;

    HAL_GPIO_Init(GPIOB, &gpioInit);

    gpioInit.Pin = ICE40_CDONE_Pin;
    gpioInit.Mode = GPIO_MODE_INPUT;
    gpioInit.Pull = GPIO_NOPULL;

    HAL_GPIO_Init(GPIOB, &gpioInit);

    // Set initial GPIO state.
    HAL_GPIO_WritePin(ICE40_CS_GPIO_Port, ICE40_CS_Pin | ICE40_SCK_Pin, GPIO_PIN_SET);
    HAL_GPIO_WritePin(ICE40_CRESET_GPIO_Port, ICE40_CRESET_Pin, GPIO_PIN_SET);

    // Assert CS and reset.
    HAL_GPIO_WritePin(ICE40_CS_GPIO_Port, ICE40_CS_Pin, GPIO_PIN_RESET);

    HAL_GPIO_WritePin(ICE40_CRESET_GPIO_Port, ICE40_CRESET_Pin, GPIO_PIN_RESET);

    HAL_Delay(1);

    HAL_GPIO_WritePin(ICE40_CRESET_GPIO_Port, ICE40_CRESET_Pin, GPIO_PIN_SET);

    HAL_Delay(1);

    // Send the bitstream.
    for (size_t index = 0; index < bitstreamCount; index++) {
        uint8_t byte = bitstream[index];

        for (int bitIndex = 7; bitIndex >= 0; bitIndex--) {
            if ((byte >> bitIndex) & 0x01) {
                LL_GPIO_SetOutputPin(ICE40_SDI_GPIO_Port, ICE40_SDI_Pin);
            } else {
                LL_GPIO_ResetOutputPin(ICE40_SDI_GPIO_Port, ICE40_SDI_Pin);
            }

            clock();
        }
    }

    // Check done.
    bool done = LL_GPIO_IsInputPinSet(ICE40_CDONE_GPIO_Port, ICE40_CDONE_Pin);

    if (done) {
        for (int index = 0; index < 49; index++) {
            clock();
        }
    }

    // Deassert CS.
    HAL_GPIO_WritePin(ICE40_CS_GPIO_Port, ICE40_CS_Pin, GPIO_PIN_SET);

    _isConfigured = done;

    return _isConfigured;
}
