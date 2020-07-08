`default_nettype none

module coax_tx_bit_timer_tb;
    reg clk = 0;

    initial
    begin
        forever
        begin
            #1 clk <= ~clk;
        end
    end

    reg reset = 0;
    wire first_half;
    wire second_half;
    wire last_clock;

    coax_tx_bit_timer #(
        .CLOCKS_PER_BIT(8)
    ) dut (
        .clk(clk),
        .reset(reset),
        .first_half(first_half),
        .second_half(second_half),
        .last_clock(last_clock)
    );

    initial
    begin
        $dumpfile("coax_tx_bit_timer_tb.vcd");
        $dumpvars(0, coax_tx_bit_timer_tb);

        #64;

        $finish;
    end
endmodule
