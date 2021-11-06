`default_nettype none

`include "assert.v"

module tx_rx_loopback_tb;
    reg clk = 0;

    initial
    begin
        forever
        begin
            #1 clk <= ~clk;
        end
    end

    reg reset = 0;
    wire loopback;
    wire tx_active;
    reg [9:0] tx_data;
    reg tx_strobe = 0;
    wire tx_ready;
    reg tx_protocol = 0;
    reg tx_parity = 0;
    wire rx_error;
    wire [9:0] rx_data;
    wire rx_strobe;
    reg rx_protocol = 0;
    reg rx_parity = 0;

    coax_tx #(
        .CLOCKS_PER_BIT(8)
    ) dut_tx (
        .clk(clk),
        .reset(reset),
        .active(tx_active),
        .tx(loopback),
        .data(tx_data),
        .strobe(tx_strobe),
        .ready(tx_ready),
        .protocol(tx_protocol),
        .parity(tx_parity)
    );

    coax_rx #(
        .CLOCKS_PER_BIT(8)
    ) dut_rx (
        .clk(clk),
        .reset(reset),
        .rx(loopback),
        .error(rx_error),
        .data(rx_data),
        .strobe(rx_strobe),
        .protocol(rx_protocol),
        .parity(rx_parity)
    );

    initial
    begin
        $dumpfile("tx_rx_loopback_tb.vcd");
        $dumpvars(0, tx_rx_loopback_tb);

        test_3270_protocol;
        test_3299_protocol;
        test_protocol_mismatch;
        test_parity_mismatch;

        $finish;
    end

    task test_3270_protocol;
    begin
        $display("START: test_3270_protocol");

        tx_protocol = 0;
        tx_parity = 1;
        rx_protocol = 0;
        rx_parity = 1;

        `assert_equal(dut_tx.state, dut_tx.IDLE, "state should be IDLE");
        `assert_equal(dut_rx.state, dut_rx.STATE_IDLE, "state should be IDLE");

        fork: test_3270_protocol_tx_rx_fork
            begin
                tx_data = 10'b0101110101;

                #2;
                tx_strobe = 1;
                #2;
                tx_strobe = 0;

                @(posedge tx_ready);

                tx_data = 10'b1010001010;

                #2;
                tx_strobe = 1;
                #2;
                tx_strobe = 0;
            end

            begin
                @(posedge rx_strobe);

                `assert_equal(rx_data, 10'b0101110101, "RX data should be equal to TX data");

                @(posedge rx_strobe);

                `assert_equal(rx_data, 10'b1010001010, "RX data should be equal to TX data");

                disable test_3270_protocol_tx_rx_fork;
            end

            begin
                #1000;
                $display("[TIMEOUT] %m (%s:%0d)", `__FILE__, `__LINE__);
                disable test_3270_protocol_tx_rx_fork;
            end
        join

        #100;

        `assert_equal(dut_tx.state, dut_tx.IDLE, "state should be IDLE");
        `assert_equal(dut_rx.state, dut_rx.STATE_IDLE, "state should be IDLE");

        $display("END: test_3270_protocol");
    end
    endtask

    task test_3299_protocol;
    begin
        $display("START: test_3299_protocol");

        tx_protocol = 1;
        tx_parity = 1;
        rx_protocol = 1;
        rx_parity = 1;

        `assert_equal(dut_tx.state, dut_tx.IDLE, "state should be IDLE");
        `assert_equal(dut_rx.state, dut_rx.STATE_IDLE, "state should be IDLE");

        fork: test_3299_protocol_tx_rx_fork
            begin
                tx_data = 10'b0000110001;

                #2;
                tx_strobe = 1;
                #2;
                tx_strobe = 0;

                @(posedge tx_ready);

                tx_data = 10'b0101110101;

                #2;
                tx_strobe = 1;
                #2;
                tx_strobe = 0;

                @(posedge tx_ready);

                tx_data = 10'b1010001010;

                #2;
                tx_strobe = 1;
                #2;
                tx_strobe = 0;
            end

            begin
                @(posedge rx_strobe);

                `assert_equal(rx_data, 10'b0000110001, "RX data should be equal to TX data");

                @(posedge rx_strobe);

                `assert_equal(rx_data, 10'b0101110101, "RX data should be equal to TX data");

                @(posedge rx_strobe);

                `assert_equal(rx_data, 10'b1010001010, "RX data should be equal to TX data");

                disable test_3299_protocol_tx_rx_fork;
            end

            begin
                #1000;
                $display("[TIMEOUT] %m (%s:%0d)", `__FILE__, `__LINE__);
                disable test_3299_protocol_tx_rx_fork;
            end
        join

        #100;

        `assert_equal(dut_tx.state, dut_tx.IDLE, "state should be IDLE");
        `assert_equal(dut_rx.state, dut_rx.STATE_IDLE, "state should be IDLE");

        $display("END: test_3299_protocol");
    end
    endtask

    task test_protocol_mismatch;
    begin
        $display("START: test_protocol_mismatch");

        tx_protocol = 1;
        tx_parity = 1;
        rx_protocol = 0;
        rx_parity = 1;

        `assert_equal(dut_tx.state, dut_tx.IDLE, "state should be IDLE");
        `assert_equal(dut_rx.state, dut_rx.STATE_IDLE, "state should be IDLE");

        fork: test_protocol_mismatch_tx_rx_fork
            begin
                tx_data = 10'b0000110001;

                #2;
                tx_strobe = 1;
                #2;
                tx_strobe = 0;

                @(posedge tx_ready);

                tx_data = 10'b0101110101;

                #2;
                tx_strobe = 1;
                #2;
                tx_strobe = 0;

                // Wait for TX to complete... we don't want to reset the RX
                // to soon as it could be reactivated with the remaining
                // transmission.
                @(negedge tx_active);

                disable test_protocol_mismatch_tx_rx_fork;
            end

            begin
                #1000;
                $display("[TIMEOUT] %m (%s:%0d)", `__FILE__, `__LINE__);
                disable test_protocol_mismatch_tx_rx_fork;
            end
        join

        // The exact error (parity or loss of mid-bit transition) may depend
        // on the length of message and data.
        `assert_high(rx_error, "RX error should be HIGH");
        `assert_equal(rx_data, dut_rx.ERROR_LOSS_OF_MID_BIT_TRANSITION, "RX data should be ERROR_LOSS_OF_MID_BIT_TRANSITION");

        #16;

        dut_reset;

        #100;

        `assert_equal(dut_tx.state, dut_tx.IDLE, "state should be IDLE");
        `assert_equal(dut_rx.state, dut_rx.STATE_IDLE, "state should be IDLE");

        $display("END: test_protocol_mismatch");
    end
    endtask

    task test_parity_mismatch;
    begin
        $display("START: test_parity_mismatch");

        tx_protocol = 0;
        tx_parity = 1;
        rx_protocol = 0;
        rx_parity = 0;

        `assert_equal(dut_tx.state, dut_tx.IDLE, "state should be IDLE");
        `assert_equal(dut_rx.state, dut_rx.STATE_IDLE, "state should be IDLE");

        fork: test_parity_mismatch_tx_rx_fork
            begin
                tx_data = 10'b0101110101;

                #2;
                tx_strobe = 1;
                #2;
                tx_strobe = 0;

                // Wait for TX to complete... we don't want to reset the RX
                // to soon as it could be reactivated with the remaining
                // transmission.
                @(negedge tx_active);

                disable test_parity_mismatch_tx_rx_fork;
            end

            begin
                #1000;
                $display("[TIMEOUT] %m (%s:%0d)", `__FILE__, `__LINE__);
                disable test_parity_mismatch_tx_rx_fork;
            end
        join

        `assert_high(rx_error, "RX error should be HIGH");
        `assert_equal(rx_data, dut_rx.ERROR_PARITY, "RX data should be ERROR_PARITY");

        #16;

        dut_reset;

        #100;

        `assert_equal(dut_tx.state, dut_tx.IDLE, "state should be IDLE");
        `assert_equal(dut_rx.state, dut_rx.STATE_IDLE, "state should be IDLE");

        $display("END: test_parity_mismatch");
    end
    endtask

    task dut_reset;
    begin
        reset = 1;
        #2;
        reset = 0;
    end
    endtask
endmodule
