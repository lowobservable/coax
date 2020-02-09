`default_nettype none

module coax_tx (
    input clk,
    input xxx,
    output reg tx, // ??? why does thie have to be reg?
    output active
);
    parameter CLOCKS_PER_BIT = 8;

    localparam IDLE = 0;
    localparam BIT_ALIGN = 1;
    localparam LINE_QUIESCE_1 = 2;
    localparam LINE_QUIESCE_2 = 3;
    localparam LINE_QUIESCE_3 = 4;
    localparam LINE_QUIESCE_4 = 5;
    localparam LINE_QUIESCE_5 = 6;
    localparam LINE_QUIESCE_6 = 7;
    localparam CODE_VIOLATION_1 = 8;
    localparam CODE_VIOLATION_2 = 9;
    localparam CODE_VIOLATION_3 = 10;
    localparam SYNC_BIT = 11;
    localparam DATA = 12;
    localparam PARITY_BIT = 13;

    reg [$clog2(CLOCKS_PER_BIT):0] bit_counter = 0;

    wire bit_strobe;
    wire bit_first_half;

    reg [3:0] state = IDLE;
    reg [3:0] next_state;

    reg [9:0] data;
    reg [3:0] data_counter;
    reg parity_bit;

    always @(*)
    begin
        next_state <= state;

        if (bit_strobe)
        begin
            case (state)
                BIT_ALIGN: next_state <= LINE_QUIESCE_1;
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
                PARITY_BIT: next_state <= IDLE;
            endcase
        end
    end

    always @(posedge clk)
    begin
        if (xxx)
        begin
            data <= 10'b0000000101;

            // TODO: Remove BIT_ALIGN state... reset the counter here!
            state <= BIT_ALIGN;
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
    end

    assign active = (state != IDLE);
endmodule
