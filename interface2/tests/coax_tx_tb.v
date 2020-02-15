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

    reg load = 0;
    reg [9:0] data;
    wire tx;
    wire active;

    coax_tx #(
        .CLOCKS_PER_BIT(8)
    ) dut (
        .clk(clk),
        .load(load),
        .data(data),
        .tx(tx),
        .active(active)
    );

    initial
    begin
        $dumpfile("coax_tx_tb.vcd");
        $dumpvars(0, coax_tx_tb);

        #8

        data = 10'b0000000101;
        load = 1;
        #2 load = 0;

        #32

        data = 10'b1111111111;
        load = 1;
        #2 load = 0;

        repeat(1000) @(posedge clk);

        $finish;
    end
endmodule
