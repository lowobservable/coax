`default_nettype none

module coax_tx_distorter_tb;
    reg clk = 0;

    initial
    begin
        forever
        begin
            #1 clk <= ~clk;
        end
    end

    reg active_input = 0;
    reg tx_input = 0;

    coax_tx_distorter #(
        .CLOCKS_PER_BIT(8)
    ) dut (
        .clk(clk),
        .active_input(active_input),
        .tx_input(tx_input)
    );

    initial
    begin
        $dumpfile("coax_tx_distorter_tb.vcd");
        $dumpvars(0, coax_tx_distorter_tb);

        #16;

        active_input = 1;

        tx_input = 1;
        #8;

        tx_input = 0;
        #8;
        tx_input = 1;
        #8;

        tx_input = 0;
        #8;
        tx_input = 1;
        #8;
        tx_input = 0;

        active_input = 0;

        #32;

        $finish;
    end
endmodule
