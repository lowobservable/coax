`default_nettype none

module coax_rx_bit_timer_tb();
    reg clk = 0;

    initial begin
        forever begin
            #1 clk <= ~clk;
        end
    end

    reg rx = 0;
    reg reset = 0;
    wire sample;
    wire synchronized;

    coax_rx_bit_timer #(
        .CLOCKS_PER_BIT(8)
    ) dut (
        .clk(clk),
        .rx(rx),
        .reset(reset),
        .sample(sample),
        .synchronized(synchronized)
    );

    initial begin
        $dumpfile("coax_rx_bit_timer_tb.vcd");
        $dumpvars(0, coax_rx_bit_timer_tb);

        // Idle
        #32;

        // Perfect
        rx_bit(1);
        rx_bit(0);
        rx_bit(1);

        // Delayed
        rx_bit_custom(0, 9, 8);

        // Shortened
        rx_bit_custom(0, 6, 7);

        // Stuck
        rx_bit_custom(1, 24, 8);

        // Reset
        reset = 1;
        #2;
        reset = 0;

        rx_bit(1);

        #32;

        $finish;
    end

    task rx_bit (
        input bit
    );
    begin
        rx = !bit;
        #8;
        rx = bit;
        #8;
        rx = 0;
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
