`default_nettype none

module coax_tx_bit_timer (
    input clk,
    input reset,
    output first_half,
    output second_half,
    output end_strobe
);
    parameter CLOCKS_PER_BIT = 8;

    reg [$clog2(CLOCKS_PER_BIT):0] counter = 0;

    always @(posedge clk or posedge reset)
    begin
        if (reset)
        begin
            counter <= 0;
        end
        else
        begin
            if (counter == CLOCKS_PER_BIT - 1)
                counter <= 0;
            else
                counter <= counter + 1;
        end
    end

    assign first_half = (counter < CLOCKS_PER_BIT / 2);
    assign second_half = ~first_half;

    assign end_strobe = (counter == CLOCKS_PER_BIT - 1);
endmodule
