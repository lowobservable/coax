`default_nettype none

module top (
    input clk_16mhz,

    output usb_pu
);
    // 19 MHz
    //
    // icepll -i 16 -o 18.869
    wire clk_19mhz;

    SB_PLL40_CORE #(
        .FEEDBACK_PATH("SIMPLE"),
        .DIVR(4'b0000),
        .DIVF(7'b0100101),
        .DIVQ(3'b101),
        .FILTER_RANGE(3'b001)
    ) clk_19mhz_pll (
        .RESETB(1'b1),
        .BYPASS(1'b0),
        .REFERENCECLK(clk_16mhz),
        .PLLOUTCORE(clk_19mhz)
    );

    assign usb_pu = 0;
endmodule
