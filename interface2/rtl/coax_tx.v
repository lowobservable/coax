`default_nettype none

module coax_tx (
    input clk,
    input xxx,
    output tx,
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

    reg [$clog2(CLOCKS_PER_BIT):0] bit_counter = 0;

    wire bit_strobe;
    wire bit_first_half;

    reg [3:0] state;
    reg [3:0] next_state;

    reg bit = 0;

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
                LINE_QUIESCE_6: next_state <= IDLE;
            endcase
        end
    end

    always @(posedge clk)
    begin
        if (xxx)
            state <= BIT_ALIGN;
        else 
            state <= next_state;
    end

    always @(posedge clk)
    begin
        if (bit_counter == CLOCKS_PER_BIT - 1)
            bit_counter <= 0;
        else
            bit_counter <= bit_counter + 1;
    end

    assign bit_strobe = (bit_counter == 7);
    assign bit_first_half = (bit_counter < CLOCKS_PER_BIT / 2);

    always @(*)
    begin
        tx <= 0;

        if (state >= LINE_QUIESCE_1 && state <= LINE_QUIESCE_6)
            tx <= bit_first_half ? 0 : 1;
    end

    assign active = (state != IDLE);
endmodule
