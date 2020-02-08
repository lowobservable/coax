`default_nettype none

module coax_tx (
    input clk,
    output tx
);
    parameter CLOCKS_PER_BIT = 8;

    reg [$clog2(CLOCKS_PER_BIT):0] bit_counter = 0;

    reg bit = 1'b1;

    always @(posedge clk)
    begin
        if (bit_counter == CLOCKS_PER_BIT - 1)
            bit_counter <= 0;
        else
            bit_counter <= bit_counter + 1;
    end

    assign tx = bit_counter < (CLOCKS_PER_BIT / 2) ? ~bit : bit;
endmodule
