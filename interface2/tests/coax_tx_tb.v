`default_nettype none

module coax_tx_tb();
    reg clk = 0;

    initial
    begin
        forever
        begin
            #1 clk <= ~clk;
        end
    end

    wire tx;
    wire active;
    reg xxx = 0;

    coax_tx #(
        .CLOCKS_PER_BIT(8)
    ) dut (
        .clk(clk),
        .xxx(xxx),
        .tx(tx),
        .active(active)
    );

    initial
    begin
        $dumpfile("coax_tx_tb.vcd");
        $dumpvars(0, coax_tx_tb);

        repeat(10) @(posedge clk);

        xxx = 1;
        #8 xxx = 0;

        repeat(1000) @(posedge clk);

        $finish;
    end
endmodule
