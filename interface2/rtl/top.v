`default_nettype none

module top (
    input clk_16mhz,

    // DP8341 receiver
    input dp8341_data_in,
    output dp8341_rx_active,
    input dp8341_register_read_n,
    output dp8341_data_available,
    input dp8341_output_enable,

    // Shared data bus
    inout [9:0] data,

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

    wire dp8341_rx_disable;

    assign dp8341_rx_disable = 0;

    dp8341_shim #(
        .CLOCKS_PER_BIT(8)
    ) dp8341 (
        .clk(clk_19mhz),
        .rx_disable(dp8341_rx_disable),
        .data_in(dp8341_data_in),
        .rx_active(dp8341_rx_active),
        .register_read_n(dp8341_register_read_n),
        .data_available(dp8341_data_available),
        .output_enable(dp8341_output_enable),
        .data_out(data)
    );

    assign usb_pu = 0;
endmodule
