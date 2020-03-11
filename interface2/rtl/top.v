`default_nettype none

module top (
    input clk_16mhz,

    // Transmitter
    input tx_load,
    output tx_full,
    output tx_active,
    output tx_delay,
    output tx_inverted,

    // Receiver
    input rx_enable,
    input rx,
    output rx_active,
    output rx_data_available,
    input rx_data_read,

    // Shared data bus
    inout [9:0] data,

    output debug,

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

    wire [9:0] tx_data;

    assign tx_data = data;

    coax_tx #(
        .CLOCKS_PER_BIT(8)
    ) coax_tx (
        .clk(clk_19mhz),
        .load(tx_load),
        .data(tx_data),
        .full(tx_full),
        .active(tx_active),
        .tx_delay(tx_delay),
        .tx_inverted(tx_inverted)
    );

    wire [9:0] rx_data;

    coax_rx #(
        .CLOCKS_PER_BIT(8)
    ) coax_rx (
        .clk(clk_19mhz),
        .rx(rx),
        .active(rx_active),
        .data(rx_data),
        .data_available(rx_data_available),
        .data_read(rx_data_read)
    );

    assign data = rx_enable ? rx_data : 10'bzzzzzzzzzz;

    assign debug = rx;

    assign usb_pu = 0;
endmodule
