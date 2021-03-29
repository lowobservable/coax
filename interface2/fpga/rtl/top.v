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

module top (
    input clk,

    input reset_n,

    // SPI
    input spi_sck,
    input spi_cs_n,
    input spi_sdi,
    output spi_sdo,

    // TX
    output tx_active,
    output tx_n,
    output tx_delay,

    // RX
    input rx,

    output irq,

    output gpio0,
    output gpio1,
    output gpio2,
    output gpio3
);
    reg [1:0] reset_n_d;
    reg [1:0] rx_d;

    always @(posedge clk)
    begin
        reset_n_d <= { reset_n_d[0], reset_n };
        rx_d <= { rx_d[0], rx };
    end

    reg reset;

    always @(posedge clk)
    begin
        reset <= !reset_n_d[1];
    end

    wire clk_fast;

    SB_PLL40_CORE #(
        .FEEDBACK_PATH("SIMPLE"),
        .DIVR(4'b0000),
        .DIVF(7'b0010000),
        .DIVQ(3'b011),
        .FILTER_RANGE(3'b011)
    ) clk_fast_pll (
        .RESETB(1'b1),
        .BYPASS(1'b0),
        .REFERENCECLK(clk),
        .PLLOUTCORE(clk_fast)
    );

    wire [7:0] spi_rx_data;
    wire spi_rx_strobe;
    wire [7:0] spi_tx_data;
    wire spi_tx_strobe;

    dual_clock_spi_device spi (
        .clk_slow(clk),
        .clk_fast(clk_fast),
        .spi_sck(spi_sck),
        .spi_cs_n(spi_cs_n),
        .spi_sdi(spi_sdi),
        .spi_sdo(spi_sdo),
        .rx_data(spi_rx_data),
        .rx_strobe(spi_rx_strobe),
        .tx_data(spi_tx_data),
        .tx_strobe(spi_tx_strobe)
    );

    wire loopback;

    wire tx_reset;
    wire internal_tx_active;
    wire internal_tx;
    wire [9:0] tx_data;
    wire tx_load_strobe;
    wire tx_start_strobe;
    wire tx_empty;
    wire tx_full;
    wire tx_ready;
    wire tx_parity;

    coax_buffered_tx #(
        .CLOCKS_PER_BIT(16),
        .DEPTH(2048),
        .START_DEPTH(1536)
    ) coax_buffered_tx (
        .clk(clk),
        .reset(reset || tx_reset),
        .active(internal_tx_active),
        .tx(internal_tx),
        .data(tx_data),
        .load_strobe(tx_load_strobe),
        .start_strobe(tx_start_strobe),
        .empty(tx_empty),
        .full(tx_full),
        .ready(tx_ready),
        .parity(tx_parity)
    );

    reg internal_rx;

    always @(posedge clk)
    begin
        internal_rx <= loopback ? internal_tx : (!internal_tx_active ? rx_d[1] : 0);
    end

    wire rx_reset;
    wire rx_active;
    wire rx_error;
    wire [9:0] rx_data;
    wire rx_read_strobe;
    wire rx_empty;
    wire rx_parity;

    coax_buffered_rx #(
        .CLOCKS_PER_BIT(16),
        .DEPTH(2048)
    ) coax_buffered_rx (
        .clk(clk),
        .reset(reset || rx_reset),
        .rx(internal_rx),
        .active(rx_active),
        .error(rx_error),
        .data(rx_data),
        .read_strobe(rx_read_strobe),
        .empty(rx_empty),
        .parity(rx_parity)
    );

    control control (
        .clk(clk),
        .reset(reset),

        .spi_cs_n(spi_cs_n),
        .spi_rx_data(spi_rx_data),
        .spi_rx_strobe(spi_rx_strobe),
        .spi_tx_data(spi_tx_data),
        .spi_tx_strobe(spi_tx_strobe),

        .loopback(loopback),

        .tx_reset(tx_reset),
        .tx_active(internal_tx_active),
        .tx_data(tx_data),
        .tx_load_strobe(tx_load_strobe),
        .tx_start_strobe(tx_start_strobe),
        .tx_empty(tx_empty),
        .tx_full(tx_full),
        .tx_ready(tx_ready),
        .tx_parity(tx_parity),

        .rx_reset(rx_reset),
        .rx_active(rx_active),
        .rx_error(rx_error),
        .rx_data(rx_data),
        .rx_read_strobe(rx_read_strobe),
        .rx_empty(rx_empty),
        .rx_parity(rx_parity)
    );

    coax_tx_distorter #(
        .CLOCKS_PER_BIT(16)
    ) coax_tx_distorter (
        .clk(clk),
        .active_input(!loopback && internal_tx_active),
        .tx_input(internal_tx),
        .active_output(tx_active),
        .tx_delay(tx_delay),
        .tx_n(tx_n)
    );

    assign irq = rx_active || rx_error;

    assign gpio0 = rx_d[1];
    assign gpio1 = tx_active;
    assign gpio2 = rx_active;
    assign gpio3 = 0;
endmodule
