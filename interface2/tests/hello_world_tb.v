`default_nettype none

module hello_world_tb();
    reg clk = 0;

    initial
    begin
        forever
        begin
            #1 clk <= ~clk;
        end
    end

    wire tx;
    wire tx_active;

    hello_world dut (
        .clk(clk),
        .tx(tx),
        .tx_active(tx_active)
    );

    initial
    begin
        $dumpfile("hello_world_tb.vcd");
        $dumpvars(0, hello_world_tb);

        repeat(2000) @(posedge clk);

        $finish;
    end
endmodule
