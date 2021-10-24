// Copyright (c) 2021, Andrew Kay
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

`default_nettype none

module coax_rx_ss_detector (
    input clk,
    input reset,
    input enable,
    input rx,
    output reg strobe = 0
);
    parameter CLOCKS_PER_BIT = 8;

    localparam CLOCKS_PER_1_5_BIT = CLOCKS_PER_BIT + (CLOCKS_PER_BIT / 2);
    localparam CLOCKS_PER_2_BIT = CLOCKS_PER_BIT * 2;
    localparam CLOCKS_PER_2_5_BIT = (CLOCKS_PER_BIT * 2) + (CLOCKS_PER_BIT / 2);
    localparam CLOCKS_PER_3_5_BIT = (CLOCKS_PER_BIT * 3) + (CLOCKS_PER_BIT / 2);

    // Number of pulses (or "bits") required before the code violation.
    localparam PULSE_COUNT = 5;

    localparam STATE_IDLE = 0;
    localparam STATE_PULSE = 1;
    localparam STATE_CODE_VIOLATION_FIRST_HALF = 2;
    localparam STATE_CODE_VIOLATION_SECOND_HALF = 3;

    reg [1:0] state = STATE_IDLE;
    reg [1:0] next_state;

    reg next_strobe;

    reg [$clog2(CLOCKS_PER_3_5_BIT):0] rx_negedge_counter;
    reg [$clog2(CLOCKS_PER_3_5_BIT):0] next_rx_negedge_counter;

    reg [$clog2(PULSE_COUNT-1):0] pulse_counter;
    reg [$clog2(PULSE_COUNT-1):0] next_pulse_counter;

    reg previous_rx;

    always @(*)
    begin
        next_state = state;

        next_strobe = 0;

        // Count the clocks since the last negedge.
        next_rx_negedge_counter = rx_negedge_counter + 1;

        if (!rx && previous_rx)
            next_rx_negedge_counter = 0;

        next_pulse_counter = pulse_counter;

        case (state)
            STATE_IDLE:
            begin
                if (!rx && previous_rx)
                    next_state = STATE_PULSE;

                // Consider this the first pulse.
                next_pulse_counter = 1;
            end

            STATE_PULSE:
            begin
                if (!rx && previous_rx)
                begin
                    if (pulse_counter == (PULSE_COUNT - 1))
                        next_state = STATE_CODE_VIOLATION_FIRST_HALF;
                    else
                        next_pulse_counter = pulse_counter + 1;
                end
                else if (rx_negedge_counter > CLOCKS_PER_1_5_BIT)
                begin
                    next_state = STATE_IDLE;
                end
            end

            STATE_CODE_VIOLATION_FIRST_HALF:
            begin
                if (rx && !previous_rx && rx_negedge_counter > CLOCKS_PER_BIT)
                    next_state = STATE_CODE_VIOLATION_SECOND_HALF;
                else if (rx_negedge_counter > CLOCKS_PER_2_BIT)
                    next_state = STATE_IDLE;
            end

            STATE_CODE_VIOLATION_SECOND_HALF:
            begin
                // Although this is a negedge, the negedge_counter will not
                // reset until the next clock cycle so this comparison is valid.
                if (!rx && rx_negedge_counter > CLOCKS_PER_2_5_BIT)
                begin
                    next_strobe = 1;
                    next_state = STATE_IDLE;
                end
                else if (rx_negedge_counter > CLOCKS_PER_3_5_BIT)
                begin
                    next_state = STATE_IDLE;
                end
            end
        endcase
    end

    always @(posedge clk)
    begin
        state <= next_state;

        strobe <= next_strobe;

        rx_negedge_counter <= next_rx_negedge_counter;
        pulse_counter <= next_pulse_counter;

        if (reset || !enable)
        begin
            state <= STATE_IDLE;

            strobe <= 0;

            rx_negedge_counter <= 0;
            pulse_counter <= 0;
        end

        previous_rx <= rx;
    end
endmodule
