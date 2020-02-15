`default_nettype none

module coax_rx_bit_timer (
    input clk,
    input rx,
    input enable,
    output sample
);
    parameter CLOCKS_PER_BIT = 8;

    reg previous_rx;

    reg [$clog2(CLOCKS_PER_BIT/2):0] counter = 0;

    always @(posedge clk)
    begin
        if (enable)
        begin
            if (counter == 0)
            begin
                if (rx != previous_rx)
                    counter <= 1;
            end
            else
            begin
                counter <= counter + 1;
            end
        end
        else
        begin
            counter <= 0;
        end

        previous_rx <= rx;
    end

    assign sample = (enable && counter == CLOCKS_PER_BIT / 4);
endmodule
