`default_nettype none

`include "assert.v"

module regression_memorex_tb;
    reg clk = 0;

    initial
    begin
        forever
        begin
            #1 clk <= ~clk;
        end
    end

    reg rx = 0;
    reg reset = 0;

    coax_rx #(
        .CLOCKS_PER_BIT(8)
    ) dut (
        .clk(clk),
        .reset(reset),
        .rx(rx),
        .protocol(1'b0),
        .parity(1'b1)
    );

    initial
    begin
        $dumpfile("regression_memorex_tb.vcd");
        $dumpvars(0, regression_memorex_tb);

        test_1;

        $finish;
    end

    task test_1;
    begin
        $display("START: test_1");

        `assert_equal(dut.state, dut.STATE_IDLE, "state should be STATE_IDLE");

        rx = 0;
        #20;
        rx = 1;
        #5;
        rx = 0;
        #10;
        rx = 1;
        #10;
        rx = 0;
        #5;
        rx = 1;
        #10;
        rx = 0;
        #10;
        rx = 1;
        #10;
        rx = 0;
        #5;
        rx = 1;
        #10;
        rx = 0;
        #10;
        rx = 1;
        #5;
        rx = 0;
        #10;
        rx = 1;
        #10;
        rx = 0;
        #5;
        rx = 1;
        #10;
        rx = 0;
        #10;
        rx = 1;
        #10;
        rx = 0;
        #5;
        rx = 1;
        #10;
        rx = 0;
        #5;
        rx = 1;
        #10;
        rx = 0;
        #10;
        rx = 1;
        #10;
        rx = 0;
        #5;
        rx = 1;
        #10;
        rx = 0;
        #10;
        rx = 1;
        #10;
        rx = 0;
        #5;
        rx = 1;
        #10;
        rx = 0;
        #5;
        rx = 1;
        #10;
        rx = 0;
        #10;
        rx = 1;
        #10;
        rx = 0;
        #5;
        rx = 1;
        #10;
        rx = 0;
        #25;
        rx = 1;
        #25;
        rx = 0;
        #10;
        rx = 1;
        #15;
        rx = 0;
        #10;
        rx = 1;
        #10;
        rx = 0;
        #5;
        rx = 1;
        #10;
        rx = 0;
        #10;
        rx = 1;
        #5;
        rx = 0;
        #10;
        rx = 1;
        #10;
        rx = 0;
        #5;
        rx = 1;
        #10;
        rx = 0;
        #20;
        rx = 1;
        #15;
        rx = 0;
        #15;
        rx = 1;
        #20;
        rx = 0;
        #15;
        rx = 1;
        #20;
        rx = 0;
        #5;
        rx = 1;
        #35;
        rx = 0;

        #64;

        `assert_equal(dut.state, dut.STATE_IDLE, "state should be STATE_IDLE");

        `assert_equal(dut.data, 10'b0000001010, "data not correct")

        $display("END: test_1");
    end
    endtask
endmodule
