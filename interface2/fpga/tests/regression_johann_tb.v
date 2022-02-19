`default_nettype none

`include "assert.v"

module regression_johann_tb;
    reg clk = 0;

    initial
    begin
        forever
        begin
            #1 clk <= ~clk;
        end
    end

    reg probe_rx = 0;
    reg probe_error = 0;

    reg reset = 0;

    coax_rx #(
        .CLOCKS_PER_BIT(16)
    ) dut (
        .clk(clk),
        .reset(reset),
        .rx(probe_rx),
        .protocol(1'b0),
        .parity(1'b1)
    );

    initial
    begin
        $dumpfile("regression_johann_tb.vcd");
        $dumpvars(0, regression_johann_tb);

        test_1;

        $finish;
    end

    task test_1;
    begin
        $display("START: test_1");

        `assert_equal(dut.state, dut.STATE_IDLE, "state should be STATE_IDLE");

        // ... | vcd2v -s 2 -t nnnn probe_rx=top.internal_rx probe_error=top.rx_error
        //
        // vvv
#200;
probe_rx = 1;
probe_error = 0;
#18;
probe_rx = 0;
probe_error = 0;
#16;
probe_rx = 1;
probe_error = 0;
#16;
probe_rx = 0;
probe_error = 0;
#16;
probe_rx = 1;
probe_error = 0;
#16;
probe_rx = 0;
probe_error = 0;
#16;
probe_rx = 1;
probe_error = 0;
#16;
probe_rx = 0;
probe_error = 0;
#16;
probe_rx = 1;
probe_error = 0;
#16;
probe_rx = 0;
probe_error = 0;
#16;
probe_rx = 1;
probe_error = 0;
#16;
probe_rx = 0;
probe_error = 0;
#48;
probe_rx = 1;
probe_error = 0;
#48;
probe_rx = 0;
probe_error = 0;
#16;
probe_rx = 1;
probe_error = 0;
#32;
probe_rx = 0;
probe_error = 0;
#16;
probe_rx = 1;
probe_error = 0;
#16;
probe_rx = 0;
probe_error = 0;
#16;
probe_rx = 1;
probe_error = 0;
#16;
probe_rx = 0;
probe_error = 0;
#16;
probe_rx = 1;
probe_error = 0;
#16;
probe_rx = 0;
probe_error = 0;
#16;
probe_rx = 1;
probe_error = 0;
#16;
probe_rx = 0;
probe_error = 0;
#16;
probe_rx = 1;
probe_error = 0;
#16;
probe_rx = 0;
probe_error = 0;
#32;
probe_rx = 1;
probe_error = 0;
#32;
probe_rx = 0;
probe_error = 0;
#32;
probe_rx = 1;
probe_error = 0;
#32;
probe_rx = 0;
probe_error = 0;
#32;
probe_rx = 1;
probe_error = 0;
#4;
probe_rx = 1;
probe_error = 1;
#28;
probe_rx = 0;
probe_error = 1;
#16;
probe_rx = 1;
probe_error = 1;
#82;
probe_rx = 0;
probe_error = 1;
#258;
probe_rx = 0;
probe_error = 0;
        // ^^^

        #64;

        `assert_equal(dut.state, dut.STATE_IDLE, "state should be STATE_IDLE");

        `assert_equal(dut.data, 10'b0000001010, "data not correct")

        $display("END: test_1");
    end
    endtask
endmodule
