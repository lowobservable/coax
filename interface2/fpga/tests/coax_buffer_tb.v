`default_nettype none

`include "assert.v"

module coax_buffer_tb;
    reg clk = 0;

    initial
    begin
        forever
        begin
            #1 clk <= ~clk;
        end
    end

    reg reset = 0;
    reg [9:0] write_data = 0;
    reg write_strobe = 0;
    reg read_strobe = 0;

    coax_buffer #(
        .DEPTH(16),
        .ALMOST_EMPTY_THRESHOLD(4),
        .ALMOST_FULL_THRESHOLD(12)
    ) dut (
        .clk(clk),
        .reset(reset),
        .write_data(write_data),
        .write_strobe(write_strobe),
        .read_strobe(read_strobe)
    );

    initial
    begin
        $dumpfile("coax_buffer_tb.vcd");
        $dumpvars(0, coax_buffer_tb);

        test_1;

        $finish;
    end

    task test_1;
    begin
        $display("START: test_1");

        write_data = 0;
        write_strobe = 0;
        read_strobe = 0;

        dut_reset;

        #16;

        repeat (16)
        begin
            write_strobe = 1;
            #2;
            write_strobe = 0;

            #2;

            write_data = write_data + 1;
        end

        #16;

        repeat (16)
        begin
            read_strobe = 1;
            #2;
            read_strobe = 0;

            #2;
        end

        #64;

        $display("END: test_1");
    end
    endtask

    task dut_reset;
    begin
        reset = 1;
        #2;
        reset = 0;
    end
    endtask
endmodule
