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
#include <cstdint>
#include <cstddef>

#include "tim.h"
#include "usb_device.h"

#include "pins.h"
#include "config.h"
#include "indicators.h"
#include "ice40.h"
#include "coax.h"
#include "message.h"
#include "interface.h"
#include "debug.h"

void handleMessage(const uint8_t *, size_t);
void handleMessageReceiverError(MessageReceiverError);

extern "C" void SystemClock_Config();

Indicators indicators;

const uint8_t ice40Bitstream[] = {
#include "bitstream.inc"
};

ICE40 ice40;

SPICoaxTransceiver spiCoaxTransceiver;

volatile uint16_t coaxBuffer[COAX_BUFFER_SIZE];

Coax coax(spiCoaxTransceiver, CoaxParity::Even, coaxBuffer, COAX_BUFFER_SIZE);

volatile uint8_t messageBuffer[MESSAGE_BUFFER_SIZE];

MessageReceiver messageReceiver(messageBuffer, MESSAGE_BUFFER_SIZE, handleMessage,
        handleMessageReceiverError);

Interface interface(coax, indicators);

int main(void)
{
    HAL_Init();

    SystemClock_Config();

    // Initialize the debug UART and GPIO devices.
    Debug::init();

    Debug::banner();

    // Initialize the USB CDC device.
    printf("\r\nInitializing USB CDC device...");

    MX_USB_DEVICE_Init();

    printf(" done.\r\n");

    // Initialize the indicators.
    MX_TIM6_Init();

    indicators.init();

    HAL_Delay(500);

    HAL_TIM_Base_Start_IT(&htim6);

    indicators.setStatus(INDICATORS_STATUS_CONFIGURING);

    // Configure the iCE40 FPGA.
    printf("Configuring iCE40 FPGA...");

    while (!ice40.configure(ice40Bitstream, sizeof(ice40Bitstream))) {
        indicators.error();

        HAL_Delay(1000);
    }

    printf(" done.\r\n");

    // Initialize the coax module.
    printf("Initializing coax module...");

    while (!coax.init()) {
        indicators.error();

        HAL_Delay(1000);
    }

    printf(" done.\r\n");

    HAL_Delay(500);

    indicators.setStatus(INDICATORS_STATUS_RUNNING);

    printf("\r\nREADY.\r\n");

    while (true) {
        messageReceiver.dispatch();
    }
}

extern "C" void handleMessageData(const uint8_t *buffer, size_t bufferCount)
{
    messageReceiver.load(buffer, bufferCount);
}

void handleMessage(const uint8_t *buffer, size_t bufferCount)
{
    interface.handleMessage(const_cast<uint8_t *>(buffer), bufferCount);
}

void handleMessageReceiverError(MessageReceiverError error)
{
    interface.handleError(error);
}

void HAL_TIM_PeriodElapsedCallback(TIM_HandleTypeDef *htim)
{
    if (htim->Instance == htim6.Instance) {
        indicators.update();
    }
}

void HAL_GPIO_EXTI_Callback(uint16_t GPIO_Pin)
{
    if (GPIO_Pin == COAX_IRQ_Pin) {
        coax.handleInterrupt();
    }
}

void SystemClock_Config(void)
{
    LL_FLASH_SetLatency(LL_FLASH_LATENCY_4);

    while (LL_FLASH_GetLatency() != LL_FLASH_LATENCY_4) {
    }

    LL_PWR_SetRegulVoltageScaling(LL_PWR_REGU_VOLTAGE_SCALE1);

    LL_RCC_MSI_Enable();

    while (LL_RCC_MSI_IsReady() != 1) {
    }

    LL_RCC_MSI_EnableRangeSelection();
    LL_RCC_MSI_SetRange(LL_RCC_MSIRANGE_6);
    LL_RCC_MSI_SetCalibTrimming(0);

    LL_RCC_PLL_ConfigDomain_SYS(LL_RCC_PLLSOURCE_MSI, LL_RCC_PLLM_DIV_1, 40, LL_RCC_PLLR_DIV_2);
    LL_RCC_PLL_EnableDomain_SYS();
    LL_RCC_PLL_Enable();

    while (LL_RCC_PLL_IsReady() != 1) {
    }

    LL_RCC_PLLSAI1_ConfigDomain_48M(LL_RCC_PLLSOURCE_MSI, LL_RCC_PLLM_DIV_1, 24, LL_RCC_PLLSAI1Q_DIV_2);
    LL_RCC_PLLSAI1_EnableDomain_48M();
    LL_RCC_PLLSAI1_Enable();

    while (LL_RCC_PLLSAI1_IsReady() != 1) {
    }

    LL_RCC_SetSysClkSource(LL_RCC_SYS_CLKSOURCE_PLL);

    while (LL_RCC_GetSysClkSource() != LL_RCC_SYS_CLKSOURCE_STATUS_PLL) {
    }

    LL_RCC_SetAHBPrescaler(LL_RCC_SYSCLK_DIV_1);
    LL_RCC_SetAPB1Prescaler(LL_RCC_APB1_DIV_1);
    LL_RCC_SetAPB2Prescaler(LL_RCC_APB2_DIV_1);
    LL_SetSystemCoreClock(80000000);

    if (HAL_InitTick(TICK_INT_PRIORITY) != HAL_OK) {
        Error_Handler();
    }

    LL_RCC_SetUSARTClockSource(LL_RCC_USART1_CLKSOURCE_PCLK2);
    LL_RCC_SetUSBClockSource(LL_RCC_USB_CLKSOURCE_PLLSAI1);
}

void Error_Handler(void)
{
}

uint32_t bootMagic = 0x00000000;

void resetToBootloader()
{
    bootMagic = 0x32703270;

    NVIC_SystemReset();
}
