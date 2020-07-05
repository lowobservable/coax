`default_nettype none

module top (
    input clk_16mhz,

    // Receiver
    input rx,
    output rx_active,
    output rx_error,
    output rx_data_available,
    input rx_read,

    // Shared data bus
    inout [9:0] data,

    input reset,
    output debug,

    output usb_pu
);
    // 38 MHz
    //
    // icepll -i 16 -o 37.738
    wire clk_38mhz;

    SB_PLL40_CORE #(
        .FEEDBACK_PATH("SIMPLE"),
        .DIVR(4'b0000),
        .DIVF(7'b0100101),
        .DIVQ(3'b100),
        .FILTER_RANGE(3'b001)
    ) clk_38mhz_pll (
        .RESETB(1'b1),
        .BYPASS(1'b0),
        .REFERENCECLK(clk_16mhz),
        .PLLOUTCORE(clk_38mhz)
    );

    reg rx_0 = 0;
    reg rx_1 = 0;

    reg rx_read_0 = 0;
    reg rx_read_1 = 0;

    always @(posedge clk_38mhz)
    begin
        rx_0 <= rx;
        rx_1 <= rx_0;

        rx_read_0 <= rx_read;
        rx_read_1 <= rx_read_0;
    end

    wire [9:0] rx_data;

    coax_rx #(
        .CLOCKS_PER_BIT(16)
    ) coax_rx (
        .clk(clk_38mhz),
        .rx(rx_1),
        .reset(reset),
        .active(rx_active),
        .error(rx_error),
        .data(rx_data),
        .data_available(rx_data_available),
        .read(rx_read_1)
    );

    assign data = rx_data;

    assign debug = rx_1;

    assign usb_pu = 0;
endmodule
