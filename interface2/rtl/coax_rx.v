`default_nettype none

module coax_rx (
    input clk,
    input rx,
    input reset,
    output active,
    output error,
    output reg [9:0] data,
    output reg data_available = 0,
    input read
);
    parameter CLOCKS_PER_BIT = 8;

    localparam LOSS_OF_MID_BIT_TRANSITION_ERROR = 10'b0000000001;
    localparam PARITY_ERROR = 10'b0000000010;
    localparam INVALID_END_SEQUENCE_ERROR = 10'b0000000100;
    localparam OVERFLOW_ERROR = 10'b0000001000;

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
    localparam ERROR = 15;

    reg [3:0] state = IDLE;
    reg [3:0] next_state;
    reg [3:0] previous_state;
    reg [7:0] state_counter;

    reg previous_rx;

    reg bit_timer_reset = 0;
    reg next_bit_timer_reset;

    reg [9:0] next_data;
    reg next_data_available;

    reg [9:0] internal_data;
    reg [9:0] next_internal_data;
    reg [3:0] bit_counter = 0;
    reg [3:0] next_bit_counter;

    reg previous_read;

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

        next_bit_timer_reset = 0;

        next_data = data;
        next_data_available = data_available;

        next_internal_data = internal_data;
        next_bit_counter = bit_counter;

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
                    begin
                        next_bit_counter = 0;
                        next_state = DATA_BIT;
                    end
                    else
                    begin
                        next_state = IDLE;
                    end
                end
                else if (state_counter >= CLOCKS_PER_BIT)
                begin
                    next_state = IDLE;
                end
           end

           SYNC_BIT:
           begin
               if (sample)
               begin
                   if (synchronized)
                   begin
                       if (rx)
                       begin
                           next_bit_counter = 0;
                           next_state = DATA_BIT;
                       end
                       else
                       begin
                           next_state = END_SEQUENCE_1;
                       end
                   end
                   else
                   begin
                       next_data = LOSS_OF_MID_BIT_TRANSITION_ERROR;
                       next_state = ERROR;
                   end
               end
           end

           DATA_BIT:
           begin
               if (sample)
               begin
                   if (synchronized)
                   begin
                       next_internal_data = { internal_data[8:0], rx };

                       if (bit_counter < 9)
                       begin
                           next_bit_counter = bit_counter + 1;
                       end
                       else
                       begin
                           next_state = PARITY_BIT;
                       end
                   end
                   else
                   begin
                       next_data = LOSS_OF_MID_BIT_TRANSITION_ERROR;
                       next_state = ERROR;
                   end
               end
           end

           PARITY_BIT:
           begin
               if (sample)
               begin
                   if (synchronized)
                   begin
                       // Even parity includes the sync bit.
                       if (rx == ^{ 1'b1, internal_data })
                       begin
                           if (!data_available)
                           begin
                               next_data_available = 1;
                               next_data = internal_data;
                               next_state = SYNC_BIT;
                           end
                           else
                           begin
                               next_data = OVERFLOW_ERROR;
                               next_state = ERROR;
                           end
                       end
                       else
                       begin
                           next_data = PARITY_ERROR;
                           next_state = ERROR;
                       end
                   end
                   else
                   begin
                       next_data = LOSS_OF_MID_BIT_TRANSITION_ERROR;
                       next_state = ERROR;
                   end
               end
           end

           END_SEQUENCE_1:
           begin
               if (rx)
               begin
                   next_state = END_SEQUENCE_2;
               end
               else if (state_counter >= CLOCKS_PER_BIT)
               begin
                   next_data = INVALID_END_SEQUENCE_ERROR;
                   next_state = ERROR;
               end
           end

           END_SEQUENCE_2:
           begin
               // TODO: Let's do more!
               next_state = IDLE;
           end
        endcase
    end

    always @(posedge clk)
    begin
        state <= next_state;
        state_counter <= (state == next_state) ? state_counter + 1 : 0;

        bit_timer_reset <= next_bit_timer_reset;

        data <= next_data;
        data_available <= next_data_available;

        internal_data <= next_internal_data;
        bit_counter <= next_bit_counter;

        if (reset)
        begin
            bit_timer_reset <= 1;

            state <= IDLE;
            state_counter <= 0;

            data <= 10'b0000000000;
            data_available <= 0;

            internal_data <= 10'b0000000000;
            bit_counter <= 0;
        end
        else if (data_available && !read && previous_read)
        begin
            data_available <= 0;
        end

        previous_rx <= rx;
        previous_state <= state;
        previous_read <= read;
    end

    assign active = (state >= SYNC_BIT && state <= PARITY_BIT);
    assign error = (state == ERROR);
endmodule
