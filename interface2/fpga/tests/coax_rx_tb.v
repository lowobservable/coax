`default_nettype none

`include "assert.v"
`include "mock_tx.v"

module coax_rx_tb;
    reg clk = 0;

    initial
    begin
        forever
        begin
            #1 clk <= ~clk;
        end
    end

    wire rx;

    mock_tx mock_tx (
        .tx(rx)
    );

    reg reset = 0;

    coax_rx #(
        .CLOCKS_PER_BIT(8)
    ) dut (
        .clk(clk),
        .reset(reset),
        .rx(rx),
        .parity(1'b1)
    );

    initial
    begin
        $dumpfile("coax_rx_tb.vcd");
        $dumpvars(0, coax_rx_tb);

        test_reset;
        test_invalid_start_sequence_1_pulse;
        test_invalid_start_sequence_2_pulse;
        test_invalid_start_sequence_3_pulse;
        test_invalid_start_sequence_4_pulse;
        test_invalid_start_sequence_code_violation_first_half;
        test_invalid_start_sequence_code_violation_second_half;
        test_invalid_sync_bit;
        test_loss_of_mid_bit_transition_error_data_bit_1;
        test_loss_of_mid_bit_transition_error_data_bit_5;
        test_loss_of_mid_bit_transition_error_parity_bit;
        test_parity_error;
        test_loss_of_mid_bit_transition_error_sync_end_bit;
        test_invalid_end_sequence;
        test_data;

        $finish;
    end

    task test_reset;
    begin
        $display("START: test_reset");

        `assert_equal(dut.state, dut.STATE_IDLE, "state should be STATE_IDLE");

        dut_reset;

        #8;

        `assert_equal(dut.state, dut.STATE_IDLE, "state should be STATE_IDLE");

        $display("END: test_reset");
    end
    endtask

    task test_invalid_start_sequence_1_pulse;
    begin
        $display("START: test_invalid_start_sequence_1_pulse");

        `assert_equal(dut.state, dut.STATE_IDLE, "state should be STATE_IDLE");

        mock_tx.tx_set(1);

        #64;

        `assert_equal(dut.state, dut.STATE_IDLE, "state should be STATE_IDLE");
        `assert_equal(dut.ss_detector.state, dut.ss_detector.STATE_IDLE, "ss_detector.state should be STATE_IDLE");

        $display("END: test_invalid_start_sequence_1_pulse");
    end
    endtask

    task test_invalid_start_sequence_2_pulse;
    begin
        $display("START: test_invalid_start_sequence_2_pulse");

        `assert_equal(dut.state, dut.STATE_IDLE, "state should be STATE_IDLE");

        mock_tx.tx_set(1);
        #16;
        mock_tx.tx_set(0);

        mock_tx.tx_bit(1);

        #64;

        `assert_equal(dut.state, dut.STATE_IDLE, "state should be STATE_IDLE");
        `assert_equal(dut.ss_detector.state, dut.ss_detector.STATE_IDLE, "ss_detector.state should be STATE_IDLE");

        $display("END: test_invalid_start_sequence_2_pulse");
    end
    endtask

    task test_invalid_start_sequence_3_pulse;
    begin
        $display("START: test_invalid_start_sequence_3_pulse");

        `assert_equal(dut.state, dut.STATE_IDLE, "state should be STATE_IDLE");

        mock_tx.tx_set(1);
        #16;
        mock_tx.tx_set(0);

        mock_tx.tx_bit(1);
        mock_tx.tx_bit(1);

        #64;

        `assert_equal(dut.state, dut.STATE_IDLE, "state should be STATE_IDLE");
        `assert_equal(dut.ss_detector.state, dut.ss_detector.STATE_IDLE, "ss_detector.state should be STATE_IDLE");

        $display("END: test_invalid_start_sequence_3_pulse");
    end
    endtask

    task test_invalid_start_sequence_4_pulse;
    begin
        $display("START: test_invalid_start_sequence_4_pulse");

        `assert_equal(dut.state, dut.STATE_IDLE, "state should be STATE_IDLE");

        mock_tx.tx_set(1);
        #16;
        mock_tx.tx_set(0);

        mock_tx.tx_bit(1);
        mock_tx.tx_bit(1);
        mock_tx.tx_bit(1);

        #64;

        `assert_equal(dut.state, dut.STATE_IDLE, "state should be STATE_IDLE");
        `assert_equal(dut.ss_detector.state, dut.ss_detector.STATE_IDLE, "ss_detector.state should be STATE_IDLE");

        $display("END: test_invalid_start_sequence_4_pulse");
    end
    endtask

    task test_invalid_start_sequence_code_violation_first_half;
    begin
        $display("START: test_invalid_start_sequence_code_violation_first_half");

        `assert_equal(dut.state, dut.STATE_IDLE, "state should be STATE_IDLE");

        mock_tx.tx_set(1);
        #16;
        mock_tx.tx_set(0);

        mock_tx.tx_bit(1);
        mock_tx.tx_bit(1);
        mock_tx.tx_bit(1);
        mock_tx.tx_bit(1);

        #64;

        `assert_equal(dut.state, dut.STATE_IDLE, "state should be STATE_IDLE");
        `assert_equal(dut.ss_detector.state, dut.ss_detector.STATE_IDLE, "ss_detector.state should be STATE_IDLE");

        $display("END: test_invalid_start_sequence_code_violation_first_half");
    end
    endtask

    task test_invalid_start_sequence_code_violation_second_half;
    begin
        $display("START: test_invalid_start_sequence_code_violation_second_half");

        `assert_equal(dut.state, dut.STATE_IDLE, "state should be STATE_IDLE");

        mock_tx.tx_set(1);
        #16;
        mock_tx.tx_set(0);

        mock_tx.tx_bit(1);
        mock_tx.tx_bit(1);
        mock_tx.tx_bit(1);
        mock_tx.tx_bit(1);
        mock_tx.tx_bit(1);

        mock_tx.tx_set(0);
        #24;
        mock_tx.tx_set(1);

        #64;

        `assert_equal(dut.state, dut.STATE_IDLE, "state should be STATE_IDLE");
        `assert_equal(dut.ss_detector.state, dut.ss_detector.STATE_IDLE, "ss_detector.state should be STATE_IDLE");

        mock_tx.tx_set(0);

        $display("END: test_invalid_start_sequence_code_violation_second_half");
    end
    endtask

    task test_invalid_sync_bit;
    begin
        $display("START: test_invalid_sync_bit");

        `assert_equal(dut.state, dut.STATE_IDLE, "state should be STATE_IDLE");

        mock_tx.tx_start_sequence;

        mock_tx.tx_set(0);

        #64;

        `assert_equal(dut.state, dut.STATE_IDLE, "state should be STATE_IDLE");
        `assert_equal(dut.ss_detector.state, dut.ss_detector.STATE_IDLE, "ss_detector.state should be STATE_IDLE");

        $display("END: test_invalid_sync_bit");
    end
    endtask

    task test_loss_of_mid_bit_transition_error_data_bit_1;
    begin
        $display("START: test_loss_of_mid_bit_transition_error_data_bit_1");

        `assert_equal(dut.state, dut.STATE_IDLE, "state should be STATE_IDLE");

        mock_tx.tx_start_sequence;
        mock_tx.tx_bit(1); // SYNC_BIT

        #64;

        `assert_equal(dut.state, dut.STATE_ERROR, "State should be STATE_ERROR");

        `assert_high(dut.error, "error should be HIGH");
        `assert_equal(dut.data, dut.ERROR_LOSS_OF_MID_BIT_TRANSITION, "data should be ERROR_LOSS_OF_MID_BIT_TRANSITION");

        dut_reset;

        #16;

        `assert_equal(dut.state, dut.STATE_IDLE, "state should be STATE_IDLE");

        $display("END: test_loss_of_mid_bit_transition_error_data_bit_1");
    end
    endtask

    task test_loss_of_mid_bit_transition_error_data_bit_5;
    begin
        $display("START: test_loss_of_mid_bit_transition_error_data_bit_5");

        `assert_equal(dut.state, dut.STATE_IDLE, "state should be STATE_IDLE");

        mock_tx.tx_start_sequence;
        mock_tx.tx_bit(1); // SYNC_BIT
        mock_tx.tx_bit(0); // MSB DATA_BIT
        mock_tx.tx_bit(1);
        mock_tx.tx_bit(1);
        mock_tx.tx_bit(0);
        mock_tx.tx_bit(1);

        #64;

        `assert_equal(dut.state, dut.STATE_ERROR, "State should be STATE_ERROR");

        `assert_high(dut.error, "error should be HIGH");
        `assert_equal(dut.data, dut.ERROR_LOSS_OF_MID_BIT_TRANSITION, "data should be ERROR_LOSS_OF_MID_BIT_TRANSITION");

        dut_reset;

        #16;

        `assert_equal(dut.state, dut.STATE_IDLE, "state should be STATE_IDLE");

        $display("END: test_loss_of_mid_bit_transition_error_data_bit_5");
    end
    endtask

    task test_loss_of_mid_bit_transition_error_parity_bit;
    begin
        $display("START: test_loss_of_mid_bit_transition_error_parity_bit");

        `assert_equal(dut.state, dut.STATE_IDLE, "state should be STATE_IDLE");

        mock_tx.tx_start_sequence;
        mock_tx.tx_bit(1); // SYNC_BIT
        mock_tx.tx_bit(0); // MSB DATA_BIT
        mock_tx.tx_bit(1);
        mock_tx.tx_bit(1);
        mock_tx.tx_bit(0);
        mock_tx.tx_bit(1);
        mock_tx.tx_bit(1);
        mock_tx.tx_bit(0);
        mock_tx.tx_bit(0);
        mock_tx.tx_bit(1);
        mock_tx.tx_bit(1); // LSB DATA_BIT

        #64;

        `assert_equal(dut.state, dut.STATE_ERROR, "State should be STATE_ERROR");

        `assert_high(dut.error, "error should be HIGH");
        `assert_equal(dut.data, dut.ERROR_LOSS_OF_MID_BIT_TRANSITION, "data should be ERROR_LOSS_OF_MID_BIT_TRANSITION");

        dut_reset;

        #16;

        `assert_equal(dut.state, dut.STATE_IDLE, "state should be STATE_IDLE");

        $display("END: test_loss_of_mid_bit_transition_error_parity_bit");
    end
    endtask

    task test_parity_error;
    begin
        $display("START: test_parity_error");

        `assert_equal(dut.state, dut.STATE_IDLE, "state should be STATE_IDLE");

        mock_tx.tx_start_sequence;
        mock_tx.tx_bit(1); // SYNC_BIT
        mock_tx.tx_bit(0); // MSB DATA_BIT
        mock_tx.tx_bit(1);
        mock_tx.tx_bit(1);
        mock_tx.tx_bit(0);
        mock_tx.tx_bit(1);
        mock_tx.tx_bit(1);
        mock_tx.tx_bit(0);
        mock_tx.tx_bit(0);
        mock_tx.tx_bit(1);
        mock_tx.tx_bit(1); // LSB DATA_BIT
        mock_tx.tx_bit(0); // PARITY_BIT

        #64;

        `assert_equal(dut.state, dut.STATE_ERROR, "State should be STATE_ERROR");

        `assert_high(dut.error, "error should be HIGH");
        `assert_equal(dut.data, dut.ERROR_PARITY, "data should be ERROR_PARITY");

        dut_reset;

        #16;

        `assert_equal(dut.state, dut.STATE_IDLE, "state should be STATE_IDLE");

        $display("END: test_parity_error");
    end
    endtask

    task test_loss_of_mid_bit_transition_error_sync_end_bit;
    begin
        $display("START: test_loss_of_mid_bit_transition_error_sync_end_bit");

        `assert_equal(dut.state, dut.STATE_IDLE, "state should be STATE_IDLE");

        mock_tx.tx_start_sequence;
        mock_tx.tx_bit(1); // SYNC_BIT
        mock_tx.tx_bit(0); // MSB DATA_BIT
        mock_tx.tx_bit(1);
        mock_tx.tx_bit(1);
        mock_tx.tx_bit(0);
        mock_tx.tx_bit(1);
        mock_tx.tx_bit(1);
        mock_tx.tx_bit(0);
        mock_tx.tx_bit(0);
        mock_tx.tx_bit(1);
        mock_tx.tx_bit(1); // LSB DATA_BIT
        mock_tx.tx_bit(1); // PARITY_BIT

        #64;

        `assert_equal(dut.state, dut.STATE_ERROR, "State should be STATE_ERROR");

        `assert_high(dut.error, "error should be HIGH");
        `assert_equal(dut.data, dut.ERROR_LOSS_OF_MID_BIT_TRANSITION, "data should be ERROR_LOSS_OF_MID_BIT_TRANSITION");

        dut_reset;

        #16;

        `assert_equal(dut.state, dut.STATE_IDLE, "state should be STATE_IDLE");

        $display("END: test_loss_of_mid_bit_transition_error_sync_end_bit");
    end
    endtask

    task test_invalid_end_sequence;
    begin
        $display("START: test_invalid_end_sequence");

        `assert_equal(dut.state, dut.STATE_IDLE, "state should be STATE_IDLE");

        mock_tx.tx_start_sequence;
        mock_tx.tx_bit(1); // SYNC_BIT
        mock_tx.tx_bit(0); // MSB DATA_BIT
        mock_tx.tx_bit(1);
        mock_tx.tx_bit(1);
        mock_tx.tx_bit(0);
        mock_tx.tx_bit(1);
        mock_tx.tx_bit(1);
        mock_tx.tx_bit(0);
        mock_tx.tx_bit(0);
        mock_tx.tx_bit(1);
        mock_tx.tx_bit(1); // LSB DATA_BIT
        mock_tx.tx_bit(1); // PARITY_BIT
        mock_tx.tx_bit(0);

        #64;

        `assert_equal(dut.state, dut.STATE_ERROR, "State should be STATE_ERROR");

        `assert_high(dut.error, "error should be HIGH");
        `assert_equal(dut.data, dut.ERROR_INVALID_END_SEQUENCE, "data should be INVALID_END_SEQUENCE_STATE_ERROR");

        dut_reset;

        #16;

        `assert_equal(dut.state, dut.STATE_IDLE, "state should be STATE_IDLE");

        $display("END: test_invalid_end_sequence");
    end
    endtask

    task test_data;
    begin
        $display("START: test_data");

        `assert_equal(dut.state, dut.STATE_IDLE, "state should be STATE_IDLE");

        mock_tx.tx_start_sequence;
        mock_tx.tx_bit(1); // SYNC_BIT
        mock_tx.tx_bit(0); // MSB DATA_BIT
        mock_tx.tx_bit(1);
        mock_tx.tx_bit(1);
        mock_tx.tx_bit(0);
        mock_tx.tx_bit(1);
        mock_tx.tx_bit(1);
        mock_tx.tx_bit(0);
        mock_tx.tx_bit(0);
        mock_tx.tx_bit(1);
        mock_tx.tx_bit(1); // LSB DATA_BIT
        mock_tx.tx_bit(1); // PARITY_BIT
        mock_tx.tx_end_sequence;

        #64;

        `assert_equal(dut.state, dut.STATE_IDLE, "state should be STATE_IDLE");

        `assert_equal(dut.data, 10'b0110110011, "data not correct")

        $display("END: test_data");
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
