`default_nettype none

module coax_tx_distorter (
    input clk,
    input active_input,
    input tx_input,
    output reg active_output,
    output reg tx_output,
    output reg tx_delay,
    output reg tx_inverted
);
    parameter CLOCKS_PER_BIT = 8;

    localparam DELAY_CLOCKS = CLOCKS_PER_BIT / 4;

    reg [DELAY_CLOCKS-1:0] tx_delay_buffer = { (DELAY_CLOCKS){1'b1} };

    always @(posedge clk)
    begin
        if (active_input)
        begin
            tx_delay_buffer <= { tx_delay_buffer[DELAY_CLOCKS-1:0], tx_input };

            active_output <= active_input;
            tx_output <= tx_input;
            tx_delay <= tx_delay_buffer[DELAY_CLOCKS-1];
            tx_inverted <= ~tx_input;
        end
        else
        begin
            tx_delay_buffer <= { (DELAY_CLOCKS){1'b1} };

            active_output <= 0;
            tx_output <= 0;
            tx_delay <= 0;
            tx_inverted <= 0;
        end
    end
endmodule
