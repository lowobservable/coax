`default_nettype none

module top (
    input clk_16mhz,
    output tx_active,
    output tx,
    output tx_delay,
    output tx_inverted,
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

    wire load;
    reg [9:0] data = 10'b0000000101;

    coax_tx coax_tx (
        .clk(clk_19mhz),
        .load(load),
        .data(data),
        .active(tx_active),
        .tx(tx),
        .tx_delay(tx_delay),
        .tx_inverted(tx_inverted)
    );

    assign load = (counter == 16'b1111_1111_1111_1111);

    reg [15:0] counter = 0;

    always @(posedge clk_19mhz)
    begin
        counter <= counter + 1;
    end

    assign usb_pu = 0;
endmodule
