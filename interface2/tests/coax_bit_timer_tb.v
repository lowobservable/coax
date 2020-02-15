`default_nettype none

module coax_bit_timer_tb();
    reg clk = 0;

    initial
    begin
        forever
        begin
            #1 clk <= ~clk;
        end
    end

    reg reset = 0;
    wire strobe;
    wire first_half;
    wire second_half;

    coax_bit_timer #(
        .CLOCKS_PER_BIT(8)
    ) dut (
        .clk(clk),
        .reset(reset),
        .strobe(strobe),
        .first_half(first_half),
        .second_half(second_half)
    );

    initial
    begin
        $dumpfile("coax_bit_timer_tb.vcd");
        $dumpvars(0, coax_bit_timer_tb);

        repeat(100) @(posedge clk);

        reset = 1;
        #2 reset = 0;

        repeat(100) @(posedge clk);

        $finish;
    end
endmodule
