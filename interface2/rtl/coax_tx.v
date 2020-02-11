`default_nettype none

module coax_tx (
    input clk,
    input xxx,
    output reg tx, // ??? why does thie have to be reg?
    output active
);
    parameter CLOCKS_PER_BIT = 8;

    localparam IDLE = 0;
    localparam LINE_QUIESCE_1 = 1;
    localparam LINE_QUIESCE_2 = 2;
    localparam LINE_QUIESCE_3 = 3;
    localparam LINE_QUIESCE_4 = 4;
    localparam LINE_QUIESCE_5 = 5;
    localparam LINE_QUIESCE_6 = 6;
    localparam CODE_VIOLATION_1 = 7;
    localparam CODE_VIOLATION_2 = 8;
    localparam CODE_VIOLATION_3 = 9;
    localparam SYNC_BIT = 10;
    localparam DATA = 11;
    localparam PARITY_BIT = 12;
    localparam END_1 = 13;
    localparam END_2 = 14;
    localparam END_3 = 15;

    reg [$clog2(CLOCKS_PER_BIT):0] bit_counter = 0;

    wire bit_strobe;
    wire bit_first_half;

    reg [4:0] state = IDLE;
    reg [4:0] next_state;

    reg [9:0] data;
    reg [3:0] data_counter;
    reg parity_bit;

    always @(*)
    begin
        next_state <= state;

        if (bit_strobe)
        begin
            case (state)
                LINE_QUIESCE_1: next_state <= LINE_QUIESCE_2;
                LINE_QUIESCE_2: next_state <= LINE_QUIESCE_3;
                LINE_QUIESCE_3: next_state <= LINE_QUIESCE_4;
                LINE_QUIESCE_4: next_state <= LINE_QUIESCE_5;
                LINE_QUIESCE_5: next_state <= LINE_QUIESCE_6;
                LINE_QUIESCE_6: next_state <= CODE_VIOLATION_1;
                CODE_VIOLATION_1: next_state <= CODE_VIOLATION_2;
                CODE_VIOLATION_2: next_state <= CODE_VIOLATION_3;
                CODE_VIOLATION_3: next_state <= SYNC_BIT;
                SYNC_BIT: next_state <= DATA;
                DATA: next_state <= data_counter == 9 ? PARITY_BIT : DATA;
                PARITY_BIT: next_state <= END_1;
                END_1: next_state <= END_2;
                END_2: next_state <= END_3;
                END_3: next_state <= IDLE;
            endcase
        end
    end

    always @(posedge clk)
    begin
        if (xxx)
        begin
            data <= 10'b0000000101;
            bit_counter <= 0; // ??? is this ok to do this here with other block below?

            state <= LINE_QUIESCE_1;
        end
        else 
            state <= next_state;

        if (state == DATA)
        begin
            if (bit_strobe)
            begin
                data <= { data[8:0], 1'b0 };
                data_counter <= data_counter + 1;

                if (data[9])
                    parity_bit <= ~parity_bit;
            end
        end
        else
        begin
            data_counter <= 0;
            parity_bit <= 1; // Even parity includes sync bit
        end
    end

    always @(posedge clk)
    begin
        if (bit_counter == CLOCKS_PER_BIT - 1)
            bit_counter <= 0;
        else
            bit_counter <= bit_counter + 1;
    end

    assign bit_strobe = (bit_counter == CLOCKS_PER_BIT - 1);
    assign bit_first_half = (bit_counter < CLOCKS_PER_BIT / 2);

    always @(*) // ??? is this best?
    begin
        tx <= 0;

        if (state >= LINE_QUIESCE_1 && state <= LINE_QUIESCE_6)
            tx <= bit_first_half ? 0 : 1;
        else if (state == CODE_VIOLATION_1)
            tx <= 0;
        else if (state == CODE_VIOLATION_2)
            tx <= bit_first_half ? 0 : 1;
        else if (state == CODE_VIOLATION_3)
            tx <= 1;
        else if (state == SYNC_BIT)
            tx <= bit_first_half ? 0 : 1;
        else if (state == DATA)
            tx <= bit_first_half ? ~data[9] : data[9];
        else if (state == PARITY_BIT)
            tx <= bit_first_half ? ~parity_bit : parity_bit;
        else if (state == END_1)
            tx <= bit_first_half ? 1 : 0;
        else if (state == END_2 || state == END_3)
            tx <= 1;
    end

    assign active = ((state == LINE_QUIESCE_1 && !bit_first_half) || state > LINE_QUIESCE_1);
endmodule
