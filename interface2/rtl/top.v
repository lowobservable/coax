`default_nettype none

module top (
    input clk_16mhz,
    output tx_active,
    output tx,
    output tx_delay,
    output tx_inverted,
    input rx,
    output rx_active,
    output xxx_debug_1,
    output xxx_debug_2,
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

    coax_rx coax_rx (
        .clk(clk_19mhz),
        .rx(rx),
        .active(rx_active)
    );

    assign usb_pu = 0;
endmodule
