IVERILOG ?= iverilog
VVP ?= vvp

RTL = ../rtl

all: coax_tx_bit_timer_tb.vcd coax_tx_tb.vcd coax_tx_distorter_tb.vcd coax_rx_bit_timer_tb.vcd coax_rx_tb.vcd

coax_tx_bit_timer_tb: coax_tx_bit_timer_tb.v $(RTL)/coax_tx_bit_timer.v
coax_tx_tb: coax_tx_tb.v $(RTL)/coax_tx.v $(RTL)/coax_tx_bit_timer.v
coax_tx_distorter_tb: coax_tx_distorter_tb.v $(RTL)/coax_tx_distorter.v
coax_rx_bit_timer_tb: coax_rx_bit_timer_tb.v $(RTL)/coax_rx_bit_timer.v
coax_rx_tb: coax_rx_tb.v $(RTL)/coax_rx.v $(RTL)/coax_rx_bit_timer.v

clean:
	rm -f *_tb *.vcd

%_tb:
	$(IVERILOG) -o $@ $^

%_tb.vcd: %_tb
	$(VVP) -N $<

.PHONY: all, clean
