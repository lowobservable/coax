`default_nettype none

module top (
    input clk,
    output tx,
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
        .tx(tx)
    );

    assign usb_pu = 0;
endmodule
