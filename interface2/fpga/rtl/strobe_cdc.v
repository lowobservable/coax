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

module strobe_cdc (
    input clk_in,
    input strobe_in,
    input clk_out,
    output reg strobe_out
);
    reg toggle_in;

    always @(posedge clk_in)
    begin
        if (strobe_in)
            toggle_in <= ~toggle_in;
    end

    reg [2:0] toggle_out;

    always @(posedge clk_out)
    begin
        toggle_out <= { toggle_out[1:0], toggle_in };

        strobe_out <= 0;

        if (toggle_out[2] != toggle_out[1])
            strobe_out <= 1;
    end
endmodule
