// Copyright (c) 2021, Andrew Kay
//
// Permission to use, copy, modify, and/or distribute this software for any
// purpose with or without fee is hereby granted, provided that the above
// copyright notice and this permission notice appear in all copies.
//
// THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
// WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
// MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
// ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
// WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
// ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
// OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

`default_nettype none

module coax_tx_rx_frontend (
    input clk,
    input reset,

    input loopback,
    input tx_active_input,
    input tx_input,
    output rx_output,

    // The outside world...
    output tx_active_output,
    output tx_output,
    output tx_n_output,
    output tx_delay_output,
    input rx_input,

    output rx_debug
);
    parameter CLOCKS_PER_BIT = 8;

    coax_tx_distorter #(
        .CLOCKS_PER_BIT(CLOCKS_PER_BIT)
    ) coax_tx_distorter (
        .clk(clk),
        .active_input(!loopback && tx_active_input),
        .tx_input(tx_input),
        .active_output(tx_active_output),
        .tx_output(tx_output),
        .tx_delay_output(tx_delay_output),
        .tx_n_output(tx_n_output)
    );

    reg [1:0] rx_input_d;
    reg internal_rx;

    always @(posedge clk)
    begin
        rx_input_d <= { rx_input_d[0], rx_input };

        internal_rx <= loopback ? tx_input : rx_input_d[1];
    end

    coax_rx_blanker #(
        .DELAY_CLOCKS(2 + 4) // To account for the RX input 2FF synchronizer and more
    ) coax_rx_blanker (
        .clk(clk),
        .reset(reset),
        .enable(!loopback),
        .rx_input(internal_rx),
        .tx_active(tx_active_output),
        .rx_output(rx_output)
    );

    assign rx_debug = internal_rx;
endmodule
