`default_nettype none

module coax_rx (
    input clk,
    input rx,
    input enable,
    input data_read,
    output active,
    output reg [9:0] data = 10'b0,
    output reg data_available = 0
);
    parameter CLOCKS_PER_BIT = 8;

    reg rx_0 = 0;
    reg rx_1 = 0;

    localparam IDLE = 0;
    localparam LINE_QUIESCE_1 = 1;
    localparam LINE_QUIESCE_2 = 2;
    localparam LINE_QUIESCE_3 = 3;
    localparam LINE_QUIESCE_4 = 4;
    localparam LINE_QUIESCE_5 = 5;
    localparam LINE_QUIESCE_6 = 6;
    localparam CODE_VIOLATION_1A = 7;
    localparam CODE_VIOLATION_1B = 8;
    localparam CODE_VIOLATION_2 = 9;
    localparam CODE_VIOLATION_3A = 10;
    localparam CODE_VIOLATION_3B = 11;
    localparam SYNC_BIT = 12;
    localparam DATA = 13;
    localparam PARITY_BIT = 14;
    localparam END_1 = 15;

    reg [4:0] state = IDLE;
    reg [4:0] next_state;
    reg [4:0] previous_state = IDLE;

    wire bit_timer_enable;
    wire bit_timer_sample;

    assign bit_timer_enable = (enable && state != CODE_VIOLATION_1A && state != CODE_VIOLATION_3B);

    coax_rx_bit_timer #(
        .CLOCKS_PER_BIT(CLOCKS_PER_BIT)
    ) bit_timer (
        .clk(clk),
        .rx(rx_1),
        .enable(bit_timer_enable),
        .sample(bit_timer_sample)
    );

    reg [9:0] input_data = 10'b0;
    reg [4:0] input_data_counter;
    reg parity_bit;

    always @(*)
    begin
        next_state <= state;

        if (state == IDLE)
        begin
            if (rx_1)
                next_state <= LINE_QUIESCE_1;
        end
        else if (state == CODE_VIOLATION_1A)
        begin
            if (~rx_1)
                next_state <= CODE_VIOLATION_1B;
        end
        else if (state == CODE_VIOLATION_1B)
        begin
            if (~rx_1)
                next_state <= CODE_VIOLATION_2;
        end
        else if (state == CODE_VIOLATION_3A)
        begin
            if (rx_1)
                next_state <= CODE_VIOLATION_3B;
        end
        else if (state == CODE_VIOLATION_3B)
        begin
            if (~rx_1)
                next_state <= SYNC_BIT;
        end
        else if (bit_timer_sample)
        begin
            case (state)
                LINE_QUIESCE_1: next_state <= rx_1 ? LINE_QUIESCE_2 : IDLE;
                LINE_QUIESCE_2: next_state <= rx_1 ? LINE_QUIESCE_3 : IDLE;
                LINE_QUIESCE_3: next_state <= rx_1 ? LINE_QUIESCE_4 : IDLE;
                LINE_QUIESCE_4: next_state <= rx_1 ? LINE_QUIESCE_5 : IDLE;
                LINE_QUIESCE_5: next_state <= rx_1 ? LINE_QUIESCE_6 : IDLE;
                LINE_QUIESCE_6: next_state <= rx_1 ? CODE_VIOLATION_1A : IDLE;
                CODE_VIOLATION_2: next_state <= rx_1 ? CODE_VIOLATION_3A: IDLE;
                SYNC_BIT: next_state <= rx_1 ? DATA : /* TODO: ERROR */ IDLE;
                DATA: next_state <= input_data_counter == 9 ? PARITY_BIT : DATA;
                PARITY_BIT: next_state <= rx_1 == parity_bit ? END_1 : /* TODO: ERROR... also check for overflow of data */ IDLE;
                END_1: next_state <= rx_1 ? DATA : IDLE; // TODO: END_2
            endcase
        end
    end

    always @(posedge clk)
    begin
        rx_0 <= rx;
        rx_1 <= rx_0;

        if (enable)
        begin
            if (data_read && data_available)
                data_available <= 0;

            if (state == DATA)
            begin
                if (state != previous_state)
                begin
                    input_data <= 10'b0;
                    input_data_counter <= 0;

                    parity_bit <= 1; // Even parity includes sync bit
                end
                else if (bit_timer_sample)
                begin
                    input_data <= { input_data[8:0], rx_1 };
                    input_data_counter <= input_data_counter + 1;

                    if (rx_1)
                        parity_bit <= ~parity_bit;
                end
            end
            else if (state == END_1 && state != previous_state)
            begin
                data <= input_data;
                data_available <= 1;
            end

            state <= next_state;
            previous_state <= state;
        end
        else
        begin
            state <= IDLE;
            previous_state <= IDLE;

            data <= 10'b0;
            data_available <= 0;
        end
    end

    assign active = (state >= SYNC_BIT && state <= END_1);
endmodule
