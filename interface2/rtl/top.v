`default_nettype none

module top (
    input clk,
    output tx,
    output usb_pu
);
    coax_tx coax_tx (
        .clk(clk),
        .tx(tx)
    );

    assign usb_pu = 0;
endmodule
