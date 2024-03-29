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

module coax_tx (
    input clk,
    input reset,
    output reg active,
    output reg tx,
    input [9:0] data,
    input strobe,
    output ready,
    input protocol,
    input parity
);
    parameter CLOCKS_PER_BIT = 8;

    localparam IDLE = 0;
    localparam START_SEQUENCE_1 = 1;
    localparam START_SEQUENCE_2 = 2;
    localparam START_SEQUENCE_3 = 3;
    localparam START_SEQUENCE_4 = 4;
    localparam START_SEQUENCE_5 = 5;
    localparam START_SEQUENCE_6 = 6;
    localparam START_SEQUENCE_7 = 7;
    localparam START_SEQUENCE_8 = 8;
    localparam START_SEQUENCE_9 = 9;
    localparam SYNC_BIT = 10;
    localparam DATA_BIT = 11;
    localparam PARITY_BIT = 12;
    localparam END_SEQUENCE_1 = 13;
    localparam END_SEQUENCE_2 = 14;
    localparam END_SEQUENCE_3 = 15;

    reg [3:0] state = IDLE;
    reg [3:0] next_state;

    reg next_tx;

    reg first_word;
    reg next_first_word;
    reg end_sequence;
    reg next_end_sequence;

    reg [9:0] output_data;
    reg [9:0] next_output_data;
    reg output_data_full = 0;
    reg next_output_data_full;
    reg parity_bit;
    reg next_parity_bit;
    reg output_parity_bit;
    reg next_output_parity_bit;

    reg [3:0] bit_counter = 0;
    reg [3:0] next_bit_counter;

    reg bit_timer_reset = 0;
    reg next_bit_timer_reset;

    wire first_half;
    wire second_half;
    wire last_clock;

    coax_tx_bit_timer #(
        .CLOCKS_PER_BIT(CLOCKS_PER_BIT)
    ) bit_timer (
        .clk(clk),
        .reset(bit_timer_reset),
        .first_half(first_half),
        .second_half(second_half),
        .last_clock(last_clock)
    );

    always @(*)
    begin
        next_state = state;

        next_tx = 0;

        next_first_word = first_word;
        next_end_sequence = 0;

        next_output_data = output_data;
        next_output_data_full = output_data_full;
        next_parity_bit = parity_bit;
        next_output_parity_bit = output_parity_bit;

        if (strobe && ready)
        begin
            next_output_data = data;
            next_output_data_full = 1;

            // Parity includes the sync bit.
            next_parity_bit = (parity == 1 ? ^{ 1'b1, data } : ~^{ 1'b1, data });
        end

        next_bit_counter = bit_counter;

        next_bit_timer_reset = 0;

        case (state)
            IDLE:
            begin
                next_bit_timer_reset = 1;

                if (output_data_full)
                begin
                    next_state = START_SEQUENCE_1;
                end
            end

            START_SEQUENCE_1:
            begin
                next_tx = 1;

                // TODO... off by 1
                if (second_half)
                begin
                    next_bit_timer_reset = 1;
                    next_state = START_SEQUENCE_2;
                end
            end

            START_SEQUENCE_2:
            begin
                next_tx = first_half ? 0 : 1;

                if (last_clock)
                    next_state = START_SEQUENCE_3;
            end

            START_SEQUENCE_3:
            begin
                next_tx = first_half ? 0 : 1;

                if (last_clock)
                    next_state = START_SEQUENCE_4;
            end

            START_SEQUENCE_4:
            begin
                next_tx = first_half ? 0 : 1;

                if (last_clock)
                    next_state = START_SEQUENCE_5;
            end

            START_SEQUENCE_5:
            begin
                next_tx = first_half ? 0 : 1;

                if (last_clock)
                    next_state = START_SEQUENCE_6;
            end

            START_SEQUENCE_6:
            begin
                next_tx = first_half ? 0 : 1;

                if (last_clock)
                    next_state = START_SEQUENCE_7;
            end

            START_SEQUENCE_7:
            begin
                next_tx = 0;

                if (last_clock)
                    next_state = START_SEQUENCE_8;
            end

            START_SEQUENCE_8:
            begin
                next_tx = first_half ? 0 : 1;

                if (last_clock)
                    next_state = START_SEQUENCE_9;
            end

            START_SEQUENCE_9:
            begin
                next_tx = 1;
                next_first_word = 1;

                if (last_clock)
                    next_state = SYNC_BIT;
            end

            SYNC_BIT:
            begin
                next_tx = first_half ? 0 : 1;

                if (last_clock)
                begin
                    // First word is 6 bits in 3299 protocol mode.
                    if (protocol == 1 && first_word)
                    begin
                        next_output_data = { output_data[5:0], 4'b0 };
                        next_bit_counter = 5;
                    end
                    else
                    begin
                        next_bit_counter = 9;
                    end

                    next_state = DATA_BIT;
                end
            end

            DATA_BIT:
            begin
                next_tx = first_half ? ~output_data[9] : output_data[9];

                if (last_clock)
                begin
                    next_output_data = { output_data[8:0], output_data[9] };
                    next_bit_counter = bit_counter - 1;

                    if (bit_counter == 0)
                    begin
                        next_output_data_full = 0;
                        next_output_parity_bit = parity_bit;

                        next_state = PARITY_BIT;
                    end
                end
            end

            PARITY_BIT:
            begin
                next_tx = first_half ? ~output_parity_bit : output_parity_bit;

                if (last_clock)
                begin
                    next_first_word = 0;

                    if (output_data_full)
                    begin
                        next_state = SYNC_BIT;
                    end
                    else
                    begin
                        next_end_sequence = 1;
                        next_state = END_SEQUENCE_1;
                    end
                end
            end

            END_SEQUENCE_1:
            begin
                next_tx = first_half ? 1 : 0;
                next_end_sequence = 1;

                if (last_clock)
                    next_state = END_SEQUENCE_2;
            end

            END_SEQUENCE_2:
            begin
                next_tx = 1;
                next_end_sequence = 1;

                if (last_clock)
                    next_state = END_SEQUENCE_3;
            end

            END_SEQUENCE_3:
            begin
                next_tx = 1;
                next_end_sequence = 1;

                if (last_clock)
                begin
                    next_tx = 0;
                    next_end_sequence = 0;
                    next_state = IDLE;
                end
            end
        endcase
    end

    always @(posedge clk)
    begin
        state <= next_state;

        active <= (state != IDLE); // TODO: this causes active to remain high one additional clock cycle
        tx <= next_tx;

        first_word <= next_first_word;
        end_sequence <= next_end_sequence;

        output_data <= next_output_data;
        output_data_full <= next_output_data_full;
        parity_bit <= next_parity_bit;
        output_parity_bit <= next_output_parity_bit;

        bit_counter <= next_bit_counter;

        bit_timer_reset <= next_bit_timer_reset;

        if (reset)
        begin
            state <= IDLE;

            active <= 0;
            tx <= 0;

            end_sequence <= 0;

            output_data_full <= 0;
        end
    end

    assign ready = (!output_data_full && !end_sequence);
endmodule
