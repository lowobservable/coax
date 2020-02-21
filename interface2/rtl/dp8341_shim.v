`default_nettype none

module dp8341_shim (
    input clk,
    input rx_disable,
    input data_in,
    output rx_active,
    // TODO: error
    input register_read_n,
    output data_available,
    // TODO: output_control
    input output_enable,
    inout [9:0] data_out
);
    parameter CLOCKS_PER_BIT = 8;

    wire rx;

    // TODO: Move receiver enable to coax_rx and correctly handle case where
    // receiver is disabled while active.
    assign rx = (~rx_disable | rx_active) & data_in;

    wire [9:0] data;

    assign data_out = (output_enable ? data : 10'bzzzzzzzzzz);

    reg register_read_n_0 = 1'b1;
    reg register_read_n_1 = 1'b1;
    reg previous_register_read_n = 1'b1;

    always @(posedge clk)
    begin
        register_read_n_0 <= register_read_n;
        register_read_n_1 <= register_read_n_0;

        previous_register_read_n <= register_read_n_1;
    end

    wire data_read;

    assign data_read = register_read_n_1 && ~previous_register_read_n;

    coax_rx #(
        .CLOCKS_PER_BIT(CLOCKS_PER_BIT)
    ) coax_rx (
        .clk(clk),
        .rx(rx),
        .data_read(data_read),
        .active(rx_active),
        .data(data),
        .data_available(data_available)
    );
endmodule
