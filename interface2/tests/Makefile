IVERILOG ?= iverilog
VVP ?= vvp

RTL = ../rtl

all: coax_tx_tb.vcd

coax_tx_tb: coax_tx_tb.v $(RTL)/coax_tx.v

clean:
	rm -f *_tb *.vcd

%_tb:
	$(IVERILOG) -o $@ $^

%_tb.vcd: %_tb
	$(VVP) -N $< -lxt2

.PHONY: all, clean
