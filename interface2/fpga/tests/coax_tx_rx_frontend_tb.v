`default_nettype none

`include "assert.v"

module coax_tx_rx_frontend_tb;
    reg clk = 0;

    initial
    begin
        forever
        begin
            #1 clk <= ~clk;
        end
    end

    reg reset = 0;
    reg loopback = 0;
    reg tx_active_input = 0;
    reg tx_input = 0;
    reg rx_input = 0;

    coax_tx_rx_frontend #(
        .CLOCKS_PER_BIT(8)
    ) dut (
        .clk(clk),
        .reset(reset),
        .loopback(loopback),
        .tx_active_input(tx_active_input),
        .tx_input(tx_input),
        .rx_input(rx_input)
    );

    initial
    begin
        $dumpfile("coax_tx_rx_frontend_tb.vcd");
        $dumpvars(0, coax_tx_rx_frontend_tb);

        test_loopback;
        test_not_loopback;

        $finish;
    end

    task test_loopback;
    begin
        $display("START: test_loopback");

        loopback = 1;
        tx_active_input = 1;
        tx_input = 1;
        rx_input = 0;

        #16;

        tx_active_input = 0;
        tx_input = 0;

        #8;

        loopback = 0;

        #16;

        $display("END: test_loopback");
    end
    endtask

    task test_not_loopback;
    begin
        $display("START: test_not_loopback");

        loopback = 0;
        tx_active_input = 1;
        tx_input = 1;
        rx_input = 1;

        #16;

        tx_active_input = 0;
        tx_input = 0;
        rx_input = 0;

        #16;

        $display("END: test_not_loopback");
    end
    endtask
endmodule
