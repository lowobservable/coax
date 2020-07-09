`default_nettype none

module top (
    input clk_16mhz,

    input reset,

    // Transmitter
    output tx_active,
    output tx_delay,
    output tx_inverted,
    input tx_load,
    output tx_full,

    // Receiver
    input rx,
    input rx_enable,
    output rx_active,
    output rx_error,
    output rx_data_available,
    input rx_read,

    // Shared data bus
    inout [9:0] data,

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

    reg tx_load_0 = 0;
    reg tx_load_1 = 0;

    reg rx_0 = 0;
    reg rx_1 = 0;

    reg rx_read_0 = 0;
    reg rx_read_1 = 0;

    always @(posedge clk_38mhz)
    begin
        tx_load_0 <= tx_load;
        tx_load_1 <= tx_load_0;

        rx_0 <= rx;
        rx_1 <= rx_0;

        rx_read_0 <= rx_read;
        rx_read_1 <= rx_read_0;
    end

    wire tx_active_undistorted;
    wire tx_undistorted;
    wire [9:0] tx_data;

    assign tx_data = data;

    coax_tx #(
        .CLOCKS_PER_BIT(16)
    ) coax_tx (
        .clk(clk_38mhz),
        .reset(reset),
        .active(tx_active_undistorted),
        .tx(tx_undistorted),
        .data(tx_data),
        .load(tx_load_1),
        .full(tx_full)
    );

    wire tx;

    coax_tx_distorter #(
        .CLOCKS_PER_BIT(16)
    ) coax_tx_distorter (
        .clk(clk_38mhz),
        .active_input(tx_active_undistorted),
        .tx_input(tx_undistorted),
        .active_output(tx_active),
        .tx_output(tx),
        .tx_delay(tx_delay),
        .tx_inverted(tx_inverted)
    );

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

    assign data = rx_enable ? rx_data : 10'bzzzzzzzzzz;

    assign debug = rx_enable ? rx_1 : tx;

    assign usb_pu = 0;
endmodule
