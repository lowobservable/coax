`default_nettype none

module dp8340_shim (
    input clk,
    input [9:0] data_in,
    input reg_load_n,
    output reg_full,
    input auto_response_n,
    output tx_active,
    input parity_control,
    // TODO: even_odd_parity not supported by coax_tx
    output data_out_n,
    output data_out,
    output data_delay
);
    parameter CLOCKS_PER_BIT = 8;

    wire [9:0] data;

    always @(*)
    begin
        data <= data_in;

        if (~auto_response_n)
            data <= 10'b0;
        else if (~parity_control)
            data <= { data_in[9:2], ^data_in[9:2], data_in[0] };
    end

    coax_tx #(
        .CLOCKS_PER_BIT(CLOCKS_PER_BIT)
    ) coax_tx (
        .clk(clk),
        .load(~reg_load_n),
        .data(data),
        .full(reg_full),
        .active(tx_active),
        .tx(data_out),
        .tx_delay(data_delay),
        .tx_inverted(data_out_n)
    );
endmodule
