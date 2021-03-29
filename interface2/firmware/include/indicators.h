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

#pragma once

enum IndicatorsStatus {
    INDICATORS_STATUS_UNKNOWN,
    INDICATORS_STATUS_CONFIGURING,
    INDICATORS_STATUS_RUNNING
};

class Indicators
{
public:
    Indicators();

    void init();

    void setStatus(IndicatorsStatus status);

    void tx();
    void rx();
    void error();

    void update();

private:
    volatile IndicatorsStatus _status;
    volatile uint8_t _txState;
    volatile uint8_t _rxState;
    volatile uint8_t _errorState;
};
