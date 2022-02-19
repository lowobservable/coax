`default_nettype none

module snoopie (
    input clk,
    input enable,

    input [3:0] probes,

    output [7:0] xxx_write_address,
    output [15:0] read_data,
    input read_strobe
);
reg previous_enable = 0;
    reg [11:0] counter;

    reg [3:0] previous_probes;

    reg [7:0] write_address;
    reg [15:0] write_data;
    reg write_enable;

    reg [7:0] read_address;

    ram_sdp #(
        .AWIDTH(8),
        .DWIDTH(16)
    ) ram (
        .clk(clk),

        .wr_addr(write_address),
        .wr_data(write_data),
        .wr_ena(write_enable),

        .rd_addr(read_address),
        .rd_data(read_data),
        .rd_ena(1'b1)
    );

    always @(posedge clk)
    begin
        counter <= counter + 1;

        // Writer...
        if (enable && !previous_enable)
            write_address <= 0;
        else if (write_enable)
            write_address <= write_address + 1;

        write_enable <= 0;

        if (enable && probes != previous_probes)
        begin
            write_data <= { counter[11:0], probes[3:0] };
            write_enable <= 1;
        end

        // Reader...
        if (enable && !previous_enable)
            read_address <= 0;
        else if (read_strobe)
            read_address <= read_address + 1;

        previous_probes <= probes;
        previous_enable <= enable;
    end

    assign xxx_write_address = write_address;
endmodule
