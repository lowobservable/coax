`default_nettype none

module coax_tx (
    input clk,
    input load,
    input [9:0] data,
    output full,
    output active,
    output reg tx, // ??? why does thie have to be reg?
    output tx_delay,
    output tx_inverted
);
    parameter CLOCKS_PER_BIT = 8;

    localparam IDLE = 0;
    localparam LINE_QUIESCE_1 = 1;
    localparam LINE_QUIESCE_2 = 2;
    localparam LINE_QUIESCE_3 = 3;
    localparam LINE_QUIESCE_4 = 4;
    localparam LINE_QUIESCE_5 = 5;
    localparam LINE_QUIESCE_6 = 6;
    localparam CODE_VIOLATION_1 = 7;
    localparam CODE_VIOLATION_2 = 8;
    localparam CODE_VIOLATION_3 = 9;
    localparam SYNC_BIT = 10;
    localparam DATA = 11;
    localparam PARITY_BIT = 12;
    localparam END_1 = 13;
    localparam END_2 = 14;
    localparam END_3 = 15;

    reg [4:0] state = IDLE;
    reg [4:0] next_state;
    reg [4:0] previous_state = IDLE;

    reg previous_load = 0;
    reg [1:0] data_valid = 2'b00;
    reg [9:0] holding_data;
    reg [9:0] output_data;
    reg [3:0] output_data_counter;
    reg parity_bit;

    reg bit_counter_reset = 0;
    wire bit_strobe;
    wire bit_first_half;
    wire bit_second_half;

    coax_bit_timer #(
        .CLOCKS_PER_BIT(CLOCKS_PER_BIT)
    ) bit_timer (
        .clk(clk),
        .reset(bit_counter_reset),
        .strobe(bit_strobe),
        .first_half(bit_first_half),
        .second_half(bit_second_half)
    );

    localparam TX_DELAY_CLOCKS = CLOCKS_PER_BIT / 4;

    reg [TX_DELAY_CLOCKS-1:0] tx_delay_buffer;

    always @(*)
    begin
        next_state <= state;

        if (bit_strobe)
        begin
            case (state)
                LINE_QUIESCE_1: next_state <= LINE_QUIESCE_2;
                LINE_QUIESCE_2: next_state <= LINE_QUIESCE_3;
                LINE_QUIESCE_3: next_state <= LINE_QUIESCE_4;
                LINE_QUIESCE_4: next_state <= LINE_QUIESCE_5;
                LINE_QUIESCE_5: next_state <= LINE_QUIESCE_6;
                LINE_QUIESCE_6: next_state <= CODE_VIOLATION_1;
                CODE_VIOLATION_1: next_state <= CODE_VIOLATION_2;
                CODE_VIOLATION_2: next_state <= CODE_VIOLATION_3;
                CODE_VIOLATION_3: next_state <= SYNC_BIT;
                SYNC_BIT: next_state <= DATA;
                DATA: next_state <= output_data_counter == 9 ? PARITY_BIT : DATA;
                PARITY_BIT: next_state <= data_valid[1] ? SYNC_BIT : END_1;
                END_1: next_state <= END_2;
                END_2: next_state <= END_3;
                END_3: next_state <= IDLE;
            endcase
        end
    end

    always @(posedge clk)
    begin
        previous_state <= state;
        state <= next_state;

        bit_counter_reset <= 0;

        if (load && !previous_load)
        begin
            if (full)
            begin
                // TODO: error...
            end
            else if (data_valid[0])
            begin
                data_valid <= { 1'b1, data_valid[0] };
                holding_data <= data;
            end
            else
            begin
                data_valid <= { data_valid[1], 1'b1 };
                output_data <= data;
            end

            if (state == IDLE)
            begin
                bit_counter_reset <= 1;

                // Let's go!
                state <= LINE_QUIESCE_1;
            end
        end

        previous_load <= load;

        if (state == SYNC_BIT && state != previous_state)
        begin
            if (!data_valid[0])
            begin
                data_valid <= { 1'b0, data_valid[1] };
                output_data <= holding_data;
            end

            output_data_counter <= 0;

            parity_bit <= 1; // Even parity includes sync bit
        end
        else if (state == DATA && bit_strobe)
        begin
            output_data <= { output_data[8:0], 1'b0 };
            output_data_counter <= output_data_counter + 1;

            if (output_data[9])
                parity_bit <= ~parity_bit;
        end
        else if (state == PARITY_BIT && state != previous_state)
        begin
            data_valid <= { data_valid[1], 1'b0 };
        end
    end

    assign full = data_valid[1]; // TODO: full should be indicated to give setup time at bit 10

    assign active = ((state == LINE_QUIESCE_1 && bit_second_half) || state > LINE_QUIESCE_1);

    always @(*) // ??? is this best?
    begin
        tx <= 0;

        if (state >= LINE_QUIESCE_1 && state <= LINE_QUIESCE_6)
            tx <= bit_first_half ? 0 : 1;
        else if (state == CODE_VIOLATION_1)
            tx <= 0;
        else if (state == CODE_VIOLATION_2)
            tx <= bit_first_half ? 0 : 1;
        else if (state == CODE_VIOLATION_3)
            tx <= 1;
        else if (state == SYNC_BIT)
            tx <= bit_first_half ? 0 : 1;
        else if (state == DATA)
            tx <= bit_first_half ? ~output_data[9] : output_data[9];
        else if (state == PARITY_BIT)
            tx <= bit_first_half ? ~parity_bit : parity_bit;
        else if (state == END_1)
            tx <= bit_first_half ? 1 : 0;
        else if (state == END_2 || state == END_3)
            tx <= 1;
    end

    always @(posedge clk)
    begin
        // The delayed output is "stretched" to go high when active.
        if (!active)
            tx_delay_buffer <= { TX_DELAY_CLOCKS{1'b1} };
        else
            tx_delay_buffer <= { tx_delay_buffer[TX_DELAY_CLOCKS-2:0], tx };
    end

    assign tx_delay = active ? tx_delay_buffer[TX_DELAY_CLOCKS-1] : 0;
    assign tx_inverted = active ? ~tx : 0;
endmodule
