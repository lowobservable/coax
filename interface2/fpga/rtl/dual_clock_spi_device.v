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

module dual_clock_spi_device (
    input clk_slow,
    input clk_fast,
    input spi_sck,
    input spi_cs_n,
    input spi_sdi,
    output spi_sdo,
    output reg [7:0] rx_data,
    output reg rx_strobe,
    input [7:0] tx_data,
    input tx_strobe
);
    wire [7:0] rx_data_fast;
    wire rx_strobe_fast;
    reg [7:0] tx_data_fast;
    wire tx_strobe_fast;

    spi_device spi (
        .clk(clk_fast),
        .spi_sck(spi_sck),
        .spi_cs_n(spi_cs_n),
        .spi_sdi(spi_sdi),
        .spi_sdo(spi_sdo),
        .rx_data(rx_data_fast),
        .rx_strobe(rx_strobe_fast),
        .tx_data(tx_data_fast),
        .tx_strobe(tx_strobe_fast)
    );

    wire rx_strobe_slow;

    strobe_cdc rx_strobe_cdc (
        .clk_in(clk_fast),
        .strobe_in(rx_strobe_fast),
        .clk_out(clk_slow),
        .strobe_out(rx_strobe_slow)
    );

    strobe_cdc tx_strobe_cdc (
        .clk_in(clk_slow),
        .strobe_in(tx_strobe),
        .clk_out(clk_fast),
        .strobe_out(tx_strobe_fast)
    );

    always @(posedge clk_slow)
    begin
        if (tx_strobe)
            tx_data_fast <= tx_data;

        rx_strobe <= 0;

        if (rx_strobe_slow)
        begin
            rx_data <= rx_data_fast;
            rx_strobe <= 1;
        end
    end
endmodule
