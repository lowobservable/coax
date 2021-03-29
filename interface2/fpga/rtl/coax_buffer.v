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

module coax_buffer (
    input clk,
    input reset,
    input [9:0] write_data,
    input write_strobe,
    output [9:0] read_data,
    input read_strobe,
    output empty,
    output full,
    output reg almost_empty,
    output reg almost_full
);
    parameter DEPTH = 256;
    parameter ALMOST_EMPTY_THRESHOLD = 64;
    parameter ALMOST_FULL_THRESHOLD = 192;

    fifo_sync_ram #(
        .DEPTH(DEPTH),
        .WIDTH(10)
    ) fifo (
        .wr_data(write_data),
        .wr_ena(write_strobe),
        .wr_full(full),
        .rd_data(read_data),
        .rd_ena(read_strobe),
        .rd_empty(empty),
        .clk(clk),
        .rst(reset)
    );

    reg write_strobe_only;
    reg read_strobe_only;
    reg not_empty;
    reg not_full;

    always @(posedge clk)
    begin
        write_strobe_only <= (write_strobe && !read_strobe);
        read_strobe_only <= (read_strobe && !write_strobe);

        not_empty <= !empty;
        not_full <= !full;
    end

    reg increment_level;
    reg decrement_level;

    always @(posedge clk)
    begin
        increment_level <= (write_strobe_only && not_full);
        decrement_level <= (read_strobe_only && not_empty);

        if (reset)
        begin
            increment_level <= 0;
            decrement_level <= 0;
        end
    end

    reg [$clog2(DEPTH):0] level;

    always @(posedge clk)
    begin
        if (increment_level)
            level <= level + 1;
        else if (decrement_level)
            level <= level - 1;

        if (reset)
            level <= 0;
    end

    always @(posedge clk)
    begin
        almost_empty <= (level <= ALMOST_EMPTY_THRESHOLD);
        almost_full <= (level >= ALMOST_FULL_THRESHOLD);
    end
endmodule
