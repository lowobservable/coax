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

    reg rx_data_read = 0;
    wire rx_data_available;

    coax_rx #(
        .CLOCKS_PER_BIT(8)
    ) dut (
        .clk(clk),
        .rx(tx_tx),
        .data_read(rx_data_read),
        .data_available(rx_data_available)
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

        repeat(200) @(posedge clk);

        rx_data_read = 1;
        #4 rx_data_read = 0;

        repeat(100) @(posedge clk);

        rx_data_read = 1;
        #4 rx_data_read = 0;

        repeat(100) @(posedge clk);

        $finish;
    end
endmodule
