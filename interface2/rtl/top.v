`default_nettype none

module top (
    input clk,
    output tx,
    output tx_active,
    output usb_pu
);
    wire coax_clk;

    // 19 MHz
    //
    // icepll -i 16 -o 18.869
    SB_PLL40_CORE #(
        .FEEDBACK_PATH("SIMPLE"),
        .DIVR(4'b0000),        // DIVR =  0
        .DIVF(7'b0100101),     // DIVF = 37
        .DIVQ(3'b101),         // DIVQ =  5
        .FILTER_RANGE(3'b001)  // FILTER_RANGE = 1
    ) coax_clk_pll (
        .RESETB(1'b1),
        .BYPASS(1'b0),
        .REFERENCECLK(clk),
        .PLLOUTCORE(coax_clk)
    );

    coax_tx coax_tx (
        .clk(coax_clk),
        .xxx(do_it),
        .tx(tx),
        .active(tx_active)
    );

    wire do_it;

    assign do_it = (counter == 16'b1111_1111_1111_1111);

    reg [15:0] counter = 0;

    always @(posedge coax_clk)
    begin
        counter <= counter + 1;
    end

    assign usb_pu = 0;
endmodule
