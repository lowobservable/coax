`default_nettype none

module coax_tx (
    input clk,
    input reset,
    output reg active,
    output reg tx,
    input [9:0] data,
    input load,
    output full
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

    reg next_active;
    reg next_tx;

    reg previous_load;

    reg [9:0] holding_data;
    reg [9:0] next_holding_data;
    reg holding_data_full = 0;
    reg next_holding_data_full;

    reg [9:0] output_data;
    reg [9:0] next_output_data;
    reg output_data_full = 0;
    reg next_output_data_full;

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

        next_holding_data = holding_data;
        next_holding_data_full = holding_data_full;
        next_output_data = output_data;
        next_output_data_full = output_data_full;

        if (!load && previous_load)
        begin
            if (!holding_data_full && !output_data_full)
            begin
                next_output_data = data;
                next_output_data_full = 1;
            end
            else if (!holding_data_full)
            begin
                next_holding_data = data;
                next_holding_data_full = 1;
            end
        end
        
        next_bit_counter = bit_counter;
        
        next_bit_timer_reset = 0;

        case (state)
            IDLE:
            begin
                if (output_data_full)
                begin
                    next_bit_timer_reset = 1;
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

                if (last_clock)
                    next_state = SYNC_BIT;
            end

            SYNC_BIT:
            begin
                next_tx = first_half ? 0 : 1;

                if (last_clock)
                begin
                    next_bit_counter = 9;
                    next_state = DATA_BIT;
                end
            end

            DATA_BIT:
            begin
                next_tx = first_half ? ~output_data[9] : output_data[9];

                if (last_clock)
                begin
                    if (bit_counter == 0)
                    begin
                        next_state = PARITY_BIT;
                    end
                    else
                    begin
                        next_output_data = { output_data[8:0], output_data[9] };
                        next_bit_counter = bit_counter - 1;
                    end
                end
            end

            PARITY_BIT:
            begin
                // Even parity includes the sync bit.
                next_tx = first_half ? ~^{ 1'b1, output_data } : ^{ 1'b1, output_data };

                if (last_clock)
                begin
                    next_output_data_full = 0;

                    if (holding_data_full)
                    begin
                        next_output_data = holding_data;
                        next_output_data_full = 1;
                        next_holding_data_full = 0;

                        next_state = SYNC_BIT;
                    end
                    else
                    begin
                        next_state = END_SEQUENCE_1;
                    end
                end
            end

            END_SEQUENCE_1:
            begin
                next_tx = first_half ? 1 : 0;

                if (last_clock)
                    next_state = END_SEQUENCE_2;
            end

            END_SEQUENCE_2:
            begin
                next_tx = 1;

                if (last_clock)
                    next_state = END_SEQUENCE_3;
            end

            END_SEQUENCE_3:
            begin
                next_tx = 1;

                if (last_clock)
                begin
                    next_tx = 0;
                    next_state = IDLE;
                end
            end
        endcase
    end

    always @(*)
    begin
        next_active = (next_state != IDLE);
    end

    always @(posedge clk)
    begin
        state <= next_state;

        active <= next_active;
        tx <= next_tx;

        holding_data <= next_holding_data;
        holding_data_full <= next_holding_data_full;
        output_data <= next_output_data;
        output_data_full <= next_output_data_full;

        bit_counter <= next_bit_counter;

        bit_timer_reset <= next_bit_timer_reset;

        if (reset)
        begin
            state <= IDLE;

            active <= 0;
            tx <= 0;

            holding_data <= 10'b0000000000;
            holding_data_full <= 0;
            output_data <= 10'b0000000000;
            output_data_full <= 0;

            bit_counter <= 0;

            bit_timer_reset <= 0;
        end

        previous_load <= load;
    end

    assign full = holding_data_full; // TODO: also after bit 10 if holding is empty...
endmodule
