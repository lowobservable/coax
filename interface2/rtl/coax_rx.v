`default_nettype none

module coax_rx (
    input clk,
    input rx,
    input reset
);
    parameter CLOCKS_PER_BIT = 8;

    localparam IDLE = 0;

    reg [1:0] state = IDLE;
    reg [1:0] next_state;

    wire sample;
    wire synchronized;

    coax_rx_bit_timer #(
        .CLOCKS_PER_BIT(CLOCKS_PER_BIT)
    ) bit_timer (
        .clk(clk),
        .rx(rx),
        .reset(reset),
        .sample(sample),
        .synchronized(synchronized)
    );

    always @(*)
    begin
        next_state = state;

        case (state)
            IDLE: next_state = synchronized && sample && rx ? 
        endcase
    end

    always @(posedge clk)
    begin
        state <= next_state;

        if (reset)
            state <= IDLE;
    end
endmodule
