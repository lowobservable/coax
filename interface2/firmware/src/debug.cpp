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

#include <cstdio>
#include <cstdarg>

#include "stm32l4xx_hal.h"

#include "pins.h"

#include "debug.h"

UART_HandleTypeDef huart1;

bool Debug::init()
{
    // Configure UART.
    huart1.Instance = USART1;

    huart1.Init.BaudRate = 115200;
    huart1.Init.WordLength = UART_WORDLENGTH_8B;
    huart1.Init.StopBits = UART_STOPBITS_1;
    huart1.Init.Parity = UART_PARITY_NONE;
    huart1.Init.Mode = UART_MODE_TX_RX;
    huart1.Init.HwFlowCtl = UART_HWCONTROL_NONE;
    huart1.Init.OverSampling = UART_OVERSAMPLING_16;
    huart1.Init.OneBitSampling = UART_ONE_BIT_SAMPLE_DISABLE;

    huart1.AdvancedInit.AdvFeatureInit = UART_ADVFEATURE_NO_INIT;

    if (HAL_UART_Init(&huart1) != HAL_OK) {
        return false;
    }

    // Configure GPIO.
    __HAL_RCC_GPIOB_CLK_ENABLE();

    HAL_GPIO_WritePin(GPIOB, GPIO0_Pin | GPIO1_Pin, GPIO_PIN_RESET);

    GPIO_InitTypeDef gpioInit = { 0 };

    gpioInit.Pin = GPIO0_Pin | GPIO1_Pin;
    gpioInit.Mode = GPIO_MODE_OUTPUT_PP;
    gpioInit.Pull = GPIO_NOPULL;
    gpioInit.Speed = GPIO_SPEED_FREQ_LOW;

    HAL_GPIO_Init(GPIOB, &gpioInit);

    // Set initial GPIO state.
    HAL_GPIO_WritePin(GPIOB, GPIO0_Pin | GPIO1_Pin, GPIO_PIN_RESET);

    return true;
}

void Debug::banner()
{
    printf("\r\n");
    printf("****** Coax\r\n");
    printf("  **** Build " FIRMWARE_BUILD_WHAT " by " FIRMWARE_BUILD_WHO " on " FIRMWARE_BUILD_WHEN "\r\n");
    printf("    **\r\n");
}

void Debug::setMarker(int marker)
{
    if (marker == 0) {
        HAL_GPIO_WritePin(GPIOB, GPIO0_Pin, GPIO_PIN_SET);
    } else if (marker == 1) {
        HAL_GPIO_WritePin(GPIOB, GPIO1_Pin, GPIO_PIN_SET);
    }
}

void Debug::resetMarker(int marker)
{
    if (marker == 0) {
        HAL_GPIO_WritePin(GPIOB, GPIO0_Pin, GPIO_PIN_RESET);
    } else if (marker == 1) {
        HAL_GPIO_WritePin(GPIOB, GPIO1_Pin, GPIO_PIN_RESET);
    }
}

void Debug::trap(int number)
{
    printf("%lu TRAP[%d]\r\n", HAL_GetTick(), number);
}

void Debug::trap(int number, const char *format, ...)
{
    printf("%lu TRAP[%d] ", HAL_GetTick(), number);

    va_list args;

    va_start(args, format);
    vprintf(format, args);
    va_end(args);

    printf("\r\n");
}

extern "C" void HAL_UART_MspInit(UART_HandleTypeDef *uartHandle)
{
    GPIO_InitTypeDef gpioInit = { 0 };

    if (uartHandle->Instance == USART1) {
        __HAL_RCC_USART1_CLK_ENABLE();
        __HAL_RCC_GPIOA_CLK_ENABLE();

        gpioInit.Pin = GPIO_PIN_9 | GPIO_PIN_10;
        gpioInit.Mode = GPIO_MODE_AF_PP;
        gpioInit.Pull = GPIO_NOPULL;
        gpioInit.Speed = GPIO_SPEED_FREQ_VERY_HIGH;
        gpioInit.Alternate = GPIO_AF7_USART1;

        HAL_GPIO_Init(GPIOA, &gpioInit);
    }
}

extern "C" void HAL_UART_MspDeInit(UART_HandleTypeDef *uartHandle)
{
    if (uartHandle->Instance == USART1) {
        __HAL_RCC_USART1_CLK_DISABLE();

        HAL_GPIO_DeInit(GPIOA, GPIO_PIN_9 | GPIO_PIN_10);
    }
}

extern "C" int _write(int file, char *ptr, int len)
{
    HAL_UART_Transmit(&huart1, reinterpret_cast<uint8_t *>(ptr), len, 100);

    return len;
}
