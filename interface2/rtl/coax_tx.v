`default_nettype none

module coax_tx (
    input clk,
    output tx
);
    reg state = 0;

    always @(posedge clk)
    begin
        state <= ~state;
    end

    assign tx = state;
endmodule
