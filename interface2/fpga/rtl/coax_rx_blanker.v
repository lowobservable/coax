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

module coax_rx_blanker (
    input clk,
    input reset,
    input enable,

    input rx_input,
    input tx_active,

    output reg rx_output
);
    parameter DELAY_CLOCKS = 2;

    reg rx_input_d0;

    always @(posedge clk)
    begin
        rx_input_d0 <= rx_input;
    end

    reg [DELAY_CLOCKS-1:0] blank;

    always @(posedge clk)
    begin
        if (reset)
            blank <= { (DELAY_CLOCKS){1'b0} };
        else if (tx_active)
            blank <= { (DELAY_CLOCKS){1'b1} };
        else
            blank <= { blank[DELAY_CLOCKS-2:0], 1'b0 };
    end

    always @(posedge clk)
    begin
        // TODO: should enable be delayed 1 clock to match input?
        if (!enable || !blank[DELAY_CLOCKS-1])
            rx_output <= rx_input_d0;
        else
            rx_output <= 1'b0;
    end
endmodule
