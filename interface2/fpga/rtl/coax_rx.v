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

`default_nettype none

module coax_rx (
    input clk,
    input reset,
    input rx,
    output reg active,
    output reg error,
    output reg [9:0] data,
    output reg strobe = 0,
    input parity
);
    parameter CLOCKS_PER_BIT = 8;

    localparam CLOCKS_PER_HALF_BIT = CLOCKS_PER_BIT / 2;
    localparam CLOCKS_PER_2_BIT = CLOCKS_PER_BIT * 2;
    localparam CLOCKS_PER_3_BIT = CLOCKS_PER_BIT * 3;
    localparam CLOCKS_LOSS_OF_MID_BIT_TRANSITION = CLOCKS_PER_BIT + (CLOCKS_PER_BIT / 2);

    localparam ERROR_LOSS_OF_MID_BIT_TRANSITION = 10'b0000000001;
    localparam ERROR_PARITY = 10'b0000000010;
    localparam ERROR_INVALID_END_SEQUENCE = 10'b0000000100;

    localparam STATE_IDLE = 0;
    localparam STATE_FIRST_SYNC_BIT = 1;
    localparam STATE_SYNC_BIT = 2;
    localparam STATE_DATA_BIT = 3;
    localparam STATE_PARITY_BIT = 4;
    localparam STATE_END_SEQUENCE_1 = 5;
    localparam STATE_END_SEQUENCE_2 = 6;
    localparam STATE_ERROR = 7;

    reg [2:0] state = STATE_IDLE;
    reg [2:0] next_state;

    reg previous_rx;

    reg [$clog2(CLOCKS_PER_3_BIT):0] mid_bit_counter;
    reg [$clog2(CLOCKS_PER_3_BIT):0] next_mid_bit_counter;

    reg [9:0] next_data;
    reg next_strobe;

    reg [9:0] input_data;
    reg [9:0] next_input_data;
    reg input_data_parity;

    reg [3:0] bit_counter = 0;
    reg [3:0] next_bit_counter;

    reg next_active;
    reg next_error;

    wire ss_detector_strobe;

    coax_rx_ss_detector #(
        .CLOCKS_PER_BIT(CLOCKS_PER_BIT)
    ) ss_detector (
        .clk(clk),
        .reset(reset),
        .enable(state == STATE_IDLE),
        .rx(rx),
        .strobe(ss_detector_strobe)
    );

    always @(*)
    begin
        next_state = state;

        next_mid_bit_counter = mid_bit_counter + 1;

        next_data = data;
        next_strobe = 0;

        next_input_data = input_data;
        next_bit_counter = bit_counter;

        next_active = 0;
        next_error = 0;

        case (state)
            STATE_IDLE:
            begin
                if (ss_detector_strobe)
                begin
                    // The start sequence ends with a code violation, so reset
                    // the mid bit counter as if the next mid-bit transition
                    // is half a bit away.
                    next_mid_bit_counter = CLOCKS_PER_HALF_BIT;
                    next_state = STATE_FIRST_SYNC_BIT;
                end
            end

            STATE_FIRST_SYNC_BIT:
            begin
                // This is really the first STATE_SYNC_BIT, but we treat it
                // differently and consider it part of the start sequence as
                // it must be a 1 and we don't consider the receiver active
                // until this has been detected.
                next_bit_counter = 0;

                if (rx != previous_rx && mid_bit_counter > CLOCKS_PER_HALF_BIT)
                begin
                    next_mid_bit_counter = 0;

                    if (rx)
                        next_state = STATE_DATA_BIT;
                    else
                        next_state = STATE_IDLE;
                end
                else if (mid_bit_counter > CLOCKS_LOSS_OF_MID_BIT_TRANSITION)
                begin
                    next_state = STATE_IDLE;
                end
            end

            STATE_SYNC_BIT:
            begin
                next_active = 1;
                next_bit_counter = 0;

                if (rx != previous_rx && mid_bit_counter > CLOCKS_PER_HALF_BIT)
                begin
                    next_mid_bit_counter = 0;

                    if (rx)
                        next_state = STATE_DATA_BIT;
                    else
                        next_state = STATE_END_SEQUENCE_1;
                end
                else if (mid_bit_counter > CLOCKS_LOSS_OF_MID_BIT_TRANSITION)
                begin
                    next_data = ERROR_LOSS_OF_MID_BIT_TRANSITION;
                    next_state = STATE_ERROR;
                end
            end

            STATE_DATA_BIT:
            begin
                next_active = 1;

                if (rx != previous_rx && mid_bit_counter > CLOCKS_PER_HALF_BIT)
                begin
                    next_mid_bit_counter = 0;

                    next_input_data = { input_data[8:0], rx };

                    if (bit_counter < 9)
                        next_bit_counter = bit_counter + 1;
                    else
                        next_state = STATE_PARITY_BIT;
                end
                else if (mid_bit_counter > CLOCKS_LOSS_OF_MID_BIT_TRANSITION)
                begin
                    next_data = ERROR_LOSS_OF_MID_BIT_TRANSITION;
                    next_state = STATE_ERROR;
                end
            end

            STATE_PARITY_BIT:
            begin
                next_active = 1;

                if (rx != previous_rx && mid_bit_counter > CLOCKS_PER_HALF_BIT)
                begin
                    if (rx == input_data_parity)
                    begin
                        next_strobe = 1;
                        next_data = input_data;
                        next_state = STATE_SYNC_BIT;
                    end
                    else
                    begin
                        next_data = ERROR_PARITY;
                        next_state = STATE_ERROR;
                    end

                    next_mid_bit_counter = 0;
                end
                else if (mid_bit_counter > CLOCKS_LOSS_OF_MID_BIT_TRANSITION)
                begin
                    next_data = ERROR_LOSS_OF_MID_BIT_TRANSITION;
                    next_state = STATE_ERROR;
                end
            end

            STATE_END_SEQUENCE_1:
            begin
                if (rx)
                begin
                    next_state = STATE_END_SEQUENCE_2;
                    next_mid_bit_counter = 0;
                end
                else if (mid_bit_counter > CLOCKS_PER_BIT)
                begin
                    next_data = ERROR_INVALID_END_SEQUENCE;
                    next_state = STATE_ERROR;
                end
            end

            STATE_END_SEQUENCE_2:
            begin
                if (!rx)
                begin
                    next_state = STATE_IDLE;
                end
                else if (mid_bit_counter > CLOCKS_PER_3_BIT)
                begin
                    // TODO: should this go to ERROR on timeout?
                    next_state = STATE_IDLE;
                end
            end

            STATE_ERROR:
            begin
                next_error = 1;
            end
        endcase
    end

    always @(posedge clk)
    begin
        state <= next_state;

        mid_bit_counter <= next_mid_bit_counter;

        data <= next_data;
        strobe <= next_strobe;

        input_data <= next_input_data;

        // Parity includes the sync bit.
        input_data_parity <= (parity == 1 ? ^{ 1'b1, input_data } : ~^{ 1'b1, input_data });

        bit_counter <= next_bit_counter;

        active <= next_active;
        error <= next_error;

        if (reset)
        begin
            state <= STATE_IDLE;

            strobe <= 0;

            active <= 0;
            error <= 0;
        end

        previous_rx <= rx;
    end
endmodule
