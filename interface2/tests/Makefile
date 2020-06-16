IVERILOG ?= iverilog
VVP ?= vvp

RTL = ../rtl

all: coax_rx_bit_timer_tb.vcd

coax_rx_bit_timer_tb: coax_rx_bit_timer_tb.v $(RTL)/coax_rx_bit_timer.v

clean:
	rm -f *_tb *.vcd

%_tb:
	$(IVERILOG) -o $@ $^

%_tb.vcd: %_tb
	$(VVP) -N $<

.PHONY: all, clean
