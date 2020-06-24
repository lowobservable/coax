`default_nettype none

module coax_rx_tb;
    reg clk = 0;

    initial begin
        forever begin
            #1 clk <= ~clk;
        end
    end

    reg rx = 0;
    reg reset = 0;

    coax_rx #(
        .CLOCKS_PER_BIT(8)
    ) dut (
        .clk(clk),
        .rx(rx),
        .reset(reset)
    );

    initial begin
        $dumpfile("coax_rx_tb.vcd");
        $dumpvars(0, coax_rx_tb);

        test_1;
        test_2;

        $finish;
    end

    task test_1;
    begin
        $display("START: test_1");

        dut_reset;

        #8;

        $display("END: test_1");
    end
    endtask

    task test_2;
    begin
        $display("START: test_2");

        rx = 1;

        #64;

        $display("END: test_2");
    end
    endtask

    task dut_reset;
    begin
        reset = 1;
        #2;
        reset = 0;
    end
    endtask

    task rx_bit (
        input bit
    );
    begin
        rx_bit_custom(bit, 8, 8);
    end
    endtask

    task rx_start_sequence;
    begin
        rx_bit(1);
        rx_bit(1);
        rx_bit(1);
        rx_bit(1);
        rx_bit(1);

        rx = 0;
        #24;
        rx = 1;
        #24;
    end
    endtask

    task rx_end_sequence;
    begin
        rx_bit(0);

        rx = 1;
        #32;
    end
    endtask

    task rx_bit_custom (
        input bit,
        input [15:0] first_half_duration,
        input [15:0] second_half_duration
    );
    begin
        rx = !bit;
        #first_half_duration;
        rx = bit;
        #second_half_duration;
        rx = 0;
    end
    endtask
endmodule
