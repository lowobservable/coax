`default_nettype none

module coax_rx_tb();
    reg clk = 0;

    initial
    begin
        forever
        begin
            #1 clk <= ~clk;
        end
    end

    reg tx_load = 0;
    reg [9:0] tx_data;
    wire tx_tx;

    coax_tx #(
        .CLOCKS_PER_BIT(8)
    ) tx (
        .clk(clk),
        .load(tx_load),
        .data(tx_data),
        .tx(tx_tx)
    );

    coax_rx #(
        .CLOCKS_PER_BIT(8)
    ) dut (
        .clk(clk),
        .rx(tx_tx)
    );

    initial
    begin
        $dumpfile("coax_rx_tb.vcd");
        $dumpvars(0, coax_rx_tb);

        #8

        tx_data = 10'b0000000101;
        tx_load = 1;
        #2 tx_load = 0;

        #32

        tx_data = 10'b1111111111;
        tx_load = 1;
        #2 tx_load = 0;

        repeat(1000) @(posedge clk);

        $finish;
    end
endmodule
