`default_nettype none

module hello_world (
    input clk,
    output tx_active,
    output tx,
    output tx_delay,
    output tx_inverted
);
    wire load;
    reg [9:0] data;
    wire full;

    coax_tx coax_tx (
        .clk(clk),
        .load(load),
        .data(data),
        .full(full),
        .active(tx_active),
        .tx(tx),
        .tx_delay(tx_delay),
        .tx_inverted(tx_inverted)
    );

    localparam IDLE = 0;
    localparam WORD_1 = 1;
    localparam WORD_2 = 2;
    localparam WORD_3 = 3;
    localparam WORD_4 = 4;
    localparam WORD_5 = 5;
    localparam WORD_6 = 6;
    localparam WORD_7 = 7;
    localparam WORD_8 = 8;
    localparam WORD_9 = 9;
    localparam WORD_10 = 10;
    localparam WORD_11 = 11;
    localparam WORD_12 = 12;

    reg [4:0] state = IDLE;
    reg [4:0] next_state;
    reg [4:0] previous_state;

    always @(*)
    begin
        next_state <= state;

        case (state)
            WORD_1: next_state <= WORD_2;
            WORD_2: next_state <= WORD_3;
            WORD_3: next_state <= WORD_4;
            WORD_4: next_state <= WORD_5;
            WORD_5: next_state <= WORD_6;
            WORD_6: next_state <= WORD_7;
            WORD_7: next_state <= WORD_8;
            WORD_8: next_state <= WORD_9;
            WORD_9: next_state <= WORD_10;
            WORD_10: next_state <= WORD_11;
            WORD_11: next_state <= WORD_12;
            WORD_12: next_state <= IDLE;
        endcase
    end

    reg [23:0] counter = 0;
    reg [8:0] state_counter = 0;

    always @(posedge clk)
    begin
        previous_state <= state;

        if (counter == 50)
        begin
            state <= WORD_1;
            state_counter <= 0;
        end
        else if (state > IDLE)
        begin
            if (state_counter > 32 && !full)
            begin
                state <= next_state;
                state_counter <= 0;
            end
            else
                state_counter <= state_counter + 1;
        end

        counter <= counter + 1;
    end

    always @(*)
    begin
        data <= 10'b0000000000;

        case (state)
            WORD_1: data <= 10'b0000110001; // WRITE_DATA
            WORD_2: data <= 10'b1010011100; // H
            WORD_3: data <= 10'b1000010010; // e
            WORD_4: data <= 10'b1000101110; // l
            WORD_5: data <= 10'b1000101110; // l
            WORD_6: data <= 10'b1000111010; // o
            WORD_7: data <= 10'b0000000010; // <space>
            WORD_8: data <= 10'b1001011010; // w
            WORD_9: data <= 10'b1000111010; // o
            WORD_10: data <= 10'b1001000100; // r
            WORD_11: data <= 10'b1000101110; // l
            WORD_12: data <= 10'b1000001100; // d
        endcase
    end

    assign load = state != IDLE && state_counter < 8;
endmodule
