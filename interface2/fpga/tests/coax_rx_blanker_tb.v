`default_nettype none

`include "assert.v"

module coax_rx_blanker_tb;
    reg clk = 0;

    initial
    begin
        forever
        begin
            #1 clk <= ~clk;
        end
    end

    reg reset = 0;
    reg enable = 0;
    reg rx_input = 0;
    reg tx_active = 0;

    coax_rx_blanker #(
        .DELAY_CLOCKS(6)
    ) dut (
        .clk(clk),
        .reset(reset),
        .enable(enable),
        .rx_input(rx_input),
        .tx_active(tx_active)
    );

    initial
    begin
        $dumpfile("coax_rx_blanker_tb.vcd");
        $dumpvars(0, coax_rx_blanker_tb);

        test_not_enabled;
        test_enabled_tx_not_active;
        test_enabled_tx_active;

        $finish;
    end

    task test_not_enabled;
    begin
        $display("START: test_not_enabled");

        enable = 0;
        rx_input = 1;

        #4;

        `assert_high(dut.rx_output, "rx_output should be HIGH");

        rx_input = 0;

        #4;

        `assert_low(dut.rx_output, "rx_output should be LOW");

        #16;

        $display("END: test_not_enabled");
    end
    endtask

    task test_enabled_tx_not_active;
    begin
        $display("START: test_enabled_tx_not_active");

        enable = 1;
        rx_input = 1;
        tx_active = 0;

        #4;

        `assert_high(dut.rx_output, "rx_output should be HIGH");

        rx_input = 0;

        #4;

        `assert_low(dut.rx_output, "rx_output should be LOW");

        #16;

        $display("END: test_enabled_tx_not_active");
    end
    endtask

    task test_enabled_tx_active;
    begin
        $display("START: test_enabled_tx_active");

        enable = 1;
        rx_input = 1;
        tx_active = 1;

        #4;

        `assert_low(dut.rx_output, "rx_output should be LOW");

        tx_active = 0;

        #4;

        `assert_low(dut.rx_output, "rx_output should be LOW");

        #12;

        `assert_high(dut.rx_output, "rx_output should be HIGH");

        #16;

        $display("END: test_enabled_tx_active");
    end
    endtask
endmodule
