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

module spi_device (
    input clk,
    input spi_sck,
    input spi_cs_n,
    input spi_sdi,
    output spi_sdo,
    output reg [7:0] rx_data,
    output reg rx_strobe,
    input [7:0] tx_data,
    input tx_strobe
);
    reg [1:0] cs_n_d;
    reg [2:0] sck_d;
    reg [2:0] sdi_d;

    always @(posedge clk)
    begin
        cs_n_d <= { cs_n_d[0], spi_cs_n };

        sck_d <= { sck_d[1:0], spi_sck };
        sdi_d <= { sdi_d[1:0], spi_sdi };
    end

    reg [3:0] counter;
    reg [7:0] input_data;
    reg [7:0] output_data;

    always @(posedge clk)
    begin
        rx_strobe <= 0;

        if (tx_strobe)
            output_data <= tx_data;

        if (cs_n_d[1])
        begin
            counter <= 0;
        end
        else
        begin
            if (!sck_d[2] && sck_d[1])
            begin
                input_data <= { input_data[6:0], sdi_d[2] };
                counter <= counter + 1;
            end

            if (sck_d[2] && !sck_d[1])
            begin
                output_data <= { output_data[6:0], 1'b0 };

                if (counter == 8)
                begin
                    rx_data <= input_data;
                    rx_strobe <= 1;

                    counter <= 0;
                end
            end
        end
    end

    assign spi_sdo = output_data[7];
endmodule
