// Copyright (c) 2020, Andrew Kay
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

module coax_tx_bit_timer (
    input clk,
    input reset,
    output first_half,
    output second_half,
    output last_clock
);
    parameter CLOCKS_PER_BIT = 8;

    reg [$clog2(CLOCKS_PER_BIT):0] counter = 0;
    reg [$clog2(CLOCKS_PER_BIT):0] next_counter;

    always @(*)
    begin
        next_counter = last_clock ? 0 : counter + 1;
    end

    always @(posedge clk)
    begin
        counter <= next_counter;

        if (reset)
            counter <= 0;
    end

    assign first_half = (counter < CLOCKS_PER_BIT / 2);
    assign second_half = ~first_half;

    assign last_clock = (counter == CLOCKS_PER_BIT - 1);
endmodule
