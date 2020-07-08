`default_nettype none

module coax_tx_bit_timer (
    input clk,
    input reset,
    output first_half,
    output second_half,
    output last_clock
);
    parameter CLOCKS_PER_BIT = 8;

    reg [$clog2(CLOCKS_PER_BIT):0] counter = 0;
    reg [$clog2(CLOCKS_PER_BIT):0] next_counter;

    always @(*)
    begin
        next_counter = last_clock ? 0 : counter + 1;
    end

    always @(posedge clk)
    begin
        counter <= next_counter;

        if (reset)
            counter <= 0;
    end

    assign first_half = (counter < CLOCKS_PER_BIT / 2);
    assign second_half = ~first_half;

    assign last_clock = (counter == CLOCKS_PER_BIT - 1);
endmodule
