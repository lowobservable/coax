`default_nettype none

module coax_tx_tb();
    reg clk = 0;

    initial
    begin
        clk <= 1'h0;

        forever
        begin
            #1 clk <= ~clk;
        end
    end

    wire tx;

    coax_tx dut (
        .clk(clk),
        .tx(tx)
    );

    initial
    begin
        $dumpfile("coax_tx_tb.vcd");
        $dumpvars(0, coax_tx_tb);

        repeat(100) @(posedge clk);

        $finish;
    end
endmodule
