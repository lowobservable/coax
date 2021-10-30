IVERILOG ?= iverilog

RTL = ../rtl
TESTS = $(patsubst %.v,%,$(wildcard *_tb.v))

all: test

coax_buffer_tb: coax_buffer_tb.v $(RTL)/coax_buffer.v $(RTL)/third_party/*.v
coax_buffered_rx_tb: coax_buffered_rx_tb.v $(RTL)/coax_buffered_rx.v $(RTL)/coax_rx.v $(RTL)/coax_rx_ss_detector.v $(RTL)/coax_buffer.v $(RTL)/third_party/*.v
coax_buffered_tx_tb: coax_buffered_tx_tb.v $(RTL)/coax_buffered_tx.v $(RTL)/coax_tx.v $(RTL)/coax_tx_bit_timer.v $(RTL)/coax_buffer.v $(RTL)/third_party/*.v
coax_rx_tb: coax_rx_tb.v $(RTL)/coax_rx.v $(RTL)/coax_rx_ss_detector.v
coax_tx_bit_timer_tb: coax_tx_bit_timer_tb.v $(RTL)/coax_tx_bit_timer.v
coax_tx_distorter_tb: coax_tx_distorter_tb.v $(RTL)/coax_tx_distorter.v
coax_tx_tb: coax_tx_tb.v $(RTL)/coax_tx.v $(RTL)/coax_tx_bit_timer.v
coax_rx_blanker_tb: coax_rx_blanker_tb.v $(RTL)/coax_rx_blanker.v
coax_tx_rx_frontend_tb: coax_tx_rx_frontend_tb.v $(RTL)/coax_tx_rx_frontend.v $(RTL)/coax_tx_distorter.v $(RTL)/coax_rx_blanker.v
control_tb: control_tb.v $(RTL)/control.v $(RTL)/coax_buffered_tx.v $(RTL)/coax_tx.v $(RTL)/coax_tx_bit_timer.v $(RTL)/coax_buffer.v $(RTL)/third_party/*.v
regression_memorex_tb: regression_memorex_tb.v $(RTL)/coax_rx.v $(RTL)/coax_rx_ss_detector.v

test: $(TESTS)
	./run_tests.sh

clean:
	rm -f *_tb *.vcd

%_tb:
	$(IVERILOG) -o $@ $^

.PHONY: all, clean
