`default_nettype none

module coax_rx (
    input clk,
    input rx,
    input reset,
    output active,
    output error,
    output reg [9:0] data
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
    localparam DATA = 11;
    localparam ERROR = 50;

    // TODO: size...
    reg [8:0] state = IDLE;
    reg [8:0] next_state;
    reg [8:0] previous_state;
    reg [8:0] state_counter;
    reg [8:0] next_state_counter;

    reg previous_rx;

    reg bit_timer_reset = 0;
    reg next_bit_timer_reset;

    reg [9:0] next_data;

    wire sample;
    wire synchronized;

    coax_rx_bit_timer #(
        .CLOCKS_PER_BIT(CLOCKS_PER_BIT)
    ) bit_timer (
        .clk(clk),
        .rx(rx),
        .reset(bit_timer_reset),
        .sample(sample),
        .synchronized(synchronized)
    );

    always @(*)
    begin
        next_state = state;
        next_state_counter = state_counter + 1;

        next_bit_timer_reset = 0;

        next_data = 10'b0000000000;

        case (state)
            IDLE:
            begin
                // TODO: should I move this to all the IDLE transitions?
                if (previous_state != IDLE)
                    next_bit_timer_reset = 1;

                if (rx != previous_rx)
                begin
                    if (rx && !previous_rx)
                        next_state = START_SEQUENCE_1;
                    else
                        next_bit_timer_reset = 1;
                end
            end

            START_SEQUENCE_1:
            begin
                if (sample)
                begin
                    if (synchronized && rx)
                        next_state = START_SEQUENCE_2;
                    else
                        next_state = IDLE;
                end
            end

            START_SEQUENCE_2:
            begin
                if (sample)
                begin
                    if (synchronized && rx)
                        next_state = START_SEQUENCE_3;
                    else
                        next_state = IDLE;
                end
            end

            START_SEQUENCE_3:
            begin
                if (sample)
                begin
                    if (synchronized && rx)
                        next_state = START_SEQUENCE_4;
                    else
                        next_state = IDLE;
                end
            end

            START_SEQUENCE_4:
            begin
                if (sample)
                begin
                    if (synchronized && rx)
                        next_state = START_SEQUENCE_5;
                    else
                        next_state = IDLE;
                end
            end

            START_SEQUENCE_5:
            begin
                if (sample)
                begin
                    if (synchronized && rx)
                        next_state = START_SEQUENCE_6;
                    else
                        next_state = IDLE;
                end
            end

            START_SEQUENCE_6:
            begin
                if (!rx)
                    next_state = START_SEQUENCE_7;
                else if (state_counter >= CLOCKS_PER_BIT)
                    next_state = IDLE;
            end

            START_SEQUENCE_7:
            begin
                if (rx)
                    next_state = START_SEQUENCE_8;
                else if (state_counter >= (CLOCKS_PER_BIT * 2))
                    next_state = IDLE;
            end

            START_SEQUENCE_8:
            begin
                if (!rx)
                begin
                    next_bit_timer_reset = 1;
                    next_state = START_SEQUENCE_9;
                end
                else if (state_counter >= (CLOCKS_PER_BIT * 2))
                begin
                    next_state = IDLE;
                end
            end

            START_SEQUENCE_9:
            begin
                // This is really the first SYNC_BIT but we treat it
                // differently and consider it part of the start
                // sequence.

                if (sample && synchronized)
                begin
                    if (rx)
                        next_state = DATA;
                    else
                        next_state = IDLE;
                end
                else if (state_counter >= CLOCKS_PER_BIT)
                begin
                    next_state = IDLE;
                end
           end

           SYNC_BIT:
           begin
               // TODO
           end

           DATA:
           begin
               if (sample)
               begin
                   if (synchronized)
                   begin
                       // TODO
                   end
                   else
                   begin
                       next_data = 10'b0000000001; // TODO: LOSS OF MID-BIT TRANSITION
                       next_state = ERROR;
                   end
               end
           end
        endcase
    end

    always @(posedge clk)
    begin
        if (state != next_state)
            state_counter <= 0;
        else
            state_counter <= next_state_counter;

        state <= next_state;

        bit_timer_reset <= next_bit_timer_reset;

        data <= next_data;

        if (reset)
        begin
            bit_timer_reset = 1;

            state_counter <= 0;
            state <= IDLE;

            data <= 10'b0000000000;
        end

        previous_rx <= rx;
        previous_state <= state;
    end

    assign active = (state >= SYNC_BIT && state <= DATA);
    assign error = (state == ERROR);
endmodule
